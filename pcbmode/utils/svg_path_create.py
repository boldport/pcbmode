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
    k = 0.5522847498

    sig_dig = config.cfg["params"]["significant-digits"]

    width = float(width)
    height = float(height)

    # Condition the array
    if all(br == 0 for br in bor_rad):
        bor_rad = []
    elif len(bor_rad) == 1:
        bor_rad = [bor_rad[0]] * 4
    elif len(bor_rad) == 2:
        bor_rad.append(bor_rad[0])
        bor_rad.append(bor_rad[1])
    elif len(bor_rad) == 3:
        bor_rad.append(bor_rad[1])

    bor_rad = [float(i) for i in bor_rad]

    if bor_rad != []:

        top_left = bor_rad[0]
        top_right = bor_rad[1]
        bot_right = bor_rad[2]
        bot_left = bor_rad[3]

        path = f"m {round(-width / 2, sig_dig)},0 "
        if top_left == 0:
            path += "v %f h %f " % (-height / 2, width / 2)
        else:
            r = top_left
            round_r = round(r, sig_dig)
            path += "v %f c %f,%f %f,%f %f,%f h %f " % (
                round(-(height / 2 - r), sig_dig),
                0,
                round(-k * r, sig_dig),
                round(-r * (k - 1), sig_dig),
                -round_r,
                round_r,
                -round_r,
                round(width / 2 - r, sig_dig),
            )
        if top_right == 0:
            path += "h %f v %f " % (width / 2, height / 2)
        else:
            r = top_right
            round_r = round(r, sig_dig)
            path += "h %f c %f,%f %f,%f %f,%f v %f " % (
                round(width / 2 - r, sig_dig),
                round(k * r, sig_dig),
                0,
                round_r,
                round(-r * (k - 1), sig_dig),
                round_r,
                round_r,
                round(height / 2 - r, sig_dig),
            )
        if bot_right == 0:
            path += "v %f h %f " % (height / 2, -width / 2)
        else:
            r = bot_right
            round_r = round(r, sig_dig)
            path += "v %f c %f,%f %f,%f %f,%f h %f " % (
                round(height / 2 - r, sig_dig),
                0,
                round(k * r, sig_dig),
                round(r * (k - 1), sig_dig),
                round_r,
                -round_r,
                round_r,
                round(-(width / 2 - r), sig_dig),
            )
        if bot_left == 0:
            path += "h %f v %f " % (-width / 2, -height / 2)
        else:
            r = bot_left
            round_r = round(r, sig_dig)
            path += "h %f c %f,%f %f,%f %f,%f v %f " % (
                round(-(width / 2 - r), sig_dig),
                round(-k * r, sig_dig),
                0,
                -round_r,
                round(r * (k - 1), sig_dig),
                -round_r,
                -round_r,
                round(-(height / 2 - r), sig_dig),
            )
        path += "z"

    else:
        path = "m %f,%f h %f v %f h %f v %f z" % (
            round(-width / 2, sig_dig),
            round(-height / 2, sig_dig),
            round(width, sig_dig),
            round(height, sig_dig),
            round(-width, sig_dig),
            round(-height, sig_dig),
        )

    return path


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
