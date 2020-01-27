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
    'p_' xor 's_' prefixes mean parsed xor stringed
    'r_' prefix means relative path
    """

    def __init__(self, path, scale=1, rotate=0, rotate_point=None, mirror=False):

        self._path_in = path

        # PyParsing SVG path grammar
        # TODO: remove this when transform is fixed
        self._grammar = svg_path_grammar.get_grammar()

        self._p_path = self._parse_path(self._path_in)
        self._p_r_path = self._p_path_to_relative(self._p_path)
        self._width, self._height, self._bbox_tl, self._bbox_br = self._bbox(
            self._p_r_path
        )
        self._num_of_segs = self._get_num_of_segs(self._p_r_path)

    def _get_num_of_segs(self, r_p_path):
        """ Return the number of segments of a relative parsed path """
        num = 0
        for seg in r_p_path:
            if seg[0] == "m":  # keep track of number of segments
                num += 1
        return num

    def _parse_path(self, path_in):
        """
        Parse the SVG path into PCBmodE list structure
        """
        p_path = []

        svg_path_cmds = r"MmCcQqTtLlVvHhSsAaZz"
        svg_path_nums = r"\s\+\-0-9eE\.,"
        svg_coord = r"[+-]?[\d+\.]*\d*[Ee]?[+-]?\d+"

        # Split path into segments
        segs = re.findall(f"([{svg_path_cmds}])([{svg_path_nums}]*)?", path_in)

        for seg in segs:
            seg_cmd = seg[0]
            seg_list = [seg_cmd]

            if seg_cmd.lower() in ["h", "v"]:  # these only have x or y, respectively
                coords = re.findall(f"{svg_coord}", seg[1])
            else:
                coords = re.findall(f"{svg_coord}[,\s]{svg_coord}", seg[1])

            for coord in coords:
                if seg_cmd.lower() == "h":
                    seg_list.append(Point([coord, 0]))
                elif seg_cmd.lower() == "v":
                    seg_list.append(Point([0, coord]))
                else:
                    seg_list.append(Point(re.split(",| ", coord)))

            p_path.append(seg_list)

        return p_path

    def _stringify_path(self):
        """
        Creates an SVG path string from the parsed list of the relative path
        """
        s_path = ""
        for seg in self._p_r_path:
            cmd_type = seg[0]
            s = ""
            for coord in seg[1:]:
                if cmd_type == "v":
                    s += f"{coord.py()} "
                elif cmd_type == "h":
                    s += f"{coord.px()} "
                else:
                    s += f"{coord.px()},{coord.py()} "
            s_path += f"{cmd_type} {s}"
        self._s_r_path = s_path

    def get_relative(self):
        try:
            return self._s_r_path
        except:
            self._stringify_path()
            return self._s_r_path

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

    def _p_path_to_relative(self, path):
        """
        Convert a parsed path to a relative parsed path
        """

        # Check if already relative
        for p in path:
            if p[0] in ["M", "C", "Q", "T", "L", "V", "H", "S", "A"]:
                break
        else:
            return path

        r_path = []

        abspos = Point([0, 0])  # absolute coordinates as the path is converted
        patho = Point([0, 0])

        for seg in range(0, len(path)):

            cmd_type = path[seg][0]

            if re.match("M", cmd_type, re.I):  # 'move to'
                r_coords = []  # relative coords
                coord = path[seg][1]
                if seg == 0:  # first M/m coord is always absolute
                    abspos = coord
                    r_coords.append(abspos)
                    patho = coord
                else:
                    if cmd_type == "m":
                        r_coords.append(coord)
                        abspos += coord
                        patho = abspos
                    else:
                        r_coords.append(coord - abspos)
                        abspos = coord
                        patho.x = coord.x
                for coord in path[seg][2:]:  # the rest of the coordinates
                    if cmd_type == "m":
                        r_coords.append(coord)
                        abspos += coord
                    else:
                        r_coords.append(coord - abspos)
                        abspos = coord
                r_path.append(["m"] + r_coords)

            elif re.match("C", cmd_type, re.I):  # cubic Bezier (PCCP)
                r_coords = []
                if cmd_type == "c":
                    for coord in path[seg][1:]:
                        r_coords.append(coord)
                    # To keep track of the absolute position, we need to add up every
                    # *third* coordinate of the cubic Bezier curve
                    for coord in path[seg][3::3]:
                        abspos += coord
                if cmd_type == "C":
                    for n in range(1, len(path[seg]) - 1, 3):
                        for m in range(0, 3):
                            coord = path[seg][n + m]
                            r_coords.append(coord - abspos)
                        abspos = coord
                r_path.append(["c"] + r_coords)

            elif re.match("Q", cmd_type, re.I):  # quadratic Bezier (PCP)
                r_coords = []
                if cmd_type == "q":
                    for coord in path[seg][1:]:
                        r_coords.append(coord)
                    # To keep track of the absolute position, we need to add up every
                    # *third* coordinate of the cubic Bezier curve
                    for coord in path[seg][2::2]:
                        abspos += coord
                if cmd_type == "Q":
                    for j in range(1, len(path[seg]) + 1, 2):
                        for coord in path[seg][j : j + 2]:
                            r_coords.append(coord - abspos)
                        abspos = coord
                r_path.append(["q"] + r_coords)

            elif re.match("T", cmd_type, re.I):  # simple cubic bezier
                r_coords = []
                if cmd_type == "t":
                    for coord in path[seg][1:]:
                        r_coords.append(coord)
                        # to keep track of the absolute position, we need to add up
                        # every *third* coordinate of the cubic Bezier curve
                        abspos += coord
                if cmd_type == "T":
                    for coord in path[seg][1:]:
                        r_coords.append(coord - abspos)
                    abspos = coord
                r_path.append(["t"] + r_coords)

            elif re.match("S", cmd_type, re.I):
                r_coords = []
                if cmd_type == "s":
                    for coord in path[seg][1:]:
                        r_coords.append(coord)
                        abspos += coord
                if cmd_type == "S":
                    for coord in path[seg][1:]:
                        r_coords.append(coord - abspos)
                    abspos = coord
                r_path.append(["s"] + r_coords)

            elif re.match("L", cmd_type, re.I):  # line to
                r_coords = []
                if cmd_type == "l":
                    for coord in path[seg][1:]:
                        r_coords.append(coord)
                        abspos += coord
                if cmd_type == "L":
                    for coord in path[seg][1:]:
                        r_coords.append(coord - abspos)
                        abspos = coord
                r_path.append(["l"] + r_coords)

            elif re.match("H", cmd_type, re.I):  # hotizontal line
                r_coords = []
                if cmd_type == "h":
                    for coord in path[seg][1:]:
                        r_coords.append(coord)
                    abspos += coord
                if cmd_type == "H":
                    for coord in path[seg][1:]:
                        r_coords.append(coord - abspos)
                        abspos = coord
                r_path.append(["h"] + r_coords)

            elif re.match("V", cmd_type, re.I):  # vertical line
                r_coords = []
                if cmd_type == "v":
                    for coord in path[seg][1:]:
                        r_coords.append(coord)
                        abspos += coord
                if cmd_type == "V":
                    for coord in path[seg][1:]:
                        r_coords.append(coord - abspos)
                        abspos = coord
                r_path.append(["v"] + r_coords)

            elif re.match("Z", cmd_type, re.I):  # close shape
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

    def _bbox_update(self, tl, br, p):
        """
        Updates top-left and bottom-right coords with input point
        """
        tl_new = Point([min(p.x, tl.x), max(p.y,tl.y)]) 
        br_new = Point([max(p.x, br.x), min(p.y,br.y)]) 
        return tl_new, br_new

    def _bbox(self, p_path):
        """
        Measure the bounding box of a parsed relative path 
        """

        path = p_path

#        print(f"ORIGIN: {self._path_in}")
#        print(f"PARSED: {p_path}")

        # For the t/T (shorthand bezier) command, we need to keep track
        # of the last bezier control point from previous Q/q/T/t command
        last_bezier_control_point = Point([0, 0])

 
        for i, seg in enumerate(path):
            cmd_type = seg[0]
            if cmd_type == 'm':  # move to
                if i == 0: # first segment special case
                    abs_point = seg[1]
                    tl = seg[1] # first point
                    br = seg[1] # tl, br are equal
                else:
                    abs_point += seg[1]
                    tl, br = self._bbox_update(tl, br, abs_point)

                for coord in seg[2:]:
                    abs_point += coord
                    tl, br = self._bbox_update(tl, br, abs_point)

            elif cmd_type == "c":  # cubic bezier
                bezier_curve_path = []

                for n in range(1, len(seg) - 1, 3):
                    bezier_curve_path.append(abs_point)
                    for m in range(0, 3):
                        coord = seg[n + m]
                        bezier_curve_path.append(abs_point + coord)
                    abs_point += seg[n + m]

                for n in range(0, len(bezier_curve_path), 4):
                    bezier_points_x = []
                    bezier_points_y = []
                    # Split points of bezier into 'x' and 'y' coordinate arrays
                    # as this is what the point array function expects
                    for m in range(0, 4):
                        bezier_points_x.append(bezier_curve_path[n + m].x)
                        bezier_points_y.append(bezier_curve_path[n + m].y)
                    # Caluclate the individual points along the bezier curve for 'x'
                    # and 'y'
                    points_x = self._flatten_cubic(bezier_points_x, 100)
                    points_y = self._flatten_cubic(bezier_points_y, 100)
                    bezier_point_array = []
                    # Put those points back into a Point type array
                    for n in range(0, len(points_x)):
                        bezier_point_array.append(Point([points_x[n], points_y[n]]))
                    # Check each point if it extends the boundary box
                    for n in range(0, len(bezier_point_array)):
                        tl, br = self._bbox_update(tl, br, bezier_point_array[n])

            elif cmd_type == "q":  # quadratic bezier
                bezier_curve_path = []
                for n in range(1, len(path[i]) - 1, 2):
                    bezier_curve_path.append(abs_point)
                    for m in range(0, 2):
                        coord = seg[n + m]
                        bezier_curve_path.append(abs_point + coord)
                        # inject a second, identical control point so this quadratic
                        # bezier looks like a cubic one
                        if m == 1:
                            bezier_curve_path.append(abs_point + coord)
                        if m == 0:
                            last_bezier_control_point = abs_point + coord
                    abs_point += seg[n + m]

                for n in range(0, len(bezier_curve_path), 4):
                    bezier_points_x = []
                    bezier_points_y = []
                    # split points of bezier into 'x' and 'y' coordinate arrays
                    # as this is what the point array function expects
                    for m in range(0, 4):
                        bezier_points_x.append(bezier_curve_path[n + m].x)
                        bezier_points_y.append(bezier_curve_path[n + m].y)
                    # caluclate the individual points along the bezier curve for 'x'
                    # and 'y'
                    points_x = self._flatten_cubic(bezier_points_x, 100)
                    points_y = self._flatten_cubic(bezier_points_y, 100)
                    bezier_point_array = []
                    # Put those points back into a Point type array
                    for n in range(0, len(points_x)):
                        bezier_point_array.append(Point([points_x[n], points_y[n]]))
                    # Check each point if it extends the boundary box
                    for n in range(0, len(bezier_point_array)):
                        tl, br = self._bbox_update(tl, br, bezier_point_array[n])

            elif cmd_type == "t":  # simple cubic bezier
                bezier_curve_path = []
                for n in range(1, len(path[i])):
                    bezier_curve_path.append(abs_point)
                    coord = path[i][n]
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
                    abs_point += coord

                for n in range(0, len(bezier_curve_path), 4):
                    bezier_points_x = []
                    bezier_points_y = []
                    # Split points of bezier into 'x' and 'y' coordinate arrays
                    # as this is what the point array function expects
                    for m in range(0, 4):
                        bezier_points_x.append(bezier_curve_path[n + m].x)
                        bezier_points_y.append(bezier_curve_path[n + m].y)
                    # Caluclate the individual points along the bezier curve for 'x'
                    # and 'y'
                    points_x = self._flatten_cubic(bezier_points_x, 100)
                    points_y = self._flatten_cubic(bezier_points_y, 100)
                    bezier_point_array = []
                    # Put those points back into a Point type array
                    for n in range(0, len(points_x)):
                        bezier_point_array.append(Point([points_x[n], points_y[n]]))
                    # Check each point if it extends the boundary box
                    for m in range(0, len(bezier_point_array)):
                        tl, br = self._bbox_update(tl, br, bezier_point_array[m])

            elif cmd_type in ['l', 'h', 'v']:  # line to, horizontal, vertical
                for coord in seg[1:]:
                    abs_point += coord
                    tl, br = self._bbox_update(tl, br, abs_point)

            else:
                print(
                    "BBOX... ERROR: found an unsupported SVG path command "
                    + str(cmd_type)
                )

        width = br.x - tl.x
        height = abs(br.y - tl.y)

        print(f"TL, BR: {tl},{br}")
        print(f"W,H: {width},{height}")

        return (width, height, tl, br)

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

        # TODO: this needs to be fixed so that the correct path is in
        # p_r_path when invoking the following function
        # self._bbox(path)
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

        # parsed = self._parse_path(new_p)
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
        # self._bbox(self._transformed)

        return

    def _flatten_cubic(self, cp, steps):
        """
        This function receives four points [start, control, control, end]
        and returns points on the cubic Bezier curve that they define. As
        'steps' decreases, so do the amount of points that are returned,
        making the curve less, well, curvey. 
     
        The code for this function was adapted/copied from:
        http://www.niksula.cs.hut.fi/~hkankaan/Homepages/bezierfast.html
        http://www.pygame.org/wiki/BezierCurve

        cp: list of four cubuc bezier points
        """

        t = 1.0 / steps
        temp = t * t

        f = cp[0]
        fd = 3 * (cp[1] - cp[0]) * t
        fdd_per_2 = 3 * (cp[0] - 2 * cp[1] + cp[2]) * temp
        fddd_per_2 = 3 * (3 * (cp[1] - cp[2]) + cp[3] - cp[0]) * temp * t

        fddd = 2 * fddd_per_2
        fdd = 2 * fdd_per_2
        fddd_per_6 = fddd_per_2 / 3.0

        fcp = []  # flattened cubic points
        for x in range(steps):
            fcp.append(f)
            f += fd + fdd_per_2 + fddd_per_6
            fd += fdd + fddd_per_2
            fdd += fddd
            fdd_per_2 += fddd_per_2
        fcp.append(f)

        return fcp

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

    def get_num_of_segments(self):
        """
        """
        return self._num_of_segs

