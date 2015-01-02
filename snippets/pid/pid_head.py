#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
A PID controller suitable for line following, with little added bells and
whistles.

Inspiration for this code has been taken from 
    
    http://www.inpharmix.com/jps/PID_Controller_For_Lego_Mindstorms_Robots.html

Tuning parameters can be performed using the formula below. Pay attention to
environmental conditions since they may affect parameter tuning.

    critical_gain = 140
    oscillation_period = 0.6
    time_per_loop = 0.042

    proportional_const = 0.60 * critical_gain
    integral_const = 2 * proportional_const * time_per_loop / oscillation_period
    derivative_const = proportional_const*oscillation_period/(8*time_per_loop)

"""

from __future__ import division, print_function

import sys
import signal
from time import time, sleep
from ev3.ev3dev import Motor
from ev3.lego import ColorSensor
from ev3.lego import InfraredSensor

__authors__ = ["Marco Squarcina <squarcina at dais.unive.it>"]
__status__  =  "Development"


# global variables (instances of sensors/motors)

ir_sensor = InfraredSensor()
motor_head = Motor(port = Motor.PORT.A)
motor_left = Motor(port = Motor.PORT.D)
motor_right = Motor(port = Motor.PORT.B)
color_sensor = ColorSensor()


# function definitions

def stop(signal = None, frame = None):
    """Stop all the motors and exit if a Ctrl-C is triggered."""

    motor_left.stop()
    motor_right.stop()
    motor_head.stop()
    if signal:
        sys.exit(1)

def rotate_head(angle, speed=200):
    """Rotate the head by a desired angle from 0 to 180."""

    motor_head.run_position_limited(position_sp=angle, speed_sp=speed,
                                    regulation_mode=True)

def main():
    # bind Ctrl-C to the execution of the stop() function
    signal.signal(signal.SIGINT, stop)
   
    # tunable constants for the PID controller
    proportional_const = 84
    integral_const = 12
    derivative_const = 150
    # we assume line_color to be darker than plane_color. Adjust these values
    # according to environmental conditions
    line_color = 9
    plane_color = 68
    # offset repesents the color on the line border. It is simply computed as
    # the average of line_color and plane_color
    offset = (line_color + plane_color)//2
    # power of both motors when running straight (error = 0)
    target_power = 70
    # adjust the bot speed from 0 to target_power when an obstacle is found
    # within the range below
    max_distance = 70
    min_distance = 40
    # naively assume that the turn value corresponds to the degrees of rotation
    rotation_const = 1

    # PID values
    integral = 0
    last_error = 0
    derivative = 0
    last_turns = []
    # line slope controlling the actual speed, precomputed before entering the
    # while loop for better performance
    slope = 1 / (max_distance - min_distance)

    # invert the polarity so that the robot can move forward by providing
    # positive values for the motors
    motor_left.polarity_mode = 'inverted'
    motor_right.polarity_mode = 'inverted'
    # put the head motor to the left so that we can set position 0 when it is on a
    # known position (looking on the left side)
    motor_head.run_time_limited(time_sp=1000, speed_sp=-40, regulation_mode=False)
    sleep(1)
    motor_head.position = 0

    while True:
        # adjust the power by a speed factor so that the robot slows down when
        # it is close to an obstacle and speeds up when there's nothing on its
        # way
        speed_factor = max(min(slope * (ir_sensor.prox - min_distance), 1), 0)

        # update the PID controller values
        error = color_sensor.reflect - offset
        integral = integral + error
        derivative = error - last_error
        turn = proportional_const*error + integral_const*integral \
             + derivative_const*derivative
        turn = turn/100
        power_left = speed_factor * (target_power + turn)
        power_right = speed_factor * (target_power - turn)

        # change the power provided to the motors, if actual_power is out of
        # the accepted range (+/- 100) just ignore the error (should be faster
        # than value normalization)
        try:
            motor_left.run_forever(power_left, regulation_mode=False)
            motor_right.run_forever(power_right, regulation_mode=False)
        except IOError:
            pass

        # update error for the next loop 
        last_error = error
        
        # smoothly rotate the head in the turning direction
        last_turns.insert(0, turn)
        if len(last_turns) == 5:
            rotation = sum(last_turns)/5
            rotate_head(rotation_const * rotation + 92)
            last_turns.pop()
               
    sys.exit(0)

if __name__ == '__main__':
    main()
