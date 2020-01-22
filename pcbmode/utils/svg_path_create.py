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


from pcbmode.config import config
from pcbmode.utils.point import Point
from pcbmode.utils.utils import pn


def rect(width, height, bor_rad=[]):
    """
    Returns a centered path based on width and height; optional rounded
    corners are defined like CSS's 'border-radius' property as a list of
    one to four parameters.
    """

    # The calculation to obtain the 'k' coefficient can be found here:
    # http://itc.ktu.lt/itc354/Riskus354.pdf
    # "APPROXIMATION OF A CUBIC BEZIER CURVE BY CIRCULAR ARCS AND VICE VERSA"
    # by Aleksas Riskus
    K = 0.5522847498

    w = float(width)
    h = float(height)

    # Condition the array according to CSS expansion rules for 'border-radius'
    if all(br == 0 for br in bor_rad):
        bor_rad = []
    elif len(bor_rad) == 1:
        bor_rad = [bor_rad[0]] * 4
    elif len(bor_rad) == 2:
        bor_rad.append(bor_rad[0])
        bor_rad.append(bor_rad[1])
    elif len(bor_rad) == 3:
        bor_rad.append(bor_rad[1])

    if bor_rad != []:

        bor_rad = [float(i) for i in bor_rad]

        # Top left corner, clockwise
        r1 = bor_rad[0]
        r2 = bor_rad[1]
        r3 = bor_rad[2]
        r4 = bor_rad[3]

        # Calculate side lengths, top clockwise
        sl = [pn(w - r1 - r2), pn(h - r2 - r3), pn(w - r3 - r4), pn(h - r3 - r1)]

        # Bezier arcs, clockwise from top right
        arcs = [
            f"c {0},{pn(-K * r1)} {pn(-r1 * (K - 1))},{pn(-r1)} {pn(r1)},{pn(-r1)} ",
            f"c {pn(K * r2)},{0} {pn(r2)},{pn(-r2 * (K - 1))} {pn(r2)},{pn(r2)} ",
            f"c {0},{pn(K * r3)} {pn(r3 * (K - 1))},{pn(r3)} {pn(-r3)},{pn(r3)} ",
            f"c {pn(-K * r4)},{0} {pn(-r4)},{pn(r4 * (K - 1))} {pn(-r4)},{pn(-r4)} ",
        ]

        p = f"m {pn(-w/2)},{pn(-(h/2-r1))} "
        if r1 != 0:
            p += arcs[0]
        p += f"h {sl[0]} "
        if r2 != 0:
            p += arcs[1]
        p += f"v {sl[1]} "
        if r3 != 0:
            p += arcs[2]
        p += f"h {-sl[2]} "
        if r4 != 0:
            p += arcs[3]
        p += f"v {-sl[3]} "
        p += "z"

    else:
        p = f"m {pn(-w / 2)},{pn(-h / 2)} h {pn(w)} v {pn(h)} h {pn(-w)} v {pn(-h)} z"

    return p


def ring(d1, d2):
    """
    Returns a path for a ring based on two diameters; the
    function automatically determines which diameter is the
    inner and which is the outer diameter
    """

    path = None

    if d1 == d2:
        path = circle(d1)
    else:
        if d1 > d2:
            outer = d1
            inner = d2
        else:
            outer = d2
            inner = d1
        path = circle(outer)
        path += circle(inner, Point(0, outer / 2))

    return path


def circle(d, offset=None):
    """
    Returns an SVG path of a circle of diameter 'diameter'
    """

    if offset is None:
        offset = Point()

    r = d / 2.0

    # The calculation to obtain the 'k' coefficient can be found here:
    # http://itc.ktu.lt/itc354/Riskus354.pdf
    # "APPROXIMATION OF A CUBIC BEZIER CURVE BY CIRCULAR ARCS AND VICE VERSA"
    # by Aleksas Riskus
    k = 0.5522847498

    return (
        "m %s,%s c %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s z"
        % (
            0,
            r - offset.y,
            k * r,
            0,
            r,
            -r * (1 - k),
            r,
            -r,
            0,
            -r * k,
            -r * (1 - k),
            -r,
            -r,
            -r,
            -r * k,
            0,
            -r,
            r * (1 - k),
            -r,
            r,
            0,
            r * k,
            r * (1 - k),
            r,
            r,
            r,
        )
    )


def drill(diameter):
    """
    Returns an SVG path for a drill symbol of diameter 'diameter'
    """

    r = diameter / 2.0

    # The calculation to obtain the 'k' coefficient can be found here:
    # http://itc.ktu.lt/itc354/Riskus354.pdf
    # "APPROXIMATION OF A CUBIC BEZIER CURVE BY CIRCULAR ARCS AND VICE VERSA"
    # by Aleksas Riskus
    k = 0.5522847498

    # Internal circle
    b = r * 0.9

    return (
        "m %s,%s c %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s z m %s,%s %s,%s c %s,%s %s,%s %s,%s l %s,%s %s,%s c %s,%s %s,%s %s,%s z"
        % (
            0,
            r,
            k * r,
            0,
            r,
            -r * (1 - k),
            r,
            -r,
            0,
            -r * k,
            -r * (1 - k),
            -r,
            -r,
            -r,
            -r * k,
            0,
            -r,
            r * (1 - k),
            -r,
            r,
            0,
            r * k,
            r * (1 - k),
            r,
            r,
            r,
            0,
            -(r - b),
            0,
            -2 * b,
            -b * k,
            0,
            -b,
            b * (1 - k),
            -b,
            b,
            b,
            0,
            b,
            0,
            0,
            k * b,
            -b * (1 - k),
            b,
            -b,
            b,
        )
    )


def marker():
    """
    Returns a path for the placement marker
    """
    diameter = 0.2

    r = diameter / 2.0

    # The calculation to obtain the 'k' coefficient can be found here:
    # http://itc.ktu.lt/itc354/Riskus354.pdf
    # "APPROXIMATION OF A CUBIC BEZIER CURVE BY CIRCULAR ARCS AND VICE VERSA"
    # by Aleksas Riskus
    k = 0.5522847498

    # Extension
    b = r * 1.8

    return (
        "m %s,%s c %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s %s,%s m %s,%s %s,%s z"
        % (
            0,
            r,
            k * r,
            0,
            r,
            -r * (1 - k),
            r,
            -r,
            0,
            -r * k,
            -r * (1 - k),
            -r,
            -r,
            -r,
            -r * k,
            0,
            -r,
            r * (1 - k),
            -r,
            r,
            0,
            r * k,
            r * (1 - k),
            r,
            r,
            r,
            -b,
            -r,
            2 * b,
            0,
        )
    )


def arrow(width, height, base, bar, gap):
    """
    width: width of arrow
    bar: length of the bar against arrow head
    height: height of arrow's head
    base: width of arrow's head
    gap: the gap for where the text goes
    """

    path = (
        "m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s"
        % (
            -gap / 2,
            0,
            -width / 2 + gap / 2,
            0,
            0,
            bar / 2,
            0,
            -bar,
            height,
            (bar - base) / 2,
            -height,
            base / 2,
            height,
            base / 2,
            -height,
            -base / 2,
            width / 2,
            0,
            gap / 2,
            0,
            width / 2 - gap / 2,
            0,
            0,
            bar / 2,
            0,
            -bar,
            -height,
            (bar - base) / 2,
            height,
            base / 2,
            -height,
            base / 2,
            height,
            -base / 2,
        )
    )
    return path
