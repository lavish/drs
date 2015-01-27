import json
from threading import Lock
from enum import Enum
from flask import Flask, redirect, render_template, request, url_for
from conf import Color, web_server_port

class DRSServer(Flask):
    '''Wrapper around the Flask class used to store additional information.'''

    def __init__(self, *args, **kwargs):
        super(DRSServer, self).__init__(*args, **kwargs)

        # dictionary representing the graph, where the key is the node
        # identifier (i.e. the value of an element of class Color) and values
        # are lists of four pairs of (node identifier, weight), one for each
        # possible direction if an edge is present, None otherwise. If there's
        # an edge on a certain direction, but the destination node is unknown,
        # we set the pair to [Color.unknown.value, -1]
        self.graph = dict()
        # list of positions of each robot (last visited node) having elements
        # of kind Color.<color>.value: 'unknown' at the beginning of the game
        # and always defined after visiting the first node 
        self.positions = None
        # list of directions taken by the robots
        self.directions = None
        # whether or not the protocol started
        self.started = False

# global lock used to avoid race conditions
lock = Lock()
# instance of the web application
app = DRSServer(__name__)
# the final answer
inside = 42

@app.route('/started')
def started():
    """Page polled by the bots in order to start the game."""

    return '1' if app.started else '0'

@app.route('/graph')
def dump_data():
    """Page polled via Ajax requests, used to depict the graph."""

    return json.dumps(app.graph)

@app.route('/marker_update', methods = ['POST'])
def marker_update():
    """When a bot enters a node, a request to this resource is made in order to
    update the shared position list and eventually the graph, while returning
    to the bots performing the request the updated graph structure."""

    # update the shared data structures after locking
    with lock:
        can_enter = False
        has_to_explore = False

        robot = request.form.get('robot', type=int)
        destination_node = request.form.get('destination_node', type=int)
        destination_orientation = request.form.get('destination_orientation', type=int)
        edge_length = request.form.get('edge_length', type=int)
        # 0 explore edge (full, do everything)
        # 1 moving (do not check anything in the graph, just check locking)
        exploring = request.form.get('exploring', type=bool)
        print(request.form)

        # save old values
        old_position = app.positions[robot]
        old_direction = app.directions[robot]
        # set the answers
        can_enter = not destination_node in app.positions
        if can_enter:
            app.positions[robot] = destination_node
            app.directions[robot] = inside

        if exploring:
            has_to_explore = not destination_node in app.graph

            # check if the current node is included in the graph. If it already is,
            # update the edge starting from direction_in, if needed, otherwise
            # create it from scratch
            if destination_node not in app.graph:
                # create a list with four elements representing the 4 possible
                # directions, all set to None at the beginning
                app.graph[destination_node] = [None for _ in range(4)]
                app.graph[destination_node][destination_orientation] = [old_position, edge_length]
            if old_position != Color.unknown.value:
                # add the edge from old_node to the current node, in case it's
                # missing. We assume old_node to be already visited (excluding the
                # case in which the old_node is unknown), hence included in the
                # graph
                if app.graph[old_position][old_direction][0] != destination_node: 
                    app.graph[old_position][old_direction] = [destination_node, edge_length]
                if app.graph[destination_node][destination_orientation][0] != old_position:
                    # update the list with information about the edge we used to
                    # enter the current node
                    app.graph[destination_node][destination_orientation] = [old_position, edge_length]

    return json.dumps([app.graph, app.positions, has_to_explore, can_enter])

@app.route('/outupdate', methods = ['POST'])
def outupdate():
    """When a bot leaves a node, a request to this resource is made in order to
    update the shared list of directions and eventually increasing the
    knowledge about the graph by sending the discovered edges starting from the
    current node."""

    robot = request.form.get('robot', type=int)
    node = Color[request.form.get('node')].value
    direction_out = Direction[request.form.get('dirout')].value
    app.directions[robot] = direction_out

    # eventually update the information about the edges starting from the
    # current node
    try:
        out_edges = [request.form.get(k) for k in Direction.__members__ if k != 'i']
        # update the reference to the out edge only if found by the robot and
        # not already defined within the graph structure
        for d in range(4):
            if out_edges[d] == '1' and app.graph[node][d] == None:
                app.graph[node][i] = ['unknown', -1]
    except KeyError:
        pass

    # return 1 just to confirm that the operation succeeded
    return '1'

@app.route('/start')
def start():
    app.started = True
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('base.html', started=app.started)

if __name__ == '__main__':
    n_robots = 4

    # initialization of the shared data structures
    app.positions = [Color.unknown.value for _ in range(n_robots)]
    # assume that each robot starts in the direction represented by its own id
    app.directions = range(n_robots)
    # start listening
    app.run(host='0.0.0.0', debug=True)
