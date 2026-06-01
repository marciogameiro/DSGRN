### PlotMorseComponent.py
### MIT LICENSE 2024 Marcio Gameiro

import graphviz

def MorseComponent(morse_graph, stg, graded_complex, morse_node, blowup=True):
    """Return the subgraph of the STG corresponding to the SCC of morse_node.
    If blowup is True return cells in the blowup complex, otherwise return
    cells in the original cubical complex.
    """
    # Number of Morse sets
    num_morse_sets = len(morse_graph.vertices())
    if (morse_node < 0) or (morse_node >= num_morse_sets):
        raise ValueError('Invalid Morse graph node')
    # Get a map from Morse node indexing to Morse graph vertices
    # vertex_index = lambda v: int(morse_graph.vertex_label(v).split(':')[0].strip())
    # index2vertex = {vertex_index(v): v for v in morse_graph.vertices()}
    index2vertex = {morse_graph.vertex_label(v)[0]: v for v in morse_graph.vertices()}
    # The grading value for the Morse node
    node_grading = index2vertex[morse_node]
    # Get the cell complex dimension
    dim = graded_complex.complex().dimension()

    def cell_index(cell):
        """Return cell index"""
        if blowup:
            return cell
        return stg.blowup2cubical(cell)

    def cell_coordinates(cell):
        """Return cell coordinates"""
        if blowup:
            return graded_complex.complex().coordinates(cell)
        return stg.cubical_complex.coordinates(stg.blowup2cubical(cell))

    def cell_shape_vector(cell):
        """Return cell shape vector"""
        if blowup:
            # Only top cells for the blowup
            cell_shape_vec = [1]*dim
            return cell_shape_vec
        cubic_cell = stg.blowup2cubical(cell)
        shape = stg.cubical_complex.cell_shape(cubic_cell)
        shape_vec = [1 if (shape & (1 << d)) else 0 for d in range(dim)]
        return shape_vec

    # Get cells in the Morse set
    morse_node_cells = set()
    for cell in graded_complex.complex()(dim):
        # Skip cells with a different grading (includes fringe cells)
        if graded_complex.value(cell) != node_grading:
            continue
        morse_node_cells.add(cell)
    # Get the vertices and list of edges in the SCC, where the vertices
    # are represented by a dictionary of the form index: [coords, shape]
    morse_node_vertices = {}
    morse_node_edges = set()
    for cell1 in morse_node_cells:
        # Add vertex to dictionary
        cell1_index = cell_index(cell1)
        cell1_coord = tuple(cell_coordinates(cell1))
        cell1_shape = tuple(cell_shape_vector(cell1))
        morse_node_vertices[cell1_index] = [cell1_coord, cell1_shape]
        # Get list of adjacencies of cell1 in the SCC
        adjacencies = [c for c in stg.digraph.adjacencies(cell1) if c in morse_node_cells]
        for cell2 in adjacencies:
            cell2_index = cell_index(cell2)
            morse_node_edges.add((cell1_index, cell2_index))
    return morse_node_vertices, morse_node_edges

def PlotMorseComponent(morse_graph, stg, graded_complex, morse_node, blowup=True, label_type='cell', rankdir='TB'):
    """Plot the subgraph of the STG corresponding to the SCC of morse_node."""
    # Check that label_type is valid
    if label_type not in ['cell', 'index']:
        raise ValueError('Invalid label_type value')
    # Get Morse node component graph
    vertices, edges = MorseComponent(morse_graph, stg, graded_complex, morse_node, blowup=blowup)
    # Graphviz node shape and margin
    shape = 'ellipse'
    margin = '0.0, 0.04'
    # Make graphviz string
    gv = 'digraph {\n'
    gv += 'rankdir=' + rankdir + ';\n'
    for v in vertices:
        v_label = str(v) if (label_type == 'index') else str(vertices[v])
        gv += str(v) + ' [label="' + v_label + '", shape=' + shape + ', margin="' + margin + '"];\n'
        # gv += str(v) + ' [label="' + v_label + '", shape=' + shape + ', fontname="Arial", margin="' + margin + '"];\n'
    # Set the graph edges
    for (u, v) in edges:
        gv += str(u) + ' -> ' + str(v) + ';\n'
    gv += '}\n' # Close bracket
    return graphviz.Source(gv)
