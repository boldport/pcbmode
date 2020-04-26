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


import copy

from pcbmode.config import config
from pcbmode.utils import messages as msg
from pcbmode.utils import svg
from pcbmode.utils import utils
from pcbmode.utils import place
from pcbmode.utils.style import Style
from pcbmode.utils.point import Point
from pcbmode.utils.shape import Shape


class Footprint:
    """
    """

    def __init__(self, footprint, mirror=False):

        self._footprint = footprint
        self._mirror = mirror  # all the shapes of the footprint

        # This is where the shapes for placement are stored, by layer
        self._shapes = {
            "conductor": {},
            "pours": {},
            "soldermask": {},
            "silkscreen": {},
            "assembly": {},
            "solderpaste": {},
            "drills": {},
        }
        self._process_pins()
        self._process_pours()
        self._process_shapes()
        self._process_assembly_shapes()

    def get_shapes(self):
        return self._shapes

    def _process_pins(self):
        """
        Converts pin instantiation into Shapes.
        A package 'pin' uses a 'pad' defined in the footprint file. Each 'pad' can have
        multiple shapes, which are converted into Shape objects.
        """
        pins_d = self._footprint.get("pins", {})  # pin: instance of a pin
        pads_d = self._footprint.get("pads", {})  # pad: the shape/footprint of a pin

        for pin_name in pins_d:

            pin_d = pins_d[pin_name]["layout"]
            pin_loc_p = Point(pin_d.get("location", [0, 0]))
            pin_rotate = pin_d.get("rotate", 0)
            pin_rotate_p = Point(pin_d.get("rotate-origin", [0, 0]))

            # We need this copy in order to start fresh with each instance of the 'pad'
            # since it is modified by the 'pin' parameters
            pad_d = copy.deepcopy(pads_d[pin_d["pad"]])
            pad_s_d_l = pad_d.get("shapes", [])  # pad_(s)hapes_(d)ict_(l)ist

            for s_d in pad_s_d_l:
                # Add the pin's location to the pad's location
                s_loc = s_d.get("location", [0, 0])

                # TODO: NASTY hack, but can't continue without it for now
                if isinstance(s_loc, Point) is True:
                    s_loc_p = s_loc
                else:
                    s_loc_p = Point(s_loc)

                s_d["location"] = pin_loc_p + s_loc_p

                # Add the pin's rotation to the pad's rotation
                s_d["rotate"] = (s_d.get("rotate", 0)) + pin_rotate

                s_d["rotate_p"] = Point(s_d.get("rotate-origin", [0, 0]))

                # We don't want to rotate the location if there's no new origin. When we
                # don't, the shape is rotated around its center, and only then placed
                # at its location. If we apply the new origin, the object is rotated
                # around that point, not around its center.
                if s_d["rotate_p"].is_not_00():
                    s_d["location"].rotate(
                        s_d["rotate"], s_d["rotate_p"] + s_d["location"]
                    )

                # Which layer(s) to place the shape on
                layers = utils.getExtendedLayerList(s_d.get("layers", ["top"]))

                for layer in layers:

                    s_d_c = copy.deepcopy(s_d)  # must be deepcopy!
                    pad_s_o = Shape(s_d_c)

                    # Add the label to the shape instance and not to the dict so
                    # that is doesn't propagate to the other derived shapes later on
                    if pin_d.get("show-label", True) is True:
                        # Use 'label' or default to the pin name
                        pad_s_o.set_label(pin_d.get("label", pin_name))
                        pad_s_o.set_label_style_class("pad-labels")

                    # Add the exact shape to the conductor layer shapes
                    if layer in self._shapes["conductor"]:
                        self._shapes["conductor"][layer].append(pad_s_o)
                    else:
                        self._shapes["conductor"][layer] = [pad_s_o]

                    # Adds soldermask and solderpaste shapes
                    self._add_special_shapes(layer, s_d)

            drills_d = pad_d.get("drills", [])
            for drill_d in drills_d:
                drill_d["type"] = drill_d.get("type") or "drill"
                drill_loc_p = Point(drill_d.get("location", [0, 0]))
                drill_d["location"] = drill_loc_p + pin_loc_p
                s_o = Shape(drill_d)

                if "top" in self._shapes["drills"]:
                    self._shapes["drills"]["top"].append(s_o)
                else:
                    self._shapes["drills"]["top"] = [s_o]

    def _add_special_shapes(self, layer, s_d):
        """
        Add soldermask and solderpaste to pin pad shape

        'layer': the layer onto which to add the shapes 
        's_d': the shape's dictionary
        """

        # Add modified shapes basied on the 's_d' prototype to the following sheets
        # within 'layer'
        sheets = ["soldermask", "solderpaste"]

        for sheet in sheets:

            # We need to create a copy of the dictionary since we will modify it
            # differently depending on the sheet
            s_d_c = copy.deepcopy(s_d)  # (s)hape_(d)ict_(c)opy

            # Look for a shape dict definition for the specific sheet
            s_l = s_d_c.get(sheet, None)  # (s)hape_(l)ist

            # Here we'll store the shape objects
            s_o_l = []  # (s)hape_(o)bject_(l)ist

            if s_l == "none":  # don't place the shape
                continue
            elif s_l == "same":  # place shape as-is
                s_o_l.append(Shape(s_d_c))
            elif s_l is None:  # default behaviour
                s_type = s_d_c["type"]
                cfg_def = config.cfg["distances"][sheet]  # settings for sheet
                if s_type == "path":
                    s_d_c["scale"] = s_d_c.get("scale", 1) * cfg_def["path-scale"]
                elif s_type == "rect":
                    s_d_c["width"] += cfg_def["rect-buffer"]
                    s_d_c["height"] += cfg_def["rect-buffer"]
                elif s_type == "circle":
                    s_d_c["diameter"] += cfg_def["circle-buffer"]
                s_o_l.append(Shape(s_d_c))
            else:  # so it's actually a list of shapes!
                for sp_s_d in s_l:
                    sp_s_d_c = sp_s_d.copy()
                    sp_s_d_c["rotate"] = (sp_s_d_c.get("rotate", 0)) + s_d_c["rotate"]
                    s_loc = Point(sp_s_d_c.get("location", [0, 0]))
                    s_loc.rotate(sp_s_d_c["rotate"])
                    sp_s_d_c["location"] = Point(
                        sp_s_d_c.get("location", [0, 0])
                    ) + s_d_c.get("location", Point([0, 0]))
                    s_o_l.append(Shape(sp_s_d_c))

            # Add shape to footprint's shape dictionary
            try:
                self._shapes[sheet][layer]
            except:
                self._shapes[sheet][layer] = []

            for s_o in s_o_l:
                self._shapes[sheet][layer].append(s_o)

    def _process_pours(self):
        """
        Add pour shapes to the object's shape list
        """
        try:
            pour_shapes = self._footprint["layout"]["pours"]
        except:
            return  # no pours
        shapes_list = pour_shapes.get("shapes", [])
        for shape_dict in shapes_list:
            layers = utils.getExtendedLayerList(shape_dict.get("layers") or ["top"])
            for layer in layers:
                shape_obj = Shape(shape_dict)
                if layer in self._shapes["pours"]:
                    self._shapes["pours"][layer].append(shape_obj)
                else:
                    self._shapes["pours"][layer] = [shape_obj]

    def _process_shapes(self):
        """
        """

        sheets = ["conductor", "silkscreen", "soldermask"]

        for sheet in sheets:

            try:
                shapes = self._footprint["layout"][sheet]["shapes"] or []
            except:
                shapes = []

            for shape_dict in shapes:
                layers = utils.getExtendedLayerList(shape_dict.get("layers") or ["top"])
                for layer in layers:
                    # Mirror the shape if it's text and on bottom later,
                    # but let explicit shape setting override
                    if layer == "bottom":
                        if shape_dict["type"] == "text":
                            shape_dict["mirror"] = shape_dict.get("mirror") or "True"
                    shape = Shape(shape_dict)

                    if layer in self._shapes[sheet]:
                        self._shapes[sheet][layer].append(shape)
                    else:
                        self._shapes[sheet][layer] = [shape]

    def _process_assembly_shapes(self):
        """
        """
        try:
            shapes = self._footprint["layout"]["assembly"]["shapes"]
        except:
            return

        for shape_dict in shapes:
            layers = utils.getExtendedLayerList(shape_dict.get("layer") or ["top"])
            for layer in layers:
                shape = Shape(shape_dict)

                if layer in self._shapes["assembly"]:
                    self._shapes["assembly"][layer].append(shape)
                else:
                    self._shapes["assembly"][layer] = [shape]
