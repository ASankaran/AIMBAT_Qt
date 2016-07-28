#!/usr/bin/env python
#------------------------------------------------
# Filename: utils.py
#   Author: Arnav Sankaran
#    Email: arnavsankaran@gmail.com
#
# Copyright (c) 2016 Arnav Sankaran
#------------------------------------------------
def convertToRGBA(color, alpha):
	colors = {
		'b': (0, 0, 255, alpha),
		'g': (0, 255, 0, alpha),
		'r': (255, 0, 0, alpha),
		'c': (0, 255, 255, alpha),
		'm': (255, 0, 255, alpha),
		'y': (255, 255, 0, alpha),
		'k': (0, 0, 0, alpha),
		'w': (255, 255, 255, alpha),
		'd': (150, 150, 150, alpha),
		'l': (200, 200, 200, alpha),
		's': (100, 100, 150, alpha),
	}
	return colors[color]

def convertToRGB(color):
	colors = {
		'b': (0, 0, 255),
		'g': (0, 255, 0),
		'r': (255, 0, 0),
		'c': (0, 255, 255),
		'm': (255, 0, 255),
		'y': (255, 255, 0),
		'k': (0, 0, 0),
		'w': (255, 255, 255),
		'd': (150, 150, 150),
		'l': (200, 200, 200),
		's': (100, 100, 150),
	}
	return colors[color]