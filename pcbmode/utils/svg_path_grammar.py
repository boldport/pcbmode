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


import pyparsing as PP


def get_grammar():
    """ 
    Return the pyparsing grammar for an SVG path
    """

    comma = PP.Literal(",").suppress() # suppress doesn't capture the 'comma
    coord = PP.Regex(r"-?\d+(\.\d*)?([Ee][+-]?\d+)?")
    coord_x1 = PP.Group(coord)
    xy_x1 = PP.Group(coord + PP.Optional(comma) + coord)
    xy_x2 = (xy_x1 + PP.Optional(comma))*2
    xy_x3 = (xy_x1 + PP.Optional(comma))*3

    # Note to future self trying to optimise (from pp docs):
    # CaselessLiteral - construct with a string to be matched, but without case
    # checking;results are always returned as the defining literal, NOT as they are 
    # found in the input string

    c_M = PP.Literal("M") + PP.OneOrMore(xy_x1)
    c_m = PP.Literal("m") + PP.OneOrMore(xy_x1)
    c_C = PP.Literal("C") + PP.OneOrMore(xy_x3)
    c_c = PP.Literal("c") + PP.OneOrMore(xy_x3)
    c_Q = PP.Literal("Q") + PP.OneOrMore(xy_x2)
    c_q = PP.Literal("q") + PP.OneOrMore(xy_x2)
    c_T = PP.Literal("T") + PP.OneOrMore(xy_x1)
    c_t = PP.Literal("t") + PP.OneOrMore(xy_x1)
    c_L = PP.Literal("L") + PP.OneOrMore(xy_x1)
    c_l = PP.Literal("l") + PP.OneOrMore(xy_x1)
    c_V = PP.Literal("V") + PP.OneOrMore(coord_x1)
    c_v = PP.Literal("v") + PP.OneOrMore(coord_x1)
    c_H = PP.Literal("H") + PP.OneOrMore(coord_x1)
    c_h = PP.Literal("h") + PP.OneOrMore(coord_x1)
    c_S = PP.Literal("S") + PP.OneOrMore(xy_x2)
    c_s = PP.Literal("s") + PP.OneOrMore(xy_x2)
    c_z = PP.Literal("z")
    c_Z = PP.Literal("Z")

    path_cmd = (
          c_M | c_m
        | c_C | c_c
        | c_Q | c_q
        | c_T | c_t
        | c_L | c_l
        | c_V | c_v
        | c_H | c_h
        | c_S | c_s
        | c_Z | c_z
    )

    return PP.OneOrMore(PP.Group(path_cmd))
