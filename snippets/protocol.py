from __future__ import division

from time import time, sleep

from enum import Enum

import dijkstra

States = Enum('States', 'explore_node_init explore_node explore_edge_init explore_edge_before_marker explore_edge escaping_init escaping waiting_for_clearance moving_init moving_before_marker moving idling')

global current_state = States.explore_node_init

global graph = dict()

global current_node = Color.red.value

global current_edge = [Color.red.value, (Color.unknown.value, -1), Direction.n.value]

#global unexplored_edges = []

global rotating_mate = None

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

def edge_update(source, source_orientation, destination, destination_orientation, edge_length):
    raise Exception('edge_update: Not implemented')

def get_seen_robots():
    raise Exception('get_seen_robots: Not implemented')

def on_marker():
    raise Exception('on_marker: Not implemented')

def identfy_marker():
    raise Exception('identfy_marker: Not implemented')

def explored():
    raise Exception('explored: Not implemented')

def identfy_node():
    raise Exception('identfy_node: Not implemented')

def release_lock(color):
    raise Exception('release_lock: Not implemented')

def lock(color):
    raise Exception('lock: Not implemented')

def is_locked(color):
    raise Exception('is_locked: Not implemented')

def is_edge_locked(edge):
    raise Exception('is_edge_locked: Not implemented')

def filter_locked(graph):
    raise Exception('filter_locked: Not implemented')

def right_of_way(seen_robots):
    raise Exception('right_of_way: Not implemented')

def reset_motor_position():
    raise Exception('reset_motor_position: Not implemented')

def get_motor_position():
    raise Exception('get_motor_position: Not implemented')

def turn_around():
    raise Exception('turn_around: Not implemented')

def notify_clearance():
    raise Exception('notify_clearance: Not implemented')

def filter_explored():
    raise Exception('filter_explored: Not implemented')

def seventeen():
    raise Exception('seventeen: Not implemented')

def update():
    while True:

        if state == States.explore_node_init:
            stop()
            inupdate()
            color = identify_node()
            current_node = color
            if not explored(color):
                rotate_in_node()
                #for edge in get_unexplored_edges(graph, current_node):
                #    unexplored_edges.append(edge)
            state = States.explore_node

        elif state == States.explore_node:
            unexplored_edges = get_min_available_unexplored(graph, current_node)
            if len(unexplored_edges) == 0:
                state = States.idling
            else:
                current_edge = unexplored_edges.pop()
                if current_edge[0] != current_node:
                    state = States.moving_init
                else:
                    if not is_edge_locked(current_edge):
                        state = States.explore_edge_init

        elif state == States.explore_edge_init:
            outupdate() # with direction or lock on edges
            move_to_edge(current_edge)
            state = States.explore_edge_before_marker

        elif state == States.explore_edge_before_marker:
            if on_marker():
                stop()
                color = identfy_marker()
                release_lock(color)
                reset_motor_position()
                state = States.explore_edge

        elif state == States.explore_edge:
            seen_robots = get_seen_robots()
            if not right_of_way(seen_robots):
                state = States.escaping_init
            elif len(seen_robots) > 0 and right_of_way(seen_robots):
                state = States.waiting_for_clearance 
                rotating_mate = seen_robots[0] # since there can only be one
                # I'm not saving old state because waiting for clearance can only happen on exploring, since moving has the lowest priority on edges
            if on_node():
                state = States.explore_node_init
            elif on_marker():
                stop()
                marker_color = identfy_marker()
                if is_locked(marker_color):
                    edge_length = get_motor_position()
                    edge_update(current_edge[0], (marker_color, edge_length), current_edge[2])
                    state = States.escaping_init
                else:
                    edge_length = get_motor_position()
                    orientation = get_orientation()
                    edge_update(current_edge[0], current_edge[2], marker_color, orientation, edge_length)
                    lock(color)

        elif state == States.escaping_init:
            turn_around() # check marker lock
            notify_clearance()
            state = States.escaping

        elif state == States.escaping:
            seen_robots = get_seen_robots()
            if on_node():
                state = States.explore_node_init
            elif on_marker():
                stop()
                marker_color = identfy_marker()
                if is_locked(marker_color):
                    state = escaping_init
                else:
                    lock(color)

        elif state == States.moving_init:
            available_graph = filter_locked(graph)
            next = get_next_direction(available_graph, current_node, current_edge[0])
            if next != None:
                state = States.moving
                outupdate() # with direction or lock on edges
                move_to_edge(current_edge)
                state = States.moving_before_marker
            else:
                get_other_destination()

        elif state == States.moving_before_marker:
            if on_marker():
                stop()
                color = identfy_marker()
                release_lock(color)
                state = States.moving

        elif state == States.moving:
            seen_robots = get_seen_robots()
            if len(seen_robots) > 0:
                unexplored_edges.append(current_edge) #source of possibles deadlocks... Maybe enqueue
                state = State.escaping_init
            if on_node():
                unexplored_edges.append(current_edge) #safe, no deadlocks
                state = States.explore_node_init
            elif on_marker():
                stop()
                marker_color = identfy_marker()
                if is_locked(marker_color):
                    unexplored_edges.append(current_edge) #source of possibles deadlocks... Maybe enqueue
                    state = States.escaping_init
                #missing


