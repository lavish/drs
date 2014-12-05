#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

from time import sleep
from ev3.ev3dev import Motor
from ev3.lego import LargeMotor
from ev3.lego import ColorSensor
import sys

# left motor
motor_b = LargeMotor(port = Motor.PORT.B)
# right motor
motor_c = LargeMotor(port = Motor.PORT.C)
color = ColorSensor()
tic = 0.01

def main():
    speed = 30
    black = 16
    white = 21
    gray = (black + white) // 2

    motor_b.run_forever(speed, regulation_mode=False)
    motor_c.run_forever(speed, regulation_mode=False)

    while True:
        try:
            sleep(tic)
            reflect = color.reflect

            if reflect > gray:
                # turn left
                cur_speed = int(round(max(min((white - reflect) * (speed * 2) / (white - gray) - speed, speed), -speed)))
                motor_b.run_forever(cur_speed, regulation_mode=False)
                motor_c.run_forever(speed, regulation_mode=False)   
            elif reflect < gray:
                # turn right
                cur_speed = int(round(max(min((black - reflect) * (speed * 2) / (black - gray) - speed, speed), -speed)))
                motor_b.run_forever(speed, regulation_mode=False)
                motor_c.run_forever(cur_speed, regulation_mode=False)
            else:
                # go straight
                motor_b.run_forever(speed, regulation_mode=False)
                motor_c.run_forever(speed, regulation_mode=False)
        except KeyboardInterrupt:
            motor_b.stop()
            motor_c.stop()
            sys.exit()

if __name__ == '__main__':
    main()
