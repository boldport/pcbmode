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
import copy

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
    Recursive function to find and resolve all instantiation definitions that need
    to be expanded.
    """
    is_d = d.get("instances", None)  # get the instantiations
    if is_d == None:  # we're at the end, expand the shapes (soldermask, solderpaste)
        expand_shapes(d)
        return

    # Resolve where the definitions are, and place them in 'definitions-here'
    ds_d = d.get("definitions", None)

    # Iterate on the named instances (like pins 1, 2, 3, etc.). Each of those
    # instances will indicate where a definition for it is (-here, -name, -file)
    for n, i_d in is_d.items():
        i_d["definition-here"] = resolve_definition(n, i_d, ds_d)
        # Recursive call to get through the hierarchy, looking for more instance
        # definitions
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

    The outcome is that each instance has a 'definition-here' rather than a reference
    """

    # Check if none, or more than one definition is specified
    def_here = inst_d.get("definition-here", None)
    def_name = inst_d.get("definition-name", None)
    def_file = inst_d.get("definition-file", None)
    count = [def_here, def_name, def_file].count(None)  # how many 'None'?
    if count == 3:
        logging.warning(f"'{name}' has no definition; proceeding with an empty one")
        def_here = {}
    elif count == 1:
        logging.error(f"'{name}' has multiple definitions but should have only one")
        raise Exception  # TODO: is this the right one to raise?

    # Get defintions. ('-here' is implicitly already there if others are not)
    if def_file is not None:
        path_o = Path(config.tmp["project-path"])
        def_file = def_file.split("/")
        for s in def_file:  # TODO: check if works on Windows
            path_o = Path(path_o / s)
        inst_d["definition-here"] = utils.json_to_dict(path_o)
        logging.info(f"Processed '{path_o}' for '{name}'")
    elif def_name is not None:
        try:
            inst_d["definition-here"] = copy.deepcopy(definitions_d[def_name])
        except:
            logging.error(f"'{def_name}' not found for '{name}'")
            raise Exception  # TODO: is this the right one to raise?

    return inst_d["definition-here"]


def expand_shapes(d_d):
    """
    When adding a soldering pad it's convenient to also add a slightly enlarged shape
    on the soldermask layer and a slightly reduced shape on the solderpaste layer.
    Here we use two directives (soldermask-in and solderpaste-in) to let the user
    place those without needing to redefine these shapes in another entry. 

    This function copies the shape and adds it to the list of shapes after applying
    the default modifiers. If the user doesn't enter these directives, the shapes are
    not added.
    """
    foils = ["solderpaste", "soldermask"]
    s_d_l = d_d.get("shapes", [])  # shape dicts list
    add_l = []  # List of new shapes
    for s_d in s_d_l:  # iterate on shape dicts
        for foil in foils:
            sm_place = expand_layers(s_d.get(f"{foil}-in", []))
            if sm_place != []:
                s_d_c = copy.deepcopy(s_d)  # work on the copy!
                s_d_c["place-in"] = sm_place  # assign to new foil
                foil_dist = config.cfg["distances"][foil]
                if s_d_c["shape-type"] == "path":
                    # We need to 'add' the Transforms in order to create a new shape
                    # that's only different by the scale defined in the global
                    # configuration
                    t_add_o = Transform(f"scale({foil_dist['path']})")
                    t_shape_o = Transform(s_d_c.get("transform", ""))
                    s_d_c["transform"] = (t_shape_o + t_add_o).get_str()
                elif s_d_c["shape-type"] == "circle":
                    s_d_c["diameter"] += foil_dist["circle"]
                elif s_d_c["shape-type"] == "rect":
                    s_d_c["height"] += foil_dist["rect"]
                    s_d_c["width"] += foil_dist["rect"]
                add_l.append(s_d_c)
    s_d_l += add_l  # add the new shapes to list of shapes


def apply_transformations(d, t_o_in=None):
    """
    Recursively stacks up transformations from the top level down to the shapes.
    The -g stands for 'global', which represents the absolute position on the canvas.
    """
    if t_o_in == None:
        t_o_in = Transform()

    d["t-o"] = Transform(d.get("transform", ""))
    d["t-g-o"] = Transform(d["t-o"].get_str()) + t_o_in

    is_d = d.get("instances", None)
    if is_d == None:
        return
    for n, i_d in is_d.items():
        i_d["t-o"] = Transform(i_d.get("transform", ""))
        i_d["t-g-o"] = Transform(i_d["t-o"].get_str()) + d["t-g-o"]
        shapes = i_d["definition-here"].get("shapes", {})
        for shape in shapes:
            shape["t-o"] = Transform(shape.get("transform", ""))
            shape["t-g-o"] = Transform(shape["t-o"].get_str()) + i_d["t-g-o"]
        apply_transformations(i_d["definition-here"], i_d["t-g-o"])
    return


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


def expand_layers(l):
    """
    We can use wildcards for placing shapes in all signal layers by using '*' as the
    top level hierarchy component. This function expands that wildcard into an
    explicit list of layers, and removed duplicates.
    """
    n_l = []
    for p in l:
        p_l = p.split("/")
        if p_l[0] == "*":  #  expand '*' wildcard to all signal layers
            for signal_layer in config.stk["signal-layers"]:
                n_l.append(f"{signal_layer}/{'/'.join(p_l[1:])}")
        else:
            n_l.append(p)
    n_l = list(dict.fromkeys(n_l))  # remove duplicates
    return n_l


def place_shape_objects(d, layers_d):
    """
    Recursively converts shape definitions into shape objects
    """

    ns_pcm = config.cfg["ns"]["pcbmode"]

    instances_d = d.get("instances", None)  # instances dict
    if instances_d == None:
        return

    # Keep track of the placement groups we've already used so that shapes are
    # grouped appropriately
    stored_groups = {}

    for n, i_d in instances_d.items():
        # Since we 'flattened' the instantiations, all the shapes are at
        # ["definition-here"]
        shapes = i_d["definition-here"].get("shapes", {})

        for shape in shapes:
            place_in_new = expand_layers(shape.get("place-in", []))
            # Place the shape in all the specified layers. First traverse the
            # hierarchy of the layers dictionary to get the placement layer, then
            # create a group for placement, and then place the shape
            for p in place_in_new:
                p_l = p.split("/")  # split layer/foil hierarchy
                place_layer = layers_d[p_l[0]]  # get the top-level layer
                for p_h in p_l[1:]:
                    place_layer = place_layer[p_h]  # traverse hierarchy for layer

                shape_group = stored_groups.get(p, None)
                if shape_group is None:
                    shape_group = et.SubElement(place_layer["layer"], "g")
                    shape_group.set(f"{{{ns_pcm}}}type", "module-shapes")
                    stored_groups[p] = shape_group

                place.place_shape(shape["shape-object"], shape_group)

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
        if "outline" in inst_d.get("place-in", []):
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
    # print(json.dumps(config.brd, indent=2))

    apply_transformations(config.brd)

    # Convert all the shape definitions in a dict to Shape objects
    create_shape_objects(config.brd)
    # print(config.brd)

    svg_doc = create_svg(config.brd)

    save_svg(svg_doc)
