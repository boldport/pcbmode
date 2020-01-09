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


def rect(width, height, radii=None):
    """
    Returns a centered path based on width and height; smooth corners
    can be defined with radii
    """

    width = float(width)
    height = float(height)

    # The calculation to obtain the 'k' coefficient can be found here:
    # http://itc.ktu.lt/itc354/Riskus354.pdf
    # "APPROXIMATION OF A CUBIC BEZIER CURVE BY CIRCULAR ARCS AND VICE VERSA"
    # by Aleksas Riskus
    k = 0.5522847498

    all_zeros = True

    if radii is not None:
        # check if all values are equal to '0'
        for value in radii.values():
            if value != 0:
                all_zeros = False

        if all_zeros is True:
            path = "m %f,%f h %f v %f h %f v %f z" % (
                -width / 2,
                -height / 2,
                width,
                height,
                -width,
                -height,
            )
        else:

            top_left = float(radii.get("tl") or radii.get("top_left") or 0)
            top_right = float(radii.get("tr") or radii.get("top_right") or 0)
            bot_right = float(
                radii.get("br")
                or radii.get("bot_right")
                or radii.get("bottom_right")
                or 0
            )
            bot_left = float(
                radii.get("bl")
                or radii.get("bot_left")
                or radii.get("bottom_left")
                or 0
            )

            path = "m %f,%f " % (-width / 2, 0)
            if top_left == 0:
                path += "v %f h %f " % (-height / 2, width / 2)
            else:
                r = top_left
                path += "v %f c %f,%f %f,%f %f,%f h %f " % (
                    -(height / 2 - r),
                    0,
                    -k * r,
                    -r * (k - 1),
                    -r,
                    r,
                    -r,
                    width / 2 - r,
                )

            if top_right == 0:
                path += "h %f v %f " % (width / 2, height / 2)
            else:
                r = top_right
                path += "h %f c %f,%f %f,%f %f,%f v %f " % (
                    width / 2 - r,
                    k * r,
                    0,
                    r,
                    -r * (k - 1),
                    r,
                    r,
                    height / 2 - r,
                )

            if bot_right == 0:
                path += "v %f h %f " % (height / 2, -width / 2)
            else:
                r = bot_right
                path += "v %f c %f,%f %f,%f %f,%f h %f " % (
                    height / 2 - r,
                    0,
                    k * r,
                    r * (k - 1),
                    r,
                    -r,
                    r,
                    -(width / 2 - r),
                )

            if bot_left == 0:
                path += "h %f v %f " % (-width / 2, -height / 2)
            else:
                r = bot_left
                path += "h %f c %f,%f %f,%f %f,%f v %f " % (
                    -(width / 2 - r),
                    -k * r,
                    0,
                    -r,
                    r * (k - 1),
                    -r,
                    -r,
                    -(height / 2 - r),
                )

            path += "z"

    else:
        path = "m %f,%f h %f v %f h %f v %f z" % (
            -width / 2,
            -height / 2,
            width,
            height,
            -width,
            -height,
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


def circle(d, offset=Point()):
    """
    Returns an SVG path of a circle of diameter 'diameter'
    """

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
