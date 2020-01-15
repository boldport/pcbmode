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
from pcbmode.utils.style import Style
from pcbmode.utils.footprint import Footprint
from pcbmode.utils import css_utils


class Component:
    """
    """

    def __init__(self, refdef, comp_dict):
        """
        """

        self._refdef = refdef
        self._layer = comp_dict.get("layer") or "top"

        self._rotate = comp_dict.get("rotate") or 0
        if self._layer == "bottom":
            self._rotate *= -1

        self._rotate_point = Point(comp_dict.get("rotate-point", [0, 0]))
        self._scale = comp_dict.get("scale", 1)
        self._location = Point(comp_dict.get("location", [0, 0]))

        # Get footprint definition and shapes
        try:
            self._footprint_name = comp_dict["footprint"]
        except:
            msg.error(f"Cannot find a 'footprint' name for refdef {refdef}.")

        filename = f"{self._footprint_name}.json"

        # Look for the files in both components and shapes paths.
        paths = [
            Path(config.tmp["project-path"] / config.cfg["components"]["path"]),
            Path(config.tmp["project-path"] / config.cfg["shapes"]["path"]),
        ]

        footprint_dict = None
        for path in paths:
            if (path / filename).exists():
                footprint_dict = utils.dictFromJsonFile(path / filename)
                break

        if footprint_dict == None:
            fname_list = ""
            for path in paths:
                fname_list += " %s" % path
            msg.error(
                "Couldn't find shape file. Looked for it here:\n%s" % (fname_list)
            )

        footprint = Footprint(footprint_dict)
        footprint_shapes = footprint.get_shapes()

        # ------------------------------------------------
        # Apply component-specific modifiers to footprint
        # ------------------------------------------------
        for sheet in [
            "conductor",
            "soldermask",
            "solderpaste",
            "pours",
            "silkscreen",
            "assembly",
            "drills",
        ]:
            for layer in config.stk["layer-names"]:
                for shape in footprint_shapes[sheet].get(layer) or []:

                    # In order to apply the rotation we need to adust the location
                    shape.rotateLocation(self._rotate, self._rotate_point)

                    shape.transformPath(
                        scale=self._scale,
                        rotate=self._rotate,
                        rotate_point=self._rotate_point,
                        mirror=shape.getMirrorPlacement(),
                        add=True,
                    )

        # --------------------------------------------------------------
        # Remove silkscreen and assembly shapes if instructed
        # --------------------------------------------------------------
        # If the 'show' flag is 'false then remove these items from the
        # shapes dictionary
        # --------------------------------------------------------------
        for sheet in ["silkscreen", "assembly"]:

            try:
                shapes_dict = comp_dict[sheet].get("shapes") or {}
            except:
                shapes_dict = {}

            # If the setting is to not show silkscreen shapes for the
            # component, delete the shapes from the shapes' dictionary
            if shapes_dict.get("show") == False:
                for pcb_layer in utils.getSurfaceLayers():
                    footprint_shapes[sheet][pcb_layer] = []

        # ----------------------------------------------------------
        # Add silkscreen and assembly reference designator (refdef)
        # ----------------------------------------------------------
        for sheet in ["silkscreen", "assembly"]:

            try:
                refdef_dict = comp_dict[sheet].get("refdef", {})
            except:
                refdef_dict = {}

            if refdef_dict.get("show") != False:
                layer = refdef_dict.get("layer") or "top"

                # Rotate the refdef; if unspecified the rotation is the same as
                # the rotation of the component
                refdef_dict["rotate"] = refdef_dict.get("rotate") or 0

                # Sometimes you'd want to keep all refdefs at the same angle
                # and not rotated with the component
                if refdef_dict.get("rotate-with-component") != False:
                    refdef_dict["rotate"] += self._rotate

                refdef_dict["rotate-point"] = Point(
                    refdef_dict.get("rotate-point", self._rotate_point)
                )

                refdef_dict["location"] = Point(refdef_dict.get("location", [0, 0]))
                refdef_dict["type"] = "text"
                refdef_dict["value"] = refdef_dict.get("value") or refdef

                refdef_dict["font-family"] = css_utils.get_prop(
                    config.stl["layout"], f"{sheet}-refdef", "font-family"
                )

                refdef_dict["font-size"] = css_utils.get_prop(
                    config.stl["layout"], f"{sheet}-refdef", "font-size"
                )

                refdef_shape = Shape(refdef_dict)
                refdef_shape.is_refdef = True
                refdef_shape.rotateLocation(self._rotate, self._rotate_point)

                # Add the refdef to the silkscreen/assembly list. It's
                # important that this is added at the very end since the
                # placement process assumes the refdef is last
                try:
                    footprint_shapes[sheet][layer]
                except:
                    footprint_shapes[sheet][layer] = []

                footprint_shapes[sheet][layer].append(refdef_shape)

        # ------------------------------------------------------
        # Invert layers
        # ------------------------------------------------------
        # If the placement is on the bottom of the baord then we need
        # to invert the placement of all components. This affects the
        # surface laters but also internal layers

        if self._layer == "bottom":
            layers = config.stk["layer-names"]

            for sheet in [
                "conductor",
                "pours",
                "soldermask",
                "solderpaste",
                "silkscreen",
                "assembly",
            ]:
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

    def getShapes(self):
        """
        """
        return self._footprint_shapes

    def get_location(self):
        """
        """
        return self._location

    def getRefdef(self):
        return self._refdef

    def getPlacementLayer(self):
        return self._layer

    def getFootprintName(self):
        return self._footprint_name

    def getRotation(self):
        return self._rotate
