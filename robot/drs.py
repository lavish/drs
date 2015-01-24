#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import sys
import signal
import zmq
import conf
import logging
import atexit
from time import sleep, time
from colorsys import rgb_to_hsv
from urllib2 import urlopen, URLError
from collections import deque
from threading import Thread
from enum import Enum
from ev3dev import *

__authors__ = ["Marco Squarcina <squarcina at dais.unive.it>"]
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
# zmq context definitions
context = zmq.Context()
# possible states
State = Enum('State', ('explore_node_init explore_node explore_edge_init '
                       'explore_edge_before_marker explore_edge escaping_init '
                       'escaping waiting_for_clearance moving_init '
                       'moving_before_marker moving idling '
                        'in_marker'))


# function definitions

def message_server():
    sock = context.socket(zmq.REP)
    sock.bind("tcp://0.0.0.0:{}".format(conf.message_port))
    
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

def follow_line(value, offset, pulses = conf.base_pulses):
    """Adjust the speed of the two motors to keep up with the line tracking."""

    error = value * 1000 - offset
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

    return rgb_to_hsv(*[col_sensor.value(i)/1022 for i in range(col_sensor.num_values())])

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

def in_border(saturation):
    return saturation > conf.saturation_thr

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
    sock.connect("tcp://192.168.10.101:{}".format(conf.message_port))
    logging.info("sending message")
    sock.send("HALT")
    logging.info("receiving message")
    print(sock.recv())
    '''

    # offset repesents the color on the line border. It is simply computed as
    # the average of the value (as in HSV) between the line and the border
    offset = (conf.line_value + conf.plane_value)/2

    greet()
    initialize()
    state = State.moving
    while True:
        # query the ir sensor in SEEK mode to avoid collisions
        avoid_collision()

        # read the HSV triple from the color sensor and act accordingly to the
        # protocol
        hue, saturation, value = get_hsv_colors()
        if state == State.moving:
            if in_border(saturation):
                # found a marker, we need to stop as soon as we find a matching
                # color
                state = State.in_marker
                stop_motors()
                sound.speak("Oh geez, I found a marker. Now I will go on slowly because it is boring to stay here!", True)
                start_motors()
            else:
                follow_line(value, offset)
        elif state == State.in_marker:
            follow_line(value, offset, 80)
        else:
            logging.critical("WTF?")
            break

    reset()
    # [TODO] join the MessageServer thread
    sys.exit(0)

if __name__ == '__main__':
    main()
