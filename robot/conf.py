#!/usr/bin/python
# -*- coding: utf-8 -*-

from enum import Enum

# [CHANGE ME]
# set this value to reflect the id of your robot. Allowed values are [0..3]
robot_id = 0

# number of ir samples to consider for median calculation
n_ir_samples = 51

# constant for the line following task: the lower the smoother
proportional_const = 500

# we assume line_color to be darker than plane_color (actually line_value and
# plane_value have been multiplied by a factor of 1000)
line_value = 0.042
plane_value = 0.390
border_saturation_thr = 0.6
n_col_samples = 5

# power of both motors when running straight
base_pulses = 200
slow_pulses = 100
# number of cicles needed to complete a full 360 rotation
full_rotation_degrees = 905
turn_rotation_difference = 270

# web server ip/port
web_server_ip = '10.42.0.1'
web_server_port = 5000

# possible ips for robots
#robot_ips = ['192.168.1.10{}'.format(i) for i in range(1, 5)]
robot_ips = ['10.42.0.{}'.format(3+i) for i in range(1, 5)]
# tcp port used for the messaging protocol
robot_port = 31337

# all the possible colors assumed by the nodes in the graph, plus unknown
Color = Enum('Color', 'red yellow green magenta sadyellow darkgreen orange sadbrown darkred sadgreen cyan unknown')
hsv_colors = {
    'darkgreen': (0.28, 0.62, 0.04),
    'sadyellow': (0.18, 0.74, 0.24),
    'sadbrown': (0.22, 0.7, 0.04),
    'sadgreen': (0.3, 0.73, 0.16),
    'yellow': (0.18, 0.86, 0.25),
    'green': (0.27, 0.83, 0.18),
    'darkred': (0.06, 0.75, 0.07),
    'orange': (0.09, 0.9, 0.25),
    'cyan': (0.34, 0.62, 0.16),
    'magenta': (0.0, 0.68, 0.17),
    'red': (0.03, 0.89, 0.21)}
