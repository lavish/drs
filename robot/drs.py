#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import sys
import signal
import zmq
from colorsys import rgb_to_hsv
from collections import deque
from ev3.ev3dev import Motor
from ev3.lego import ColorSensor
from ev3.lego import InfraredSensor

__authors__ = ["Marco Squarcina <squarcina at dais.unive.it>"]
__status__  =  "Development"


# global variables 

# instances of motors
motor_left = Motor(port = Motor.PORT.D)
motor_right = Motor(port = Motor.PORT.B)
# instances of sensors
color_sensor = ColorSensor()
ir_sensor  = InfraredSensor()
# other variables
n_ir_samples = 15
ir_buffer = [[deque(), deque()] for _ in range(4)]
ir_medians = [[None, None] for _ in range(4)]
# zmq context and sockets definitions
context = zmq.Context()
sock_in = context.socket(zmq.REP)
sock_out = context.socket(zmq.REQ)

# function definitions

def stop(signal = None, frame = None):
    motor_left.stop()
    motor_right.stop()
    if signal:
        sys.exit(1)

def median(data):
    data = sorted(data)
    n = len(data)
    if n == 0:
        raise Exception('No median for an empty list')
    if n%2 == 1:
        return data[n//2]
    else:
        i = n//2
        return (data[i-1] + data[i])/2

def main():
    signal.signal(signal.SIGINT, stop)
   

    motor_left.polarity_mode = 'normal'
    motor_right.polarity_mode = 'normal'

    # tunable constant
    proportional_const = 0.2

    # we assume line_color to be darker than plane_color
    line_light = 85
    plane_light = 266
    # offset repesents the color on the line border. It is simply computed as
    # the average of line_color and plane_color
    offset = (line_light + plane_light)/2
    # power of both motors when running straight
    target_power = 25
 
    while True:
        # query the ir sensor in SEEK mode to avoid collisions
        seek = ir_sensor.seek
        for chan in range(4):
            # remove the heads
            if len(ir_buffer[chan][0]) >= n_ir_samples:
                ir_buffer[chan][0].popleft()
                ir_buffer[chan][1].popleft()
            # update the angle
            ir_buffer[chan][0].append(seek[chan][0])
            # update the distance
            ir_buffer[chan][1].append(abs(seek[chan][1]))
            # recompute the median
            ir_medians[chan][0] = median(ir_buffer[chan][0]) 
            ir_medians[chan][1] = median(ir_buffer[chan][1])
            
        print(ir_medians)

        # update the speed of each motor
        value = rgb_to_hsv(*color_sensor.rgb)[2]
        error = value - offset
        turn = proportional_const * error
        power_left = target_power + turn
        power_right = target_power - turn
        try:
            motor_left.run_forever(power_left, regulation_mode = False)
            motor_right.run_forever(power_right, regulation_mode = False)
        except IOError:
            pass

    stop()
    sys.exit(0)

if __name__ == '__main__':
    main()
