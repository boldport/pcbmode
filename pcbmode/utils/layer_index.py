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


from lxml import etree as et

from pcbmode.config import config
from pcbmode.utils import utils
from pcbmode.utils import place
from pcbmode.utils import svg
from pcbmode.utils import css_utils
from pcbmode.utils import svg_path_create
from pcbmode.utils.shape import Shape
from pcbmode.utils.point import Point


def place_index(layers, width, height):
    """
    """

    ns_pcm = config.cfg["ns"]["pcbmode"]

    # Get font properties
    font_family = css_utils.get_prop(config.stl["layout"], "layer-index", "font-family")
    font_size = css_utils.get_prop(config.stl["layout"], "layer-index", "font-size")
    font_line_height = css_utils.get_prop(
        config.stl["layout"], "layer-index", "line-height"
    )

    #    text_dict = config.stl["layout"]["layer-index"]["text"]
    text_dict = {}
    text_dict["type"] = "text"
    text_dict["font-family"] = font_family
    text_dict["font-size"] = font_size
    text_dict["line-height"] = font_line_height

    # There's a small rectangle next to the text, this sets its size
    rect_width = rect_height = utils.parse_dimension(font_size)[0]
    rect_gap = 0.25

    # Location of index
    default_loc = [width / 2 + 2, config.cfg["iya"] * -(height / 2 - rect_height / 2)]
    drill_index = config.brd.get("layer-index", {"location": default_loc})
    location = Point(drill_index.get("location", default_loc))

    rect_dict = {}
    rect_dict["type"] = "rect"
    rect_dict["width"] = rect_width
    rect_dict["height"] = rect_height

    # Create group for placing index
    for pcb_layer in config.stk["layer-names"]:
        if pcb_layer in config.stk["surface-layer-names"]:
            sheets = [
                "conductor",
                "soldermask",
                "silkscreen",
                "assembly",
                "solderpaste",
            ]
        else:
            sheets = ["conductor"]

        for sheet in sheets:
            layer = layers[pcb_layer][sheet]["layer"]
            transform = f"translate({location.px()},{config.cfg['iya']*location.py()})"
            group = et.SubElement(layer, "g", transform=transform)
            group.set(f"{{{ns_pcm}}}type", "layer-index")
            rect_shape = Shape(rect_dict)
            place.place_shape(rect_shape, group)
            text_dict["value"] = f"{pcb_layer} {sheet}"
            text_shape = Shape(text_dict)
            text_width = text_shape.get_width()
            element = place.place_shape(text_shape, group)
            element.set(
                "transform",
                f"translate({rect_width / 2 + rect_gap + text_width / 2},0)",
            )
            location.y += config.cfg["iya"] * (rect_height + rect_gap)
        location.y += config.cfg["iya"] * (rect_height + rect_gap * 1.5)
