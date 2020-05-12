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

import re
import math


class Transform:
    def __init__(self, t=""):
        self._parse(t)

    def _parse(self, t):
        """
        """
        t_p_l = []  # _t_ransform _p_arsed

        # Here we have (?:...) to indicate a non-capturing group so that it doesn't
        # interfere with the group numbering. This was helpful:
        # https://stackoverflow.com/questions/2703029/    why-isnt-the-regular-expressions-non-capturing-group-working
        num = "[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?"
        types = "matrix|translate|rotate|scale|skewX|skewY"

        # Capture up to 6 parameters. Variable names aren't possible:
        # https://stackoverflow.com/questions/61565226/    python-regex-named-result-with-variable
        regex = f"({types})\((?P<a1>{num})(?:,?\s?(?P<a2>{num}))?(?:,?\s?(?P<a3>{num}))?(?:,?\s?(?P<a4>{num}))?(?:,?\s?(?P<a5>{num}))?(?:,?\s?(?P<a6>{num}))?\)"

        for match in re.finditer(regex, t):
            cmd = match.group(1)  # the command (translate, scale, etc.)
            args = {k: float(v) for k, v in match.groupdict().items() if v is not None}
            an = len(args)  # number of arguments
            if cmd == "translate":
                inst = {cmd: []}
                if an > 2:
                    logging.warning(
                        f"In transform '{t}', '{cmd}' can only have 1 or 2 argument; ignoring"
                    )
                elif an == 0:
                    inst[cmd].append(0)
                    inst[cmd].append(0)
                elif an == 1:
                    inst[cmd].append(args["a1"])
                    inst[cmd].append(0)
                else:
                    inst[cmd].append(args["a1"])
                    inst[cmd].append(args["a2"])
                t_p_l.append(inst)
            elif cmd == "scale":
                inst = {cmd: []}
                if an > 2:
                    logging.warning(
                        f"In transform '{t}', '{cmd}' can have only 1 or 2 arguments; ignoring"
                    )
                elif an == 0:
                    inst[cmd].append(1)
                    inst[cmd].append(1)
                elif an == 1:
                    inst[cmd].append(args["a1"])
                    inst[cmd].append(args["a1"])
                else:
                    inst[cmd].append(args["a1"])
                    inst[cmd].append(args["a2"])
                t_p_l.append(inst)
            elif cmd == "rotate":
                inst = {cmd: []}
                if (an > 3) or (an == 2):
                    logging.warning(
                        f"In transform '{t}', '{cmd}' can only have 1 or 3 arguments; ignoring"
                    )
                elif an == 0:
                    inst[cmd].append(0)
                elif an == 1:
                    inst[cmd].append(args["a1"])
                else:
                    inst[cmd].append(args["a1"])
                    inst[cmd].append(args["a2"])
                    inst[cmd].append(args["a3"])
                t_p_l.append(inst)
            elif cmd == "matrix":
                inst = {cmd: []}
                if an != 6:
                    logging.warning(
                        f"In transform '{t}', '{cmd}' must have 6 arguments; ignoring"
                    )
                else:
                    for i in range(1, 7):
                        inst[cmd].append(args[f"a{i}"])
                    cmd_l = self._decompose_matrix(inst[cmd])
                t_p_l += cmd_l  # add the decomposed matrix elements
            elif (cmd == "skewX") or (cmd == "skewY"):
                if an != 1:
                    logging.warning(
                        f"In transform '{t}', {cmd} must have only 1 arguments; ignoring"
                    )
                else:
                    t_p_l.append({cmd: [args["a1"]]})
            else:
                logging.warning(f"In transform '{t}', '{cmd}' is not yet supported")

        self._t_p_l = t_p_l


    def _decompose_matrix(self, matrix_l):
        """
        Decomposes an SVG transformation matrix into 'translate', 'rotate', and 'scale'.
        
        'matrix_l': list of 6 elements.
    
        The code below is based on the following resources:
        https://stackoverflow.com/questions/5107134/    find-the-rotation-and-skew-of-a-matrix-transformation
        http://frederic-wang.fr/decomposition-of-2d-transform-matrices.html
        https://stackoverflow.com/questions/4361242/    extract-rotation-scale-values-from-2d-transformation-matrix/4361442#4361442
        """

        if len(matrix_l) != 6:
            logging.warning(f"Matrix {matrix_l} must contain 6 elements; ignoring")
            return

        a, b, c, d, e, f = matrix_l  # conventional variable naming
        translate = [e, f]
        radicand = math.pow(a, 2) + math.pow(b, 2)
        sqrt = math.sqrt(radicand)
        scale = [sqrt, (a * d - b * c) / sqrt]
        rotate = [math.degrees(math.atan2(b, a))]
        skewX = math.degrees(math.atan2(a * c + b * d, radicand))
        skewY = 0  # QR-like decomposition

        cmd_l = []
        if translate != [0, 0]:
            cmd_l.append({"translate": translate})
        if scale != [1, 1]:
            cmd_l.append({"scale": scale})
        if rotate != 0:
            cmd_l.append({"rotate": rotate})
        if skewX != 0:
            cmd_l.append({"skewX": skewX})

        return cmd_l

    def get_list(self):
        return self._t_p_l

    def get_str(self):
        t_str = ""
        print(self._t_p_l)
        for cmd_d in self._t_p_l:
            for cmd,args in cmd_d.items():
                arg_str = ",".join(str(x) for x in args)
                t_str += f"{cmd}({arg_str}) "
        return t_str.rstrip()