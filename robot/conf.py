#!/usr/bin/python
# -*- coding: utf-8 -*-

from enum import Enum

# [CHANGE ME]
# set this value to reflect the id of your robot. Allowed values are [0..3]
my_robot_id = 0

# number of ir samples to consider for median calculation
n_ir_samples = 15

# constant for the line following task: the lower the smoother
proportional_const = 0.5

# we assume line_color to be darker than plane_color
line_value = 42
plane_value = 390

# power of both motors when running straight
base_pulses = 200

# web server ip/port
web_server_ip = '10.42.0.1'
web_server_port = 5000

# possible ips for robots
#robot_ips = ['192.168.1.10{}'.format(i) for i in range(1, 5)]
robot_ips = ['10.42.0.{}'.format(3+i) for i in range(1, 5)]
# tcp port used for the messaging protocol
message_port = 31337

# all the possible colors assumed by the nodes in the graph
Color = Enum('Color', 'red green cyan violet unknown')

saturation_thr = 0.6
