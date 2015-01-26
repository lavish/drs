#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import sys
import signal
import zmq
import conf
import logging
import atexit
import random
from time import sleep, time
from math import sqrt
from colorsys import rgb_to_hsv
from urllib2 import urlopen, URLError
from collections import deque
from threading import Thread
from enum import Enum
from ev3dev import *
from ev3dev_utils import *

# [TODO] are all the mails correct?
__authors__ = ["Marco Squarcina <squarcina at dais.unive.it>", 
               "Enrico Steffinlongo <enrico.steffinlongo at unive.it>",
               "Francesco Di Giacomo <fdigiacom at gmail.com>",
               "Michele Schiavinato <mschiavi at dais.unive.it>",
               "Alan Del Piccolo <alan.delpiccolo at gmail.com>",
               "Filippo Cavallin <840031 at stud.unive.it>",
               "Eyasu Zemene Mequanint <eyasu201011 at gmail.com>"]

__status__  =  "Development"


# global variables 

# instances of motors
motor_left = large_motor(OUTPUT_D)
motor_right = large_motor(OUTPUT_B)
# instances of sensors
col_sensor = color_sensor()
ir_sensor  = infrared_sensor()
# other variables
ir_buffer = [[deque(), deque()] for _ in range(4)]
ir_medians = [[None, None] for _ in range(4)]
# mean between the value of the line and the plane
mid_value = (conf.line_value + conf.plane_value)/2
# queue of the last samples taken by the color sensor
last_hsvs = deque()

# zmq context definitions
context = zmq.Context()
# possible states
State = Enum('State', ('begin explore_node_init explore_node '
                       'explore_edge_init explore_edge_before_marker '
                       'explore_edge explore_edge_after_marker escaping_init '
                       'escaping waiting_for_clearance moving_init '
                       'moving_before_marker moving moving_after_marker idling'))

# function definitions

def message_server():
    sock = context.socket(zmq.REP)
    sock.bind("tcp://0.0.0.0:{}".format(conf.robot_port))
    
    # log incoming messages and reply back
    # [TODO] define a poison pill to kill this thread
    while True:
        message = sock.recv()
        sock.send("Echoed: [{}]".format(message))
        logging.info(message)

def reset(signal = None, frame = None):
    """Stop the motors. [FIXME] is it possible to break?"""

    motor_left.reset()
    motor_right.reset()
    if signal:
        sys.exit(1)

def stop_motors():
    motor_left.stop()
    motor_right.stop()

def start_motors():
    motor_left.run()
    motor_right.run()

def wait_launch():
    """Block until the game is started (click play on the web interface)."""

    url_to_check = "http://{}:{}/started".format(
        conf.web_server_ip, conf.web_server_port)
    started = False
    while not started:
        try:
            f = urlopen(url_to_check)
            started = True if f.read() == '1' else False
        except URLError:
            logging.error('Unable to connect to the web server, proceeding')
            break
        sleep(0.5)

def greet():
    """Say hello before starting the protocol."""

    # set the second parameter to False for non-blocking call
    sound.speak("Hello, I am the robot number {}".format(conf.my_robot_id), True)

def follow_line(value, pulses = conf.base_pulses):
    """Adjust the speed of the two motors to keep up with the line tracking."""

    error = value - mid_value
    correction = int(conf.proportional_const * error)
    motor_left.pulses_per_second_setpoint = pulses + correction
    motor_right.pulses_per_second_setpoint = pulses - correction

def initialize():
    # explicitly set the color sensor in RGB mode
    col_sensor.mode = 'RGB-RAW'
    # explicitly set the infrared sensor in SEEK mode
    ir_sensor.mode = infrared_sensor.mode_ir_seeker
    # prepare the motors
    motor_left.regulation_mode = motor.mode_on
    motor_right.regulation_mode = motor.mode_on
    # set motors ready to run
    start_motors()

def get_hsv_colors():
    """Return the Hue, Saturation, Value triple of the sampled color assuming
    that the color sensor is in RAW-RGB mode."""

    hsv = rgb_to_hsv(*[col_sensor.value(i)/1022 for i in range(col_sensor.num_values())])
    if len(last_hsvs) >= conf.n_col_samples:
        last_hsvs.popleft()
    last_hsvs.append(hsv)

    return hsv

def avoid_collision():
    # query the ir sensor in SEEK mode to avoid collisions
    seek = [ir_sensor.value(i) for i in range(ir_sensor.num_values())]
    for robot_id in range(4):
        # remove the heads
        if len(ir_buffer[robot_id][0]) >= conf.n_ir_samples:
            ir_buffer[robot_id][0].popleft()
            ir_buffer[robot_id][1].popleft()
        # update the angle
        ir_buffer[robot_id][0].append(seek[robot_id*2])
        # update the distance
        ir_buffer[robot_id][1].append(abs(seek[robot_id*2+1]))
        # recompute the median
        ir_medians[robot_id][0] = median(ir_buffer[robot_id][0]) 
        ir_medians[robot_id][1] = median(ir_buffer[robot_id][1])
    
        if ir_medians[robot_id][1] < 20:
            # [TODO] handle collisions
            pass

def identify_color(hsv_color):
    """Return the string id of the color closer to the provide HSV triple."""

    # compute the distances among the acquired color and all known colors
    distances = {k : color_distance(v, hsv_color) for k, v in conf.hsv_colors.iteritems()}
    # return the closest one
    return min(distances, key=distances.get)

def on_border():
    """Use the saturation mean to see if we fall on a border."""

    saturation = mean([hsv[1] for hsv in last_hsvs])
    return saturation > conf.border_saturation_thr

def choose_random_direction(edges):
    direction = random.choice([i for i in range(4) if edges[i]])
    return direction

def rotate(direction = -1):
    """Rotate within a node.

    This function can be used to identify all the out edges starting from the
    current node or, when a direction is provided, to perform a rotation until
    the given direction is reached. Return the list of discovered edges in the
    first case, else nothing."""

    # if the direction is 0 we are already in the right place, there's nothing
    # to do
    if direction == 0:
        return

    # reset position
    motor_left.position = 0
    motor_right.position = 0

    # start with a queue made only of white values
    # [TODO] there's a global queue for handling this, we should use it
    last_values = deque(conf.plane_value for _ in range(conf.n_col_samples))
    # ... and obviously assume that the previous color is white
    prev_color = color = 'white'

    # list of edges to be returned in case we are in discovery mode
    edges = [False for _ in range(4)]

    # start rotating at half of the maximum allowed speed
    motor_left.pulses_per_second_setpoint = conf.base_pulses//2
    motor_right.pulses_per_second_setpoint = -conf.base_pulses//2

    while True:
        # leave if a 360 degrees rotation has been done
        if motor_left.position > conf.full_rotation_degrees:
            break

        # update the queue of sampled color values
        last_values.popleft()
        last_values.append(get_hsv_colors()[2])

        # update the current color according to the sampled value
        mean_value = mean(last_values)
        if mean_value < conf.line_value + 0.1:
            color = 'black'
        if mean_value > conf.plane_value - 0.1:
            color = 'white'

        # from white we just fallen on a black line
        if prev_color != color and color == 'black':
            cur_direction = int(round(motor_left.position / (conf.full_rotation_degrees//4)))
            if cur_direction == direction:
                # arrived at destination, it's time to leave ;)
                break
            elif cur_direction <= 3:
                # keep trace of the new edge just found 
                edges[cur_direction] = True
            else:
                # this is the 5th edge, we are back in the starting position on
                # a node with 4 edges, we should stop here
                break
        prev_color = color

    return edges if direction == -1 else None

def cross_bordered_area(marker=True):
    """Cross a bordered colored region and return the color."""
    
    color = conf.Color.unknown
    low_pulses = conf.base_pulses//3
    # assume that we are on a border
    local_state = 'border'
    if not marker:
        # if we are on a node just go straight until the end is reached because
        # we have already sampled the color in the previous marker
        local_state = 'sampled'
        run_for(motor_left, ever=True, power=low_pulses)
        run_for(motor_right, ever=True, power=low_pulses)
    count = 0

    while True:
        # sample color
        hsv_color = get_hsv_colors()

        if local_state == 'border':
            # slightly move forward so that we are exactly over the color
            stop_motors()
            sleep(1)
            start_motors()
            run_for(motor_left, power=low_pulses, degrees=10)
            run_for(motor_right, power=low_pulses, degrees=10)
            sleep(0.5)
            local_state = 'inside'
            # start moving again
            run_for(motor_left, ever=True, power=low_pulses)
            run_for(motor_right, ever=True, power=low_pulses)
        elif local_state == 'inside':
            # time to pick up some samples to identify the color
            count += 1
            if count >= conf.n_col_samples:
                mean_hsv_color = mean(list(last_hsvs))
                color = conf.Color[identify_color(hsv_color)]
                local_state = 'sampled'
                logging.info(color)
        elif local_state == 'sampled':
            # determine the end of the bordered area using the saturation
            if not on_border():
                return color
        else:
            raise Exception("Uh?")

def turn_around():
    """Change direction to avoid collisions and tell if a marker is found."""

    marker_found = False
    # reset position
    motor_left.position = 0
    motor_right.position = 0
    # start with a queue made only of white values
    for _ in range(conf.n_col_samples):
        last_hsvs.append((0, 0, conf.plane_value))

    while True:
        get_hsv_colors()
        # check if we are on a marker, this is kind of a code duplication, but
        # it's much faster than computing the mean of the same list two times
        # in a row
        _, saturation, value = mean(last_hsvs)

        if saturation > conf.border_saturation_thr:
            marker_found = True
            if motor_left.position > conf.full_rotation_degrees//2:
                # we are performing the rotation ovr the marker
                break
        elif motor_left.position > conf.full_rotation_degrees//3 and value < mid_value:
            # we performed the turn_around and we are back on track
            break
        elif motor_left.position < conf.full_rotation_degrees*0.75:
            # clockwise rotation
            motor_left.pulses_per_second_setpoint = conf.slow_pulses
            motor_right.pulses_per_second_setpoint = -conf.slow_pulses
        else:
            raise Exception("Lost the track")

    return marker_found

def mean(data):
    """Compute the mean of the provided data."""

    n = len(data)
    try:
        return [float(sum(l))/len(l) for l in zip(*data)]
    except TypeError:
        return sum(data)/n

def median(data):
    """Compute the median of the provided data, used for ir smoothing."""

    data = sorted(data)
    n = len(data)
    if n == 0:
        raise Exception('No median for an empty list')
    if n%2 == 1:
        return data[n//2]
    else:
        i = n//2
        return (data[i-1] + data[i])/2

def color_distance(a, b):
    """Compute the euclidean distance of 2 values.

    This function also accounts for the heuristic corrections of the two
    colors. Color near to red can be recognized with hue component near to 0 or
    1 (due to cylindrical hsv color space). On the other hand, the height of
    the color sensor wrt the surface involves heavily on the value component,
    so we reduce the value by a constant multiplicative factor."""

    # red correction on hue component and value reduction
    a, b = [(0 if (x[0] >= 0.9) else x[0], x[1], x[2]*0.3) for x in a, b]
    # euclidean distance of all components (hue, saturation, value)
    return sqrt(sum((a - b)**2 for a, b in zip(a, b)))

def get_orientation(old_orientation):
    delta_motors = motor_left.position - motor_right.position
    orientation = int(round(delta_motors / conf.turn_rotation_difference) + old_orientation) % 4 

    return orientation

# [TODO] remove source and source_orientation since it's not needed, the server
# can deduce both using the position list
def edge_update(destination_node, destination_orientation, edge_length):
    raise Exception('edge_update: Not implemented')

def update():
    """OMG our huge state machine!!!!!!! x_X."""
    
    state = State.begin
    orientation = conf.robot_id
    current_node = Color.unknown
    graph = dict()

    while True:
        # [TODO] insert here control operations (e.g. follow_line, sample
        # colors, etc) wrt states

        # update the global color queue
        get_hsv_colors()

        # Begin before a marker, update the vertex infos.
        # NEXT_STATE: EXPLORE_EDGE_AFTER_MARKER.
        if state == State.begin:
            if on_border():
                stop_motors()
                color = cross_bordered_area(marker = True)
                orientation = get_orientation()
                graph, _ = edge_update(color, orientation, -1)
                state = State.explore_edge_after_marker

        # Receive the updated graph, identify the node, explore the node if it is unexplored
        # by rotating around and counting the edges under the color sensor.
        # NEXT STATE: EXPLORE_NODE
        elif state == State.explore_node_init:
            cross_bordered_area(maker=False)
            if not explored(color):
                edges = rotate_in_node()
                # [TODO] update local graph
            state = State.explore_node

        # Find the direction to reach the closes unexplored edge. If the edge is adjacent to
        # the current node then start exploring it, otherwise move to the node in the minimum path.
        # If there is no unexplored reachable edge switch to idle mode.
        # NEXT STATES: IDLING, MOVING_INIT, EXPLORE_EDGE_INIT

        
        elif state == State.explore_node:
            directions = get_min_dest_direction(graph, current_node)
            if directions == None:
                state = State.idling
            else:
                dest = directions[randint(0, len(directions) - 1)]
                current_edge = (current_node, dest[1], dest[0])
                if dest[0] == Color.unknown.value:
                    state = State.explore_edge_init
                else:
                    state = State.moving_init

        # Update the graph infos on the server when exiting the node. Rotate and align with the edge to explore.
        # Start moving on the edge.
        # NEXT_STATE: EXPLORE_EDGE_BEFORE_MARKER

        elif state == State.explore_edge_init:
            outupdate() # with direction or lock on edges
            move_to_edge(current_edge[1])
            state = State.explore_edge_before_marker
            #START!!!

        # Try to spot a robot. If one exists solve the collision (in this case the robot always has the right of way) and
        # start waiting until the other robot has turned around. If the position is on a marker and no robot has been spotted
        # move past the marker.
        # NEXT STATE: EXPLORE_EDGE


        elif state == State.explore_edge_before_marker:
            seen_robots = get_seen_robots()
            if len(seen_robots) > 0:
                stop()
                solve_collision(seen_robots, current_edge, -1)
                state = State.waiting_for_clearance # corrosive husking candling pathos
            if on_border():
                stop()
                cross_bordered_area()
                reset_motor_position()
                state = State.explore_edge

        # Try to spot a robot. If one exists solve the collision and starts escaping. If no collision exists and it reachers a marker
        # see if the destination is locked. If it is locked update the edge infos and escape. Otherwise lock the destination and unlock 
        # the starting node.
        # NEXT_STATES: ESCAPING_INIT, EXPLORE_EDGE_AFTER_MARKER

        elif state == State.explore_edge:
            seen_robots = get_seen_robots() #maybe replace returned list with None or element: more shortage close ordering
            if len(seen_robots) > 0:
                stop()
                solve_collision(seen_robots, current_edge, get_motor_position())
                state = State.escaping_init
            elif on_border():
                stop()
                edge_length = get_motor_position()
                marker_color = cross_bordered_area()
                orientation = get_orientation()
                is_locked = edge_update(current_edge[0], current_edge[2], marker_color, orientation, edge_length)
                if is_locked:
                    state = State.escaping_init
                else:
                    current_node = marker_color
                    state = State.explore_edge_after_marker

        # If we find a node we release the lock on the current edge and we start the node exploration.
        # NEXT_STATE: EXPLORE_NODE_INIT

        elif state == State.explore_edge_after_marker:             
            if on_border():
                state = State.explore_node_init

        # Start turning. If there is a waiting mate we notify that the way is clear.
        # If we find a marker while turning we simply go back and we run the standard escape code.
        # NEXT_STATES: EXPLORE_EDGE_AFTER_MARKER, ESCAPING

        elif state == State.escaping_init:
            found_marker = turn_around() # check marker
            #if waiting_mate != None:
            #    notify_clearance(waiting_mate) # to be removed if waiting_for_clearance only sleeps for some seconds
            if found_marker:
                state = State.explore_edge_after_marker
            else:
                state = State.escaping

        # We wait until we are on a marker. We identify it and we change state to notify we are past the marker.
        # NEXT_STATE: EXPLORE_EDGE_AFTER_MARKER

        elif state == State.escaping:
            if on_border():
                stop()
                cross_bordered_area()
                state = State.explore_edge_after_marker

        # We update graph infos. We move towards the edge.
        # NEXT_STATE: MOVING_BEFORE_MARKER

        elif state == State.moving_init:
            outupdate() # with direction or lock on edges
            move_to_edge(current_edge[1])
            state = State.moving_before_marker

        # We wait until we are on the marker. We start moving.
        # NEXT_STATE: MOVING

        elif state == State.moving_before_marker:
            if on_border():
                stop()
                cross_bordered_area()
                state = State.moving

        # If we are on a node we start exploring it. If we are on a marker and it is lock, we escape. Otherwise we release lock
        # just as for the edge exploration.
        # NEXT_STATES: ESCAPING_INIT, EXPLORE_EDGE_AFTER_MARKER

        elif state == State.moving:
            if on_border():
                stop()
                marker_color = cross_bordered_area()
                can_enter = inupdate(marker_color)
                if can_enter:
                    current_node = marker_color
                    state = State.explore_edge_after_marker
                else:
                    state = State.escaping_init


        elif state == State.moving_after_marker:
            if on_border():
                state = State.explore_node_init
                
        # We sleep for 5 seconds (measured rotation time) and we start the exploration
        # NEXT_STATE: EXPLORE_EDGE_BEFORE_MARKER

        elif state == State.waiting_for_clearance:
            #response = check_messages()
            #if response:
            #    state = State.explore_edge_before_marker
            #else:
            sleep(5) # the time needed for rotation of the mate
            state = State.explore_edge_before_marker

        # We wait for 5 seconds and then we poll the node to see if we can reach an unexplored edge.
        # NEXT_STATE: EXPLORE_NODE

        elif state == State.idling:
            sleep(5)
            state = State.explore_node

        # Enrico did something wrong because my code is always bug free.

        else:
            raise Exception("Undefined state...")

def main():
    # register anti-panic handlers
    signal.signal(signal.SIGINT, reset)
    atexit.register(reset)

    # configure how logging should be done
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-10s) %(message)s', )

    # parse command line options
    if len(sys.argv) > 1 and sys.argv[1] == '--wait':
        # wait the protocol to be started
        wait_launch()

    # create a thread for reading incoming zmq messages
    server = Thread(name='MessageServer', target=message_server)
    server.setDaemon(True)
    server.start()
    # [TODO] create the socket for sending messages

    greet()
    initialize()
    update()
    reset()
    # [TODO] join the MessageServer thread
    sys.exit(0)

    '''
    while True:
        # query the ir sensor in SEEK mode to avoid collisions
        avoid_collision()

        # read the HSV triple from the color sensor and act accordingly to the
        # protocol
        hue, saturation, value = get_hsv_colors()
        if state == State.moving:
            if on_border():
                if not marker_crossed:
                    # found a marker, we need to stop as soon as we find a
                    # matching color
                    state = State.in_marker
                    stop_motors()
                else:
                    color = cross_bordered_area(marker=False)
                    available_edges = rotate()
                    stop_motors()
                    sound.speak("Found edges on positions {}".format(', '.join(str(i) for i in range(4) if available_edges[i])), True)
                    direction = choose_random_direction(available_edges)
                    sound.speak("Moving to direction {}".format(direction), True)
                    start_motors()
                    rotate(direction)
                    stop_motors()
                    break
            else:
                follow_line(value)
        elif state == State.in_marker:
            #sound.speak("I found a marker!", True)
            start_motors()
            # go straight until the border is found (end of the marker reached)
            color = cross_bordered_area()
            stop_motors()
            marker_crossed = True
            logging.info("Found color {}".format(color))
            sound.speak("Found color {}".format(color), True)
            state = State.moving
            start_motors()
        else:
            logging.critical("WTF?")
            break
    '''

if __name__ == '__main__':
    main()
