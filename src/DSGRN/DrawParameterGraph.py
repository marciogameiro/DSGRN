### DrawParameterGraph.py
### MIT LICENSE 2020 Marcio Gameiro
#
# Marcio Gameiro
# 2024-12-09

import DSGRN
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
import networkx as nx
import graphviz
import itertools
import math

def logic_factor_graph(parameter_graph, node_index):
    """Get logic factor graph of node given by node_index"""
    # Get list of hex codes
    hex_codes = parameter_graph.factorgraph(node_index)
    # Get list of vertices
    vertices = list(range(len(hex_codes)))
    # Get the essential network spec
    ess_net_spec = DSGRN.essential_network_spec(parameter_graph)
    # Construct essential network and its parameter graph
    ess_network = DSGRN.Network(ess_net_spec)
    ess_parameter_graph = DSGRN.ParameterGraph(ess_network)
    # Get list of essential hex codes and their indices
    ess_hex_codes = ess_parameter_graph.factorgraph(node_index)
    ess_vertices = [v for v in vertices if hex_codes[v] in ess_hex_codes]
    # Alternative way to get essential hex code indices
    # n = len(parameter_graph.network().inputs(node_index))
    # m = len(parameter_graph.network().outputs(node_index))
    # ess_vertices = [v for v in vertices if DSGRN.essential(hex_codes[v], n, m)]
    # Function to check if two hex codes are adjacent
    adjacent = lambda u, v: DSGRN.isAdjacentHexcode(hex_codes[u], hex_codes[v])
    # Get list of edges (the adjacency check enforces that u < v)
    edges = [(u, v) for u in vertices for v in vertices if adjacent(u, v)]
    return vertices, edges, ess_vertices, hex_codes

def order_factor_graph(parameter_graph, node_index):
    """Get order factor graph of node given by node_index"""
    # Get list of order parameters
    m = len(parameter_graph.network().outputs(node_index))
    order_size = parameter_graph.ordersize(node_index)
    order_params = [DSGRN.OrderParameter(m, k) for k in range(order_size)]
    # Get list of vertices
    vertices = list(range(len(order_params)))
    # Function to check if two order parameters are adjacent
    adjacent = lambda u, v: order_params[v] in order_params[u].adjacencies()
    # Get list of edges (require u < v so we don't add double edges)
    edges = [(u, v) for u in vertices for v in vertices if adjacent(u, v) and u < v]
    return vertices, edges, order_params

def factor_graph(parameter_graph, node_index):
    """Get factor graph of node given by node_index"""
    # Get logic factor graph vertices and edges
    logic_verts, logic_edges, logic_ess_verts, hex_codes = logic_factor_graph(parameter_graph, node_index)
    # Get order factor graph vertices and edges
    order_verts, order_edges, order_params = order_factor_graph(parameter_graph, node_index)
    # Get vertices of the product of logic and order factor graphs
    vertices = list(itertools.product(logic_verts, order_verts))
    # Get list of essential vertices
    ess_vertices = [v for v in vertices if v[0] in logic_ess_verts]
    # Get the edges given by edges in the logic factor graph
    edges_logic_edges = [((u1, v), (u2, v)) for u1, u2 in logic_edges for v in order_verts]
    # Get the edges given by edges in the order factor graph
    edges_order_edges = [((u, v1), (u, v2)) for u in logic_verts for v1, v2 in order_edges]
    # Get edges of the product of logic and order factor graphs
    edges = edges_logic_edges + edges_order_edges
    return vertices, edges, ess_vertices, hex_codes, order_params

def draw_logic_factor_graph(parameter_graph, node_index, node_color='lightblue',
                            ess_node_color='red', node_label='hex', node_size=None):
    """Draw logic factor graph of node given by node_index"""

    def vert_label(v):
        """Return vertex label"""
        if node_label == 'hex':
            return hex_codes[v]
        if node_label == 'index':
            return str(v)
        if node_label == 'index:hex':
            return str(v) + ': ' + hex_codes[v]
        # Default ('hex')
        return hex_codes[v]

    # Get vertices and edges of logic factor graph
    vertices, edges, ess_vertices, hex_codes = logic_factor_graph(parameter_graph, node_index)
    # Create a vertex name dictionary
    vertex_name = {v: str(v) for v in vertices}
    # Create a vertex label dictionary
    vertex_label = {v: vert_label(v) for v in vertices}
    # Create a vertex color dictionary
    vert_color = lambda v: ess_node_color if v in ess_vertices else node_color
    vertex_color = {v: vert_color(v) for v in vertices}
    # Node width parameters
    fixed_size = 'true'
    max_label_size = max([len(label) for label in vertex_label.values()])
    if node_size == None:
        node_size = max(0.4, max_label_size * 0.13)
        if max_label_size > 6:
            fixed_size = 'false'
    node_width = str(node_size)
    # Get a graphviz string for the graph
    graphviz_str = 'graph {' + '\n'.join(['"' + vertex_name[v] + '" [label="' + \
                    vertex_label[v] + '"; shape="circle"; fixedsize=' + fixed_size + \
                    '; width=' + node_width + '; style="filled"; fontsize=12; fillcolor="' + \
                    vertex_color[v] + '"];' for v in vertices]) + '\n' + \
                    '\n'.join(['"' + vertex_name[u] + '" -- "' + vertex_name[v]  + \
                    '";' for (u, v) in edges ]) + '\n' + '}\n'
    return graphviz.Source(graphviz_str)

def draw_order_factor_graph(parameter_graph, node_index, node_color='lightblue',
                            node_label='perm', node_size=None):
    """Draw order factor graph of node given by node_index"""

    def vert_label(v):
        """Return vertex label"""
        perm = tuple(order_params[v].permutation())
        if node_label == 'perm':
            return str(perm)
        if node_label == 'index':
            return str(v)
        if node_label == 'index:perm':
            return str(v) + ': ' + str(perm)
        # Default ('perm')
        return str(perm)

    # Get vertices and edges of order factor graph
    vertices, edges, order_params = order_factor_graph(parameter_graph, node_index)
    # Create a vertex name dictionary
    vertex_name = {v: str(v) for v in vertices}
    # Create a vertex label dictionary
    vertex_label = {v: vert_label(v) for v in vertices}
    # Create a vertex_color dictionary
    vertex_color = {v: node_color for v in vertices}
    # Node width parameters
    fixed_size = 'true'
    max_label_size = max([len(label) for label in vertex_label.values()])
    if node_size == None:
        node_size = max(0.4, max_label_size * 0.08)
        if max_label_size > 10:
            fixed_size = 'false'
    node_width = str(node_size)
    # Get a graphviz string for the graph
    graphviz_str = 'graph {' + '\n'.join(['"' + vertex_name[v] + '" [label="' + \
                    vertex_label[v] + '"; shape="circle"; fixedsize=' + fixed_size + \
                    '; width=' + node_width + '; style="filled"; fontsize=12; fillcolor="' + \
                    vertex_color[v] + '"];' for v in vertices]) + '\n' + \
                    '\n'.join(['"' + vertex_name[u] + '" -- "' + vertex_name[v]  + \
                    '";' for (u, v) in edges ]) + '\n' + '}\n'
    return graphviz.Source(graphviz_str)

def draw_factor_graph(parameter_graph, node_index, node_color='lightblue',
                      ess_node_color='red', node_label='hex:perm', node_size=None):
    """Draw factor graph of node given by node_index"""

    def vert_label(v):
        """Return vertex label"""
        if node_label == 'index':
            return str(vertices.index(v))
        if node_label == 'coords':
            return str(v)
        if node_label == 'index:hex':
            return str(vertices.index(v)) + ': ' + hex_codes[v[0]]
        if node_label == 'hex:perm':
            perm = tuple(order_params[v[1]].permutation())
            return '[' + hex_codes[v[0]] + ', ' + str(perm) + ']'
        # Default ('hex:perm')
        return '[' + hex_codes[v[0]] + ', ' + str(perm) + ']'

    # Get vertices and edges of the factor graph
    vertices, edges, ess_vertices, hex_codes, order_params = factor_graph(parameter_graph, node_index)
    # Create a vertex name dictionary
    vertex_name = {v: str(v) for v in vertices}
    # Create a vertex label dictionary
    vertex_label = {v: vert_label(v) for v in vertices}
    # Create a vertex color dictionary
    vert_color = lambda v: ess_node_color if v in ess_vertices else node_color
    vertex_color = {v: vert_color(v) for v in vertices}
    # Node width parameters
    fixed_size = 'true'
    max_label_size = max([len(label) for label in vertex_label.values()])
    if node_size == None:
        node_size = max(0.4, max_label_size * 0.08)
        if max_label_size > 20:
            fixed_size = 'false'
    node_width = str(node_size)
    # Get a graphviz string for the graph
    graphviz_str = 'graph {' + '\n'.join(['"' + vertex_name[v] + '" [label="' + \
                    vertex_label[v] + '"; shape="ellipse"; fixedsize=' + fixed_size + \
                    '; width=' + node_width + '; style="filled"; fontsize=12; fillcolor="' + \
                    vertex_color[v] + '"];' for v in vertices]) + '\n' + \
                    '\n'.join(['"' + vertex_name[u] + '" -- "' + vertex_name[v]  + \
                    '";' for (u, v) in edges ]) + '\n' + '}\n'
    return graphviz.Source(graphviz_str)

def draw_parameter_graph(parameter_graph, vertices=None, node_color='lightblue', ess_node_color='red',
                         node_colors=None, node_classes=None, cmap=None, clist=None, node_shapes=None,
                         node_size=None, adj_type='codim1'):
    """Draw parameter graph using graphviz"""

    def vert_color(v):
        """Retunr vertex color"""
        if node_colors and v in node_colors:
            return node_colors[v]
        # Ignore node_classes if node_colors
        if node_classes and node_colors == None:
            if v in vert_clr_index:
                # Return color from colormap
                clr_index = vert_clr_index[v]
                clr = matplotlib.colors.to_hex(cmap(cmap_norm(clr_index)), keep_alpha=True)
                return str(clr)
        # Return default colors
        return ess_node_color if v in ess_vertices else node_color

    def vert_shape(v):
        """Retunr vertex color"""
        if node_shapes and v in node_shapes:
            return node_shapes[v]
        # Default shape
        return 'circle'

    # Set the default colormap
    default_cmap = matplotlib.cm.jet
    if node_classes is not None:
        # Select default comormap for few colors
        max_clr_index = max(node_classes.keys())
        if max_clr_index < 10:
            default_cmap = matplotlib.cm.tab10
        elif max_clr_index < 20:
            default_cmap = matplotlib.cm.tab20
        # Set colormap to use if unset
        if clist and cmap == None:
            cmap = matplotlib.colors.ListedColormap(clist[:max_clr_index + 1], name='clist')
        if cmap == None:
            cmap = default_cmap
        # Normalization for color map
        cmap_norm = matplotlib.colors.Normalize(vmin=0, vmax=max_clr_index)
        # Set a map from vertex to color index
        vert_clr_index = {v: clr_index for clr_index in node_classes for v in node_classes[clr_index]}
    # Get list of vertices if not given
    if vertices == None:
        vertices = list(range(parameter_graph.size()))
    # Get list of essential parameter indices
    ess_vertices = DSGRN.essential_parameters(parameter_graph)
    # Get list of edges (require u < v so we don't add double edges)
    edges = [(u, v) for u in vertices for v in parameter_graph.adjacencies(u, type=adj_type) if u < v and v in vertices]
    # Create a vertex name dictionary
    vertex_name = {v: str(v) for v in vertices}
    # Create a vertex label dictionary
    vertex_label = {v: str(v) for v in vertices}
    # Create a vertex color dictionary
    vertex_color = {v: vert_color(v) for v in vertices}
    # Create a vertex shape dictionary
    vertex_shape = {v: vert_shape(v) for v in vertices}
    # Node width parameters
    fixed_size = 'true'
    max_label_size = max([len(label) for label in vertex_label.values()])
    if node_size == None:
        node_size = 0.3 if max_label_size < 4 else 0.36
        if max_label_size > 4:
            fixed_size = 'false'
    node_width = str(node_size)
    # Get a graphviz string for the graph
    graphviz_str = 'graph {' + '\n'.join(['"' + vertex_name[v] + '" [label="' + \
                    vertex_label[v] + '"; shape="' + vertex_shape[v] + '"; fixedsize=' + fixed_size + \
                    '; width=' + node_width + '; style="filled"; fontsize=12; fillcolor="' + \
                    vertex_color[v] + '"];' for v in vertices]) + '\n' + \
                    '\n'.join(['"' + vertex_name[u] + '" -- "' + vertex_name[v]  + \
                    '";' for (u, v) in edges ]) + '\n' + '}\n'
    return graphviz.Source(graphviz_str)

def draw_parameter_graph_nx(parameter_graph, vertices=None, node_color='lightblue', ess_node_color='red',
                            node_colors=None, node_classes=None, cmap=None, clist=None, node_shape='o',
                            layout='spring', node_size=None, adj_type='codim1', fig_w=10, fig_h=10):
    """Draw parameter graph using networkx"""

    def vert_color(v):
        """Retunr vertex color"""
        if node_colors and v in node_colors:
            return node_colors[v]
        # Ignore node_classes if node_colors
        if node_classes and node_colors == None:
            if v in vert_clr_index:
                # Return color from colormap
                clr_index = vert_clr_index[v]
                clr = matplotlib.colors.to_hex(cmap(cmap_norm(clr_index)), keep_alpha=True)
                return str(clr)
        # Return default colors
        return ess_node_color if v in ess_vertices else node_color

    # Set the default colormap
    default_cmap = matplotlib.cm.jet
    if node_classes is not None:
        # Select default comormap for few colors
        max_clr_index = max(node_classes.keys())
        if max_clr_index < 10:
            default_cmap = matplotlib.cm.tab10
        elif max_clr_index < 20:
            default_cmap = matplotlib.cm.tab20
        # Set colormap to use if unset
        if clist and cmap == None:
            cmap = matplotlib.colors.ListedColormap(clist[:max_clr_index + 1], name='clist')
        if cmap == None:
            cmap = default_cmap
        # Normalization for color map
        cmap_norm = matplotlib.colors.Normalize(vmin=0, vmax=max_clr_index)
        # Set a map from vertex to color index
        vert_clr_index = {v: clr_index for clr_index in node_classes for v in node_classes[clr_index]}
    # Get list of vertices if not given
    if vertices == None:
        vertices = list(range(parameter_graph.size()))
    # Set node size
    if node_size == None:
        node_size = 900
    # Get list of essential parameter indices
    ess_vertices = DSGRN.essential_parameters(parameter_graph)
    # Get list of edges (require u < v so don't add double edges)
    edges = [(u, v) for u in vertices for v in parameter_graph.adjacencies(u, type=adj_type) if u < v and v in vertices]
    # Create a vertex label dictionary
    vertex_label = {v: str(v) for v in vertices}
    # Create a vertex color dictionary
    vertex_color = {v: vert_color(v) for v in vertices}
    # Create graph
    G = nx.Graph()
    # Set node positions for grid layout
    if layout == 'grid':
        # Position nodes on an n-by-n grid
        n = math.ceil(math.sqrt(len(vertices)))
        for k, v in enumerate(vertices):
            k1 = k % n
            k2 = (k - k1) // n
            G.add_node(vertex_label[v], pos=(k1, -k2))
    # Add graph edges
    for u, v in edges:
        G.add_edge(vertex_label[u], vertex_label[v])
    # Set node positions layout
    if layout == 'grid':
        pos = nx.get_node_attributes(G, 'pos')
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'spiral':
        pos = nx.spiral_layout(G)
    elif layout == 'spring':
        pos = nx.spring_layout(G)
    else:
        print('Invalid layout! Using default.')
        pos = nx.spring_layout(G)
    # Set graph options
    options = {"with_labels": True, "edgecolors": 'black'}
    # Set figure size
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    # Set node sizes and colors
    node_sizes = [node_size for v in vertices]
    node_colors = [vertex_color[v] for v in vertices]
    # Draw graph
    nx.draw_networkx(G, pos=pos, ax=ax, node_size=node_sizes, node_color=node_colors, node_shape=node_shape, **options)
    ax.axis('off')
    fig.tight_layout()
    plt.show()
