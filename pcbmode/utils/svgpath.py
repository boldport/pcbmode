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


from math import sqrt, ceil
import re

from pcbmode.config import config
from pcbmode.utils import messages as msg
from pcbmode.utils import utils
from pcbmode.utils import svg
from pcbmode.utils.point import Point
from pcbmode.utils import svg_path_grammar


class SvgPath:
    """
    'p_' prefix means parsed
    'r_' prefix means relative path
    """

    def __init__(self, path, scale=1, rotate=0, rotate_point=None, mirror=False):

        self._path_in = path

        # Find record in cache
        digest = utils.digest(path)
        self._cache_record = config.pth.get(digest)

        # PyParsing SVG path grammar
        self._grammar = svg_path_grammar.get_grammar()

        # Parse input path
        self._p_path = self._parsed_to_list(self._grammar.parseString(self._path_in))
        if self._is_relative(self._p_path):
            self._p_r_path = self._p_path
        else:
            self._p_r_path = self._p_path_to_relative(self._p_path)

        self._bbox()  # create width, height

        # # Convert to a relative path if needed, or use the input path
        # if self._is_relative(self._p_path):
        #     self._r_path = self._path_in
        #     self._p_r_path = self._p_path
        # else:
        #     self._r_path = self._p_path_to_relative(self._p_path)
        #     self._p_r_path = self._parsed_to_list(
        #         self._grammar.parseString(self._r_path)
        #     )

        # if self._cache_record == None:
        #     config.pth[digest] = {}
        #     config.pth[digest]["relative"] = self._r_path
        #     config.pth[digest]["relative-parsed"] = self._p_r_path
        #     config.pth[digest]["width"] = self._width
        #     config.pth[digest]["height"] = self._height
        #     self._cache_record = config.pth[digest]
        # else:
        #     self._r_path = self._cache_record["relative"]
        #     self._p_r_path = self._cache_record["relative-parsed"]
        #     self._width = self._cache_record["width"]
        #     self._height = self._cache_record["height"]

    def _parsed_to_list(self, parsed):
        """
        Convery the output of PyParsing to a Python list, and coordinates to Point
        objects. 
        """
        nl = []
        for cmd in parsed:
            cmd_type = cmd[0]  # m,v,c, etc.
            lst = []
            lst.append(cmd_type)
            for coord in cmd[1:]:
                if cmd_type.lower() == "h":  # only x
                    lst.append(Point([coord[0], 0]))
                elif cmd_type.lower() == "v":  # only y
                    lst.append(Point([0, coord[0]]))
                else:
                    lst.append(Point([coord[0], coord[1]]))
            nl.append(lst)
        return nl

    def get_relative(self):
        return self._r_path

    def get_relative_parsed(self):
        return self._p_r_path

    def get_input_path(self):
        return self._path_in

    def get_first_point(self):
        """
        Return the first point of the path
        """
        try:
            return self._first_point
        except:
            self._first_point = [
                self._p_r_path[0][1].x,
                self._p_r_path[0][1].y,
            ]
            return self._first_point

    def getTransformed(self):
        return self._transformed

    def getTransformedMirrored(self):
        return self._transformed_mirrored

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height

    def _is_relative(self, path):
        """
        Check if a parsed path is relative or not by looking for absolute path commands
        """
        for p in path:
            if p[0] in ["M", "C", "Q", "T", "L", "V", "H", "S", "A"]:
                return False
        else:
            return True

    def _p_path_to_relative(self, path):
        """
        Convert a parsed path to a relative parsed path
        """

        # Store relative path here
        r_path = []

        # This variable stores the absolute coordinates as the path is converted
        abspos = Point([0, 0])

        patho = Point([0, 0])

        for seg in range(0, len(path)):

            cmd_type = path[seg][0]

            # 'move to' command
            if re.match("M", cmd_type, re.I):

                # Relative coords
                r_coords = []

                coord = path[seg][1]
                # p += "m "

                # The first M/m coordinate is always absolute
                if seg == 0:
                    abspos = coord
                    r_coords.append(abspos)
                    # p += add_xy(abspos)
                    patho = coord
                else:
                    if cmd_type == "m":
                        # p += add_xy(coord)
                        r_coords.append(coord)
                        abspos += coord
                        patho = abspos
                    else:
                        # p += add_xy(coord - abspos)
                        r_coords.append(coord - abspos)
                        abspos = coord
                        patho.x = coord.x

                # For the rest of the coordinates
                for coord in path[seg][2:]:
                    # coord.assign(coord_tmp[0], coord_tmp[1])
                    if cmd_type == "m":
                        # p += add_xy(coord)
                        r_coords.append(coord)
                        abspos += coord
                    else:
                        # p += add_xy(coord - abspos)
                        r_coords.append(coord - abspos)
                        abspos = coord

                r_path.append(["m"] + r_coords)

            # cubic Bezier (PCCP) curve command
            elif re.match("C", cmd_type, re.I):
                # p += f"{cmd_type.lower()} "

                r_coords = []

                if cmd_type == "c":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        # p += add_xy(coord)
                        r_coords.append(coord)
                    # for keeping track of the absolute position, we need to add up every
                    # *third* coordinate of the cubic Bezier curve
                    for coord in path[seg][3::3]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        abspos += coord
                        r_coords.append(coord)  # TODO: check this

                if cmd_type == "C":
                    for n in range(1, len(path[seg]) - 1, 3):
                        for m in range(0, 3):
                            # coord.assign(path[i][n + m][0], path[i][n + m][1])
                            # p += add_xy(coord - abspos)
                            r_coords.append(coord - abspos)
                        abspos = coord

                r_path.append(["c"] + r_coords)

            # quadratic Bezier (PCP) curve command
            elif re.match("Q", cmd_type, re.I):
                # p += f"{cmd_type.lower()} "

                r_coords = []

                if cmd_type == "q":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        # p += add_xy(coord)
                        r_coords.append(coord)
                    # for keeping track of the absolute position, we need to add up every
                    # *third* coordinate of the cubic Bezier curve
                    for coord in path[seg][2::2]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        abspos += coord

                if cmd_type == "Q":
                    for j in range(1, len(path[seg]) + 1, 2):
                        for coord in path[seg][j : j + 2]:
                            # coord.assign(coord_tmp[0], coord_tmp[1])
                            # p += add_xy(coord - abspos)
                            r_coords.append(coord - abspos)
                        abspos = coord

                r_path.append(["q"] + r_coords)

            # simple cubic Bezier curve command
            elif re.match("T", cmd_type, re.I):
                # p += f"{cmd_type.lower()} "

                r_coords = []

                if cmd_type == "t":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        # p += add_xy(coord)
                        r_coords.append(coord)
                        # for keeping track of the absolute position, we need to add up every
                        # *third* coordinate of the cubic Bezier curve
                        # for coord in path[i][2::2]:
                        abspos += coord

                if cmd_type == "T":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        # p += (
                        #    str(float(coord[0]) - abspos["x"])  # why like this?
                        #    + ","
                        #    + str(float(coord[1]) - abspos["y"])
                        #    + " "
                        # )
                        r_coords.append(coord - abspos)
                    abspos = coord

                r_path.append(["t"] + r_coords)

            elif re.match("S", cmd_type, re.I):
                # p += f"{cmd_type.lower()} "

                r_coords = []

                if cmd_type == "s":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        # p += add_xy(coord)
                        r_coords.append(coord)
                        abspos += coord

                if cmd_type == "S":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        # p += add_xy(coord - abspos)
                        r_coords.append(coord - abspos)
                    abspos = coord

                r_path.append(["s"] + r_coords)

            # 'line to'  command
            elif re.match("L", cmd_type, re.I):
                # p += f"{cmd_type.lower()} "

                r_coords = []

                if cmd_type == "l":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        # p += add_xy(coord)
                        r_coords.append(coord)
                        abspos += coord

                if cmd_type == "L":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], coord_tmp[1])
                        # p += add_xy(coord - abspos)
                        r_coords.append(coord - abspos)
                        abspos = coord

                r_path.append(["l"] + r_coords)

            # 'horizontal line' command
            elif re.match("H", cmd_type, re.I):
                # p += f"{cmd_type.lower()} "

                r_coords = []

                if cmd_type == "h":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], 0)
                        # p += f"{coord.px()} "
                        r_coords.append(coord)
                    abspos += coord

                if cmd_type == "H":
                    for coord in path[seg][1:]:
                        # coord.assign(coord_tmp[0], 0)
                        # p += f"{(coord.x - abspos.x).px()} "
                        r_coords.append(coord - abspos)
                        abspos = coord

                r_path.append(["h"] + r_coords)

            # 'vertical line' command
            elif re.match("V", cmd_type, re.I):
                # p += f"{cmd_type.lower()} "

                r_coords = []

                if cmd_type == "v":
                    for coord in path[seg][1:]:
                        # coord.assign(0, coord_tmp[0])
                        # p += f"{coord.py()} "
                        r_coords.append(coord)
                        abspos += coord

                if cmd_type == "V":
                    for coord in path[seg][1:]:
                        # coord.assign(0, coord_tmp[0])
                        # p += f"{(coord.y - abspos.y).py()} "
                        r_coords.append(coord - abspos)
                        abspos = coord

                r_path.append(["v"] + r_coords)

            # 'close shape' command
            elif re.match("Z", cmd_type, re.I):
                # p += f"{cmd_type.lower()} "
                abspos = abspos + (patho - abspos)
                r_path.append(["z"])

            else:
                msg.error(f"Found an unsupported SVG path command '{cmd_type}'")

        return r_path

    def _mirrorHorizontally(self, path):
        """ 
        """

        p = ""

        for i in range(0, len(path)):

            pcmd = path[i][0]

            if re.match("m", pcmd):

                if i == 0:
                    p += (
                        "m "
                        + str(-float(path[i][1][0]))
                        + ","
                        + str(path[i][1][1])
                        + " "
                    )
                else:
                    p += (
                        "m "
                        + str(-float(path[i][1][0]))
                        + ","
                        + str(path[i][1][1])
                        + " "
                    )

                for coord in path[i][2:]:
                    p += str(-float(coord[0])) + "," + coord[1] + " "

            else:
                p += path[i][0] + " "
                for coord in path[i][1:]:
                    if len(coord) > 1:
                        p += str(-float(coord[0])) + "," + str(float(coord[1])) + " "
                    else:
                        if path[i][0] == "h":
                            p += str(-float(coord[0])) + " "
                        else:
                            p += str(float(coord[0])) + " "

        return p

    def _bbox_update(self, p):
        """
        Updates top-left and bottom-right coords with input point
        """
        if p.x > self._bbox_br.x:
            self._bbox_br.x = p.x
        if p.x < self._bbox_tl.x:
            self._bbox_tl.x = p.x
        if p.y > self._bbox_tl.y:
            self._bbox_tl.y = p.y
        if p.y < self._bbox_br.y:
            self._bbox_br.y = p.y

    def _bbox(self):
        """
        Measure the bounding box of the parsed relative path and create the two
        points and width and height
        """

        path = self._p_r_path

        # last_point = Point([0,0])
        # abs_point = Point([0,0])

        # self._bbox_tl = Point([0,0])
        # self._bbox_br = Point([0,0])

        # for the t/T (shorthand bezier) command, we need to keep track
        # of the last bezier control point from previous Q/q/T/t command
        last_bezier_control_point = Point([0, 0])

        for i in range(0, len(path)):

            # 'move to' command
            if re.match("m", path[i][0]):

                if i == 0:
                    # the first coordinate is the start of both top left and bottom right
                    abs_point = path[i][1]
                    self._bbox_tl = path[i][1]
                    self._bbox_br = path[i][1]
                    # abs_point.assign(path[i][1][0], path[i][1][1])
                    # self._bbox_tl.assign(path[i][1][0], path[i][1][1])
                    # self._bbox_br.assign(path[i][1][0], path[i][1][1])
                else:
                    #                    new_point = Point(path[i][1])
                    #                    abs_point += new_point
                    abs_point += path[i][1]
                    self._bbox_update(abs_point)

                # for the rest of the coordinates
                for coord in path[i][2:]:
                    # new_point = Point(coord)
                    abs_point += coord
                    self._bbox_update(abs_point)

            # cubic Bezier curve command
            elif re.match("c", path[i][0]):

                bezier_curve_path = []

                for n in range(1, len(path[i]) - 1, 3):
                    bezier_curve_path.append(abs_point)
                    for m in range(0, 3):
                        coord = path[i][n + m]
                        # point = Point(coord)
                        bezier_curve_path.append(abs_point + coord)
                    new_point = path[i][n + m]
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
                    points_x = svg.calculate_points_of_cubic_bezier(
                        bezier_points_x, 100
                    )
                    points_y = svg.calculate_points_of_cubic_bezier(
                        bezier_points_y, 100
                    )

                    bezier_point_array = []

                    # put those points back into a Point type array
                    for n in range(0, len(points_x)):
                        bezier_point_array.append(Point([points_x[n], points_y[n]]))

                    # check each point if it extends the boundary box
                    for n in range(0, len(bezier_point_array)):
                        self._bbox_update(bezier_point_array[n])

            # quadratic Bezier curve command
            elif re.match("q", path[i][0]):

                bezier_curve_path = []

                for n in range(1, len(path[i]) - 1, 2):
                    bezier_curve_path.append(abs_point)
                    for m in range(0, 2):
                        coord = path[i][n + m]
                        # point = Point(coord)
                        bezier_curve_path.append(abs_point + coord)
                        # inject a second, identical control point so this quadratic
                        # bezier looks like a cubic one
                        if m == 1:
                            bezier_curve_path.append(abs_point + coord)
                        if m == 0:
                            last_bezier_control_point = abs_point + coord
                    # new_point = Point(path[i][n + m])
                    abs_point += path[i][n + m]  # new_point

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
                    points_x = svg.calculate_points_of_cubic_bezier(
                        bezier_points_x, 100
                    )
                    points_y = svg.calculate_points_of_cubic_bezier(
                        bezier_points_y, 100
                    )

                    bezier_point_array = []

                    # put those points back into a Point type array
                    for n in range(0, len(points_x)):
                        bezier_point_array.append(Point([points_x[n], points_y[n]]))

                    # check each point if it extends the boundary box
                    for n in range(0, len(bezier_point_array)):
                        self._bbox_update(bezier_point_array[n])

            # simple cubic Bezier curve command
            elif re.match("t", path[i][0]):
                bezier_curve_path = []

                for n in range(1, len(path[i])):
                    bezier_curve_path.append(abs_point)
                    coord = path[i][n]
                    # point = Point(coord)
                    end_point = abs_point + coord
                    diff = Point(
                        [
                            abs_point.x - last_bezier_control_point.x,
                            abs_point.y - last_bezier_control_point.y,
                        ]
                    )
                    control_point = abs_point + diff
                    bezier_curve_path.append(control_point)
                    bezier_curve_path.append(end_point)
                    bezier_curve_path.append(end_point)
                    last_bezier_control_point = control_point
                    # new_point = Point(path[i][n])
                    abs_point += coord

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
                    points_x = svg.calculate_points_of_cubic_bezier(
                        bezier_points_x, 100
                    )
                    points_y = svg.calculate_points_of_cubic_bezier(
                        bezier_points_y, 100
                    )

                    bezier_point_array = []

                    # put those points back into a Point type array
                    for n in range(0, len(points_x)):
                        bezier_point_array.append(Point([points_x[n], points_y[n]]))

                    # check each point if it extends the boundary box
                    for m in range(0, len(bezier_point_array)):
                        self._bbox_update(bezier_point_array[m])

            # 'line to' command
            elif re.match("l", path[i][0]):
                for coord in path[i][1:]:
                    # new_point = Point(coord)
                    abs_point += coord  # new_point
                    self._bbox_update(abs_point)

            # 'horizontal line' command
            elif re.match("h", path[i][0]):
                for coord in path[i][1:]:
                    # new_point = Point([coord[0], 0])
                    abs_point.x += coord.x  # new_point
                    self._bbox_update(abs_point)

            # 'vertical line' command
            elif re.match("v", path[i][0]):
                for coord in path[i][1:]:
                    # new_point = Point([0, coord[0]])
                    abs_point.y += coord.y  # new_point
                    self._bbox_update(abs_point)

            # 'close shape' command
            elif re.match("Z", path[i][0], re.I):
                pass

            else:
                print("ERROR: found an unsupported SVG path command " + str(path[i][0]))

        self._width = self._bbox_br.x - self._bbox_tl.x
        self._height = abs(self._bbox_br.y - self._bbox_tl.y)

    def transform(
        self, scale=1, rotate_angle=0, rotate_point=None, mirror=False, center=True
    ):
        """
        Transforms a parsed path 
        """

        if rotate_point is None:
            rotate_point = Point()

        path = self._p_r_path

        string = "%s%s%s%s%s%s" % (
            path,
            scale,
            rotate_angle,
            rotate_point,
            mirror,
            center,
        )
        digest = utils.digest(string)

        #        record = self._cache_record.get(digest)
        #        if record != None:
        #            pass
        # self._transformed = record["path"]
        # self._transformed_mirrored = record["mirrored"]
        # self._width = record["width"]
        # self._height = record["height"]
        #        else:

        # TODO: this needs to be fixed so that the correct path is in
        # p_r_path when invoking the following function
        self._bbox()
        # width, height = self._get_dimensions(path)
        # first point of path
        first_point = path[0][1]
        if center is True:
            # center point of path
            origin_point = Point(
                [self._bbox_tl.x + self._width / 2, self._bbox_tl.y - self._height / 2,]
            )
            # caluclate what's the new starting point of path based on the new origin
            new_first_point = Point(
                [first_point.x - origin_point.x, first_point.y - origin_point.y]
            )
        else:
            new_first_point = Point([first_point.x, first_point.y])
        new_first_point.rotate(rotate_angle, rotate_point)
        new_first_point.mult(scale)
        new_p = f"m {new_first_point.px()},{new_first_point.py()} "
        tmpp = Point()
        origin = Point()
        for n in range(0, len(path)):
            if path[n][0] == "m" and n == 0:
                for m in range(2, len(path[n])):
                    tmpp = path[n][m]
                    tmpp.rotate(rotate_angle, rotate_point)
                    tmpp.mult(scale)
                    new_p += f"{str(tmpp.px())},{str(tmpp.py())} "
            else:
                if path[n][0] == "h" or path[n][0] == "v":
                    new_p += "l "
                else:
                    new_p += path[n][0] + " "
                for m in range(1, len(path[n])):
                    if path[n][0] == "h":
                        tmpp.assign(path[n][m].x, 0)
                    elif path[n][0] == "v":
                        tmpp.assign(0, path[n][m].y)
                    else:
                        tmpp = path[n][m]
                    tmpp.rotate(rotate_angle, rotate_point)
                    tmpp.mult(scale)
                    new_p += f"{str(tmpp.px())},{str(tmpp.py())} "
        parsed = self._grammar.parseString(new_p)
        mirrored = self._mirrorHorizontally(parsed)
        if mirror == False:
            self._transformed_mirrored = mirrored
            self._transformed = new_p
        else:
            self._transformed_mirrored = new_p
            self._transformed = mirrored
        # TODO: this needs to be fixed so that the correct path is in
        # p_r_path when invoking the following function
        self._bbox()
        # width, height = self._get_dimensions(parsed)
        # self._width = width
        # self._height = height
        # self._cache_record[digest] = {}
        # self._cache_record[digest]["path"] = self._transformed
        # self._cache_record[digest]["mirrored"] = self._transformed_mirrored
        # self._cache_record[digest]["width"] = self._width
        # self._cache_record[digest]["height"] = self._height

        return

    def _linearizeCubicBezier(self, p, steps):
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

    def _getCubicBezierLength(self, px, py):
        """
        Return the length of a cubic bezier
        """

        length = 0.0

        prev = Point(px[0], py[0])

        for i in range(1, len(px)):
            length += sqrt((px[i] - prev.x) ** 2 + (py[i] - prev.y) ** 2)
            prev = Point([px[i], py[i]])

        return length

    def getCoordList(self, steps, length):
        return self._makeCoordList(self._relative_parsed, steps, length)

    def _makeCoordList(self, path, steps, length):
        """
        """

        # absolute position
        ap = Point()

        # path origin
        po = Point()

        points = []
        p = []

        # TODO: legacy
        pd = path

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
                    points_x = self._linearizeCubicBezier(bezier_points_x, steps)
                    points_y = self._linearizeCubicBezier(bezier_points_y, steps)

                    path_length = self._getCubicBezierLength(points_x, points_y)

                    if path_length == 0:
                        steps_tmp = 1
                    else:
                        steps_tmp = ceil(path_length / length)
                    skip = int(ceil(steps / steps_tmp))

                    bezier_point_array = []

                    # put thos points back into a Point type array
                    for n in range(0, len(points_x), skip):
                        bezier_point_array.append(Point([points_x[n], points_y[n]]))
                    bezier_point_array.append(
                        Point(
                            [points_x[len(points_x) - 1], points_y[len(points_x) - 1]]
                        )
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
                    points_x = self._linearizeCubicBezier(bezier_points_x, steps)
                    points_y = self._linearizeCubicBezier(bezier_points_y, steps)

                    path_length = self._getCubicBezierLength(points_x, points_y)
                    skip = int(ceil(steps / (path_length / length)))

                    bezier_point_array = []

                    # put those points back into a Point type array
                    for n in range(0, len(points_x), skip):
                        bezier_point_array.append(Point([points_x[n], points_y[n]]))
                    bezier_point_array.append(
                        Point(
                            [points_x[len(points_x) - 1], points_y[len(points_x) - 1]]
                        )
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
                        [
                            ap.x - last_bezier_control_point.x,
                            ap.y - last_bezier_control_point.y,
                        ]
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
                    points_x = self._linearizeCubicBezier(bezier_points_x, steps)
                    points_y = self._linearizeCubicBezier(bezier_points_y, steps)

                    path_length = self._getCubicBezierLength(points_x, points_y)
                    skip = int(ceil(steps / (path_length / length)))

                    bezier_point_array = []

                    # put those points back into a Point type array
                    for m in range(0, len(points_x), skip):
                        bezier_point_array.append(Point([points_x[m], points_y[m]]))
                    bezier_point_array.append(
                        Point(
                            [points_x[len(points_x) - 1], points_y[len(points_x) - 1]]
                        )
                    )

                    p += bezier_point_array

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
                msg.error("Found an unsupported SVG path command, '%s'" % cmd)

        points.append(p)

        return points

    def getNumberOfSegments(self):
        """
        """
        return self._r_path.lower().count("m")
