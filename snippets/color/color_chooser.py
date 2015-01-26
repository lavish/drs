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
    saturationLimit = 0.6
    minDistColor = 0.06
    i = 0
    data = {}
    """
    # Acquires the set of colors to filter
    print ("Read color (press 'enter' to save a color, 'e' to finish):")
    b = getch.__call__()
    while(b != 'e'):
        data[i] = acquireColor()
        print(str(i) +": (" + ",".join([str(round(x,2)) for x in data[i]]) + ")")
        b = getch.__call__()
        i = i+1

    """

    # List of all the 40 hsv colors (Ids from Palette 1 [0-19] to Palette 2 [20-39])
    data = {
        0: (0.03,0.89,0.21),
        1: (0.18,0.86,0.25),
        2: (0.5,0.37,0.07),
        3: (0.27,0.83,0.18),
        4: (0.0,0.68,0.17),
        5: (0.15,0.67,0.13),
        6: (0.18,0.74,0.24),
        7: (0.43,0.59,0.18),
        8: (0.28,0.62,0.04),
        9: (0.51,0.39,0.07),
        10: (0.02,0.86,0.23),
        11: (0.09,0.9,0.25),
        12: (0.22,0.7,0.04),
        13: (0.3,0.8,0.14),
        14: (0.09,0.43,0.2),
        15: (0.06,0.75,0.07),
        16: (0.11,0.86,0.13),
        17: (0.3,0.73,0.16),
        18: (0.34,0.62,0.16),
        19: (0.13,0.65,0.04),
        20: (0.1,0.62,0.09),
        21: (0.18,0.87,0.18),
        22: (0.26,0.34,0.21),
        23: (0.02,0.48,0.09),
        24: (0.14,0.85,0.22),
        25: (0.06,0.6,0.18),
        26: (0.2,0.73,0.18),
        27: (0.42,0.38,0.04),
        28: (0.19,0.32,0.03),
        29: (0.07,0.9,0.2),
        30: (0.01,0.87,0.13),
        31: (0.22,0.87,0.2),
        32: (0.41,0.59,0.08),
        33: (0.94,0.15,0.05),
        34: (0.24,0.76,0.2),
        35: (0.09,0.63,0.04),
        36: (0.12,0.85,0.2),
        37: (0.39,0.68,0.13),
        38: (0.04,0.14,0.08),
        39: (0.3,0.79,0.14)
    }

    """
    # Shows the distance between each pair of those which are acquired
    print("Distances between colors:")
    for colorId in range(0, len(data)):
        for colorId2 in range(colorId+1, len(data)):
            print("("+str(colorId) + ","+str(colorId2)+"): %.2f" % norm(data[colorId],data[colorId2]))
    """

    # Removes the color with saturation less wrt saturationLimit
    data = {k: v for k, v in data.iteritems() if v[1] > saturationLimit}

    # Removes the ambiguous colors from those which are acquired
    invalidColors = []
    for colorId in data:
        if colorId in invalidColors:
            continue
        for colorId2 in {k: v for k, v in data.iteritems() if k > colorId and not k in invalidColors}:
            if norm(data[colorId], data[colorId2]) < minDistColor:
                invalidColors.append(colorId2)

    data = {k: v for k, v in data.iteritems() if not (k in invalidColors)}
    sortedIndex = sorted(data)

    print ("List of %d accepted colors (min distance %.2f and saturation %.2f) by Id:" % (len(data), minDistColor, saturationLimit))
    for colorId in sortedIndex:
        print (str(colorId) + ": (" + ",".join([str(round(x,2)) for x in data[colorId]]) + "),")

if __name__ == '__main__':
    main()
