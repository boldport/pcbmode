#!/usr/bin/python

# PCBmodE, a printed circuit design software with a twist
# Copyright (C) 2020 Saar Drimer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from math import pi, sin, cos
import decimal

from pcbmode.config import config


DEG2RAD = 2 * pi / 360


class Point:
    def __init__(self, x=0, y=0):
        try:
            self.sig_dig = config.cfg["params"].get("significant-digits") or 8
        except:
            self.sig_dig = 8
        self.x = round(float(x), self.sig_dig)
        self.y = round(float(y), self.sig_dig)

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
        return not ((self.x == p.x) and (self.y == p.y))

    def assign(self, x=0, y=0):
        self.x = round(float(x), self.sig_dig)
        self.y = round(float(y), self.sig_dig)
        return

    def rotate(self, deg, p):
        """ rotate the point in degrees around another point """
        rad = deg * DEG2RAD
        x = self.x
        y = self.y
        self.x = x * cos(rad) + y * sin(rad)
        self.y = x * -sin(rad) + y * cos(rad)
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
