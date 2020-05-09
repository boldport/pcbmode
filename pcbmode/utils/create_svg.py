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
from pathlib import Path

import logging

from pcbmode.config import config
from pcbmode.utils import inkscape_svg
from pcbmode.utils import svg_layers
from pcbmode.utils import place
from pcbmode.utils import utils
from pcbmode.utils import dims_arrows
from pcbmode.utils.shape import Shape


def create_shapes():
    """
    """
    shapes_d = {}

    instances_d = expand_instances(config.brd.get("instances", {}))
    print(config.brd)

    # Outline
    shapes_o_l = []  # shape object list
    for shape_d in get_outline_d():
        shapes_o_l.append(Shape(shape_d))
    shapes_d["outline"] = shapes_o_l

    return shapes_d


def expand_instances(instances_d):
    """
    Instances can specify a file where the data for their footprint is. Here we read
    in those files to 'source-data'. It's done in a way that should work also with OSs that use a sifferent path hierarchy delimeter, like Windows.
    """
    for refdef, inst in instances_d.items():
        def_file = inst.get("definition-file", None)
        if def_file is not None:
            path_o = Path(config.tmp["project-path"])
            def_file = def_file.split("/")
            for s in def_file:  # TODO: check if works on Windows
                path_o = Path(path_o / s)
            inst["definition"] = utils.json_to_dict(path_o)
            logging.info(f"Processed defintion file '{def_file}' for refdef '{refdef}'")

        # Check for the case where no `definition-file` or `definition` were given
        if inst.get("definition", None) is None:
            logging.warning(f"Couldn't find a definition for refdef '{refdef}'")
            inst["definition"] = {}

    return instances_d


def get_outline_d():
    """
    Get the (optional) outline.
    There can be one or more shapes defined in the list under 'shapes' 
    """
    outline_d = config.brd.get("outline", None)
    if outline_d is not None:
        outline_shapes_l = outline_d.get("shapes", [])
    else:
        outline_shapes_l = []
    return outline_shapes_l


def create_svg(create_d):
    """
    """

    ns_pcm = config.cfg["ns"]["pcbmode"]

    # We need the dimension of the outline shapes in order to create the SVG size based
    # on their overall bounding box
    # TODO: make work with multiple shapes. Right now it'll only consider the last
    # one (or the only one) for the abounding box calculation.
    for shape in create_d["outline"]:
        dims_p = shape.get_dims()
    center_p = dims_p.copy()
    center_p.mult(0.5)  # center point

    # Create the Inkscape SVG document
    svg_data = inkscape_svg.create(dims_p.px(), dims_p.py())
    svg_doc = et.ElementTree(svg_data)

    # Create a dictionary of SVG layers
    transform = f"translate({center_p.px()} {center_p.py()})"
    layers_d = svg_layers.create_layers(svg_data, transform)
    masks_d = inkscape_svg.add_defs(svg_data, transform)

    # Place outline
    shape_group = et.SubElement(layers_d["outline"]["layer"], "g")
    shape_group.set(f"{{{ns_pcm}}}type", "module-shapes")
    for shape in create_d["outline"]:
        place.place_shape(shape, shape_group)
    pour_buffer = config.cfg["distances"]["from-pour-to"]["outline"]
    for pcb_layer in config.stk["layer-names"]:
        if utils.checkForPoursInLayer(pcb_layer) is True:
            for shape in create_d["outline"]:
                mask_element = place.place_shape(shape, masks_d[pcb_layer])
                # Override style so that we get the desired effect
                # We stroke the outline with twice the size of the buffer, so
                # we get the actual distance between the outline and board
                style = (
                    "fill:none;stroke:#000;stroke-linejoin:round;stroke-width:%s;"
                    % str(pour_buffer * 2)
                )
                mask_element.set("style", style)
                # Also override mask's gerber-lp and set to all clear
                path = shape.get_path_str()
                segments = path.count("m")
                mask_element.set(f"{{{ns_pcm}}}gerber-lp", "c" * segments)

    dims_arrows.create_and_place(layers_d, dims_p, center_p)

    return svg_doc


def save_svg(doc):
    """
    """
    output_file = Path(
        config.tmp["project-path"] / config.brd["project-params"]["output"]["svg-file"]
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(et.tostring(doc, encoding="unicode", pretty_print=True))


def create():
    """
    Create the SVG defined by the input files. This requires three primary steps.
    1. Combine all the input files while applying global and local settings
    2. Convert shape definitions into Shapes
    3. Create the SVG
    """

    shapes_d = create_shapes()
    svg_doc = create_svg(shapes_d)
    save_svg(svg_doc)
