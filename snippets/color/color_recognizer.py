#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
from math import sqrt, sin, cos
from time import sleep
from collections import Counter
import colorsys

from ev3.lego import InfraredSensor
from ev3.lego import TouchSensor
from ev3.ev3dev import Motor
from ev3.lego import MediumMotor
from ev3.ev3dev import Tone
from ev3.lego import ColorSensor

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()
d = ColorSensor()

# Returns the most frequent value in a list
def most_frequent(x):
    count = Counter(x)
    return count.most_common()[0][0]

# Gets a hsv color according the most frequent components from a set of measurements
def acquireColor():
    hs = []
    ss = []
    vs = []

    for i in range(0,50):
        hsv = colorsys.rgb_to_hsv(*[x/1022 for x in d.rgb])
        hs.append(hsv[0])
        ss.append(hsv[1])
        vs.append(hsv[2])

    return (most_frequent(hs), most_frequent(ss), most_frequent(vs))

# Computes a distance measure between two hsv colors
def norm(a, b):
    # Heuristic corrections of the two colors
    # - Color near to red can be recognized with hue component near to 0 or 1 (due to cylindrical hsv color space)
    # - The height of the color sensor wrt the surface involves heavily on the value component
    a = (0 if (a[0] >= 0.9) else a[0], a[1], a[2]*0.3) # red correction on hue component and value reduction
    b = (0 if (b[0] >= 0.9) else b[0], b[1], b[2]*0.3) # red correction on hue component and value reduction

    #return sqrt( (a[2]-b[2])**2 + (a[1]*cos(a[0]*360)-b[1]*cos(b[0]*360))**2 + (a[1]*sin(a[0]*360)-b[1]*sin(b[0]*360))**2 ) # hsv distance
    #return sqrt( (a[0] - b[0])**2 ) # distance just on first component (hue)
    return sqrt( sum( (a - b)**2 for a, b in zip(a, b)) ) # euclidean distance of all components (hue, saturation, value)

def main():

    # Collection of hsv color to classify (Ids from Palette 1 [0-19] to Palette 2 [20-39])
    data = {
        0: (0.03,0.89,0.21),
        1: (0.18,0.86,0.25),
        3: (0.27,0.83,0.18),
        4: (0.0,0.68,0.17),
        5: (0.15,0.67,0.13),
        6: (0.18,0.74,0.24),
        8: (0.28,0.62,0.04),
        11: (0.09,0.9,0.25),
        12: (0.22,0.7,0.04),
        15: (0.06,0.75,0.07),
        16: (0.11,0.86,0.13),
        17: (0.3,0.73,0.16),
        18: (0.34,0.62,0.16)
    }

    print ("Read color to recognize (press 'enter' to acquire, 'e' to exit):")
    b = getch.__call__()
    while(b != 'e'):
        acquiredColor = acquireColor()
        print("Acquired color: (" + ",".join([str(round(x,2)) for x in acquiredColor]) + ")")

        # Computes the distances among the acquired color and all known colors
        distances = {k : norm(data[k],acquiredColor) for k in data}

        # Select the known color which is nearer wrt the acquired color
        mostLikelyColor = min(distances, key=distances.get)

        print("The color recognized has Id: "+str(mostLikelyColor)+"\n")
        b = getch.__call__()

if __name__ == '__main__':
    main()
