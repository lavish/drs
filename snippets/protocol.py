from __future__ import division

from time import time, sleep

from enum import Enum

import dijkstra

States = Enum('States', 'explore_node_init explore_node explore_edge_init explore_edge_before_marker explore_edge escaping_init escaping moving_init moving idling')

global current_state = States.explore_node_init

global graph = dict()

global current_node = Color.red.value

global current_edge = [Color.red.value, (Color.cyan.value, 6), Direction.n.value]

global unexplored_edges = []

def stop():
    raise Exception('Stop: Not implemented')

def inupdate():
    raise Exception('inupdate: To be imported')    

def outupdate():
    raise Exception('outupdate: To be imported')

def scan_node():
    raise Exception('scan_node: Not implemented')

def move_to_edge(edge):
    raise Exception('move_to_edge: Not implemented')

def get_seen_robots():
    raise Exception('get_seen_robots: Not implemented')

def on_marker():
    raise Exception('on_marker: Not implemented')

def identfy_marker():
    raise Exception('identfy_marker: Not implemented')

def release_lock(color):
    raise Exception('release_lock: Not implemented')

def right_on_way(seen_robots):
    raise Exception('right_on_way: Not implemented')

def update():
    while True:
        if state == States.explore_node_init:
            stop()
            inupdate()
            rotate_in_node()
            for edge in get_unexplored_edges(graph, current_node):
                unexplored_edges.append(edge)
            state = States.explore_node
        elif state == States.explore_node:
            if len(s) == 0:
                state = States.idling
            else:
                current_edge = unexplored_edges.pop()
                if current_edge[0] != current_node:
                    state = States.moving_init
                else
                    state = States.explore_edge_init
        elif state == States.explore_edge_init:
            outupdate()
            move_to_edge(current_edge)
            state = States.explore_edge_before_marker
        elif state == States.explore_edge_before_marker:
            if on_marker():
                stop()
                color = identfy_marker()
                release_lock(color)
                state = States.explore_edge
        elif state == States.explore_edge:
            seen_robots = get_seen_robots()
            if not right_on_way(seen_robots):


