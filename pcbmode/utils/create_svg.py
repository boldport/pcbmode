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
import json

from pcbmode.config import config
from pcbmode.utils import inkscape_svg
from pcbmode.utils import svg_layers
from pcbmode.utils import place
from pcbmode.utils import utils
from pcbmode.utils import dims_arrows
from pcbmode.utils.shape import Shape
from pcbmode.utils.transform import Transform


def expand_instances(d):
    """
    Recursive function to fine and resolve all instantiation definitions that need
    to be expanded.
    """
    is_d = d.get("instances", None)
    if is_d == None:
        expand_shapes(d)
        return
    ds_d = d.get("definitions", None)
    for n, i_d in is_d.items():
        i_d["definition-here"] = resolve_definition(n, i_d, ds_d)
        expand_instances(i_d["definition-here"])
    return


def resolve_definition(name, inst_d, definitions_d):
    """
    Instances can be instantiated in three ways, which are mutually exclusive:
    'definition-here': defined under this key
    'definition-name': defined under this key in 'definitions'
    'definition-file': defined in this file
 
    Here we try to find where the instance information is with some error checking.
    For files it's done in a way that should work also with OSs that use a different
    path hierarchy delimeter, like Windows.
    """

    # Check if none, or more than one definition is specified
    def_here = inst_d.get("definition-here", None)
    def_name = inst_d.get("definition-name", None)
    def_file = inst_d.get("definition-file", None)
    count = [def_here, def_name, def_file].count(None)
    if count == 3:
        logging.warning(f"'{name}' has no definition; proceeding with an empty one")
        def_here = {}
    elif count == 1:
        logging.error(f"'{name}' has multiple definitions but should have only one")
        raise Exception  # TODO: is this the right one to raise?

    # Get defintions. ('-here' is implicitly already there if other are not)
    if def_file is not None:
        path_o = Path(config.tmp["project-path"])
        def_file = def_file.split("/")
        for s in def_file:  # TODO: check if works on Windows
            path_o = Path(path_o / s)
        inst_d["definition-here"] = utils.json_to_dict(path_o)
        logging.info(f"Processed '{path_o}' for '{name}'")
    elif def_name is not None:
        try:
            inst_d["definition-here"] = definitions_d[def_name]
        except:
            logging.error(f"'{def_name}' not found for '{name}'")
            raise Exception  # TODO: is this the right one to raise?

    return inst_d["definition-here"]


def expand_shapes(d_d):
    """
    Some shape definitions will have extra shape copies to 'add'. This is convinient
    way to just add the same shape into another foil without defining the same shape
    again in the list of shapes. This is mostly used for 'conductor' pads that also need the same shape applied to soldermask and solderpaste, but with a
    globally-defined scale.

    This function copies the shape and adds it to the list of shapes after applying
    the needed modifiers.
    """
    foils = ["soldermask", "solderpaste"]
    s_d_l = d_d.get("shapes", [])  # a list of shape dicts
    for s_d in s_d_l:  # get the shape dicts
        add_d = s_d.get("add", {})
        for foil in add_d:
            if foil not in foils:
                logging.warning(
                    f"Can't recognise foil '{foil}' in 'add' shape attribute; ignoring"
                )
                continue
            s_d_copy = s_d.copy()
            del s_d_copy["add"]
            s_d_copy["place-in-foils"] = [foil]  # assign to new foil
            foil_dist = config.cfg["distances"][foil]
            if s_d["shape-type"] == "path":
                # We need to 'add' the Transforms in order to create a new shape that's
                # only different by the scale defined in the global configuration
                t_add_o = Transform(f"scale({foil_dist['path']})")
                t_shape_o = Transform(s_d.get("transform", ""))
                s_d["transform"] = (t_shape_o + t_add_o).get_str()
            elif s_d["shape-type"] == "circle":
                s_d["diameter"] += foil_dist["circle"]
            elif s_d["shape-type"] == "rect":
                s_d["height"] += foil_dist["rect"]
                s_d["width"] += foil_dist["rect"]
            s_d_l.append(s_d_copy)


def create_shape_objects(d):
    """
    Recursively converts shape definition dicts into Shape objects
    """
    is_d = d.get("instances", None)
    if is_d == None:
        return
    for n, i_d in is_d.items():
        shapes = i_d["definition-here"].get("shapes", {})
        for shape in shapes:
            shape["shape-object"] = Shape(shape)
        create_shape_objects(i_d["definition-here"])
    return


def place_shape_objects(d, layers_d):
    """
    Recursively converts shape definitions into shape objects
    """

    ns_pcm = config.cfg["ns"]["pcbmode"]

    shape_group = et.SubElement(layers_d["outline"]["layer"], "g")
    shape_group.set(f"{{{ns_pcm}}}type", "module-shapes")

    is_d = d.get("instances", None)
    if is_d == None:
        return
    for n, i_d in is_d.items():
        shapes = i_d["definition-here"].get("shapes", {})
        group = et.SubElement(layers_d["outline"]["layer"], "g")
        for shape in shapes:
            place_layers = shape.get("place-in-layers", None)
            place_sheets = shape.get("place-in-foils", None)
#            if place_layers == 'all':
#                place_layers = utils.get_all_layers_names()
#            print(place_layers, place_sheets)
            shape_o = shape["shape-object"] 
            place.place_shape(shape_o, shape_group)
        place_shape_objects(i_d["definition-here"], layers_d)
    return


def create_svg(d):
    """
    """

    ns_pcm = config.cfg["ns"]["pcbmode"]
    definitions_d = d.get("definitions", {})
    instances_d = d.get("instances", {})

    # We need the dimension of the outline shapes in order to create the SVG size based
    # on their overall bounding box
    # TODO: make work with multiple shapes. Right now it'll only consider the last
    # one (or the only one) for the abounding box calculation.
    for name, inst_d in instances_d.items():
        if inst_d.get("place-in-foil", None) == "outline":
            shapes = inst_d["definition-here"]["shapes"]
            for shape in shapes:
                dims_p = shape["shape-object"].get_dims()
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

    place_shape_objects(d, layers_d)

    # for shape in create_d["outline"]:
    #     place.place_shape(shape, shape_group)
    # pour_buffer = config.cfg["distances"]["from-pour-to"]["outline"]
    # for pcb_layer in config.stk["layer-names"]:
    #     if utils.checkForPoursInLayer(pcb_layer) is True:
    #         for shape in create_d["outline"]:
    #             mask_element = place.place_shape(shape, masks_d[pcb_layer])
    #             # Override style so that we get the desired effect
    #             # We stroke the outline with twice the size of the buffer, so
    #             # we get the actual distance between the outline and board
    #             style = (
    #                 "fill:none;stroke:#000;stroke-linejoin:round;stroke-width:%s;"
    #                 % str(pour_buffer * 2)
    #             )
    #             mask_element.set("style", style)
    #             # Also override mask's gerber-lp and set to all clear
    #             path = shape.get_path_str()
    #             segments = path.count("m")
    #             mask_element.set(f"{{{ns_pcm}}}gerber-lp", "c" * segments)

    # dims_arrows.create_and_place(layers_d, dims_p, center_p)

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

    # Expand all the declarations of definitions from other files, and create new objects for soldermask and solderpaste
    expand_instances(config.brd)
    print(json.dumps(config.brd, indent=2))

    # Convert all the shape definitions in a dict to Shape objects
    create_shape_objects(config.brd)
    # print(config.brd)

    svg_doc = create_svg(config.brd)

    save_svg(svg_doc)
