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


import datetime
import copy
import sys
from pathlib import Path
from lxml import etree as et

from pcbmode.config import config
from pcbmode.utils import messages as msg
from pcbmode.utils import svg
from pcbmode.utils import utils
from pcbmode.utils import place
from pcbmode.utils import inkscape_svg
from pcbmode.utils import css_utils
from pcbmode.utils import svg_layers
from pcbmode.utils import drill_index
from pcbmode.utils import layer_index
from pcbmode.utils import documentation
from pcbmode.utils import svg_path_create
from pcbmode.utils.shape import Shape
from pcbmode.utils.component import Component
from pcbmode.utils.svgpath import SvgPath
from pcbmode.utils.point import Point


def create_and_place(layers_d, dims_p, center_p):
    """
    Places outline dimension arrows
    """

    # Create text shapes
    shape_dict = {}
    shape_dict["type"] = "text"
    style_class = "dimensions"
    layout_d = config.stl["layout"]
    for prop in ["font-family", "font-size", "line-height", "letter-spacing"]:
        shape_dict[prop] = css_utils.get_prop(layout_d, style_class, prop)

    # Dimension arrow properties
    arrow_gap = 1.5
    arrow_bar_length = 1.6  # bar against arrow head
    arrow_height = 2.2  # height of arrow's head
    arrow_base = 1.2  # width of arrow's head
    width_loc = [0, center_p.py() + arrow_gap]
    height_loc = [-(center_p.px() + arrow_gap), 0]

    # Width text
    width_text_dict = shape_dict.copy()
    width_text_dict["value"] = f"{center_p.px()} mm"
    width_text_dict["location"] = width_loc
    width_text = Shape(width_text_dict)

    # Height text
    height_text_dict = shape_dict.copy()
    height_text_dict["value"] = f"{center_p.py()} mm"
    height_text_dict["rotate"] = -90
    height_text_dict["location"] = height_loc
    height_text = Shape(height_text_dict)

    # Width arrow
    shape_dict = {}
    shape_dict["type"] = "path"
    shape_dict["value"] = SvgPath(
        svg_path_create.arrow(
            width=dims_p.px(),
            height=arrow_height,
            base=arrow_base,
            bar=arrow_bar_length,
            gap=width_text.get_width() * 1.5,
        )
    ).get_path_str()
    shape_dict["location"] = width_loc
    shape_dict["style"] = "stroke-width:0.2;"
    width_arrow = Shape(shape_dict)

    # Height arrow
    shape_dict = {}
    shape_dict["type"] = "path"
    shape_dict["value"] = SvgPath(
        svg_path_create.arrow(
            width=dims_p.py(),
            height=arrow_height,
            base=arrow_base,
            bar=arrow_bar_length,
            gap=height_text.get_height() * 1.5,
        )
    ).get_path_str()
    shape_dict["rotate"] = -90
    shape_dict["location"] = height_loc
    shape_dict["style"] = "stroke-width:0.2;"
    height_arrow = Shape(shape_dict)

    svg_layer = layers_d["dimensions"]["layer"]
    group = et.SubElement(svg_layer, "g")
    group.set(f"{{{config.cfg['ns']['pcbmode']}}}type", "module-shapes")
    place.place_shape(width_text, group)
    place.place_shape(height_text, group)
    place.place_shape(width_arrow, group)
    place.place_shape(height_arrow, group)
