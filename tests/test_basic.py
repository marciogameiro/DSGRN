import DSGRN

def test_build_network():
    net_spec = 'x1 : (~x1)(x2)\n x2 : (x1)(~x2)'
    network = DSGRN.Network(net_spec)
    assert network.size() == 2

def test_build_parameter_graph():
    net_spec = 'x1 : (~x1)(x2)\n x2 : (x1)(~x2)'
    network = DSGRN.Network(net_spec)
    parameter_graph = DSGRN.ParameterGraph(network)
    assert parameter_graph.size() == 1600
