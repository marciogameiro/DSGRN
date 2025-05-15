# EssentialParameterNeighbors.py
# Marcio Gameiro
# 2020-09-18
# MIT LICENSE
#
# 2024-12-08

import DSGRN

def essential_network_spec(parameter_graph):
    """Returns the essential network specification"""
    # Get network specification
    net_spec = parameter_graph.network().specification()
    # Get list of node specifications
    nodes_spec = [s.strip() for s in net_spec.strip().split('\n') if s]
    # Number of specs should equal number of nodes
    assert len(nodes_spec) == parameter_graph.dimension()
    # Check if a node spec correspond to an essential node
    essential_node = lambda spec: spec.count(':') == 2 and 'E' in spec.split(':')[2]
    # essential_node = lambda spec: spec.strip().endswith('E') and spec.count(':') == 2
    # Make all nodes essential
    ess_nodes_spec = [spec if essential_node(spec) else spec + ('' if spec.count(':') == 2 else ' : ') + 'E' for spec in nodes_spec]
    # Get the essential network spec
    ess_net_spec = '\n'.join(ess_nodes_spec)
    return ess_net_spec

def essential_parameters(parameter_graph):
    """Returns list of essential parameters in the parameter graph"""
    # Get the essential network spec
    ess_net_spec = essential_network_spec(parameter_graph)
    # Construct essential network and its parameter graph
    ess_network = DSGRN.Network(ess_net_spec)
    ess_parameter_graph = DSGRN.ParameterGraph(ess_network)
    # Get list of indices of essential parameters embedded
    # in the parameter graph of the original network
    ess_parameters = [] # Essential parameter indices
    for ess_pindex in range(ess_parameter_graph.size()):
        # Get the essential parameter
        ess_par = ess_parameter_graph.parameter(ess_pindex)
        # Get its index in the original parameter graph
        full_pindex = parameter_graph.index(ess_par)
        # Add the index to the list of essential parameters
        ess_parameters.append(full_pindex)
    return ess_parameters

def essential_parameter_neighbors(parameter_graph, level=1):
    """Returns list of essential parameters and its level edge neighbors"""
    # Get list of essential parameters in the parameter graph
    ess_parameters = essential_parameters(parameter_graph)
    # Get list of neighbors of essential parameters
    prev_level_neighbors = ess_parameters # Previous level neighbors
    next_level_neighbors = set() # Next level neighbors
    ess_par_neighbors = set() # Neighbors of essential parameters
    for lev in range(level):
        # Clear next level neighbors
        next_level_neighbors.clear()
        for ess_pindex in prev_level_neighbors:
            # Get neighbors of this essential parameter
            for p_index in parameter_graph.adjacencies(ess_pindex):
                next_level_neighbors.add(p_index)
        # Update previous level neighbors list
        prev_level_neighbors = list(next_level_neighbors)
        # Get number of neighbors before update
        num_neighbors_before = len(ess_par_neighbors)
        # Update essential parameter neighbors set
        ess_par_neighbors.update(prev_level_neighbors)
        # Check if any new neighbor was added
        if len(ess_par_neighbors) == num_neighbors_before:
            break # No more neighbors to add
    # Remove neighbors that are essential parameters
    ess_par_neighbors.difference_update(ess_parameters)
    # Return list of essential parameters and its neighbors
    return ess_parameters, list(ess_par_neighbors)
