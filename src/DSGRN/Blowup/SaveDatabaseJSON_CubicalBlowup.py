############

# Update name and stuff

# SaveDatabaseJSON_CubicalBlowup.py.py
# Marcio Gameiro
# MIT LICENSE
# 2021-03-06

import DSGRN
from pychomp import *
import DSGRN_utils
# from CubicalBlowupGraph import *
# from Poset_E import *
import itertools
import numpy as np
import json

def network_json(network):
    # Return json data for network
    nodes = []  # Get network nodes
    for d in range(network.size()):
        node = {"id": network.name(d)}
        nodes.append(node)
    # Get network edges
    edges = [(u, v) for u in range(network.size()) for v in network.outputs(u)]
    links = []
    for (u, v) in edges:
        edge_type = 1 if network.interaction(u, v) else -1
        link = {"source": network.name(u),
                "target": network.name(v),
                "type": edge_type}
        links.append(link)
    network_json_data = {"network": {"nodes": nodes, "links": links}}
    return network_json_data


def parameter_graph_json(parameter_graph, vertices=None, verts_colors=None, thres_type=None):
    # Return json data for parameter graph
    # Get list of vertices if none
    if vertices == None:
        vertices = list(range(parameter_graph.size()))
    # Set empty dictionary for verts_colors if none
    if verts_colors == None:
        verts_colors = {}
    # Set thres_type to '' if not 'T'
    if thres_type != 'T':
        thres_type = ''  # Uses the default 't' type
    all_edges = [(u, v) for u in vertices for v in parameter_graph.adjacencies(
        u, 'codim1') if v in vertices]
    # Remove double edges (all edges are double)
    edges = [(u, v) for (u, v) in all_edges if u > v]
    nodes = []
    for v in vertices:
        v_color = verts_colors[v] if v in verts_colors else ""
        v_ineqs = parameter_graph.parameter(
            v).partialorders(thres_type).split('\n')
        node = {"id": v, "color": v_color, "inequalities": v_ineqs}
        # node = {"id" : str(v), "color" : v_color, "inequalities" : v_ineqs}
        nodes.append(node)
    links = []
    for (u, v) in edges:
        link = {"source": u, "target": v}
        # link = {"source" : str(u), "target" : str(v)}
        links.append(link)
    parameter_graph_json_data = {
        "parameter_graph": {"nodes": nodes, "links": links}}
    return parameter_graph_json_data


def blowup_cc_complex_json(fc_stg):
    """Return json data for the blowup cubical complex."""

    def fringe_cell_fc(c):
        if any(fc_stg.blowup_complex.rightfringe(s) for s in fc_stg.blowup_complex.star({c})):
            return True
        for b in fc_stg.blowup_complex.boundary({c}):
            if any(fc_stg.blowup_complex.rightfringe(s) for s in fc_stg.blowup_complex.star({b})):
                return True
        return False

    # Get complex dimension
    dimension = fc_stg.dim
    # Get the blowup cubical complex.
    cubical_complex = fc_stg.blowup_complex
    # Get vertices coordinates and set a
    # mapping from coords to its index in
    # the list of coordinates.
    verts_coords = []
    coords2idx = {}
    # Get the coords of all cells of dimension 0.
    # The 0-dim cells in a cubical complex in pychomp
    # are indexed from 0 to n-1, where n is the number
    # of 0-dim cells. Hence the cell_index coincides
    # with the index of coords in the list verts_coords.
    for cell_index in cubical_complex(0):
        coords = cubical_complex.coordinates(cell_index)
        coords2idx[tuple(coords)] = cell_index
        verts_coords.append(coords)
    cells = []  # Get the cell complex data
    for cell_index in cubical_complex:
        # Ignore fringe cells
        if fringe_cell_fc(cell_index):
            continue
        # if any(cubical_complex.rightfringe(c) for c in cubical_complex.star({cell_index})):
        # if cubical_complex.rightfringe(cell_index):
        #    continue
        # Get this cell dimension
        cell_dim = cubical_complex.cell_dim(cell_index)
        # Get coords of the lower corner of the box
        coords_lower = cubical_complex.coordinates(cell_index)
        # Get index of vertex corresponding to these coords
        # Due to the way pychomp index the 0-dim cells we get
        # that idx_lower == cell_index (see coords2idx above).
        idx_lower = coords2idx[tuple(coords_lower)]
        # Get the shape of this cell (see pychomp)
        shape = cubical_complex.cell_shape(cell_index)
        # Add 1 to the appropriate entries to get coords of the upper corner
        coords_upper = [
            coords_lower[d] + (1 if shape & (1 << d) != 0 else 0) for d in range(dimension)]
        # Get index of vertex corresponding to these coords
        idx_upper = coords2idx[tuple(coords_upper)]
        # Get indices of coords that have extent
        ind_extent = [d for d in range(dimension) if shape & (1 << d) != 0]
        if cell_dim == 0:
            cell_verts = [idx_lower]
        elif cell_dim == 1:
            cell_verts = [idx_lower, idx_upper]
        elif cell_dim == 2:
            # Index of vertex 1
            idx1 = idx_lower
            # Coords and index of vertex 2
            coords_v2 = [coord for coord in coords_lower]
            coords_v2[ind_extent[0]] += 1
            idx2 = coords2idx[tuple(coords_v2)]
            # Index of vertex 3
            idx3 = idx_upper
            # Coords and index of vertex 4
            coords_v4 = [coord for coord in coords_lower]
            coords_v4[ind_extent[1]] += 1
            idx4 = coords2idx[tuple(coords_v4)]
            cell_verts = [idx1, idx2, idx3, idx4]
        elif cell_dim == 3:  # cell_dim == dimension == 3
            # First get vertices of unit cube as cartesian product of {0, 1}
            u_verts = list(itertools.product((0, 1), repeat=cell_dim))
            # Add verts of unit cube to coords_lower to get verts of this cell
            cell_verts = []
            for u in u_verts:
                coords_vert = [sum(x) for x in zip(u, coords_lower)]
                idx_vert = coords2idx[tuple(coords_vert)]
                cell_verts.append(idx_vert)
        else:  # Ignore cell if dim > 3
            continue
        cell = {"cell_dim": cell_dim,
                "cell_index": cell_index, "cell_verts": cell_verts}
        cells.append(cell)

    def transform_coords(coords):
        def scale_coord(n):
            if (n % 2) == 0:
                num_even = n // 2
                num_odd = n // 2
            else:
                num_even = (n - 1) // 2
                num_odd = (n - 1) // 2 + 1
            return num_even * 1.0 + num_odd * 0.5
        return [scale_coord(u) for u in coords]
    for k in range(len(verts_coords)):
        verts_coords[k] = transform_coords(verts_coords[k])
    complex_json_data = {"complex": {"dimension": dimension,
                                     "verts_coords": verts_coords,
                                     "cells": cells}}
    return complex_json_data

def morse_graph_json(CMG, connection_matrix):
    # Return json data for Morse graph
    # CMG: Conley Morse graph
    conley_indices = connection_matrix.count()
    val2index = { connection_matrix.value(c): c for c in connection_matrix.complex()}
    # Get vertices not in the complex (with trivial Conley index)
    N = len(val2index)
    verts_trivial_CI = [v for v in CMG.vertices() if v not in val2index]
    val2index.update({v: N + k for k, v in enumerate(verts_trivial_CI)})
    # vert_index = {v: k for k, v in enumerate(sorted(CMG.vertices()))}
    vert_index = {v: k for k, v in enumerate(CMG.vertices())}
    n = len(conley_indices[next(iter(conley_indices))])

    def vertex_rank(u):
        # Return how many levels down of children u have
        children = [v for v in CMG.adjacencies(u)]
        # children = [v for v in CMG.children(u)]
        if len(children) == 0:
            return 0
        return 1 + max([vertex_rank(v) for v in children])

    def vertex_label(u):
        # Return vertex label for Morse graph
        if u in conley_indices:
            return str(val2index[u]) + " : " + str(tuple(conley_indices[u]))
            # return str(vert_index[u]) + " : " + str(tuple(conley_indices[u]))
            # return str(u) + " : " + str(tuple(conley_indices[u]))
        else:
            return str(val2index[u]) + " : " + str(tuple([0] * n))
            # return str(vert_index[u]) + " : " + str(tuple([0] * n))
            # return str(u) + " : " + str(tuple([0] * n))

    morse_graph_data = []  # Morse graph data
    for u in CMG.vertices():
        adjacencies = [vert_index[v] for v in CMG.adjacencies(u)]
        # adjacencies = [vert_index[v] for v in CMG.children(u)]
        morse_node_data = {"node": vert_index[u],
                           "rank": vertex_rank(u),
                           "label": vertex_label(u),
                           "adjacencies": adjacencies}
        morse_graph_data.append(morse_node_data)
    morse_graph_json_data = {"morse_graph": morse_graph_data}
    return morse_graph_json_data


def morse_sets_json(fc_stg, CMG, fibration):
    # Return json data for Morse sets
    # CMG: Conley Morse graph
    vert_index = {v: k for k, v in enumerate(CMG.vertices())}

    def fringe_cell_fc(c):
        if any(fc_stg.blowup_complex.rightfringe(s) for s in fc_stg.blowup_complex.star({c})):
            return True
        for b in fc_stg.blowup_complex.boundary({c}):
            if any(fc_stg.blowup_complex.rightfringe(s) for s in fc_stg.blowup_complex.star({b})):
                return True
        return False

    def non_fringe_top_cell(c):
        if fringe_cell_fc(c):
            return False
        # if any(fc_stg.blowup_complex.rightfringe(s) for s in fc_stg.blowup_complex.star({c})):
        # if fc_stg.blowup_complex.rightfringe(c):
        #    return False
        # Get cell dim from blowup cubical complex
        cell_dim = fc_stg.blowup_complex.cell_dim(c)
        if not (cell_dim == fc_stg.dim):
            return False
        return True

    morse_sets_data = []  # Morse sets data
    for u in CMG.vertices():
        fiber = [c for c in fibration.complex() if fibration.value(c) == u]
        morse_cells = [c for c in fiber if non_fringe_top_cell(c)]
        morse_node = vert_index[u]
        morse_set = {"index": morse_node, "cells": morse_cells}
        morse_sets_data.append(morse_set)
    morse_sets_json_data = {"morse_sets": morse_sets_data}
    return morse_sets_json_data


def state_transition_graph_json(fc_stg):
    # Return json data for state transiton graph

    def fringe_cell_fc(c):
        # if fc_stg.blowup_complex.rightfringe(c):
        #     return True
        if any(fc_stg.blowup_complex.rightfringe(s) for s in fc_stg.blowup_complex.star({c})):
            return True
        for b in fc_stg.blowup_complex.boundary({c}):
            if any(fc_stg.blowup_complex.rightfringe(s) for s in fc_stg.blowup_complex.star({b})):
                return True
        return False

    stg = []  # State transition graph
    for S in fc_stg.blowup_complex(fc_stg.dim):
        if fringe_cell_fc(S):
            continue
        adj = [T for T in fc_stg.digraph.adjacencies(
            S) if not fringe_cell_fc(T)]
        S_adj = {"node": S, "adjacencies": adj}
        stg.append(S_adj)
    stg_json_data = {"stg": stg}
    return stg_json_data


def save_morse_graph_database_json(network, database_fname, param_indices=None,
                                   verts_colors=None, thres_type=None, level=4):
    net_spec = network.specification()
    network = DSGRN.Network(net_spec, edge_blowup='none')
    parameter_graph = DSGRN.ParameterGraph(network)

    if param_indices == None:
        param_indices = range(parameter_graph.size())

    par_index = param_indices[0]
    parameter = parameter_graph.parameter(par_index)
    morse_graph, stg, graded_complex = DSGRN_utils.ConleyMorseGraph(parameter, level=0)
    # fc_stg = CubicalBlowupGraph(parameter, level=0)  # level = 0 for construction
    fc_stg = stg
    network_json_data = network_json(network)
    cell_complex_json_data = blowup_cc_complex_json(fc_stg)
    param_graph_json_data = parameter_graph_json(parameter_graph, param_indices, verts_colors, thres_type)

    dynamics_database = []  # Dynamics database
    for par_index in param_indices:
        # Compute DSGRN Plus dynamics
        parameter = parameter_graph.parameter(par_index)
        if fc_stg.dim == 2:
            morse_graph, stg, graded_complex = DSGRN_utils.ConleyMorseGraph(parameter, level=level)
            fc_stg = stg
            # fc_stg = CubicalBlowupGraph(parameter, level=level)
        else:
            morse_graph, stg, graded_complex = DSGRN_utils.ConleyMorseGraph(parameter, level=level)
            fc_stg = stg
            # fc_stg = CubicalBlowupGraph(parameter, level=level)
        (dag, fibration) = FlowGradedComplex(fc_stg.complex(), fc_stg.adjacencies())
        connection_matrix = ConnectionMatrix(fibration)
        # conley_indices = connection_matrix.count()
        fringenode = fibration.value(fc_stg.complex().size() - 1)
        # A Morse set is trivial if it is a single cell with no self edge
        # Get all non-trivial Morse sets (including the ones with trivial CI)

        def non_trivial_scc(v):
            scc_v = [c for c in fc_stg.digraph.vertices()
                     if fibration.value(c) == v]
            return len(scc_v) > 1 or any(c in fc_stg.digraph.adjacencies(c) for c in scc_v)
        # CMG = InducedPoset_E(dag, lambda v: non_trivial_scc(v) and v != fringenode)
        CMG = morse_graph
        morse_graph_json_data = morse_graph_json(CMG, connection_matrix)
        morse_sets_json_data = morse_sets_json(fc_stg, CMG, fibration)
        stg_json_data = state_transition_graph_json(fc_stg)
        # Dynamics data for this parameter
        dynamics_json_data = {"parameter": par_index,
                              "morse_graph": morse_graph_json_data["morse_graph"],
                              "morse_sets": morse_sets_json_data["morse_sets"],
                              "stg": stg_json_data["stg"]}
        dynamics_database.append(dynamics_json_data)

    morse_graph_database = {"network": network_json_data["network"],
                            "complex": cell_complex_json_data["complex"],
                            "parameter_graph": param_graph_json_data["parameter_graph"],
                            "dynamics_database": dynamics_database}

    # Save database to a file
    with open(database_fname, 'w') as outfile:
        json.dump(morse_graph_database, outfile)
