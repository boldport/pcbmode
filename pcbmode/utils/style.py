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


from pcbmode.config import config
from pcbmode.utils import messages as msg
from pcbmode.utils import utils


class Style:
    """
    Manages the logic for determining the style of an object
    based on its shape definition, 'shape_dict'. In the layout
    file, default 'fill' or 'stroke' styles are defined for the
    various layers; these will be used if otherwise not specified
    in the shape definition.

    'sub_item' is used to be more specific within the style definition.
    Originally it was added for 'refdef' within silkscreen and
    soldermask, but could be used with other types.
    """

    def __init__(self, shape_dict, layer_name, sub_item=None):

        # default_style = config.stl["layout"]["defaults"]["style"][layer_name]
        # if sub_item == None:
        #     layer_style = config.stl["layout"][layer_name]
        # else:
        #     layer_style = config.stl["layout"][layer_name][sub_item]

        # Unless specified, 'text' will default to 'fill' on all layers.
        # Other 'types' depend on the layers they are on.
        if shape_dict.get("style") == None:
            if shape_dict["type"] in ["text", "refdef"]:
                self._style = "fill"
            else:
                self._style = default_style
        else:
            self._style = shape_dict["style"]

        try:
            self._style_dict = layer_style.get(self._style).copy()
        except:
            self._style_dict = None

        # Apply defaults if style dict wasn't found
        if self._style_dict == None:
            if self._style == "fill":
                self._style_dict = {"stroke": "none"}
            elif self._style == "stroke":
                self._style_dict = {"fill": "none"}
            else:
                msg.error("Encountered an unknown 'style' type, %s" % self._style)

        # If the style is 'stroke' we need to override the default 'stroke-width'
        # setting with a possible custom definition
        if self._style == "stroke":
            self._style_dict["stroke-width"] = shape_dict.get(
                "stroke-width"
            ) or layer_style[self._style].get("stroke-width")
            self._style_dict["fill"] = "none"

    def getStyleType(self):
        return self._style

    def getStyleString(self):
        return utils.dictToStyleText(self._style_dict)

    def getStrokeWidth(self):
        return self._style_dict["stroke-width"]
