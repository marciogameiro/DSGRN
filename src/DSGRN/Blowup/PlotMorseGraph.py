### PlotMorseGraph.py
### MIT LICENSE 2024 Marcio Gameiro

import matplotlib
import graphviz

def PlotMorseGraph(morse_graph, cmap=None, clist=None, alpha=0.7, shape=None, margin=None, label='c'):
    """Plot Morse graph using cmap as the colormap or clist as a list of colors"""
 
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

    # Check if input argument label is valid
    labels = {s.strip() for s in label.split(':')}
    if not labels.issubset({'size', 'cindex', 'annotation', 's', 'c', 'a', ''}):
        raise ValueError('Invalid input label string')
    # Number of vertices
    num_verts = len(morse_graph.vertices())
    # Set colormap for Morse graph
    if cmap == None and clist == None:
        clist = default_clist
    if cmap == None:
        cmap = matplotlib.colors.ListedColormap(clist[:num_verts])
    # Get number of colors in the colormap
    try:
        # Colormap is listed colors colormap
        num_colors = len(cmap.colors)
    except:
        num_colors = 0 # Colormap is "continuous"
    if (num_colors > 0) and (num_colors < num_verts):
        # Make colormap cyclic
        cmap_norm = lambda k: k % num_colors
    else:
        # Normalization for color map
        cmap_norm = matplotlib.colors.Normalize(vmin=0, vmax=num_verts-1)
    # Set default values for graphviz
    if shape == None:
        shape = 'ellipse'
    if margin == None:
        margin = '0.0, 0.04'
        # margin = '0.11, 0.055'
    margin = str(margin)
    # Get indexing of the Morse graph vertices from the labels
    # vertex_index = lambda v: int(morse_graph.vertex_label(v).split(':')[0].strip())
    # vertex_indices = {v: vertex_index(v) for v in morse_graph.vertices()}
    vertex_indices = {v: morse_graph.vertex_label(v)[0] for v in morse_graph.vertices()}
    # Get list of attractors (nodes without children)
    attractors = [v for v in morse_graph.vertices() if len(morse_graph.adjacencies(v)) == 0]

    def graphviz_string(graph):
        """Return graphviz string describing the graph"""

        def annotation(conley_index):
            """Return annotation for Conley index"""
            # Check if index is trivial
            if not any(conley_index):
                return 'T'
            # Check if all zeros and ones
            if all(b in (0, 1) for b in conley_index):
                # Count number of ones
                num_ones = conley_index.count(1)
                # Check if index of a fixed point
                if num_ones == 1:
                    return 'FP'
                # If here, there is at least one 1
                index_first_one = conley_index.index(1)
                # Check if index of a periodic orbit
                if num_ones == 2 and conley_index[index_first_one + 1] == 1:
                    return 'PO'
            # More complex invariant set
            return 'M'

        def vertex_label(v):
            """Return vertex label"""
            # return graph.vertex_label(v)
            v_label = str(graph.vertex_label(v)[0])
            if 's' in labels or 'size' in labels:
                v_label += ' : ' + str(graph.vertex_label(v)[1])
            if 'c' in labels or 'cindex' in labels:
                v_label += ' : ' + str(graph.vertex_label(v)[2])
            if 'a' in labels or 'annotation' in labels:
                conley_index = graph.vertex_label(v)[2]
                annot = annotation(conley_index)
                v_label += ' : ' + annot + '(' + str(graph.vertex_label(v)[1]) + ')'
            return v_label

        def vertex_color(v):
            """Return vertex color"""
            # Get vertex color from colormap
            clr = cmap(cmap_norm(vertex_indices[v]))
            # Set the alpha value if the variable alpha is given
            # If alpha is None keep the alpha from the colormap
            # Defaults to 1 if no alpha is set in the colormap
            if alpha is not None:
                # Set the alpha value for color
                clr = matplotlib.colors.to_rgb(clr) + (alpha,)
            clr_hex = matplotlib.colors.to_hex(clr, keep_alpha=True)
            return str(clr_hex)

        # Make graphviz string
        gv = 'digraph {\n'
        for v in graph.vertices():
            gv += str(v) + ' [label="' + vertex_label(v) + '"' + (
                ', shape=' + shape + ', style=filled, fillcolor="' + vertex_color(v) +
                '", margin="' + margin + '"];\n')
        # Set rank for attractors
        gv += '{rank=same; '
        for v in attractors:
            gv += str(v) + ' '
        gv += '}; \n'
        # Set the graph edges
        for u in graph.vertices():
            for v in graph.adjacencies(u):
                gv += str(u) + ' -> ' + str(v) + ';\n'
        gv += '}\n' # Close bracket
        return gv

    gv = graphviz_string(morse_graph) # Get graphviz string
    return graphviz.Source(gv) # Return graphviz render
