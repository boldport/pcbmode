#!/usr/bin/python

from math import pi, sin, cos
import decimal

DEG2RAD = 2 * pi / 360


class Point:
  
    def __init__(self, x=0, y=0):
        self.x = float(x)
        self.y = float(y)
       
    def __add__(self, p):
        """ add point 'p' of type Point to current point""" 
        return Point(self.x + p.x, self.y + p.y)

    def __sub__(self, p):
        """ subtract point 'p' of type Point to current point""" 
        return Point(self.x - p.x, self.y - p.y)

    def __repr__(self, d=2):
        """ 
        return a string representation; 'd' determines amount
        of significant digits to display
        """
        return "[%.*f, %.*f]" % (d, self.x, d, self.y)

    def __eq__(self, p):
        """ equality attribute """
        return (self.x == p.x) and (self.y == p.y)

    def __ne__(self, p):
        """ not equal attribute """
        return not((self.x == p.x) and (self.y == p.y))

    def assign(self, x=0, y=0):
        self.x = float(x)
        self.y = float(y)
        return

    def rotate(self, deg, p):
        """ rotate the point in degrees around another point """
        rad = deg * DEG2RAD
        x = self.x
        y = self.y
        self.x = (x * cos(rad) + y * sin(rad))
        self.y = (x * -sin(rad) + y * cos(rad))
        return

    def round(self, d):
        """ round decimal to nearest 'd' decimal digits """
        self.x = round(self.x, d)
        self.y = round(self.y, d)
        return

    def mult(self, scalar):
        """ multiply by scalar """
        self.x *= float(scalar)
        self.y *= float(scalar)
        return
