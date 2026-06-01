### PlotMorseSets.py
### MIT LICENSE 2024 Marcio Gameiro

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, FancyArrow
from matplotlib.collections import PatchCollection
from collections import defaultdict
import numpy as np

def PlotMorseSets(morse_graph, stg, graded_complex, morse_nodes=None, proj_dims=None, proj_slice=None,
                  cmap=None, clist=None, alpha=0.7, plot_bdry_cells=True, plot_arrows=True,
                  plot_self_arrows=True, plot_verts=True, plot_edges=True, arrow_clr='blue',
                  double_arrow_clr='red', self_arrow_clr='red', fig_w=7, fig_h=7, plot_axis=False,
                  axis_labels=True, xlabel='$x$', ylabel='$y$', fontsize=15, ax=None, fig_fname=None,
                  dpi=300):
    """Plot Morse sets and the state transition graph"""
    # Cells line width
    line_width = 2
    # Cells edge color
    edge_clr = 'black' if plot_edges else 'none'
    # Arrow line width
    arrow_line_width = 1.5
    # Vertex size
    vert_size = 0.02
    # Centroid (equilibrium) size
    center_size = 0.06
    # Cells minimum width
    cell_width = 0.5
    # Arrow size factor
    arrow_size_factor = 0.6
    # Flag to save figure or not (do not save figure if ax is given)
    save_fig = True if (ax is None and fig_fname is not None) else False

    # Default colormap
    # default_cmap = matplotlib.cm.cool
    # Default color list
    default_clist = ['#1f77b4', '#e6550d', '#31a354', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                     '#bcbd22', '#80b1d3', '#ffffb3', '#fccde5', '#b3de69', '#fdae6b', '#6a3d9a', '#c49c94',
                     '#fb8072', '#dbdb8d', '#bc80bd', '#ffed6f', '#637939', '#c5b0d5', '#636363', '#c7c7c7',
                     '#8dd3c7', '#b15928', '#e8cb32', '#9e9ac8', '#74c476', '#ff7f0e', '#9edae5', '#90d743',
                     '#e7969c', '#17becf', '#7b4173', '#8ca252', '#ad494a', '#8c6d31', '#a55194', '#00cc49']
    # Default color list (old)
    # default_clist = ['#fb8072', '#31a354', '#80b1d3', '#9467bd', '#e6550d', '#8c564b', '#ffed6f', '#7f7f7f',
    #                  '#1f77b4', '#fdae6b', '#b3de69', '#d62728', '#ffffb3', '#e377c2', '#c49c94', '#bcbd22',
    #                  '#fccde5', '#dbdb8d', '#bc80bd', '#636363', '#637939', '#c5b0d5', '#6a3d9a', '#c7c7c7',
    #                  '#8dd3c7', '#b15928', '#e8cb32', '#9e9ac8', '#74c476', '#ff7f0e', '#9edae5', '#90d743',
    #                  '#e7969c', '#17becf', '#7b4173', '#8ca252', '#ad494a', '#8c6d31', '#a55194', '#00cc49']

    def fringe_cell(cell):
        """Check if a cell is a fringe cell"""
        return cell_complex.rightfringe(cell)

    def boundary_cell(cell):
        """Check if a cell is a boundary cell"""
        # Fringe cells are not boundary cells
        if fringe_cell(cell):
            return False
        # A vertex is boundary if any of its star is a fringe cell
        if cell_complex.cell_dim(cell) == 0:
            return any(cell_complex.rightfringe(c) for c in cell_complex.star({cell}))
        # Other cells are boundary if any of their boundaries is a face of a fringe cell
        for cell_bdry in cell_complex.boundary({cell}):
            # It is a boundary cell if any of its boundaries is a face of a fringe cell
            if any(cell_complex.rightfringe(c) for c in cell_complex.star({cell_bdry})):
                return True
        return False

    def allowed_cell(cell):
        """Check if a top cell is allowed (to be plotted)"""
        # Fringe cells are not allowed
        if fringe_cell(cell):
            return False
        # Only plot boundary cell if plot_bdry_cells is True
        if plot_bdry_cells or not boundary_cell(cell):
            return True
        return False

    def in_projection_slice(coords):
        """Check if cell is in correct slice if a projection slice is given"""
        if proj_slice == None:
            return True
        for k in range(dim):
            if k not in {d1, d2} and coords[k] != proj_slice[k]:
                return False
        return True

    def min_node_cell(cell1, cell2):
        """Given two cells return the one with grading corresponding to the minimal Morse
           node if they both belong to Morse sets. Return the cell belonging to a Morse
           set if only one of them is in a Morse set. Return cell1 if neither of them
           belong to Morse sets. This function is used to determine a representative of
           the set of cells with the same projection and this representative cell is
           then used to determine the face color of the projected cell."""
        # Get the gradings for both cells
        cell1_grading = graded_complex.value(cell1)
        cell2_grading = graded_complex.value(cell2)
        # Return the other cell if not a Morse graph vertex
        if cell2_grading not in vertex_indices:
            return cell1
        if cell1_grading not in vertex_indices:
            return cell2
        # Return the other cell if not in list of Morse nodes
        if vertex_indices[cell2_grading] not in morse_nodes:
            return cell1
        if vertex_indices[cell1_grading] not in morse_nodes:
            return cell2
        # Return the cell corresponding to the minimal Morse node
        if vertex_indices[cell1_grading] < vertex_indices[cell2_grading]:
            return cell1
        return cell2

    def face_color(cell_grading):
        """Return face color"""
        # Color white if not a Morse graph vertex
        if cell_grading not in vertex_indices:
            return 'white'
        # Color white if not in list of Morse nodes
        if vertex_indices[cell_grading] not in morse_nodes:
            return 'white'
        # Get face color from colormap
        clr = cmap(cmap_norm(vertex_indices[cell_grading]))
        # Set the alpha value if the variable alpha is given
        # If alpha is None keep the alpha from the colormap
        # Defaults to 1 if no alpha is set in the colormap
        if alpha is not None:
            # Set the alpha value for color
            clr = matplotlib.colors.to_rgb(clr) + (alpha,)
        clr_hex = matplotlib.colors.to_hex(clr, keep_alpha=True)
        return str(clr_hex)

    def real_coord(k):
        """Return a real value for a cell coordinate"""
        # real_coord = lambda k: ((3 * k) // 2) * cell_width
        # This will return values such that the cell widths
        # alternate between cell_width and 2 * cell_width
        return ((3 * k) // 2) * cell_width

    def cell_vertices(cell):
        """Get real coordinates for the vertices of a cell"""
        # Get the cell complex coordinates of cell
        coords = cell_complex.coordinates(cell)
        # Get real coordinates for the cell vertices
        v0 = (real_coord(coords[d1]),     real_coord(coords[d2]))
        v1 = (real_coord(coords[d1] + 1), real_coord(coords[d2]))
        v2 = (real_coord(coords[d1] + 1), real_coord(coords[d2] + 1))
        v3 = (real_coord(coords[d1]),     real_coord(coords[d2] + 1))
        return [v0, v1, v2, v3]

    def cell_centroid(cell):
        """Return the cell centroid (average of vertices)"""
        # Get list of cell vertices
        cell_verts = cell_vertices(cell)
        # Centroid is the average of the cell vertices
        centroid = np.sum(cell_verts, axis=0) / len(cell_verts)
        return centroid

    def shared_face_centroid(cell1, cell2):
        """Return the centroid of the face shared by two cells"""
        # Get vertices of each cell
        cell1_verts = cell_vertices(cell1)
        cell2_verts = cell_vertices(cell2)
        # Get shared vertices
        shared_verts = set(cell1_verts).intersection(set(cell2_verts))
        # Return None if no shared vertices
        if not shared_verts:
            return None
        # Centroid is the average of the shared vertices
        centroid = np.sum(list(shared_verts), axis=0) / len(shared_verts)
        return centroid

    # Get the cell complex dimension
    dim = graded_complex.complex().dimension()
    # Number of Morse sets
    num_morse_sets = len(morse_graph.vertices())
    # Get list of Morse nodes to plot if not given
    if morse_nodes == None:
        morse_nodes = range(num_morse_sets)
    # Set colormap for Morse sets
    if cmap == None and clist == None:
        clist = default_clist
    if cmap == None:
        cmap = matplotlib.colors.ListedColormap(clist[:num_morse_sets])
    # Get number of colors in the colormap
    try:
        # Colormap is listed colors colormap
        num_colors = len(cmap.colors)
    except:
        num_colors = 0 # Colormap is "continuous"
    if (num_colors > 0) and (num_colors < num_morse_sets):
        # Make colormap cyclic
        cmap_norm = lambda k: k % num_colors
    else:
        # Normalization for color map
        cmap_norm = matplotlib.colors.Normalize(vmin=0, vmax=num_morse_sets-1)
    # Projection dimensions
    if proj_dims == None:
        d1 = 0
        d2 = 1
    else:
        d1 = proj_dims[0]
        d2 = proj_dims[1]
    # Make sure projection dimensions are valid
    assert max(d1, d2) < dim, "Wrong projection dimensions"
    # Make projection slice a list if it is int
    if isinstance(proj_slice, int):
        proj_slice = [proj_slice] * dim
        proj_slice[d1] = -1
        proj_slice[d2] = -1
    # Get the cubical cell complex
    cell_complex = graded_complex.complex()
    # Get indexing of the Morse graph vertices from the labels
    # vertex_index = lambda v: int(morse_graph.vertex_label(v).split(':')[0].strip())
    # vertex_indices = {v: vertex_index(v) for v in morse_graph.vertices()}
    vertex_indices = {v: morse_graph.vertex_label(v)[0] for v in morse_graph.vertices()}
    # # Collection of top cells to plot (collection of allowed top cells)
    # allowed_top_cells = set([cell for cell in cell_complex(dim) if allowed_cell(cell)])

    # Get projected cells and their adjacencies
    projected_cells = {}
    cells_adjacencies = defaultdict(set)
    cells_double_edges = defaultdict(set)
    for cell1 in cell_complex(dim):
        if not allowed_cell(cell1):
            continue
        # Get the cell complex coordinates of cell1
        coords1 = cell_complex.coordinates(cell1)
        # Check if cell1 is in correct slice
        if not in_projection_slice(coords1):
            continue
        # Get projected coordinates of cell1
        proj_coords1 = (coords1[d1], coords1[d2])
        # Get the representative cell associated to the projected coordinates
        cell2 = projected_cells[proj_coords1] if proj_coords1 in projected_cells else cell1
        # Update representative cell with the minimal node cell
        projected_cells[proj_coords1] = min_node_cell(cell1, cell2)
        # Get adjacencies of cell1 in the STG
        for cell2 in stg.digraph.adjacencies(cell1):
            if not allowed_cell(cell2):
                continue
            # Get the cell complex coordinates of cell2
            coords2 = cell_complex.coordinates(cell2)
            # Check if cell2 is in correct slice
            if not in_projection_slice(coords2):
                continue
            # Get projected coordinates of cell2
            proj_coords2 = (coords2[d1], coords2[d2])
            # Skip cell if same projection but not self edge
            if proj_coords1 == proj_coords2 and cell1 != cell2:
                continue
            # Add cell2 to the list of adjacencies
            cells_adjacencies[proj_coords1].add(proj_coords2)
            # Check if it is a double edges and add to list
            if cell1 in stg.digraph.adjacencies(cell2):
                cells_double_edges[proj_coords1].add(proj_coords2)

    # Make polygon patches for dim 2 and get the set of cell vertices
    polygon_patches = [[], []]
    cell_complex_vertices = set()
    # Loop through projected top cells
    for proj_coords in projected_cells:
        # Get representative cell
        cell = projected_cells[proj_coords]
        # Get cell vertices
        cell_verts = cell_vertices(cell)
        # Get the cell grading
        cell_grading = graded_complex.value(cell)
        # Get face as a tuple of vertices
        cell_face = tuple(cell_verts)
        # Get the face color
        face_clr = face_color(cell_grading)
        # Add vertices to the set of cell complex vertices
        cell_complex_vertices.update(cell_verts)
        # Plot face as a polygon and add to polygon patches
        polygon = Polygon(cell_face, fc=face_clr, ec=edge_clr, closed=True)
        polygon_patches[1].append(polygon)
    # Get polygon patches for dim 0
    for cell_v in cell_complex_vertices:
        # Plot vertex as a filled circle
        polygon = Circle(cell_v, vert_size, fc='black', ec='black')
        polygon_patches[0].append(polygon)

    # Plot STG arrows and centroids of equilibrium cells.
    # If plot_arrows and plot_self_arrows are both false it is
    # not necessary to run this portion of the code, but we will
    # keep it like this for now (these flags are honored below)
    centroid_patches = []
    arrow_patches = []
    # Loop through projected top cells
    for proj_coords1 in projected_cells:
        # Get representative cell
        cell1 = projected_cells[proj_coords1]
        # Get cell1 centroid
        cell1_center = cell_centroid(cell1)
        # Plot centroid as a filled circle if self edge
        if proj_coords1 in cells_adjacencies[proj_coords1]:
            polygon = Circle(cell1_center, center_size, fc=self_arrow_clr, ec='black')
            centroid_patches.append(polygon)
        # Plot STG edges as arrows
        for proj_coords2 in cells_adjacencies[proj_coords1]:
            # Get representative cell
            cell2 = projected_cells[proj_coords2]
            # Skip self edges
            if proj_coords2 == proj_coords1:
                continue
            # Get cell2 centroid
            cell2_center = cell_centroid(cell2)
            # Get shared face centroid
            face_center = shared_face_centroid(cell1, cell2)
            # The maximum allowed arrow half size is the minimum of the
            # distances from face_center to cell1_center and cell2_center
            dist1 = np.linalg.norm(np.array(cell1_center) - np.array(face_center))
            dist2 = np.linalg.norm(np.array(cell2_center) - np.array(face_center))
            # Maximum allowed arrow half size
            max_arrow_size = min(dist1, dist2)
            # Get a unit vector in the direction of the arrow
            dir_vec = np.array(cell2_center) - np.array(cell1_center)
            dir_vec = dir_vec / np.linalg.norm(dir_vec)
            # The arrow tail (head) is the shared face center minus (plus)
            # a fraction of max_arrow_size in the direction of the arrow
            arrow_tail = np.array(face_center) - arrow_size_factor * max_arrow_size * dir_vec
            arrow_head = np.array(face_center) + arrow_size_factor * max_arrow_size * dir_vec
            # Get the arrow coordinates
            x, dx = arrow_tail[0], arrow_head[0] - arrow_tail[0]
            y, dy = arrow_tail[1], arrow_head[1] - arrow_tail[1]
            # Get arrow color (use double_arrow_clr if double arrow)
            arr_clr = double_arrow_clr if proj_coords2 in cells_double_edges[proj_coords1] else arrow_clr
            # Plot arrow (STG edge)
            arrow = FancyArrow(x, y, dx, dy, head_width=0.1, head_length=0.1, overhang=0.5,
                               fc=arr_clr, ec=arr_clr, length_includes_head=True)
            arrow_patches.append(arrow)

    # Create patchs collections for dims 0 and 2
    if plot_verts:
        p0 = PatchCollection(polygon_patches[0], match_original=True)
    p2 = PatchCollection(polygon_patches[1], match_original=True)
    if plot_self_arrows:
        # Create patch collection of centroids and set properties
        pc = PatchCollection(centroid_patches, match_original=True)
        pc.set_linewidths(line_width)
    if plot_arrows:
        # Create patch collection of arrows and set properties
        pa = PatchCollection(arrow_patches, match_original=True)
        pa.set_linewidths(arrow_line_width)
    # Set patch properties
    p2.set_linewidths(line_width)
    # Create figure axis if ax is None
    if ax == None:
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    # Add collections to the axis
    ax.add_collection(p2)
    if plot_verts:
        ax.add_collection(p0)
    if plot_self_arrows:
        ax.add_collection(pc)
    if plot_arrows:
        ax.add_collection(pa)
    # Add axis labels
    if axis_labels:
        ax.set_xlabel(xlabel, fontsize=fontsize)
        ax.set_ylabel(ylabel, fontsize=fontsize)
    # Set tick labels size
    ax.tick_params(labelsize=fontsize)
    # Set aspect ratio
    ax.set_aspect('equal')
    # ax.set_aspect('auto')
    # Auto scale axis
    ax.autoscale_view()
    # Axis is on by default
    if not plot_axis:
        ax.axis('off')
    if save_fig:
        fig.savefig(fig_fname, dpi=dpi, bbox_inches='tight')
    # plt.show()
    # return ax
