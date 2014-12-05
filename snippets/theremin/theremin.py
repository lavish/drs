#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

from time import sleep
from ev3.ev3dev import  Tone
from ev3.lego import InfraredSensor
from ev3.lego import TouchSensor

freq_range = (100, 200)
dist_range = (0, 75)
duration = 0.01

def main():
    ir = InfraredSensor()
    touch = TouchSensor()
    tone = Tone()
    
    while True:
        sleep(duration)
        if not touch.is_pushed:
            tone.stop()
            continue
        dist = ir.prox
        freq = min(freq_range[1], max(freq_range[0], int((dist * (freq_range[0]-freq_range[1]) + dist_range[1] * freq_range[1] - dist_range[0] * freq_range[0]) / (dist_range[1]-dist_range[0]))))
        tone.play(freq)
        print("#" * dist)

if __name__ == '__main__':
    main()
