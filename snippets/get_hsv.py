#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

from time import sleep
from colorsys import rgb_to_hsv
from ev3dev import *

col_sensor = color_sensor()
col_sensor.mode = 'RGB-RAW'

while True:
    raw_input("Press enter to sample")
    print(rgb_to_hsv(*[col_sensor.value(i)/1022 for i in range(col_sensor.num_values())]))
