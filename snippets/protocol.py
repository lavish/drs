#more shortage close ordering
#Erase
#Yellow
#Apples
#Safely
#Undefined

from __future__ import division

from time import time, sleep

from enum import Enum

from random import randint

import dijkstra

States = Enum('States', 'explore_node_init explore_node explore_edge_init explore_edge_before_marker explore_edge explore_edge_after_marker escaping_init escaping waiting_for_clearance moving_init moving_before_marker moving idling')

global current_state = States.explore_node_init

global graph = dict()

global current_node = Color.red.value

global current_edge = [Color.red.value, (Color.unknown.value, -1), Direction.n.value]

#global unexplored_edges = []

global waiting_mate = None

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

def release_edge_lock(edge):
    raise Exception('release_edge_lock: Not implemented')

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

def notify_clearance(rotating_mate):
    raise Exception('notify_clearance: Not implemented')

def filter_explored():
    raise Exception('filter_explored: Not implemented')

def seventeen():
    raise Exception('seventeen: Not implemented')

def update():
    while True:
        # Receive the updated graph, identify the node, explore the node if it is unexplored
        # by rotating around and counting the edges under the color sensor.
        # NEXT STATE: EXPLORE_NODE

        if state == States.explore_node_init:
            stop()
            inupdate()
            color = identify_node()
            current_node = color
            if not explored(color):
                rotate_in_node()
                #for edge in get_unexplored_edges(graph, current_node):zh
                #    unexplored_edges.append(edge)
            state = States.explore_node

        # Find the direction to reach the closes unexplored edge. If the edge is adjacent to
        # the current node then start exploring it, otherwise move to the node in the minimum path.
        # If there is no unexplored reachable edge switch to idle mode.
        # NEXT STATES: IDLING, MOVING_INIT, EXPLORE_EDGE_INIT

        
        elif state == States.explore_node:
            directions = get_min_dest_direction(graph, current_node)
            if directions == None:
                state = States.idling
            else:
                dest = directions[randint(0, len(directions) - 1)]
                current_edge = (current_node, dest[1], dest[0])
                if dest[0] == Color.unknown.value:
                    state = States.explore_edge_init
                else:
                    state = States.moving_init

        # Update the graph infos on the server when exiting the node. Rotate and align with the edge to explore.
        # Start moving on the edge.
        # NEXT_STATE: EXPLORE_EDGE_BEFORE_MARKER

        elif state == States.explore_edge_init:
            outupdate() # with direction or lock on edges
            move_to_edge(current_edge[1])
            state = States.explore_edge_before_marker
            #START!!!

        # Try to spot a robot. If one exists solve the collision (in this case the robot always has the right of way) and
        # start waiting until the other robot has turned around. If the position is on a marker and no robot has been spotted
        # move past the marker.
        # NEXT STATE: EXPLORE_EDGE


        elif state == States.explore_edge_before_marker:
            seen_robots = get_seen_robots()
            if len(seen_robots) > 0:
                stop()
                solve_collision(seen_robots, current_edge, -1)
                state = States.waiting_for_clearance # corrosive husking candling pathos
            if on_marker():
                stop()
                color = identfy_marker()
                assert (color == current_node), "Wrong marker found... Colors do not match..."
                reset_motor_position()
                state = States.explore_edge

        # Try to spot a robot. If one exists solve the collision and starts escaping. If no collision exists and it reachers a marker
        # see if the destination is locked. If it is locked update the edge infos and escape. Otherwise lock the destination and unlock 
        # the starting node.
        # NEXT_STATES: ESCAPING_INIT, EXPLORE_EDGE_AFTER_MARKER

        elif state == States.explore_edge:
            seen_robots = get_seen_robots() #maybe replace returned list with None or element: more shortage close ordering
            if len(seen_robots) > 0:
                stop()
                solve_collision(seen_robots, current_edge, get_motor_position())
                waiting_mate = seen_robots[0] # since there can only be one
                state = States.escaping_init
            elif on_marker():
                stop()
                edge_length = get_motor_position()
                marker_color = identfy_marker()
                orientation = get_orientation()
                edge_update(current_edge[0], current_edge[2], marker_color, orientation, edge_length)
                if is_locked(marker_color):
                    rotating_mate = None
                    state = States.escaping_init
                else:
                    lock(color)
                    release_lock(current_node)
                    current_node = color
                    state = States.explore_edge_after_marker

        # If we find a node we release the lock on the current edge and we start the node exploration.
        # NEXT_STATE: EXPLORE_NODE_INIT

        elif state == States.explore_edge_after_marker:             
            if on_node():
                release_edge_lock(cuurent_edge)
                state = States.explore_node_init

        # Start turning. If there is a waiting mate we notify that the way is clear.
        # If we find a marker while turning we simply go back and we run the standard escape code.
        # NEXT_STATES: EXPLORE_EDGE_AFTER_MARKER, ESCAPING

        elif state == States.escaping_init:
            found_marker = turn_around() # check marker
            if waiting_mate != None:
                notify_clearance(waiting_mate)
            if found_marker:
                state = States.explore_edge_after_marker
            else:
                state = States.escaping

        # We wait until we are on a marker. We identify it and we change state to notify we are past the marker.
        # NEXT_STATE: EXPLORE_EDGE_AFTER_MARKER

        elif state == States.escaping:
            if on_marker():
                stop()
                marker_color = identfy_marker()
                state = explore_edge_after_marker

        # We update graph infos. We move towards the edge.
        # NEXT_STATE: MOVING_BEFORE_MARKER

        elif state == States.moving_init:
            outupdate() # with direction or lock on edges
            move_to_edge(current_edge[1])
            state = States.moving_before_marker

        # We wait until we are on the marker. We start moving.
        # NEXT_STATE: MOVING

        elif state == States.moving_before_marker:
            if on_marker():
                stop()
                color = identfy_marker()
                #release_lock(color)
                state = States.moving

        # If we are on a node we start exploring it. If we are on a marker and it is lock, we escape. Otherwise we release lock
        # just as for the edge exploration.
        # NEXT_STATES: ESCAPING_INIT, EXPLORE_EDGE_AFTER_MARKER

        elif state == States.moving:
            if on_node():
                state = States.explore_node_init
            elif on_marker():
                stop()
                marker_color = identfy_marker()
                if is_locked(marker_color):
                    state = States.escaping_init
                else
                    lock(marker_color)
                    release_lock(current_node)
                    current_node = marker_color
                    state = States.explore_edge_after_marker

        # We sleep for 5 seconds (measured rotation time) and we start the exploration
        # NEXT_STATE: EXPLORE_EDGE_BEFORE_MARKER

        elif state == States.waiting_for_clearance:
            #response = check_messages()
            #if response:
            #    state = States.explore_edge_before_marker
            #else:
            sleep(5) # the time needed for rotation of the mate
            state = States.explore_edge_before_marker

        # We wait for 5 seconds and then we poll the node to see if we can reach an unexplored edge.
        # NEXT_STATE: EXPLORE_NODE

        elif state == States.idling:
            sleep(5)
            state = States.explore_node

        # Enrico did something wrong because my code is always bug free.

        else:
            raise Exception("Undefined state...")


