from __future__ import division

from enum import Enum
from copy import deepcopy
from conf import Color

infinity = float('inf')

def indexof(predicate, data):
    for i, x in enumerate(data):
        if predicate(x):
            return i
    return -1

def contains(predicate, data):
    for x in data:
        if predicate(x):
            return True
    return False

def indexof_many(predicate, data):
    return [ i for i, x in enumerate(data) if predicate(x) ]

def shortest_path(graph, source_node, destination_node):
    """
    Return the shortest path distance between sourceNode and all other nodes
    using Dijkstra's algorithm.  See
    http://en.wikipedia.org/wiki/Dijkstra%27s_algorithm.  
    
    @attention All weights must be nonnegative.

    @type  graph: graph
    @param graph: Graph.

    @type  source_node: node
    @param source_node: Node from which to start the search.
    
    @type  destination_node: node or null
    @param destination_node: Destination node of the search. If None all paths are computed.

    @rtype  tuple
    @return A tuple containing two dictionaries, each keyed by
        targetNodes.  The first dictionary provides the shortest distance
        from the source_node to the targetNode.  The second dictionary
        provides the previous node in the shortest path traversal.
        Inaccessible targetNodes do not appear in either dictionary.
    """
    # Initialization
    dist     = { source_node: 0.0 }
    previous = {}
    q = [ k for k in graph ]

    # Algorithm loop
    while q:
        # examine_min process performed using O(nodes) pass here.
        # May be improved using another examine_min data structure.
        # See http://www.personal.kent.edu/~rmuhamma/Algorithms/MyAlgorithms/GraphAlgor/dijkstraAlgor.htm
        u = q[0]
        for node in q[1:]:
            if not dist.has_key(u) or (dist.has_key(node) and dist[node] < dist[u]) : #why the hell not dist.has_key(u)?? REMOVED: not dist.has_key(u) or
                u = node
        q.remove(u)

        if u == destination_node:
            return (dist, previous)

        # Process reachable, remaining nodes from u
        neighbours = [ n for n in graph[u] if n != None and n[0] != Color.unknown.value]
        for v, dv in neighbours:
            if v in q:
                alt = dist[u] + dv if dist.has_key(u) else infinity                #arrow weight
                if (not dist.has_key(v)) or (alt < dist[v]):
                    dist[v] = alt
                    previous[v] = u
    to_delete = []
    for k, v in dist.iteritems():
        if v == infinity:
            to_delete.append(k)
    for k in to_delete:
        del dist[k]
        del previous[k]
    return (dist, previous)

def get_next_direction(graph, source, destination):
    dists, previous = shortest_path(graph, source, destination)
    tmp_dist = destination
    if not previous.has_key(destination):
        return None
    while previous[tmp_dist] != source:
        tmp_dist = previous[tmp_dist]
    idx = indexof(lambda edge: edge != None and edge[0] == tmp_dist, graph[source])
    return (tmp_dist, idx)

def get_edges(graph, node):
    edge = [(node, e, indexof(lambda edge: edge == e, graph[node])) for e in graph[node] if e != None]
    return edge

def get_near_unexplored_edges(graph, node):
    edge = []
    for e in graph[node]:
        if e != None and e[0] == Color.unknown.value:
            edge.append(node, e, indexof(lambda edge: edge == e, graph[node]))
    #edge = [(node, e, indexof(lambda edge: edge == e, graph[node])) for e in graph[node] if e != None and e[0] == Color.unknown.value]
    return edge

def get_available_unexplored(graph, node):
    nodes = []
    for node, edges in graph.iteritems():
        if indexof(lambda edge: edge != None and edge[0] == Color.unknown.value, edges) != -1:
            nodes.append((node, edges))
    #nodes = filter(lambda (node, edges): indexof(lambda edge: edge != None and edge[0] == Color.unknown.value, edges) != -1, graph.iteritems())
    return nodes

def get_min_dest_direction(graph, source):
    nodes = get_available_unexplored(graph, source)
    dists, previous = shortest_path(graph, source, None)
    nodes = filter(lambda (node, edge): dists.has_key(node), nodes)
    print("Nodes: {}".format(nodes))
    print("Graph: {}".format(graph))
    print("Dists: {}".format(dists))

    if nodes == None or nodes == []:
        return None
    weighted_nodes = [(dists[n], n) for (n, e) in nodes]
    weighted_nodes = sorted(weighted_nodes, key=lambda (d, n): d)
    destination = weighted_nodes[0][1]
    if destination == source:
        unexplored = indexof_many(lambda edge: edge != None and edge[0] == Color.unknown.value, graph[destination])
        return [(Color.unknown.value, d) for d in unexplored]
    tmp_dist = destination
    while previous[tmp_dist] != source:
        tmp_dist = previous[tmp_dist]
    idx = indexof(lambda edge: edge != None and edge[0] == tmp_dist, graph[source])
    return [(tmp_dist, idx)]
    
def filter_graph(graph, bot_id, positions):
    print("Original graph: {}".format(graph))
    print("bot_id: {}, positions: {}".format(bot_id, positions))

    other_positions = [p for i, p in enumerate(positions) if i != bot_id]
    filtered_graph = {}
    '''
    for node, edges in graph.iteritems():
        #if indexof(lambda p: p == node and node != Color.unknown.value, other_positions) == -1:
        if node == Color.unknown.value or (not node in other_positions):
            filtered_edges = map(lambda edge: None if edge == None or indexof(lambda p: p == edge[0], other_positions) != -1 else edge, edges)
            filtered_graph[node] = filtered_edges
    '''

    for node, edges in graph.iteritems():
        if node not in other_positions:
            filtered_graph[node] = [None if (e == None or (e[0] in other_positions and e[0] != Color.unknown.value)) else e for e in graph[node]]

    print("New graph: {}".format(filtered_graph))

    return filtered_graph

def add_unknown_edges_to_graph(graph, starting_node, orientations):
    up_graph = deepcopy(graph)
    edges = [[Color.unknown.value, -1] if (orientations[i] and up_graph[starting_node][i] == None) else up_graph[starting_node][i] for i in range(4)]
    up_graph[starting_node] = edges

    return up_graph

#def filter_graph_2(graph, bot_id, positions, orientation):
#
#    other_positions = [p for i, p in enumerate(positions) if i != bot_id]
#    other_state = []
#    for pos in other_positions:
#
#    filtered_graph = {}
#    for node, edges in graph.iteritems():
#        if indexof(lambda p: p == node, other_positions) == -1:
#            filtered_edges = map(lambda edge: None if edge == None or indexof(lambda p: p == edge[0], other_positions) != -1 else edge, edges)
#            filtered_graph[node] = filtered_edges
#    return filtered_graph

def explored(graph, color):
    return graph.has_key(color)

def main():
    graph = { 
        Color.red.value: 
            [None, [Color.unknown.value, -1], [Color.cyan.value, 6], [Color.green.value, 5]],
        Color.green.value: 
            [[Color.red.value, 5], [Color.cyan.value, 7], None,None],
        Color.cyan.value:  
            [[Color.red.value, 6], [Color.violet.value, 71], None, [Color.green.value, 7]],
        Color.violet.value:
            [[Color.unknown.value, -1], [Color.orange.value, 1], [Color.unknown.value, -1], [Color.cyan.value, 71]],
        Color.orange.value: 
            [[Color.violet.value, 1], [Color.white.value, 10], None, None],
        Color.white.value: 
            [None, None, None, [Color.orange.value, 10]]}

    status = [Color.red.value, Color.cyan.value]

    my_id = 0
    my_color = status[my_id]
    graph = add_unknown_edges_to_graph(graph, Color.red.value, [True, False, True, False])
    filtered_graph = filter_graph(graph, my_id, status)
    edges = get_min_dest_direction(filtered_graph, my_color)
    print(edges)
    #print(shortest_path(graph, Color.green.value, None))
    #print(get_next_direction(graph, Color.red.value, Color.orange.value))


if __name__ == '__main__':
    main()

