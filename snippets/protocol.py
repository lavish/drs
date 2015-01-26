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

States = Enum('States', 'begin explore_node_init explore_node explore_edge_init explore_edge_before_marker explore_edge explore_edge_after_marker escaping_init escaping waiting_for_clearance moving_init moving_before_marker moving moving_after_marker idling')

global state = States.explore_node_init

global graph = dict()

global bots_positions = []

global current_node = Color.red.value

global current_edge = [Color.red.value, (Color.unknown.value, -1), Direction.n.value]

global waiting_mate = None  # to be removed if waiting_for_clearance only sleeps for some seconds

global my_id = 0

def stop():
    raise Exception('Stop: Not implemented')

def inupdate():
    raise Exception('inupdate: To be imported')    

def outupdate():
    raise Exception('outupdate: To be imported')

def update_global():
    raise Exception('update_graph: Not implemented')
    updated_graph, updated_bots_positions = query_server()
    graph = updated_graph
    bots_positions = updated_bots_positions
    #return updated_graph, updated_bots_positions

# [TODO] remove source and source_orientation since it's not needed, the server
# can deduce both using the position list
def edge_update(source, source_orientation, destination, destination_orientation, edge_length):
    raise Exception('edge_update: Not implemented')

# [TODO] on the flask server, create a page for updating the edges of the
# graph. This page will be invoked by one of the colliding bots. We suppose
# that only one of the two bots will perform the aforementioned request (let
# them play morra cinese lolz)
def solve_collision(seen_robots, current_edge, travelled_distance):
    raise Exception('solve_collision: Not implemented')
    #if travelled_distance == -1: the bot is before marker

def notify_clearance(rotating_mate): # to be removed if waiting_for_clearance only sleeps for some seconds
    raise Exception('notify_clearance: Not implemented') # to be removed if waiting_for_clearance only sleeps for some seconds

def rotate_in_node():
    raise Exception('rotate_in_node: Not implemented')

def move_to_edge(direction):
    raise Exception('move_to_edge: Not implemented')

# [TODO] maybe it's not needed since locking is done by the server during the
# /inupdate call
def update_lock(color):
    raise Exception('update_lock: Not implemented')

#def release_lock(color):
#    raise Exception('release_lock: Not implemented')

def is_locked(color):
    update_global()
    other_positions = [p for i, p in enumerate(bots_positions) if i != my_id]
    return dijkstra.contains(lambda pos: pos == color, other_positions)

def explored(color):
    return dijkstra.explored(graph, color)

def turn_around():
    raise Exception('turn_around: Not implemented')

def get_seen_robots():
    raise Exception('get_seen_robots: Not implemented')

def on_border():
    raise Exception('on_border: Not implemented')

def on_border():
    raise Exception('on_border: Not implemented')

def cross_bordered_area():
    raise Exception('cross_bordered_area: Not implemented')

def identfy_node():
    raise Exception('identfy_node: Not implemented')

def reset_motor_position():
    raise Exception('reset_motor_position: Not implemented')

def get_motor_position():
    raise Exception('get_motor_position: Not implemented')

def get_orientation():
    raise Exception('get_orientation: Not implemented')


def update():
    while True:

        # Begin before a marker, update the vertex infos.
        # NEXT_STATE: EXPLORE_EDGE_AFTER_MARKER.

        if state == States.begin:
            if on_border():
                stop()
                marker_color = cross_bordered_area()
                orientation = get_orientation()
                edge_update(Color.unknown.value, -1, marker_color, orientation, -1)
                current_node = marker_color
                state = States.explore_edge_after_marker

        # Receive the updated graph, identify the node, explore the node if it is unexplored
        # by rotating around and counting the edges under the color sensor.
        # NEXT STATE: EXPLORE_NODE

        elif state == States.explore_node_init:
            cross_bordered_area(maker=False)
            if not explored(color):
                edges = rotate_in_node()
                # [TODO] update local graph
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
            if on_border():
                stop()
                cross_bordered_area()
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
                state = States.escaping_init
            elif on_border():
                stop()
                edge_length = get_motor_position()
                marker_color = cross_bordered_area()
                orientation = get_orientation()
                is_locked = edge_update(current_edge[0], current_edge[2], marker_color, orientation, edge_length)
                if is_locked:
                    state = States.escaping_init
                else:
                    current_node = marker_color
                    state = States.explore_edge_after_marker

        # If we find a node we release the lock on the current edge and we start the node exploration.
        # NEXT_STATE: EXPLORE_NODE_INIT

        elif state == States.explore_edge_after_marker:             
            if on_border():
                state = States.explore_node_init

        # Start turning. If there is a waiting mate we notify that the way is clear.
        # If we find a marker while turning we simply go back and we run the standard escape code.
        # NEXT_STATES: EXPLORE_EDGE_AFTER_MARKER, ESCAPING

        elif state == States.escaping_init:
            found_marker = turn_around() # check marker
            #if waiting_mate != None:
            #    notify_clearance(waiting_mate) # to be removed if waiting_for_clearance only sleeps for some seconds
            if found_marker:
                state = States.explore_edge_after_marker
            else:
                state = States.escaping

        # We wait until we are on a marker. We identify it and we change state to notify we are past the marker.
        # NEXT_STATE: EXPLORE_EDGE_AFTER_MARKER

        elif state == States.escaping:
            if on_border():
                stop()
                cross_bordered_area()
                state = States.explore_edge_after_marker

        # We update graph infos. We move towards the edge.
        # NEXT_STATE: MOVING_BEFORE_MARKER

        elif state == States.moving_init:
            outupdate() # with direction or lock on edges
            move_to_edge(current_edge[1])
            state = States.moving_before_marker

        # We wait until we are on the marker. We start moving.
        # NEXT_STATE: MOVING

        elif state == States.moving_before_marker:
            if on_border():
                stop()
                cross_bordered_area()
                state = States.moving

        # If we are on a node we start exploring it. If we are on a marker and it is lock, we escape. Otherwise we release lock
        # just as for the edge exploration.
        # NEXT_STATES: ESCAPING_INIT, EXPLORE_EDGE_AFTER_MARKER

        elif state == States.moving:
            if on_border():
                stop()
                marker_color = cross_bordered_area()
                can_enter = inupdate(marker_color)
                if can_enter:
                    current_node = marker_color
                    state = States.explore_edge_after_marker
                else:
                    state = States.escaping_init


        elif state == States.moving_after_marker:
            if on_border():
                state = States.explore_node_init
                
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


