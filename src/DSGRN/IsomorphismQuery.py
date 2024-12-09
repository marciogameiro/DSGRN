### IsomorphismQuery.py
### MIT LICENSE 2024 Marcio Gameiro

import DSGRN
import DSGRN_utils
from collections import defaultdict

def IsomorphismQuery(network, param_indices=None, level=3):
    """Return a list of sets of parameters with isomorphics Morse graphs"""
    parameter_graph = DSGRN.ParameterGraph(network)
    if param_indices == None:
        param_indices = range(parameter_graph.size())
    # Dictionary of non-isomorphic Morse graphs
    distinct_morse_graphs = {}
    # Isomorphism classes
    isomorphism_classes = defaultdict(set)
    for par_index in param_indices:
        parameter = parameter_graph.parameter(par_index)
        morse_graph, stg, graded_complex = DSGRN_utils.ConleyMorseGraph(parameter, level=level)
        found_match = False
        for par_index2 in distinct_morse_graphs:
            morse_graph2 = distinct_morse_graphs[par_index2]
            if DSGRN.isomorphic_morse_graphs(morse_graph, morse_graph2):
                # Found isomorphic Morse graph
                isomorphism_classes[par_index2].add(par_index)
                found_match = True
                continue
        # Create new class if match not found
        if not found_match:
            distinct_morse_graphs[par_index] = morse_graph
            isomorphism_classes[par_index].add(par_index)
    return list(isomorphism_classes.values())
