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
from pcbmode.utils.point import Point as P
from pcbmode.utils.svgpath import SvgPath


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

        # Calculate side lengths, top hirizontal, clockwise
        sl = [w - r1 - r2, h - r2 - r3, w - r3 - r4, h - r4 - r1]

        # Cubic Bezier "arcs", clockwise from top left
        arcs = [
            ["c", P([0, -K * r1]), P([-r1 * (K - 1), -r1]), P([r1, -r1])],
            ["c", P([K * r2, 0]), P([r2, -r2 * (K - 1)]), P([r2, r2])],
            ["c", P([0, K * r3]), P([r3 * (K - 1), r3]), P([-r3, r3])],
            ["c", P([-K * r4, 0]), P([-r4, r4 * (K - 1)]), P([-r4, -r4])],
        ]

        p = []
        p.append(["m", P([-w / 2, -(h / 2 - r1)])])
        if r1 != 0:
            p.append(arcs[0])
        p.append(["h", P([sl[0], 0])])
        if r2 != 0:
            p.append(arcs[1])
        p.append(["v", P([0, sl[1]])])
        if r3 != 0:
            p.append(arcs[2])
        p.append(["h", P([-sl[2], 0])])
        if r4 != 0:
            p.append(arcs[3])
        p.append(["v", P([0, -sl[3]])])
        # TODO: missing something?
        p.append(["z"])
    else:  # No rounded corners
        p = [
            ["m", P([-w / 2, -h / 2])],
            ["h", P([w, 0])],
            ["v", P([0, h])],
            ["h", P([-w, 0])],
            ["v", P([0, -h])],
            ["z"],
        ]

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
        offset = P()

    r = d / 2.0

    # The calculation to obtain the 'k' coefficient can be found here:
    # http://itc.ktu.lt/itc354/Riskus354.pdf
    # "APPROXIMATION OF A CUBIC BEZIER CURVE BY CIRCULAR ARCS AND VICE VERSA"
    # by Aleksas Riskus
    k = 0.5522847498

    c = []
    c.append(["m", P([0, r - offset.y])])
    c.append(
        [
            "c",
            P([k * r, 0]),
            P([r, -r * (1 - k)]),
            P([r, -r]),
            P([0, -r * k]),
            P([-r * (1 - k), -r]),
            P([-r, -r]),
            P([-r * k, 0]),
            P([-r, r * (1 - k)]),
            P([-r, r]),
            P([0, r * k]),
            P([r * (1 - k), r]),
            P([r, r]),
        ]
    )
    c.append(["z"])

    return c


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

    c = []
    c.append(["m", P([0, r])])
    c.append(
        [
            "c",
            P([k * r, 0]),
            P([r, -r * (1 - k)]),
            P([r, -r]),
            P([0, -r * k]),
            P([-r * (1 - k), -r]),
            P([-r, -r]),
            P([-r * k, 0]),
            P([-r, r * (1 - k)]),
            P([-r, r]),
            P([0, r * k]),
            P([r * (1 - k), r]),
            P([r, r]),
        ]
    )
    c.append(["z"])
    c.append(["m", P([0, -(r - b)]), P([0, -2 * b])])
    c.append(["c", P([-b * k, 0]), P([-b, b * (1 - k)]), P([-b, b])])
    c.append(["l", P([b, 0]), P([b, 0])])
    c.append(["c", P([0, k * b]), P([-b * (1 - k), b]), P([-b, b])])
    c.append(["z"])

    return c


def placement_marker(diameter=0.2):
    """
    Returns an SvgPath object for a placement marker 
    """
    # The calculation to obtain the 'k' coefficient can be found here:
    # http://itc.ktu.lt/itc354/Riskus354.pdf
    # "APPROXIMATION OF A CUBIC BEZIER CURVE BY CIRCULAR ARCS AND VICE VERSA"
    # by Aleksas Riskus
    k = 0.5522847498

    r = diameter / 2.0

    # Length of bar across circle
    b = r * 1.8

    kr = k * r
    r1k = r * (1 - k)

    m = []
    m.append(["m", P([0, r])])
    m.append(
        [
            "c",
            P([kr, 0]),
            P([r, -r1k]),
            P([r, -r]),
            P([0, -kr]),
            P([-r1k, -r]),
            P([-r, -r]),
            P([-kr, 0]),
            P([-r, r1k]),
            P([-r, r]),
            P([0, kr]),
            P([r1k, r]),
            P([r, r]),
        ]
    )
    m.append(["m", P([-b, -r]), P([2 * b, 0])])
    m.append(["z"])

    return m


def arrow(width, height, base, bar, gap):
    """
    width: width of arrow
    bar: length of the bar against arrow head
    height: height of arrow's head
    base: width of arrow's head
    gap: the gap for where the text goes
    """

    a = []
    a.append(["m", P([-gap / 2, 0]), P([-width / 2 + gap / 2, 0])])
    a.append(["m", P([0, bar / 2]), P([0, -bar])])
    a.append(["m", P([height, (bar - base) / 2]), P([-height, base / 2])])
    a.append(["m", P([height, base / 2]), P([-height, -base / 2])])
    a.append(["m", P([width / 2, 0])])
    a.append(["m", P([gap / 2, 0]), P([width / 2 - gap / 2, 0])])
    a.append(["m", P([0, bar / 2]), P([0, -bar])])
    a.append(["m", P([-height, (bar - base) / 2]), P([height, base / 2])])
    a.append(["m", P([-height, base / 2]), P([height, -base / 2])])

    return a
