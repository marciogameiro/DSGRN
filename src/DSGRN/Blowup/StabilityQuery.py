### StabilityQuery.py
### MIT LICENSE 2024 Marcio Gameiro

import DSGRN
import DSGRN_utils
from collections import defaultdict

def StabilityQuery(network, param_indices=None, level=4):
    parameter_graph = DSGRN.ParameterGraph(network)
    if param_indices == None:
        param_indices = range(parameter_graph.size())
    param_stability = defaultdict(set)
    for par_index in param_indices:
        parameter = parameter_graph.parameter(par_index)
        morse_graph, stg, graded_complex = DSGRN_utils.ConleyMorseGraph(parameter, level=level)
        attractors = [v for v in morse_graph.vertices() if not morse_graph.adjacencies(v)]
        n_stable = len(attractors)
        param_stability[n_stable].add(par_index)
    return param_stability
