# MorseGraphIsomorphism.py
### MIT LICENSE 2021 Marcio Gameiro
#
# Marcio Gameiro
# 2024-12-08

import networkx as nx

def get_vertex_ranks(morse_graph, num_descendants):
    """Create a dictionary of vertex ranks (number of levels down of descendants)."""

    def vertex_rank(v):
        """Return how many levels down of descendants of v there are"""
        # Use the dictionary if available
        if v in vertex_ranks:
            return vertex_ranks[v]
        if num_descendants[v] == 0:
            return 0
        return max([vertex_rank(u) for u in morse_graph.adjacencies(v)]) + 1

    # Sort vertices by number of descendants
    sorted_vertices = sorted(morse_graph.vertices(), key=lambda v: num_descendants[v])
    # Create a dictionary of vertex ranks
    vertex_ranks = {}
    for v in sorted_vertices:
        vertex_ranks[v] = vertex_rank(v)
    return vertex_ranks

def is_isomorphism(mg1, mg2, vertices1, vertices2, vert_labels1, vert_labels2):
    """Check if the sorted vertices give an isomorphism between the two graphs."""
    # Create indexing of vertices in each graph
    vert_indices1 = {v: k for k, v in enumerate(vertices1)}
    vert_indices2 = {v: k for k, v in enumerate(vertices2)}
    for v1, v2 in zip(vertices1, vertices2):
        if vert_labels1[v1] != vert_labels2[v2]:
            return False
        adjacencies_v1 = sorted([vert_indices1[v] for v in mg1.adjacencies(v1)])
        adjacencies_v2 = sorted([vert_indices2[v] for v in mg2.adjacencies(v2)])
        if adjacencies_v1 != adjacencies_v2:
            return False
    return True

def isomorphic_morse_graphs(mg1, mg2):
    """Check if two (Morse) graphs are isomorphic"""
    # First check global properties of the graphs
    # Check if number of vertices and edges match
    if len(mg1.vertices()) != len(mg2.vertices()):
        return False
    if len(mg1.edges()) != len(mg2.edges()):
        return False
    # Check if the number of attractors match
    attractors1 = [v for v in mg1.vertices() if not mg1.adjacencies(v)]
    attractors2 = [v for v in mg2.vertices() if not mg2.adjacencies(v)]
    if len(attractors1) != len(attractors2):
        return False
    # Get local properties of vertices for each graph
    # Get number of strict descendants of each vertex
    num_descendants1 = {v: len(mg1.descendants(v)) - 1 for v in mg1.vertices()}
    num_descendants2 = {v: len(mg2.descendants(v)) - 1 for v in mg2.vertices()}
    # Get vertices ranks (number of levels down of descendants)
    vert_ranks1 = get_vertex_ranks(mg1, num_descendants1)
    vert_ranks2 = get_vertex_ranks(mg2, num_descendants2)
    # Get vertices labels as strings
    vert_labels1 = {v: mg1.vertex_label(v).split(':')[1].strip() for v in mg1.vertices()}
    vert_labels2 = {v: mg2.vertex_label(v).split(':')[1].strip() for v in mg2.vertices()}
    # Get vertices in-degrees and out-degrees
    mg1_trans = mg1.transpose()
    mg2_trans = mg2.transpose()
    in_deg1 = {v: len(mg1_trans.adjacencies(v)) for v in mg1.vertices()}
    in_deg2 = {v: len(mg2_trans.adjacencies(v)) for v in mg2.vertices()}
    out_deg1 = {v: len(mg1.adjacencies(v)) for v in mg1.vertices()}
    out_deg2 = {v: len(mg2.adjacencies(v)) for v in mg2.vertices()}
    # Get list of vertices properties for each graph
    properties1 = {}
    for v in mg1.vertices():
        properties1[v] = (vert_ranks1[v], vert_labels1[v], num_descendants1[v], in_deg1[v], out_deg1[v])
    properties2 = {}
    for v in mg2.vertices():
        properties2[v] = (vert_ranks2[v], vert_labels2[v], num_descendants2[v], in_deg2[v], out_deg2[v])
    # Check if properties agree
    if sorted(properties1.values()) != sorted(properties2.values()):
        return False
    # If we got here there is a good change that the graphs are isomorphic
    # Sort vertices into a canonical form and check if it gives an isomorphism
    vertices1 = sorted(mg1.vertices(), key=lambda v: properties1[v])
    vertices2 = sorted(mg2.vertices(), key=lambda v: properties2[v])
    # Check if the sorted vertices give an isomorphism
    if is_isomorphism(mg1, mg2, vertices1, vertices2, vert_labels1, vert_labels2):
        return True
    # Need to use networkx to decide if the graphs are isomorphic
    # Create two networkx digraphs
    G1 = nx.DiGraph()
    for v in mg1.vertices():
        G1.add_node(v, label=vert_labels1[v])
    G2 = nx.DiGraph()
    for v in mg2.vertices():
        G2.add_node(v, label=vert_labels2[v])
    for v1, v2 in mg1.edges():
        G1.add_edge(v1, v2)
    for v1, v2 in mg2.edges():
        G2.add_edge(v1, v2)
    # Check if G1 and G2 are isomorphic using networkx
    return nx.is_isomorphic(G1, G2, node_match=lambda v1, v2: v1['label'] == v2['label'])
