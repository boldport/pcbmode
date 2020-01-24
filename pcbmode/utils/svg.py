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


from math import pi, sin, cos, sqrt, ceil
import re
from lxml import etree as et

from pcbmode.config import config
from pcbmode.utils import utils
from pcbmode.utils import svg_path_create
from pcbmode.utils.point import Point
from pcbmode.utils import svg_path_grammar


def absolute_to_relative_path(path):
    """
    Converts an SVG path into a path that has only relative commands.
    This basically allows taking paths from anywhere and placing them
    in a new SVG.
    """
    # TODO: add support all commands
    # TODO: optimise 'switch' logic

    # check to see if path is empty or doesn't exist
    if (path == None) or (path == ""):
        return

    # get SVG path grammar
    look_for = svg_path_grammar.get_grammar()

    # parse the input based on this grammar
    pd = look_for.parseString(path)

    p = ""

    # This variable stores the absolute coordinates as the path is converted;
    abspos = Point()

    patho = Point()

    for i in range(0, len(pd)):

        # 'move to' command
        if re.match("M", pd[i][0], re.I):

            # TODO: write this code more concisely

            coord = Point(pd[i][1])
            p += "m "

            # if this is the start of the path, the first M/m coordinate is
            # always absolute
            if i == 0:
                abspos.assign(coord.x, coord.y)
                p += str(abspos.x) + "," + str(abspos.y) + " "
                patho.assign(coord.x, coord.y)
            else:
                if pd[i][0] == "m":
                    p += str(coord.x) + "," + str(coord.y) + " "
                    abspos += coord
                    patho = abspos

                else:
                    p += str(coord.x - abspos.x) + "," + str(coord.y - abspos.y) + " "
                    abspos.assign(coord.x, coord.y)
                    patho.assign(coord.x, coord.y)

            # do the rest of the coordinates
            for coord_tmp in pd[i][2:]:
                coord.assign(coord_tmp[0], coord_tmp[1])
                if pd[i][0] == "m":
                    p += str(coord.x) + "," + str(coord.y) + " "
                    abspos += coord
                else:
                    p += str(coord.x - abspos.x) + "," + str(coord.y - abspos.y) + " "
                    abspos.assign(coord.x, coord.y)

        # cubic Bezier (PCCP) curve command
        elif re.match("C", pd[i][0], re.I):
            p += pd[i][0].lower() + " "

            if pd[i][0] == "c":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += str(coord.x) + "," + str(coord.y) + " "
                # for keeping track of the absolute position, we need to add up every
                # *third* coordinate of the cubic Bezier curve
                for coord_tmp in pd[i][3::3]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    abspos += coord

            if pd[i][0] == "C":
                for n in range(1, len(pd[i]) - 1, 3):
                    for m in range(0, 3):
                        coord.assign(pd[i][n + m][0], pd[i][n + m][1])
                        p += (
                            str(coord.x - abspos.x)
                            + ","
                            + str(coord.y - abspos.y)
                            + " "
                        )
                    abspos.assign(coord.x, coord.y)

        # quadratic Bezier (PCP) curve command
        elif re.match("Q", pd[i][0], re.I):
            p += pd[i][0].lower() + " "

            if pd[i][0] == "q":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += str(coord.x) + "," + str(coord.y) + " "
                # for keeping track of the absolute position, we need to add up every
                # *third* coordinate of the cubic Bezier curve
                for coord_tmp in pd[i][2::2]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    abspos += coord

            if pd[i][0] == "Q":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += str(coord.x - abspos.x) + "," + str(coord.y - abspos.y) + " "
                abspos.assign(coord.x, coord.y)

        # simple cubic Bezier curve command
        elif re.match("T", pd[i][0], re.I):
            p += pd[i][0].lower() + " "

            if pd[i][0] == "t":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += str(coord.x) + "," + str(coord.y) + " "
                    # for keeping track of the absolute position, we need to add up every
                    # *third* coordinate of the cubic Bezier curve
                    # for coord in pd[i][2::2]:
                    abspos += coord

            if pd[i][0] == "T":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += (
                        str(float(coord[0]) - abspos["x"])
                        + ","
                        + str(float(coord[1]) - abspos["y"])
                        + " "
                    )
                abspos.assign(coord.x, coord.y)

        elif re.match("S", pd[i][0], re.I):
            p += pd[i][0].lower() + " "

            if pd[i][0] == "s":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += str(coord.x) + "," + str(coord.y) + " "
                    abspos += coord

            if pd[i][0] == "S":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += str(coord.x - abspos.x) + "," + str(coord.y - abspos.y) + " "
                abspos.assign(coord.x, coord.y)

        # 'line to'  command
        elif re.match("L", pd[i][0], re.I):
            p += pd[i][0].lower() + " "

            if pd[i][0] == "l":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += str(coord.x) + "," + str(coord.y) + " "
                    abspos += coord

            if pd[i][0] == "L":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += str(coord.x - abspos.x) + "," + str(coord.y - abspos.y) + " "
                    abspos.assign(coord.x, coord.y)

        # 'horizontal line' command
        elif re.match("H", pd[i][0], re.I):
            p += pd[i][0].lower() + " "

            if pd[i][0] == "h":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], 0)
                    p += str(coord.x) + " "
                abspos.x += coord.x

            if pd[i][0] == "H":
                for coord_tmp in pd[i][1:]:
                    coord.assign(coord_tmp[0], coord_tmp[1])
                    p += str(coord.x - abspos.x) + " "
                    abspos.x = coord.x

        # 'vertical line' command
        elif re.match("V", pd[i][0], re.I):
            p += pd[i][0].lower() + " "

            if pd[i][0] == "v":
                for coord_tmp in pd[i][1:]:
                    coord.assign(0, coord_tmp[0])
                    p += str(coord.y) + " "
                    abspos.y += coord.y

            if pd[i][0] == "V":
                for coord_tmp in pd[i][1:]:
                    coord.assign(0, coord_tmp[0])
                    p += str(coord.y - abspos.y) + " "
                    abspos.y = coord.y

        # 'close shape' command
        elif re.match("Z", pd[i][0], re.I):
            p += pd[i][0].lower() + " "
            abspos = abspos + (patho - abspos)

        else:
            print("ERROR: found an unsupported SVG path command " + str(pd[i][0]))

    # return the relative path
    return p


def relative_svg_path_to_absolute_coord_list(
    path, bezier_steps=100, segment_length=0.05
):
    """
    return a list of absolute coordinates from an SVG *relative* path
    """

    # get SVG path grammar
    look_for = svg_grammar()

    # parse the input based on this grammar
    pd = look_for.parseString(path)

    # absolute position
    ap = Point()

    # path origin
    po = Point()

    points = []
    p = []

    last_bezier_control_point = Point()

    for i in range(0, len(pd)):

        cmd = pd[i][0]

        # 'move to' command
        if re.match("m", cmd):
            if i == 0:
                coord = Point(pd[i][1])
                ap.assign(coord.x, coord.y)
                p.append(ap)
                po.assign(coord.x, coord.y)
            else:
                coord_tmp = Point(pd[i][1])
                ap += coord_tmp
                # a marker that a new path is starting after a previous one closed
                points.append(p)
                p = []
                p.append(ap)
                po = ap

            for coord_tmp in pd[i][2:]:
                coord = Point(coord_tmp)
                ap += coord
                p.append(ap)

        # cubic (two control points) Bezier curve command
        elif re.match("c", cmd):

            bezier_curve_path = []

            for n in range(1, len(pd[i]) - 1, 3):
                bezier_curve_path.append(ap)
                for m in range(0, 3):
                    coord = pd[i][n + m]
                    point = Point(coord)
                    bezier_curve_path.append(ap + point)
                new_point = Point(pd[i][n + m])
                ap += new_point

            for n in range(0, len(bezier_curve_path), 4):

                # clear bezier point arrays
                bezier_points_x = []
                bezier_points_y = []

                # split points of bezier into 'x' and 'y' coordinate arrays
                # as this is what the point array function expects
                for m in range(0, 4):
                    bezier_points_x.append(bezier_curve_path[n + m].x)
                    bezier_points_y.append(bezier_curve_path[n + m].y)

                # caluclate the individual points along the bezier curve for 'x'
                # and 'y'
                points_x = calculate_points_of_cubic_bezier(
                    bezier_points_x, bezier_steps
                )
                points_y = calculate_points_of_cubic_bezier(
                    bezier_points_y, bezier_steps
                )

                path_length = calculate_cubic_bezier_length(points_x, points_y)
                if path_length == 0:
                    steps = 1
                else:
                    steps = ceil(path_length / segment_length)
                skip = int(ceil(bezier_steps / steps))

                bezier_point_array = []

                # put thos points back into a Point type array
                for n in range(0, len(points_x), skip):
                    bezier_point_array.append(Point([points_x[n], points_y[n]]))
                bezier_point_array.append(
                    Point([points_x[len(points_x) - 1], points_y[len(points_x) - 1]])
                )

                p += bezier_point_array

        # quadratic (single control point) Bezier curve command
        elif re.match("q", cmd):

            bezier_curve_path = []

            for n in range(1, len(pd[i]) - 1, 2):
                bezier_curve_path.append(ap)
                for m in range(0, 2):
                    coord = pd[i][n + m]
                    point = Point(coord)
                    bezier_curve_path.append(ap + point)
                    # inject a second, identical control point so this quadratic
                    # bezier looks like a cubic one
                    if m == 1:
                        bezier_curve_path.append(ap + point)
                    if m == 0:
                        last_bezier_control_point = ap + point
                new_point = Point(pd[i][n + m])
                ap += new_point

            for n in range(0, len(bezier_curve_path), 4):

                # clear bezier point arrays
                bezier_points_x = []
                bezier_points_y = []

                # split points of bezier into 'x' and 'y' coordinate arrays
                # as this is what the point array function expects
                for m in range(0, 4):
                    bezier_points_x.append(bezier_curve_path[n + m].x)
                    bezier_points_y.append(bezier_curve_path[n + m].y)

                # caluclate the individual points along the bezier curve for 'x'
                # and 'y'
                points_x = calculate_points_of_cubic_bezier(
                    bezier_points_x, bezier_steps
                )
                points_y = calculate_points_of_cubic_bezier(
                    bezier_points_y, bezier_steps
                )

                path_length = calculate_cubic_bezier_length(points_x, points_y)
                skip = int(ceil(bezier_steps / (path_length / segment_length)))

                bezier_point_array = []

                # put those points back into a Point type array
                for n in range(0, len(points_x), skip):
                    bezier_point_array.append(Point([points_x[n], points_y[n]]))
                bezier_point_array.append(
                    Point([points_x[len(points_x) - 1], points_y[len(points_x) - 1]])
                )

                p += bezier_point_array

        # simple cubic Bezier curve command
        elif re.match("t", cmd):

            bezier_curve_path = []

            for n in range(1, len(pd[i])):
                bezier_curve_path.append(ap)
                coord = pd[i][n]
                point = Point(coord)
                end_point = ap + point
                diff = Point(
                    [ap.x - last_bezier_control_point.x,
                    ap.y - last_bezier_control_point.y]
                )
                control_point = ap + diff
                bezier_curve_path.append(control_point)
                bezier_curve_path.append(end_point)
                bezier_curve_path.append(end_point)
                last_bezier_control_point = control_point
                new_point = Point(pd[i][n])
                ap += new_point

            for n in range(0, len(bezier_curve_path), 4):

                # clear bezier point arrays
                bezier_points_x = []
                bezier_points_y = []

                # split points of bezier into 'x' and 'y' coordinate arrays
                # as this is what the point array function expects
                for m in range(0, 4):
                    bezier_points_x.append(bezier_curve_path[n + m].x)
                    bezier_points_y.append(bezier_curve_path[n + m].y)

                # caluclate the individual points along the bezier curve for 'x'
                # and 'y'
                points_x = calculate_points_of_cubic_bezier(
                    bezier_points_x, bezier_steps
                )
                points_y = calculate_points_of_cubic_bezier(
                    bezier_points_y, bezier_steps
                )

                path_length = calculate_cubic_bezier_length(points_x, points_y)
                skip = int(ceil(bezier_steps / (path_length / segment_length)))

                bezier_point_array = []

                # put those points back into a Point type array
                for m in range(0, len(points_x), skip):
                    bezier_point_array.append(Point([points_x[m], points_y[m]]))
                bezier_point_array.append(
                    Point([points_x[len(points_x) - 1], points_y[len(points_x) - 1]])
                )

                p += bezier_point_array

        #        elif re.match('s', cmd):
        #            pass

        # 'line to'  command
        elif re.match("l", cmd):
            for coord_tmp in pd[i][1:]:
                coord = Point(coord_tmp)
                ap += coord
                p.append(ap)

        # 'horizontal line' command
        elif re.match("h", cmd):
            for coord_tmp in pd[i][1:]:
                coord = Point([coord_tmp[0], 0])
                ap += coord
                p.append(ap)

        # 'vertical line' command
        elif re.match("v", cmd):
            for coord_tmp in pd[i][1:]:
                coord = Point([0, coord_tmp[0]])
                ap += coord
                p.append(ap)

        # 'close shape' command
        elif re.match("z", cmd):
            ap = ap + (po - ap)

        else:
            print("ERROR: found an unsupported SVG path command " + str(cmd))

    points.append(p)
    return points


def mirror_path_over_axis(path, axis, width):
    """ 
    mirrors a path horizontally by first converting it to a relative path
    and then mirrors it either horizontally or vertically by negating the
    x or y axis coordinates
    """
    # TODO: add vertical flipping ;)

    # check to see if path is empty or doesn't exist
    if (path == None) or (path == ""):
        return

    # convert path to relative coordinates; this simplifies the mirroring
    relative_path = absolute_to_relative_path(path)

    # get SVG path grammar
    look_for = svg_grammar()

    # parse the input based on this grammar
    pd = look_for.parseString(relative_path)

    p = ""

    for i in range(0, len(pd)):

        pcmd = pd[i][0]

        if re.match("m", pcmd):

            if i == 0:
                p += (
                    "m "
                    + str(width - float(pd[i][1][0]))
                    + ","
                    + str(pd[i][1][1])
                    + " "
                )
            else:
                p += "m " + str(-float(pd[i][1][0])) + "," + str(pd[i][1][1]) + " "

            for coord in pd[i][2:]:
                p += str(-float(coord[0])) + "," + coord[1] + " "

        else:
            p += pd[i][0] + " "
            for coord in pd[i][1:]:
                if len(coord) > 1:
                    p += str(-float(coord[0])) + "," + str(float(coord[1])) + " "
                else:
                    if pd[i][0] == "h":
                        p += str(-float(coord[0])) + " "
                    else:
                        p += str(float(coord[0])) + " "

    return p


def calculate_bounding_box_of_path(path):
    """
    Calculates the bounding box of an SVG path
    """

    # convert path to relative
    relative_path = absolute_to_relative_path(path)

    # get SVG path grammar
    look_for = svg_grammar()

    # parse the input based on this grammar
    pd = look_for.parseString(relative_path)

    last_point = Point()
    abs_point = Point()

    bbox_top_left = Point()
    bbox_bot_right = Point()

    # for the t/T (shorthand bezier) command, we need to keep track
    # of the last bezier control point from previous Q/q/T/t command
    last_bezier_control_point = Point()

    for i in range(0, len(pd)):

        # 'move to' command
        if re.match("m", pd[i][0]):

            if i == 0:
                # the first coordinate is the start of both top left and bottom right
                abs_point.assign(pd[i][1][0], pd[i][1][1])
                bbox_top_left.assign(pd[i][1][0], pd[i][1][1])
                bbox_bot_right.assign(pd[i][1][0], pd[i][1][1])
            else:
                new_point = Point(pd[i][1])
                abs_point += new_point
                bbox_top_left, bbox_bot_right = boundary_box_check(
                    bbox_top_left, bbox_bot_right, abs_point
                )

            # for the rest of the coordinates
            for coord in pd[i][2:]:
                new_point = Point(coord)
                abs_point += new_point
                bbox_top_left, bbox_bot_right = boundary_box_check(
                    bbox_top_left, bbox_bot_right, abs_point
                )

        # cubic Bezier curve command
        elif re.match("c", pd[i][0]):

            bezier_curve_path = []

            for n in range(1, len(pd[i]) - 1, 3):
                bezier_curve_path.append(abs_point)
                for m in range(0, 3):
                    coord = pd[i][n + m]
                    point = Point(coord)
                    bezier_curve_path.append(abs_point + point)
                new_point = Point(pd[i][n + m])
                abs_point += new_point

            for n in range(0, len(bezier_curve_path), 4):

                # clear bezier point arrays
                bezier_points_x = []
                bezier_points_y = []

                # split points of bezier into 'x' and 'y' coordinate arrays
                # as this is what the point array function expects
                for m in range(0, 4):
                    bezier_points_x.append(bezier_curve_path[n + m].x)
                    bezier_points_y.append(bezier_curve_path[n + m].y)

                # caluclate the individual points along the bezier curve for 'x'
                # and 'y'
                points_x = calculate_points_of_cubic_bezier(bezier_points_x, 100)
                points_y = calculate_points_of_cubic_bezier(bezier_points_y, 100)

                bezier_point_array = []

                # put those points back into a Point type array
                for n in range(0, len(points_x)):
                    bezier_point_array.append(Point([points_x[n], points_y[n]]))

                # check each point if it extends the boundary box
                for n in range(0, len(bezier_point_array)):
                    bbox_top_left, bbox_bot_right = boundary_box_check(
                        bbox_top_left, bbox_bot_right, bezier_point_array[n]
                    )

        # quadratic Bezier curve command
        elif re.match("q", pd[i][0]):

            bezier_curve_path = []

            for n in range(1, len(pd[i]) - 1, 2):
                bezier_curve_path.append(abs_point)
                for m in range(0, 2):
                    coord = pd[i][n + m]
                    point = Point(coord)
                    bezier_curve_path.append(abs_point + point)
                    # inject a second, identical control point so this quadratic
                    # bezier looks like a cubic one
                    if m == 1:
                        bezier_curve_path.append(abs_point + point)
                    if m == 0:
                        last_bezier_control_point = abs_point + point
                new_point = Point(pd[i][n + m])
                abs_point += new_point

            for n in range(0, len(bezier_curve_path), 4):

                # clear bezier point arrays
                bezier_points_x = []
                bezier_points_y = []

                # split points of bezier into 'x' and 'y' coordinate arrays
                # as this is what the point array function expects
                for m in range(0, 4):
                    bezier_points_x.append(bezier_curve_path[n + m].x)
                    bezier_points_y.append(bezier_curve_path[n + m].y)

                # caluclate the individual points along the bezier curve for 'x'
                # and 'y'
                points_x = calculate_points_of_cubic_bezier(bezier_points_x, 100)
                points_y = calculate_points_of_cubic_bezier(bezier_points_y, 100)

                bezier_point_array = []

                # put those points back into a Point type array
                for n in range(0, len(points_x)):
                    bezier_point_array.append(Point([points_x[n], points_y[n]]))

                # check each point if it extends the boundary box
                for n in range(0, len(bezier_point_array)):
                    bbox_top_left, bbox_bot_right = boundary_box_check(
                        bbox_top_left, bbox_bot_right, bezier_point_array[n]
                    )

        # simple cubic Bezier curve command
        elif re.match("t", pd[i][0]):
            bezier_curve_path = []

            for n in range(1, len(pd[i])):
                bezier_curve_path.append(abs_point)
                coord = pd[i][n]
                point = Point(coord)
                end_point = abs_point + point
                diff = Point(
                    [abs_point.x - last_bezier_control_point.x,
                    abs_point.y - last_bezier_control_point.y]
                )
                control_point = abs_point + diff
                bezier_curve_path.append(control_point)
                bezier_curve_path.append(end_point)
                bezier_curve_path.append(end_point)
                last_bezier_control_point = control_point
                new_point = Point(pd[i][n])
                abs_point += new_point

            for n in range(0, len(bezier_curve_path), 4):

                # clear bezier point arrays
                bezier_points_x = []
                bezier_points_y = []

                # split points of bezier into 'x' and 'y' coordinate arrays
                # as this is what the point array function expects
                for m in range(0, 4):
                    bezier_points_x.append(bezier_curve_path[n + m].x)
                    bezier_points_y.append(bezier_curve_path[n + m].y)

                # caluclate the individual points along the bezier curve for 'x'
                # and 'y'
                points_x = calculate_points_of_cubic_bezier(bezier_points_x, 100)
                points_y = calculate_points_of_cubic_bezier(bezier_points_y, 100)

                bezier_point_array = []

                # put those points back into a Point type array
                for n in range(0, len(points_x)):
                    bezier_point_array.append(Point([points_x[n], points_y[n]]))

                # check each point if it extends the boundary box
                for m in range(0, len(bezier_point_array)):
                    bbox_top_left, bbox_bot_right = boundary_box_check(
                        bbox_top_left, bbox_bot_right, bezier_point_array[m]
                    )

        #        elif re.match('S', pd[i][0], re.I):
        #            pass

        # 'line to'  command
        elif re.match("l", pd[i][0]):
            for coord in pd[i][1:]:
                new_point = Point(coord)
                abs_point += new_point
                bbox_top_left, bbox_bot_right = boundary_box_check(
                    bbox_top_left, bbox_bot_right, abs_point
                )

        # 'horizontal line' command
        elif re.match("h", pd[i][0]):
            for coord in pd[i][1:]:
                new_point = Point([coord[0], 0])
                abs_point += new_point
                bbox_top_left, bbox_bot_right = boundary_box_check(
                    bbox_top_left, bbox_bot_right, abs_point
                )

        # 'vertical line' command
        elif re.match("v", pd[i][0]):
            for coord in pd[i][1:]:
                new_point = Point([0, coord[0]])
                abs_point += new_point
                bbox_top_left, bbox_bot_right = boundary_box_check(
                    bbox_top_left, bbox_bot_right, abs_point
                )

        # 'close shape' command
        elif re.match("Z", pd[i][0], re.I):
            pass

        else:
            print("ERROR: found an unsupported SVG path command " + str(pd[i][0]))

    return bbox_top_left, bbox_bot_right


def calculate_points_of_cubic_bezier(p, steps=10):
    """
    This function receives four points [start, control, control, end]
    and returns points on the cubic Bezier curve that they define. As
    'steps' decreases, so do the amount of points that are returned,
    making the curve less, well, curvey. 

    The code for this function was adapted/copied from:
    http://www.niksula.cs.hut.fi/~hkankaan/Homepages/bezierfast.html
    http://www.pygame.org/wiki/BezierCurve
    """

    t = 1.0 / steps
    temp = t * t

    f = p[0]
    fd = 3 * (p[1] - p[0]) * t
    fdd_per_2 = 3 * (p[0] - 2 * p[1] + p[2]) * temp
    fddd_per_2 = 3 * (3 * (p[1] - p[2]) + p[3] - p[0]) * temp * t

    fddd = 2 * fddd_per_2
    fdd = 2 * fdd_per_2
    fddd_per_6 = fddd_per_2 / 3.0

    points = []
    for x in range(steps):
        points.append(f)
        f += fd + fdd_per_2 + fddd_per_6
        fd += fdd + fddd_per_2
        fdd += fddd
        fdd_per_2 += fddd_per_2
    points.append(f)

    return points


def transform_path(p, center=False, scale=1, rotate_angle=0, rotate_point=None):
    """
    transforms a path
    """

    if rotate_point is None:
        rotate_point = Point()

    p_tl, p_br = calculate_bounding_box_of_path(p)

    width, height = get_width_and_height_of_shape_from_two_points(p_tl, p_br)

    # get SVG path grammar
    look_for = svg_grammar()

    # parse the input based on this grammar
    pd = look_for.parseString(p)

    # first point of path
    first_point = Point(pd[0][1])

    if center is True:
        # center point of path
        origin_point = Point([p_tl.x + width / 2, p_tl.y - height / 2])

        # caluclate what's the new starting point of path based on the new origin
        new_first_point = Point(
            [first_point.x - origin_point.x, first_point.y - origin_point.y]
        )
    else:
        new_first_point = Point([first_point.x, first_point.y])

    new_first_point.rotate(rotate_angle, rotate_point)
    new_first_point.mult(scale)
    new_p = "m %f,%f " % (new_first_point.x, new_first_point.y)

    tmpp = Point()
    origin = Point()

    for n in range(0, len(pd)):
        if pd[n][0] == "m" and n == 0:
            for m in range(2, len(pd[n])):
                tmpp.assign(pd[n][m][0], pd[n][m][1])
                tmpp.rotate(rotate_angle, rotate_point)
                tmpp.mult(scale)
                new_p += str(tmpp.x) + "," + str(tmpp.y) + " "
        else:
            if pd[n][0] == "h" or pd[n][0] == "v":
                new_p += "l "
            else:
                new_p += pd[n][0] + " "

            for m in range(1, len(pd[n])):
                if pd[n][0] == "h":
                    tmpp.assign(pd[n][m][0], 0)
                elif pd[n][0] == "v":
                    tmpp.assign(0, pd[n][m][0])
                else:
                    tmpp.assign(pd[n][m][0], pd[n][m][1])

                tmpp.rotate(rotate_angle, rotate_point)
                tmpp.mult(scale)
                new_p += str(tmpp.x) + "," + str(tmpp.y) + " "

    return width, height, new_p


def get_width_and_height_of_shape_from_two_points(tl, br):
    """
    SVG's origin is top left so we need to take the absolute value, otherwise
    the length will be negative (alternatively, we can do tl.y - br.y)
    """
    return (br.x - tl.x), abs(br.y - tl.y)  # width, height




def mirror_transform(transform, axis="y"):
    """
    Returns a mirrored transfrom 
    """

    mirrored_transform = transform

    regex = r"(?P<before>.*?)translate\s?\(\s?(?P<x>-?[0-9]*\.?[0-9]+)\s+(?P<y>-?[0-9]*\.?[0-9]+\s?)\s?\)(?P<after>.*)"
    capture = re.match(regex, transform)

    if capture is not None:
        mirrored_transform = "%s translate(%g %s) %s" % (
            capture.group("before"),
            -float(capture.group("x")),
            capture.group("y"),
            capture.group("after"),
        )

    return mirrored_transform


def create_layers_for_gerber_svg(cfg, top_layer, transform=None, refdef=None):
    """
    Creates a dictionary of SVG layers

    'top_layer' is the parent layer element

    """

    # holds all SVG layers for the board
    board_svg_layers = {}

    # create layers for top and bottom PCB layers
    for pcb_layer_name in reversed(utils.get_surface_layers(cfg)):

        # create SVG layer for PCB layer
        layer_id = pcb_layer_name
        board_svg_layers[pcb_layer_name] = {}
        board_svg_layers[pcb_layer_name]["layer"] = create_svg_layer(
            cfg, top_layer, pcb_layer_name, layer_id, transform, None, refdef
        )

        # create the following PCB sheets for the PCB layer
        pcb_sheets = ["copper", "silkscreen", "soldermask"]
        for pcb_sheet in pcb_sheets:

            # define a layer id
            layer_id = "%s_%s" % (pcb_layer_name, pcb_sheet)
            if refdef is not None:
                layer_id += "_%s" % refdef

            style = utils.dict_to_style(
                cfg["layout_style"][pcb_sheet]["default"].get(pcb_layer_name)
            )
            tmp = board_svg_layers[pcb_layer_name]
            tmp[pcb_sheet] = {}
            tmp[pcb_sheet]["layer"] = create_svg_layer(
                cfg, tmp["layer"], pcb_sheet, layer_id, None, style, refdef
            )

    # create dimensions layer
    layer_name = "outline"
    # define a layer id
    layer_id = "%s" % (layer_name)
    if refdef is not None:
        layer_id += "_%s" % refdef
    style = ""  # utils.dict_to_style(cfg['layout_style'][layer_name].get('default'))
    board_svg_layers[layer_name] = {}
    board_svg_layers[layer_name]["layer"] = create_svg_layer(
        cfg, top_layer, layer_name, layer_id, transform, style, refdef
    )

    # create drills layer
    layer_name = "drills"
    # define a layer id
    layer_id = "%s" % (layer_name)
    if refdef is not None:
        layer_id += "_%s" % refdef
    style = utils.dict_to_style(cfg["layout_style"][layer_name].get("default"))
    board_svg_layers[layer_name] = {}
    board_svg_layers[layer_name]["layer"] = create_svg_layer(
        cfg, top_layer, layer_name, layer_id, transform, style, refdef
    )

    # create drills layer
    layer_name = "documentation"
    # define a layer id
    layer_id = "%s" % (layer_name)
    if refdef is not None:
        layer_id += "_%s" % refdef
    style = utils.dict_to_style(cfg["layout_style"][layer_name].get("default"))
    board_svg_layers[layer_name] = {}
    board_svg_layers[layer_name]["layer"] = create_svg_layer(
        cfg, top_layer, layer_name, layer_id, transform, style, refdef
    )

    return board_svg_layers


def rect_to_path(shape):
    """
    Takes a 'rect' definition and returns a corresponding path
    """
    width = float(shape["width"])
    height = float(shape["height"])
    border_radius = shape.get("border-radius")
    path = svg_path_create.rect(width, height, border_radius)

    return path


def create_meandering_path(params):
    """
    Returns a meander path based on input parameters
    """

    deg_to_rad = 2 * pi / 360

    radius = params.get("radius")
    theta = params.get("theta")
    width = params.get("trace-width")
    number = params.get("bus-width") or 1
    pitch = params.get("pitch") or 0

    coords = []
    coords.append(Point([0, -(number - 1) * pitch / 2]))
    for n in range(1, int(number)):
        coords.append(Point([2 * radius * cos(theta * deg_to_rad), pitch]))

    path = ""

    for coord in coords:
        path += create_round_meander(radius, theta, coord)

    # calculate the reduction of bounding box width to be used in
    # pattern spacing setting
    spacing = radius - radius * cos(theta * deg_to_rad)

    return path, spacing


def create_round_meander(radius, theta=0, offset=None):
    """
    Returns a single period of a meandering path based on radius
    and angle theta
    """

    if offset is None:
        offest = Point()

    deg_to_rad = 2 * pi / 360

    r = radius
    t = theta * deg_to_rad

    # The calculation to obtain the 'k' coefficient can be found here:
    # http://itc.ktu.lt/itc354/Riskus354.pdf
    # "APPROXIMATION OF A CUBIC BEZIER CURVE BY CIRCULAR ARCS AND VICE VERSA"
    # by Aleksas Riskus
    k = 0.5522847498

    # the control points need to be shortened relative to the angle by this factor
    j = 2 * t / pi

    path = "m %s,%s " % (-2 * r * cos(t) - offset.x, -offset.y)
    path += "c %s,%s %s,%s %s,%s " % (
        -k * r * j * sin(t),
        -k * r * j * cos(t),
        -(r - r * cos(t)),
        -r * sin(t) + r * k * j,
        -(r - r * cos(t)),
        -r * sin(t),
    )
    path += "c %s,%s %s,%s %s,%s " % (0, -k * r, r - k * r, -r, r, -r)
    path += "c %s,%s %s,%s %s,%s " % (k * r, 0, r, r - k * r, r, r)
    path += "c %s,%s %s,%s %s,%s " % (
        0,
        k * r * j,
        -(r - r * cos(t) - k * r * j * sin(t)),
        r * sin(t) - r * k * j * cos(t),
        -r + r * cos(t),
        r * sin(t),
    )
    path += "c %s,%s %s,%s %s,%s " % (
        -k * r * j * sin(t),
        k * r * j * cos(t),
        -(r - r * cos(t)),
        r * sin(t) - r * k * j,
        -(r - r * cos(t)),
        r * sin(t),
    )
    path += "c %s,%s %s,%s %s,%s " % (0, k * r, r - k * r, r, r, r)
    path += "c %s,%s %s,%s %s,%s " % (k * r, 0, r, -r + k * r, r, -r)
    path += "c %s,%s %s,%s %s,%s " % (
        0,
        -k * r * j,
        -(r - r * cos(t) - k * r * j * sin(t)),
        -r * sin(t) + r * k * j * cos(t),
        -r + r * cos(t),
        -r * sin(t),
    )

    return path


def calculate_cubic_bezier_length(px, py):
    """
    Return the length of a cubic bezier
    """

    length = 0.0

    prev = Point([px[0], py[0]])

    for i in range(1, len(px)):
        length += sqrt((px[i] - prev.x) ** 2 + (py[i] - prev.y) ** 2)
        prev = Point([px[i], py[i]])

    return length


def coord_list_to_svg_path(coord_list):
    """
    Turn a list of points into an SVG path
    """

    path = ""  #'M 0,0 '# % (coord_list[0]['coord'].x, coord_list[0]['coord'].y)
    last_action_type = ""

    for action in coord_list:
        if action["type"] == "move":
            if last_action_type != "M":
                path += "M "
            path += "%s,%s " % (action["coord"].x, -action["coord"].y)
            last_action_type = "M"
        if action["type"] == "draw":
            if last_action_type != "L":
                path += "L "
            path += "%s,%s " % (action["coord"].x, -action["coord"].y)
            last_action_type = "L"

    return path
