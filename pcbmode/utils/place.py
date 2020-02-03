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
from pcbmode.utils import messages as msg
from pcbmode.utils import utils
from pcbmode.utils import svg
from pcbmode.utils import svg_path_create
from pcbmode.utils.point import Point


def place_shape(shape, svg_layer, mirror=False, orig_path=False):
    """
    Places a shape of type 'Shape' onto SVG layer 'svg_layer'.
    'mirror'  : placed path should be mirrored
    'orig_path': use the original path, not the transformed one
    """

    ns_pcm = config.cfg["ns"]["pcbmode"]

    gerber_lp = shape.getGerberLP()
    location = shape.get_location()

    if (orig_path == False) and (location != Point([0,0])):
        translate = f"translate({((1, -1)[mirror]) * location.px()},{config.cfg['iya'] * location.py()})"
        transform = translate
    else:
        transform = None

    path_str = shape.get_path_str()
    el = et.SubElement(svg_layer, "path", d=path_str)

    style_class = shape.get_style_class()
    if style_class is not None:
        el.set("class", style_class)

    style_class = shape.get_style_class()
    if style_class is not None:
        el.set("class", style_class)

    style = shape.get_style()
    if style is not None:
        el.set("style", style)

    label = shape.get_label()
    if label is not None:
        coord_x = f"{((1, -1)[mirror]) * location.px()}"
        coord_y = f"{config.cfg['iya'] * location.py()}"
        label_el = et.SubElement(
            svg_layer,
            "text",
            x=coord_x,
            y=coord_y,
            # rotate against center, not x,y:
            transform=f"rotate({shape.get_rotate()},{coord_x},{coord_y})",
        )
        label_el.text = label
        label_el.set("class", shape.get_label_style_class())
        label_el.set("text-anchor", "middle")
        label_el.set("dominant-baseline", "central")

    if transform != None:
        el.set("transform", transform)

    if gerber_lp != None:
        el.set(f"{{{ns_pcm}}}gerber-lp", gerber_lp)

    if shape.get_type() == "text":
        el.set(f"{{{ns_pcm}}}text", shape.getText())

    return el


def place_label(shape, parent_el, label_text, label_class):
    """
    Add a label to the shape
    """


def placeDrill(drill, layer, location, scale, soldermask_layers={}, mask_groups={}):
    """
    Places the drilling point
    """

    diameter = drill.get("diameter")
    offset = utils.to_Point(drill.get("offset") or [0, 0])
    path = svg.drill_diameter_to_path(diameter)
    mask_path = svg_path_create.circle(diameter)

    sig_dig = config.cfg["params"]["significant-digits"]

    location.mult(scalar)
    offset.mult(scalar)
    transform = f"translate({(location + offset).px()} {(-location - offset).py()})"

    drill_element = et.SubElement(
        layer,
        "path",
        transform=transform,
        d=path,
        id="pad_drill",
        diameter=str(diameter),
    )

    pour_buffer = board_cfg["params"]["distances"]["from_pour_to"]["drill"]

    # add a mask buffer between pour and board outline
    if mask_groups != {}:
        for pcb_layer in surface_layers:
            mask_group = et.SubElement(mask_groups[pcb_layer], "g", id="drill_masks")
            pour_mask = et.SubElement(
                mask_group,
                "path",
                transform=transform,
                style=MASK_STYLE % str(pour_buffer * 2),
                gerber_lp="c",
                d=mask_path,
            )

    # place the size of the drill; id the drill element has a
    # "show_diameter": "no", then this can be suppressed
    # default to 'yes'
    show_diameter = drill.get("show_diameter") or "yes"
    if show_diameter.lower() != "no":
        text = "%s mm" % (str(diameter))
        text_style = config.stl["layout"]["drills"].get("text") or None
        if text_style is not None:
            text_style["font-size"] = str(diameter / 10.0) + "px"
            text_style = utils.dict_to_style(text_style)
            t = et.SubElement(
                layer,
                "text",
                x=str(location.x),
                # TODO: get rid of this hack
                y=str(-location.y - (diameter / 4)),
                style=text_style,
            )
            t.text = text

    # place soldermask unless specified otherwise
    # default is 'yes'
    add_soldermask = drill.get("add_soldermask") or "yes"
    style = utils.dict_to_style(config.stl["layout"]["soldermask"].get("fill"))
    possible_answers = [
        "yes",
        "top",
        "top only",
        "bottom",
        "bottom only",
        "top and bottom",
    ]
    if (add_soldermask.lower() in possible_answers) and (soldermask_layers != {}):
        # TODO: get this into a configuration parameter
        drill_soldermask_scale_factors = drill.get("soldermask_scale_factors") or {
            "top": 1.2,
            "bottom": 1.2,
        }
        path_top = svg_path_create.circle(
            diameter * drill_soldermask_scale_factors["top"]
        )
        path_bottom = svg_path_create.circle(
            diameter * drill_soldermask_scale_factors["bottom"]
        )

        if (
            add_soldermask.lower() == "yes"
            or add_soldermask.lower() == "top and bottom"
        ):
            drill_element = et.SubElement(
                soldermask_layers["top"],
                "path",
                transform=transform,
                style=style,
                d=path_top,
            )
            drill_element = et.SubElement(
                soldermask_layers["bottom"],
                "path",
                transform=transform,
                style=style,
                d=path_bottom,
            )
        elif add_soldermask.lower() == "top only" or add_soldermask.lower() == "top":
            drill_element = et.SubElement(
                soldermask_layers["top"],
                "path",
                transform=transform,
                style=style,
                d=path_top,
            )
        elif (
            add_soldermask.lower() == "bottom only"
            or add_soldermask.lower() == "bottom"
        ):
            drill_element = et.SubElement(
                soldermask_layers["bottom"],
                "path",
                transform=transform,
                style=style,
                d=path_bottom,
            )
        else:
            print("ERROR: unrecognised drills soldermask option")

    return
