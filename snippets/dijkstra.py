from __future__ import division

from enum import Enum


infinity = float('inf')

# cardinal directions, plus I when inside a node
Direction = Enum('Direction', 'n e s w i')
# all the possible colors used for nodes, including 'unknown' when the color of
# a node is not yet known
Color = Enum('Color', 'red green cyan violet orange unknown')

graph = { 
    Color.red.value: 
        [None, [Color.unknown.value, -1], [Color.cyan.value, 6], [Color.green.value, 5]],
    Color.green.value: 
        [[Color.red.value, 5], [Color.cyan.value, 6], None,None],
    Color.cyan.value:  
        [None, [Color.violet.value, 10], [Color.green.value, 6], [Color.red.value, 6]],
    Color.violet.value:
        [None, None, [Color.unknown.value, -1], [Color.cyan.value, 10]],
    Color.orange.value: 
        [None, None, None, None] }

def indexof(predicate, data):
    for i, x in enumerate(data):
        if predicate(x):
            return i
    return -1

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
            if (dist.has_key(node) and dist[node] < dist[u]) : #why the hell not dist.has_key(u)?? REMOVED: not dist.has_key(u) or
                u = node
        q.remove(u)

        if u == destination_node:
            return (dist, previous)

        # Process reachable, remaining nodes from u
        neighbours = [ n for n in graph[u] if n != None and n[0] != Color.unknown.value]
        for v, dv in neighbours:
            if v in q:
                alt = dist[u] + dv                #arrow weight
                if (not dist.has_key(v)) or (alt < dist[v]):
                    dist[v] = alt
                    previous[v] = u

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

def get_unexplored_edges(graph, node):
    edge = [(node, e, indexof(lambda edge: edge == e, graph[node])) for e in graph[node] if e != None and e[0] == Color.unknown.value]
    return edge

def get_available_unexplored(graph, node):
    nodes = filter(lambda (node, edges): indexof(lambda edge: edge != None and edge[0] == Color.unknown.value, edges) != -1, graph.iteritems())
    return nodes

def get_min_dest_direction(graph, source):
    nodes = get_available_unexplored(graph, source)
    dists, previous = shortest_path(graph, source, None)
    nodes = filter(lambda (node, edge): dists.has_key(node), nodes)
    if nodes == None:
        return None
    weighted_nodes = [(dists[n], n) for (n, e) in nodes]
    weighted_nodes.sort()
    destination = weighted_nodes[0][1]
    if destination == source:
        return destination
    tmp_dist = destination
    while previous[tmp_dist] != source:
        tmp_dist = previous[tmp_dist]
    idx = indexof(lambda edge: edge != None and edge[0] == tmp_dist, graph[source])
    return (tmp_dist, idx)
    

def main():
    edges = get_min_dest_direction(graph, Color.red.value)
    print(edges)
    #print(shortest_path(graph, Color.red.value, None))
    #print(get_next_direction(graph, Color.red.value, Color.orange.value))


if __name__ == '__main__':
    main()

