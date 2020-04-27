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
from pathlib import Path

from pcbmode.config import config
from pcbmode.utils import utils
from pcbmode.utils import messages as msg
from pcbmode.utils.shape import Shape
from pcbmode.utils.point import Point
from pcbmode.utils.footprint import Footprint
from pcbmode.utils import css_utils


class Component:
    """
    An object that applies modifications to a generic Footprint object
    """

    def __init__(self, refdef, comp_dict, comp_type):
        """
        'comp_type': used to determine where to look for the footprint
        """
        self._refdef = refdef
        self._layer = comp_dict.get("layer", "top")
        self._location = Point(comp_dict.get("location", [0, 0]))
        self._scale = comp_dict.get("scale", 1)
        self._rotate = comp_dict.get("rotate", 0)
        self._rotate_p = Point(comp_dict.get("rotate-origin", [0, 0]))
        if comp_dict["layer"] == "bottom":
            self._place_bot = True
        else:
            self._place_bot = False

        if self._layer == "bottom":
            self._rotate *= -1  # TODO: is this needed?
            self._mirror_shapes = True
        else:
            self._mirror_shapes = False

        self._footprint_name = comp_dict["footprint"]

        # Look for the file in a path depending on the component type
        if comp_type in ["components", "vias"]:
            path = Path(config.tmp["project-path"] / config.cfg["components"]["path"])
        elif comp_type == "shapes":
            path = Path(config.tmp["project-path"] / config.cfg["shapes"]["path"])

        footprint_dict = utils.dictFromJsonFile(path / f"{self._footprint_name}.json")
        footprint_obj = Footprint(footprint_dict, self._place_bot)
        footprint_shapes = footprint_obj.get_shapes()

        # Apply *component-specific* modifiers to footprint
        sheets = [
            "conductor",
            "soldermask",
            "solderpaste",
            "pours",
            "silkscreen",
            "assembly",
            "drills",
        ]
        for sheet in sheets:
            for layer in config.stk["layer-names"]:
                for shape in footprint_shapes[sheet].get(layer, []):
                    shape.rotate_location(-self._rotate, self._rotate_p)
                    # If the component is placed on the bottom layer we need to mirror
                    # all the shapes of the component. A mirror setting of the shape
                    # itself negates this action, hence the XOR
                    mirror_y = self._place_bot ^ shape.get_mirror_y()
                    t_dict = {  # transform dictionary
                        "scale": self._scale,
                        # TODO: This causes an issue when the component has a 'rotate'
                        "rotate": self._rotate,
                        "rotate-point": self._rotate_p,
                        "mirror-y": mirror_y,
                    }
                    shape.transform_path(t_dict)

        # Remove silkscreen and assembly shapes if instructed
        for sheet in ["silkscreen", "assembly"]:
            try:  # check if the sheet layer exists
                sheet_dict = comp_dict[sheet]
            except:
                continue
            shapes_dict = sheet_dict.get("shapes", {})
            if shapes_dict.get("show") == False:  # delete shapes
                for pcb_layer in utils.getSurfaceLayers():
                    footprint_shapes[sheet][pcb_layer] = []

        # Add silkscreen and assembly reference designator (refdef)
        for sheet in ["silkscreen", "assembly"]:
            try:  # check if the sheet layer exists
                sheet_dict = comp_dict[sheet]
            except:
                continue
            refdef_dict = sheet_dict.get("refdef", {})
            if refdef_dict.get("show") != False:
                layer = refdef_dict.get("layer", "top")
                refdef_dict["rotate"] = refdef_dict.get("rotate", 0)
                # Don't rotate with component
                if refdef_dict.get("rotate-with-component", True) != False:
                    refdef_dict["rotate"] += self._rotate
                refdef_dict["location"] = Point(refdef_dict.get("location", [0, 0]))
                refdef_dict["type"] = "text"
                refdef_dict["value"] = refdef_dict.get("value", refdef)
                refdef_dict["font-family"] = css_utils.get_prop(
                    config.stl["layout"], f"{sheet}-refdef", "font-family"
                )
                refdef_dict["font-size"] = css_utils.get_prop(
                    config.stl["layout"], f"{sheet}-refdef", "font-size"
                )
                refdef_shape = Shape(refdef_dict)
                refdef_shape.is_refdef = True
                refdef_shape.rotate_location(self._rotate, self._rotate_p)

                # Add the refdef to the silkscreen/assembly list.
                # NOTE: It's important that this is added at the very end since the
                # placement process assumes the refdef is last
                try:
                    footprint_shapes[sheet][layer].append(refdef_shape)
                except:
                    footprint_shapes[sheet][layer] = [refdef_shape]

        # Invert layers
        # If the placement is on the bottom of the baord then we need
        # to invert the placement of all components. This affects the
        # surface layers but also internal layers
        if self._place_bot is True:
            layers = config.stk["layer-names"]
            sheets = [
                "conductor",
                "pours",
                "soldermask",
                "solderpaste",
                "silkscreen",
                "assembly",
            ]
            for sheet in sheets:
                sheet_dict = footprint_shapes[sheet]
                sheet_dict_new = {}
                for i, pcb_layer in enumerate(layers):
                    try:
                        sheet_dict_new[layers[len(layers) - i - 1]] = copy.copy(
                            sheet_dict[pcb_layer]
                        )
                    except:
                        continue
                footprint_shapes[sheet] = copy.copy(sheet_dict_new)

        self._footprint_shapes = footprint_shapes

    def get_shapes(self):
        return self._footprint_shapes

    def get_location(self):
        return self._location

    def get_refdef(self):
        return self._refdef

    def get_placement_layer(self):
        return self._layer

    def getFootprintName(self):
        return self._footprint_name

    def get_rotate(self):
        return self._rotate
