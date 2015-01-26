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
import ev3dev_utils
from time import sleep, time
from math import sqrt
from colorsys import rgb_to_hsv
from urllib2 import urlopen, URLError
from collections import deque
from threading import Thread
from enum import Enum
from ev3dev import *

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
State = Enum('State', ('explore_node_init explore_node explore_edge_init '
                       'explore_edge_before_marker explore_edge escaping_init '
                       'escaping waiting_for_clearance moving_init '
                       'moving_before_marker moving idling '
                        'in_marker'))

hsv_colors = {
    0: (0.03,0.89,0.21),
    1: (0.18,0.86,0.25),
    3: (0.27,0.83,0.18),
    4: (0.0,0.68,0.17),
    5: (0.15,0.67,0.13), # border
    6: (0.18,0.74,0.24),
    8: (0.28,0.62,0.04),
    11: (0.09,0.9,0.25),
    12: (0.22,0.7,0.04),
    15: (0.06,0.75,0.07),
    16: (0.11,0.86,0.13),
    17: (0.3,0.73,0.16),
    18: (0.34,0.62,0.16)
}

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
    motor_left.stop() #pulses_per_second_setpoint = 0
    motor_right.stop() #pulses_per_second_setpoint = 0

def start_motors():
    motor_left.run()
    motor_right.run()

def median(data):
    """Compute the median of the provided data."""

    data = sorted(data)
    n = len(data)
    if n == 0:
        raise Exception('No median for an empty list')
    if n%2 == 1:
        return data[n//2]
    else:
        i = n//2
        return (data[i-1] + data[i])/2

def wait_launch():
    """Wait the game to be started (click play on the web interface) before
    running."""

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
    motor_left.run_mode = motor.run_mode_forever
    motor_right.run_mode = motor.run_mode_forever
    motor_left.run()
    motor_right.run()

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
    
        print(ir_medians[robot_id][1], end = ' ')    
        if ir_medians[robot_id][1] < 20:
            # [TODO] handle collisions
            pass
    print()

def is_in_border(saturation):
    saturation = sum(hsv[1] for hsv in last_hsvs)/len(last_hsvs)
    return saturation > conf.border_saturation_thr

def flip():
    # reset position
    motor_left.position = 0
    motor_right.position = 0
    # start with a queue made only of white values
    last_values = deque(conf.plane_value for _ in range(conf.n_col_samples))

    while True:
        last_values.popleft()
        last_values.append(get_hsv_colors()[2])
        mean = (sum(last_values)/conf.n_col_samples)
        if motor_left.position > 200 and mean < mid_value:
            break
        elif motor_left.position < 600:
            # clockwise rotation
            motor_left.pulses_per_second_setpoint = conf.base_pulses
            motor_right.pulses_per_second_setpoint = -conf.base_pulses
        else:
            raise Exception("Lost the track")

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
        mean = sum(last_values)/conf.n_col_samples
        if mean < conf.line_value + 0.1:
            color = 'black'
        if mean > conf.plane_value - 0.1:
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

def cross_bordered_region():
    """Cross a bordered colored region like a marker or a node and return the
    color."""
    
    color = 0
    # assume that we are on a border
    state = 'first_border'

    motor_left.pulses_per_second_setpoint = conf.base_pulses//2
    motor_right.pulses_per_second_setpoint = conf.base_pulses//2

    while True:
        # sample color
        hsv_color = get_hsv_colors()

        if state == 'inside':
            # escape from the node using the saturation to determine the end of
            # the node area
            if not is_in_border(hsv_color[1]):
                state = 'outside'
            else:
                continue

        if state == 'outside':
            sleep(0.1)
            return color

        if state == 'first_border':
            actual_color = identify_color(hsv_color)
            if actual_color == 5:
                # still on the border, go on
                continue
            else:   
                state = 'inside'
                color = actual_color


def norm(a, b):
    """Heuristic corrections of the two colors
    - color near to red can be recognized with hue component near to 0 or 1
      (due to cylindrical hsv color space)
    - the height of the color sensor wrt the surface involves heavily on the
      value component."""

    # red correction on hue component and value reduction
    a, b = [(0 if (x[0] >= 0.9) else x[0], x[1], x[2]*0.3) for x in a, b]
    # euclidean distance of all components (hue, saturation, value)
    return sqrt(sum((a - b)**2 for a, b in zip(a, b)))

def identify_color(hsv_color):
    """Return the color that is closer to the provided triple."""

    # compute the distances among the acquired color and all known colors
    distances = {k : norm(v, hsv_color) for k, v in hsv_colors.iteritems()}
    # return the closest one
    return min(distances, key=distances.get)

def from_marker_to_node():
    pass

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

    '''
    # instance of the socket used for sending messages
    sock = context.socket(zmq.REQ)
    logging.info("connecting")
    sock.connect("tcp://192.168.10.101:{}".format(conf.robot_port))
    logging.info("sending message")
    sock.send("HALT")
    logging.info("receiving message")
    print(sock.recv())
    '''

    greet()
    initialize()
    marker_crossed = False
    state = State.moving
    while True:
        # query the ir sensor in SEEK mode to avoid collisions
        avoid_collision()

        # read the HSV triple from the color sensor and act accordingly to the
        # protocol
        hue, saturation, value = get_hsv_colors()
        if state == State.moving:
            if is_in_border(saturation):    
                if not marker_crossed:
                    # found a marker, we need to stop as soon as we find a
                    # matching color
                    state = State.in_marker
                    stop_motors()
                else:
                    color = cross_bordered_region()
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
            color = cross_bordered_region()
            stop_motors()
            marker_crossed = True
            logging.info("Found color {}".format(color))
            sound.speak("Found color {}".format(color), True)
            state = State.moving
            start_motors()
        else:
            logging.critical("WTF?")
            break

    reset()
    # [TODO] join the MessageServer thread
    sys.exit(0)

if __name__ == '__main__':
    main()
