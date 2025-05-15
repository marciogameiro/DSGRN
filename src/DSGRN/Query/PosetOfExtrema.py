# PosetOfExtrema.py
# MIT LICENSE
# Shaun Harker 2016-12-27
#
# Marcio Gameiro
# 2021-08-04

from DSGRN._dsgrn import *

class PosetOfExtrema(Pattern):
  def __init__(self, network, events, orderings):
    """
    Initializes a poset of extrema
      network is a DSGRN network object
      events is a list of tuples of the form (NAME,'min') or (NAME,'max') for NAME a
                name of a node in the network
      orderings is list of event orderings (the code will perform transitive closure
                automatically), i.e. a list of pairs (i,j) such that events[i] occurs
                before events[j]
    """
    # Save variables
    self.network_ = network
    self.labels_ = [event[0] + " " + event[1] for event in events]
    # Construct Digraph from event and ordering data
    digraph = Digraph()
    for event in events:
      digraph.add_vertex()
    for edge in orderings:
      digraph.add_edge(edge[0], edge[1])
    self.poset_ = Poset(digraph)
    # Find final occurrence of each variable in poset
    latest_event = {}
    label = {}
    for i, event in enumerate(events):
      variable = network.index(event[0])
      if (variable not in latest_event) or self.poset_.compare(latest_event[variable], i):
        latest_event[variable] = i
        label[variable] = 2 ** (variable + network.size()) if event[1].lower() == "min" else 2 ** variable
    final_label = 0
    for variable in range(network.size()):
      if variable not in latest_event:
        label[variable] = 0
      final_label += label[variable]
    events_for_pattern = [network.index(event[0]) for event in events]
    # Create "Pattern" object instance
    super(PosetOfExtrema, self).__init__(self.poset_, events_for_pattern, final_label, self.network_.size())

  def graphviz(self):
    """
    Return graphviz string for visualization
    """ 
    N = len(self.labels_)
    gv_vertices = [ '"' + str(i) + '" [label="' + self.labels_[i] + '"];' for i in range(N) ]
    gv_edges = [ '"' + str(u) + '" -> "' + str(v) + '";' for u in range(N) for v in self.poset_.children(u) ]
    return 'digraph {\n' + '\n'.join(gv_vertices) + '\n' + '\n'.join(gv_edges) + '\n}\n'
