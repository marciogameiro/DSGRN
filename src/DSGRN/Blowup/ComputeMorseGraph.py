### ComputeMorseGraph.py
### MIT LICENSE 2024 Marcio Gameiro

import DSGRN
import pychomp
import DSGRN_utils

def ConleyMorseGraph(parameter=None, labelling=None, num_thresholds=None, prune_grad=True, level=4):
    # Check if input arguments are valid
    if parameter is None and (labelling is None or num_thresholds is None):
        raise ValueError('Either parameter or labelling and num_thresholds must be provided.')
    if parameter and (labelling or num_thresholds):
        raise ValueError('Only parameter or labelling and num_thresholds should be provided.')
    # Compute the multivalued map (state transition graph)
    stg = DSGRN_utils.CubicalBlowupGraph(parameter=parameter, labelling=labelling, num_thresholds=num_thresholds, level=level)
    # Compute the flow graded complex
    (scc_dag, graded_complex) = pychomp.FlowGradedComplex(stg.complex(), stg.adjacencies())
    # Compute the connection matrix of the graded complex
    connection_matrix = pychomp.ConnectionMatrix(graded_complex)
    # Compute the Morse graph
    morse_graph = DSGRN_utils.MorseGraph(stg, scc_dag, graded_complex, connection_matrix, prune_grad=prune_grad)
    return morse_graph, stg, graded_complex
