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
        pins_dict = self._footprint.get("pins", {}) # pin: instance of a pin
        pads_dict = self._footprint.get("pads", {}) # pad: the shape/footprint of a pin

        for pin_name in pins_dict:

            pin_dict = pins_dict[pin_name]["layout"]
            pin_loc_p = Point(pin_dict.get("location", [0, 0]))
            pin_rotate = pin_dict.get("rotate", 0)
            pin_pivot_p = Point(pin_dict.get("pivot", [0, 0]))

            pad_dict = pads_dict[pin_dict["pad"]]
            pad_shapes = pad_dict.get("shapes", [])

            # We need this copy in order to start fresh with each instance of the 'pad'
            # since it is modified by the 'pin' parameters
            pad_shapes_copy = copy.deepcopy(pad_shapes)

            for shape_dict in pad_shapes_copy:

                # Add the pin's location to the pad's location
                shape_loc = shape_dict.get("location", [0, 0])
                # TODO: NASTY hack, but can't continue without it for now
                if isinstance(shape_loc, Point) is True:
                    shape_loc_p = shape_loc
                else:
                    shape_loc_p = Point(shape_loc)
                shape_dict["location"] = pin_loc_p + shape_loc_p
                
                # Add the pin's rotation to the pad's rotation
                shape_dict["rotate"] = (shape_dict.get("rotate", 0)) + pin_rotate

                # Which layer(s) to place the shape on
                layers = utils.getExtendedLayerList(shape_dict.get("layers", ["top"]))

                for layer in layers:

                    pad_shape = Shape(shape_dict.copy())

                    # Add the label to the shape instance and not to the dict so
                    # that is doesn't propagate to the other derived shapes later on
                    if pin_dict.get("show-label", True) is True:
                        # Use 'label' or default to the pin name
                        pad_shape.set_label(pin_dict.get("label", pin_name))
                        pad_shape.set_label_style_class("pad-labels")

                    # Add the exact shape to the conductor layer shapes
                    if layer in self._shapes["conductor"]:
                        self._shapes["conductor"][layer].append(pad_shape)
                    else:
                        self._shapes["conductor"][layer] = [pad_shape]

                    self._add_special_shapes(layer, shape_dict.copy())

            drills = pad_dict.get("drills", [])
            for drill_dict in drills:
                drill_dict = drill_dict.copy()
                drill_dict["type"] = drill_dict.get("type") or "drill"
                drill_loc_p = Point(drill_dict.get("location", [0, 0]))
                drill_dict["location"] = drill_loc_p + pin_loc_p
                shape = Shape(drill_dict)

                if "top" in self._shapes["drills"]:
                    self._shapes["drills"]["top"].append(shape)
                else:
                    self._shapes["drills"]["top"] = [shape]

    def _add_special_shapes(self, layer, pad_shape_dict):
        """
        Add soldermask and solderpaste to pin pad shape
        """

        sheets = ["soldermask", "solderpaste"]

        for sheet in sheets:

            # Get a custom shape list
            shape_list = pad_shape_dict.get(sheet, None)

            shape_obj_list = []

            if shape_list == "none":  # don't place shape at all
                continue
            elif shape_list == "same":  # place same as pin pad
                shape_obj_list.append(Shape(pad_shape_dict))
            elif shape_list is None:  # default behaviour
                # Baseline on original shape
                shape_dict = pad_shape_dict.copy()
                # Apply modifier based on shape type
                shape_type = shape_dict["type"]
                cfg_def = config.cfg["distances"][sheet]
                if shape_type == "path":
                    shape_dict["scale"] = (
                        pad_shape_dict.get("scale", 1) * cfg_def["path-scale"]
                    )
                elif shape_type == "rect":
                    shape_dict["width"] += cfg_def["rect-buffer"]
                    shape_dict["height"] += cfg_def["rect-buffer"]
                elif shape_type == "circle":
                    shape_dict["diameter"] += cfg_def["circle-buffer"]
                # Create shape based on new dictionary
                shape_obj_list.append(Shape(shape_dict))
            else:  # it's a list of shapes!
                for shape_dict in shape_list:
                    shape_dict = shape_dict.copy()
                    shape_loc = Point(shape_dict.get("location", [0, 0]))
                    # Apply rotation
                    shape_dict["rotate"] = (
                        shape_dict.get("rotate", 0)
                    ) + pad_shape_dict["rotate"]
                    # Rotate location
                    shape_loc.rotate(shape_dict["rotate"])
                    shape_dict["location"] = Point(
                        shape_dict.get("location", [0, 0])
                    ) + pad_shape_dict.get("location", Point([0, 0]))
                    # Create new shape
                    shape_obj_list.append(Shape(shape_dict))

            # Add shape to footprint's shape dictionary
            try:
                self._shapes[sheet][layer]
            except:
                self._shapes[sheet][layer] = []

            for shape_obj in shape_obj_list:
                self._shapes[sheet][layer].append(shape_obj)

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
