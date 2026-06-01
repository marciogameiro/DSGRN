### MorseGraph.py
### MIT LICENSE 2024 Marcio Gameiro

import pychomp
from collections import defaultdict

def MorseGraph(stg, scc_dag, graded_complex, connection_matrix, prune_grad=True):
    """Construct the Morse graph"""

    def nontrivial_scc(v):
        """Check if the SCC with grading v is nontrivial"""
        if v == fringe_node_grade:
            return False
        if v in conley_indices:
            return True
        # Get set of cells in the SCC with grading v
        scc_v = grading_cells[v]
        # If prune_gradient is False check for multiple cells or self edge in SCC
        if not prune_grad:
            return len(scc_v) > 1 or any(c in stg.digraph.adjacencies(c) for c in scc_v)
        # Check if there are common gradient directions
        common_grad_dirs = set()
        for cell in scc_v:
            # Get gradient directions for cell
            cc_cell = stg.blowup2cubical(cell)
            grad_dirs = stg.gradient_directions(cc_cell)
            # Initialize common_grad_dirs
            if not common_grad_dirs:
                common_grad_dirs.update(grad_dirs)
            # Intersect with previous gradient directions
            common_grad_dirs.intersection_update(grad_dirs)
            # Nontrivial if no common gradient directions
            if not common_grad_dirs:
                return True
        return False

    def vertex_rank(v):
        """Return how many levels down of descendents of v there are"""
        # Use the dictionary if available
        if v in morse_graph_vert_ranks:
            return morse_graph_vert_ranks[v]
        if not descendant_lists[v]:
            return 0
        return max([vertex_rank(u) for u in descendant_lists[v]]) + 1

    def vertex_label(v):
        """Vertex label for Morse graph"""
        # return str(vertex_indices[v]) + " : " + str(tuple(conley_indices[v]))
        return [vertex_indices[v], num_cells[v], tuple(conley_indices[v])]

    # Get the grading value for fringe cells
    fringe_node_grade = graded_complex.value(stg.complex().size() - 1)
    # Get sets of cells with the same grading (same SCC)
    grading_cells = defaultdict(set)
    for cell in stg.digraph.vertices():
        val = graded_complex.value(cell)
        if val == fringe_node_grade:
            continue
        grading_cells[val].add(cell)
    # Get the cell complex dimension
    dim = graded_complex.complex().dimension()
    # Get the nontrivial Conley indices
    conley_indices = connection_matrix.count()
    # Get the Morse graph vertices
    morse_graph_verts = set([v for v in scc_dag.vertices() if nontrivial_scc(v)])
    # Update conley_indices with the trivial Conley indices
    for v in morse_graph_verts:
        if v not in conley_indices:
            conley_indices[v] = [0] * (dim + 1)
    # Get strict descendants of Morse graph vertices
    descendant_lists = {}
    for v in morse_graph_verts:
        descendant_lists[v] = {u for u in scc_dag.descendants(v) if u in morse_graph_verts and u != v}
    # Get a sorted list Morse graph vertices
    sorted_vertices = sorted(morse_graph_verts)
    # # Further sort Morse graph vertices by number of descendants
    # sorted_vertices.sort(key=lambda v: len(descendant_lists[v]))
    # Create a dictionary of vertices ranks
    morse_graph_vert_ranks = {}
    # Add the ranks to the dictionary
    for v in sorted_vertices:
        morse_graph_vert_ranks[v] = vertex_rank(v)
    # Finally sort Morse graph vertices by rank
    sorted_vertices.sort(key=lambda v: morse_graph_vert_ranks[v])
    # Make an indexing of the Morse graph vertices
    vertex_indices = {v: k for k, v in enumerate(sorted_vertices)}
    # Get the number of top dimensinal cells for each Morse graph vertex
    num_cells = {v: graded_complex.count()[v][-1] for v in sorted_vertices}
    # Define the Morse graph
    morse_graph = pychomp.DirectedAcyclicGraph()
    # Add vertices and edges
    for v in sorted_vertices:
        morse_graph.add_vertex(v, label=vertex_label(v))
    for v in sorted_vertices:
        for u in descendant_lists[v]:
            morse_graph.add_edge(v, u)
    # Morse graph is the transitive reduction of morse_graph
    return morse_graph.transitive_reduction()
