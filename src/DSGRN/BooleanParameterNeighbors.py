# BooleanParameterNeighbors.py
### MIT LICENSE 2024 Marcio Gameiro

import DSGRN

def boolean_network_spec(parameter_graph):
    """Returns the Boolean network specification"""
    # Get network specification
    net_spec = parameter_graph.network().specification()
    # Get list of node specifications
    nodes_spec = [s.strip() for s in net_spec.strip().split('\n') if s]
    # Number of specs should equal number of nodes
    assert len(nodes_spec) == parameter_graph.dimension()
    # Check if a node spec correspond to a Boolean node
    boolean_node = lambda spec: spec.count(':') == 2 and 'B' in spec.split(':')[2]
    # Make all nodes Boolean
    bool_nodes_spec = [spec if boolean_node(spec) else spec + ('' if spec.count(':') == 2 else ' : ') + 'B' for spec in nodes_spec]
    # Get the Boolean network spec
    bool_net_spec = '\n'.join(bool_nodes_spec)
    return bool_net_spec

def boolean_parameters(parameter_graph):
    """Returns list of Boolean parameters in the parameter graph"""
    # Get the Boolean network spec
    bool_net_spec = boolean_network_spec(parameter_graph)
    # Construct Boolean network and its parameter graph
    bool_network = DSGRN.Network(bool_net_spec)
    bool_parameter_graph = DSGRN.ParameterGraph(bool_network)
    # Get list of indices of Boolean parameters embedded
    # in the parameter graph of the original network
    bool_parameters = [] # Boolean parameter indices
    for bool_pindex in range(bool_parameter_graph.size()):
        # Get the Boolean parameter
        bool_par = bool_parameter_graph.parameter(bool_pindex)
        # Get its index in the original parameter graph
        full_pindex = parameter_graph.index(bool_par)
        # Add the index to the list of Boolean parameters
        bool_parameters.append(full_pindex)
    return bool_parameters

def boolean_parameter_neighbors(parameter_graph, level=1):
    """Returns list of Boolean parameters and its level edge neighbors"""
    # Get list of Boolean parameters in the parameter graph
    bool_parameters = boolean_parameters(parameter_graph)
    # Get list of neighbors of Boolean parameters
    prev_level_neighbors = bool_parameters # Previous level neighbors
    next_level_neighbors = set() # Next level neighbors
    bool_par_neighbors = set() # Neighbors of Boolean parameters
    for lev in range(level):
        # Clear next level neighbors
        next_level_neighbors.clear()
        for bool_pindex in prev_level_neighbors:
            # Get neighbors of this Boolean parameter
            for p_index in parameter_graph.adjacencies(bool_pindex):
                next_level_neighbors.add(p_index)
        # Update previous level neighbors list
        prev_level_neighbors = list(next_level_neighbors)
        # Get number of neighbors before update
        num_neighbors_before = len(bool_par_neighbors)
        # Update Boolean parameter neighbors set
        bool_par_neighbors.update(prev_level_neighbors)
        # Check if any new neighbor was added
        if len(bool_par_neighbors) == num_neighbors_before:
            break # No more neighbors to add
    # Remove neighbors that are Boolean parameters
    bool_par_neighbors.difference_update(bool_parameters)
    # Return list of Boolean parameters and its neighbors
    return bool_parameters, list(bool_par_neighbors)
