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

    def __init__(self, footprint):

        self._footprint = footprint

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
        Converts pins into 'shapes'
        """

        pins = self._footprint.get("pins", {})

        for pin in pins:

            pin_location = pins[pin]["layout"].get("location", [0, 0])

            try:
                pad_name = pins[pin]["layout"]["pad"]
            except KeyError:
                msg.error(
                    "Each defined 'pin' must have a 'pad' name that is defined in the 'pads' section of the footprint."
                )

            try:
                pad_dict = self._footprint["pads"][pad_name]
            except KeyError:
                msg.error(
                    f"There doesn't seem to be a pad definition for pad '{pad_name}'."
                )

            # Get the pin's rotation, if any
            pin_rotate = pins[pin]["layout"].get("rotate", 0)

            shapes = pad_dict.get("shapes") or []

            for shape_dict in shapes:

                shape_dict = shape_dict.copy()

                # Which layer(s) to place the shape on
                layers = utils.getExtendedLayerList(shape_dict.get("layers") or ["top"])

                # Add the pin's location to the pad's location
                shape_location = shape_dict.get("location", [0, 0])
                shape_dict["location"] = [
                    shape_location[0] + pin_location[0],
                    shape_location[1] + pin_location[1],
                ]

                # Add the pin's rotation to the pad's rotation
                shape_dict["rotate"] = (shape_dict.get("rotate") or 0) + pin_rotate

                # Determine if and which label to show
                show_name = pins[pin]["layout"].get("show-label", True)
                if show_name == True:
                    pin_label = pins[pin]["layout"].get("label", pin)

                for layer in layers:

                    shape = Shape(shape_dict)

                    if layer in self._shapes["conductor"]:
                        self._shapes["conductor"][layer].append(shape)
                    else:
                        self._shapes["conductor"][layer] = [shape]

                    for stype in ["soldermask", "solderpaste"]:

                        # Get a custom shape specification if it exists
                        sdict_list = shape_dict.get(stype)

                        # Not defined; default
                        if sdict_list == None:
                            # Use default settings for shape based on
                            # the pad shape
                            sdict = shape_dict.copy()

                            # Which shape type is the pad?
                            shape_type = shape.getType()

                            # Apply modifier based on shape type
                            if shape_type == "path":
                                sdict["scale"] = (
                                    shape.getScale()
                                    * config.cfg["distances"][stype]["path-scale"]
                                )
                            elif shape_type in ["rect", "rectangle"]:
                                sdict["width"] += config.cfg["distances"][stype][
                                    "rect-buffer"
                                ]
                                sdict["height"] += config.cfg["distances"][stype][
                                    "rect-buffer"
                                ]
                            elif shape_type in ["circ", "circle"]:
                                sdict["diameter"] += config.cfg["distances"][stype][
                                    "circle-buffer"
                                ]
                            else:
                                pass

                            # Create shape based on new dictionary
                            sshape = Shape(sdict)

                            # Define style
                            #                            sstyle = Style(sdict, stype)

                            # Apply style
                            #                            sshape.setStyle(sstyle)

                            # Add shape to footprint's shape dictionary
                            # self._shapes[stype][layer].append(sshape)
                            if layer in self._shapes[stype]:
                                self._shapes[stype][layer].append(sshape)
                            else:
                                self._shapes[stype][layer] = [sshape]

                        # Do not place shape
                        elif (sdict_list == {}) or (sdict_list == []):
                            pass

                        # Custom shape definition
                        else:

                            # If dict (as before support of multiple
                            # shapes) then append to a single element
                            # list
                            if type(sdict_list) is dict:
                                sdict_list = [sdict_list]

                            # Process list of shapes
                            for sdict_ in sdict_list:
                                sdict = sdict_.copy()
                                shape_loc = utils.toPoint(sdict.get("location", [0, 0]))

                                # Apply rotation
                                sdict["rotate"] = (sdict.get("rotate", 0)) + pin_rotate

                                # Rotate location
                                shape_loc.rotate(pin_rotate, Point())

                                sdict["location"] = [
                                    shape_loc.x + pin_location[0],
                                    shape_loc.y + pin_location[1],
                                ]

                                # Create new shape
                                sshape = Shape(sdict)

                                # Add shape to footprint's shape dictionary
                                # self._shapes[stype][layer].append(sshape)
                                if layer in self._shapes[stype]:
                                    self._shapes[stype][layer].append(sshape)
                                else:
                                    self._shapes[stype][layer] = [sshape]

                    # Add pin label
                    if pin_label != None:
                        shape.set_label(pin_label)
                        #shape.set_style_class()

            drills = pad_dict.get("drills") or []
            for drill_dict in drills:
                drill_dict = drill_dict.copy()
                drill_dict["type"] = drill_dict.get("type") or "drill"
                drill_location = drill_dict.get("location") or [0, 0]
                drill_dict["location"] = [
                    drill_location[0] + pin_location[0],
                    drill_location[1] + pin_location[1],
                ]
                shape = Shape(drill_dict)
                #                style = Style(drill_dict, "drills")
                #                shape.setStyle(style)

                if "top" in self._shapes["drills"]:
                    self._shapes["drills"]["top"].append(shape)
                else:
                    self._shapes["drills"]["top"] = [shape]

    def _process_pours(self):
        """
        """

        try:
            shapes = self._footprint["layout"]["pours"]["shapes"]
        except:
            return

        for shape_dict in shapes:
            layers = utils.getExtendedLayerList(shape_dict.get("layers") or ["top"])
            for layer in layers:
                shape = Shape(shape_dict)
                style = Style(shape_dict, "conductor", "pours")
                shape.setStyle(style)

                if layer in self._shapes["pours"]:
                    self._shapes["pours"][layer].append(shape)
                else:
                    self._shapes["pours"][layer] = [shape]

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
                    #                    style = Style(shape_dict, sheet)
                    #                    shape.setStyle(style)

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
                #                style = Style(shape_dict, "assembly")
                #                shape.setStyle(style)

                if layer in self._shapes["assembly"]:
                    self._shapes["assembly"][layer].append(shape)
                else:
                    self._shapes["assembly"][layer] = [shape]
