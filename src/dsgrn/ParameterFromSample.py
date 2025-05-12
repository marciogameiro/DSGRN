# ParameterFromSample.py
# Marcio Gameiro and Lun Zhang
# MIT LICENSE
# 2021-10-14

import dsgrn
import numpy as np
import json

def partial2hex(partial_order, n_inputs, n_outputs):
    """Computes the hex code corresponding to a given partial order
    The values in between the thresholds do not need to be sorted
    """
    par_bit_matrix = np.zeros([n_outputs, 2**n_inputs], dtype=int) # matrix of bit codes
    for k in range(n_outputs): # for each threshold
        indx = partial_order.index(-(k+1)) # index of kth threshold
        indx_left = [n for n in partial_order[:indx] if n >= 0] # indices >= 0 before threshold
        bit_array = np.ones(2**n_inputs, dtype=int) # array of bit codes for kth threshold
        bit_array[indx_left] = 0 # set entries corresponding to indx_left to zero
        par_bit_matrix[k] = list(reversed(bit_array)) # reverse and set as kth row
    par_bit_code = ''.join(map(str, par_bit_matrix.flatten('F'))) # flatten in column-major order (Fortran-style)
    n_nibbles = ((len(par_bit_code) - 1) // 4) + 1 # number of nibbles (ceil division by 4)
    fmt = '0' + str(n_nibbles) + 'X' # hex code format
    par_hex_code = format(int(par_bit_code, 2), fmt) # set parameter hex code
    return par_hex_code

def indexMask(logic):
    """Generate map i -> bit mask of i for value logic"""
    lgt = sum(logic)
    pattern = '{0:0' + str(lgt) + 'b}'
    n_orders = np.prod([2**s for s in logic])
    ret = []
    for i in range(n_orders):
        mask = pattern.format(i)
        vMask = [int(i) for i in mask]
        currMask = []
        currPos = 0
        for i in range(len(logic)):
            temp = vMask[currPos:currPos+logic[i]]
            currMask.append(temp)
            currPos += logic[i]
        ret.append(currMask)
    return ret

def evalMask(sample, masks):
    """Given masks evaluate the sample sequence of switching polynomials"""
    ret = []
    for i in range(len(masks)):
        currVal = 1
        currPos = 0
        for j in range(len(masks[i])):
            tempSum = 0
            for k in range(len(masks[i][j])):
                if masks[i][j][k] == 0:
                    tempSum += sample[currPos][0]
                else:
                    tempSum += sample[currPos][1]
                currPos += 1
            currVal *= tempSum
        ret.append(currVal)
    return ret

def binSort(x):
    prev = 0
    for i in range(len(x)):
        if x[i] < 0:
            x[prev:i] = sorted(x[prev:i])
            prev = i + 1
    lgt = len(x)
    x[prev:lgt] = sorted(x[prev:lgt])
    return x

def nodeRegion(logic, samples, thetas):
    masks = indexMask(logic)
    tempVals = evalMask(samples,masks)
    if len(np.unique(tempVals)) != len(tempVals):
        return None
    rthetas = thetas.copy()[::-1]
    tempOrd = np.argsort(tempVals + rthetas)
    for i in range(len(tempOrd)):
        if tempOrd[i] >= len(tempVals):
            tempOrd[i] -= len(tempOrd)
    # Convert to a list of ints
    tempOrd = list(map(int, tempOrd))
    return tempOrd

def par_index_from_sample_old(parameter_graph, L, U, T):
    network = parameter_graph.network()
    D = network.size()
    # The logic of each node, logics[d], is a list of the factor lengths
    logics = [[len(logic) for logic in network.logic(d)] for d in range(D)]
    logic_parameters = []
    order_parameters = []
    for d in range(D):
        # Input edges from source s to target d
        # Output edges from source d to target s
        inputs = network.inputs(d)
        inputs.sort(reverse=True)
        n_inputs = len(inputs)
        outputs = network.outputs(d)
        outputs.sort(reverse=True)
        n_outputs = len(outputs)
        L_U_values = [[L[s, d], U[s, d]] for s in inputs]
        T_values = [T[d, s] for s in outputs]
        node_region = nodeRegion(logics[d], L_U_values, T_values)
        # Return -1 for invalid input
        if node_region is None:
            return -1
        # Get the thresholds from node_region
        thres = [p for p in node_region if p < 0]
        # Get thresholds permutation (order parameter)
        order = [p + n_outputs for p in thres]
        # Get order parameter
        order_parameters.append(dsgrn.OrderParameter(order))
        # Add sorted thresholds (in increasing order) to partial order
        part_order = [thres.index(p) - n_outputs if p < 0 else p for p in node_region]
        # Get hex code from partial order
        hex_code = partial2hex(part_order, n_inputs, n_outputs)
        # Get logic parameter
        logic_parameters.append(dsgrn.LogicParameter(n_inputs, n_outputs, hex_code))
    # Get DSGRN parameter
    parameter = dsgrn.Parameter(logic_parameters, order_parameters, network)
    # Get parameter index from parameter graph
    par_index = parameter_graph.index(parameter)
    # Return parameter index if valid, else return -1
    if par_index < parameter_graph.size():
        return par_index
    return -1

def index_from_partial_orders(parameter_graph, partial_orders):
    network = parameter_graph.network()
    D = network.size()
    logic_parameters = []
    order_parameters = []
    for d in range(D):
        n_inputs = len(network.inputs(d))
        n_outputs = len(network.outputs(d))
        # Get partial order for this node
        partial_order = partial_orders[d]
        # Transform into list if is a string
        if isinstance(partial_order, str):
            # Remove white space and parentheses and split string into a list
            partial_order = partial_order.replace(' ', '')[1:-1].split(',')
        # Extract numerical values (partial order can be numeric or string)
        get_digit = lambda p : int(p[1:]) if p[0] == 'p' else int(p[1:]) - n_outputs
        # Partial order for this node (with threshold permutations)
        part_order = [p if isinstance(p, int) else get_digit(p) for p in partial_order]
        # Get the thresholds from partial_order
        thres = [p for p in part_order if p < 0]
        # Get thresholds permutation (order parameter)
        order = [p + n_outputs for p in thres]
        # Get order parameter
        order_parameters.append(dsgrn.OrderParameter(order))
        # Add sorted thresholds (in increasing order) to partial order
        partial_order = [thres.index(p) - n_outputs if p < 0 else p for p in part_order]
        # Get hex code from partial order
        hex_code = partial2hex(partial_order, n_inputs, n_outputs)
        # Get logic parameter
        logic_parameters.append(dsgrn.LogicParameter(n_inputs, n_outputs, hex_code))
    # Get DSGRN parameter
    parameter = dsgrn.Parameter(logic_parameters, order_parameters, network)
    # Get parameter index from parameter graph
    par_index = parameter_graph.index(parameter)
    # Return parameter index if valid, else return -1
    if par_index < parameter_graph.size():
        return par_index
    return -1

def par_index_from_sample(parameter_graph, L, U, T):
    network = parameter_graph.network()
    D = network.size()
    # The logic of each node, logics[d], is a list of the factor lengths
    logics = [[len(logic) for logic in network.logic(d)] for d in range(D)]
    partial_orders = []
    for d in range(D):
        # Input edges from source s to target d
        # Output edges from source d to target s
        inputs = network.inputs(d)
        inputs.sort(reverse=True)
        n_inputs = len(inputs)
        outputs = network.outputs(d)
        outputs.sort(reverse=True)
        n_outputs = len(outputs)
        L_U_values = [[L[s, d], U[s, d]] for s in inputs]
        T_values = [T[d, s] for s in outputs]
        node_region = nodeRegion(logics[d], L_U_values, T_values)
        # Return -1 for invalid input
        if node_region is None:
            return -1
        partial_orders.append(node_region)
    par_index = index_from_partial_orders(parameter_graph, partial_orders)
    return par_index
