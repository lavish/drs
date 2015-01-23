from __future__ import division

from ev3.lego import ColorSensor
from time import time, sleep

tick = 0.05

color = ColorSensor()

def median(lst):
    lst = sorted(lst)
    if len(lst) < 1:
            return None
    if len(lst) %2 == 1:
            return lst[((len(lst)+1)//2)-1]
    if len(lst) %2 == 0:
            return float(sum(lst[(len(lst)//2)-1:(len(lst)//2)+1]))/2.0

def unzip3(data):
	d1 = []
	d2 = []
	d3 = []
	for v1, v2, v3 in data:
		d1.append(v1)
		d2.append(v2)
		d3.append(v3)
	return (d1, d2, d3)

def calibration():
	print("Give me black and press enter!")
	black = []
	#raw_input()
	for i in range(1,20):
		black.append(color.rgb)
		sleep(tick)
	print("Black acquired")
	sleep(3)
	print("Give me white and press enter!")
	white = []
	#raw_input()
	for i in range(1,20):
		white.append(color.rgb)
		sleep(tick)
	print("White acquired")
	white_components = [median(l) for l in unzip3(white)]
	black_components = [median(l) for l in unzip3(black)]
	red_correction = (255 / (white_components[0] - black_components[0]), (-255 * black_components[0]) / (white_components[0] - black_components[0]))
	green_correction = (255 / (white_components[1] - black_components[1]), (-255 * black_components[1]) / (white_components[1] - black_components[1]))
	blue_correction = (255 / (white_components[2] - black_components[2]), (-255 * black_components[2]) / (white_components[2] - black_components[2]))
	adjustments = [red_correction, green_correction, blue_correction]
	print(adjustments)
	return adjustments

def acquire_adjusted(adjustments):
	value = color.rgb
	pairs = zip(value, adjustments)
	corrected = []
	for col, (a, b) in pairs:
		corrected.append((col * a) + b)
	return (corrected[0], corrected[1], corrected[2])

def main():
	adjustments = calibration()
	print(adjustments)
	while True:
		print("Gimme color")
		color = acquire_adjusted(adjustments)
		print(color)
		if raw_input() == "stop":
			break

if __name__ == '__main__':
    main()
