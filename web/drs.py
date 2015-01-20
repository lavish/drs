import json
from threading import Lock
from flask import Flask, render_template, request

class DRSServer(Flask):
    def __init__(self, *args, **kwargs):
        super(DRSServer, self).__init__(*args, **kwargs)

        # list of all possible colors, including 'unknown' when we don't know
        # where an edge is leading to
        self.nodes = None
        # dictionary representing the graph, where the key is the node
        # identifier and values are lists of four pairs of (node, weight), one
        # for each possible direction
        self.graph = dict()
        # list of positions of each robot (last visited node): None at the
        # beginning of the game, always defined after visiting the first node
        self.positions = None
        # list of directions taken by the robots, ranging from 0 to 3 (N, E, S,
        # W) plus 4 when the robot is inside a node
        self.directions = None
        # whether or not the protocol started 
        self.started = False

lock = Lock()
app = DRSServer(__name__)

@app.route('/start', methods = ['GET', 'POST'])
def start():
    if request.method == 'GET':
        return 1 if app.started else 0
    if request.method == 'POST':
        if request.form['start'] == '1':
            if not app.started:
                app.started = True
                return "Protocol started!"
            else:
                return "Game already started"
        else:
            return "WUT!?"

@app.route('/graph')
def dump_data():
    return json.dumps([app.graph, app.positions, app.directions])

@app.route('/inupdate', methods = ['POST'])
def inupdate():
    robot = int(request.form['robot'])
    node = request.form['node']
    weight = int(request.form['weight'])
    direction_in = int(request.form['dirin'])

    # update the shared data structures after locking
    with lock:
        # get the old position of the robot and update the positions list with
        # the current position and direction (4, since the robot is inside a node)
        old_node = app.positions[robot]
        old_direction = app.directions[robot]
        app.positions[robot] = node
        app.directions[robot] = 4
        # tihs is a simple graph, i.e. there are no edges connecting nodes to
        # themselves. Raise an assertion error in case one is found
        assert old_node != node
        # before checking if the current node has been already discovered, add
        # the edge from old_node to the current node, in case it's missing. We
        # assume old_node to be already visited (excluding the case in which
        # the old_node is None), hence included in the graph
        if old_node and app.graph[old_node][old_direction][0] != node:
            app.graph[old_node][old_direction] = [node, weight]
        # check if the current node is included in the graph. If it already is,
        # update the edge starting from direction_in, if needed, otherwise
        # create it from scratch
        if node not in app.graph:
            # create a list with four elements representing the 4 possible
            # directions, all set to [None, -1], where None is an eventual node
            # and -1 the eventual weight
            app.graph[node] = [[None, -1]] * 4
        if old_node and app.graph[node][direction_in][0] != old_node:
            # update the list with information about the edge we used to enter
            # the current node
            app.graph[node][direction_in] = [old_node, weight]

    return json.dumps([app.graph, app.positions])

@app.route('/outupdate', methods = ['POST'])
def outupdate():
    robot = int(request.form['robot'])
    node = request.form['node']
    direction_out = int(request.form['dirin'])

    app.directions[robot] = direction_out
    try:
        out_edges = [
            request.form['n'],
            request.form['e'],
            request.form['s'],
            request.form['w']
        ]
        app.graph[node] = [['unknown', -1] if out_edges[i] == '1' else app.graph[node][i] for i in range(4)]
    except KeyError:
        pass

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    n_robots = 4

    # initialization of the shared data structures
    app.nodes = ['red', 'green', 'cyan', 'violet', 'unknown']
    app.positions = [None] * n_robots
    app.directions = [-1] * n_robots

    app.run(host='0.0.0.0', debug=True)

