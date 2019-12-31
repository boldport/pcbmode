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
from lxml import etree as et
from pkg_resources import resource_exists, resource_filename

from pcbmode.config import config
from pcbmode.utils import messages as msg
from pcbmode.utils import utils
from pcbmode.utils import svg
from pcbmode.utils.point import Point
from pcbmode.utils.svgpath import SvgPath


class Shape:
    """
    """

    def __init__(self, shape):

        gerber_lp = None
        mirror = False

        self._shape_dict = shape

        # Invert rotation so it's clock-wise. Inkscape is counter-clockwise and
        # it's unclear to me what's the "right" direction. clockwise makes more
        # sense to me. This should be the only place to make the change.
        self._inv_rotate = -1

        self._get_shape_type()

        # A 'layer' type is a copy of the outline. Here we copy the
        # outline shape and override the type
        if self._type == "layer":
            self._shape_dict = config.brd["outline"].get("shape").copy()
            self._type = self._shape_dict.get("type")

        self._place_mirrored = shape.get("mirror") or False

        self._rotate = shape.get("rotate") or 0
        self._rotate *= self._inv_rotate
        self._rotate_point = shape.get("rotate-point") or Point(0, 0)
        self._scale = shape.get("scale") or 1
        self._pour_buffer = shape.get("buffer-to-pour")

        # A general purpose label field; intended for use for pad
        # labels
        self._label = None

        if self._type == "rect":
            path = svg.width_and_height_to_path(
                self._shape_dict["width"],
                self._shape_dict["height"],
                self._shape_dict.get("radii"),
            )
        elif self._type in ["circ", "circle", "round"]:
            path = svg.circle_diameter_to_path(self._shape_dict["diameter"])
        elif self._type in ["drill"]:
            self._diameter = self._shape_dict["diameter"]
            path = svg.drillPath(self._diameter)
        elif self._type in ["text", "string"]:
            try:
                self._text = self._shape_dict["value"]
            except KeyError:
                msg.error(
                    "Could not find the text to display. The text to be displayed should be defined in the 'value' field, for example, 'value': 'DEADBEEF\\nhar\\nhar'"
                )

            # Get the font's name
            font = (
                self._shape_dict.get("font-family")
                or config.stl["layout"]["defaults"]["font-family"]
            )
            font_filename = "%s.svg" % font

            # Search the local folder and PCBmodE's folder for the font file
            search_paths = [
                Path(config.tmp["project-path"] / config.cfg["fonts"]["path"]),
                Path(config.tmp["pcbmode-path"] / config.cfg["fonts"]["path"]),
            ]

            font_data = None
            for path in search_paths:
                filename = path / font_filename
                if filename.exists():
                    font_data = et.ElementTree(file=str(filename))
                    break

            if font_data == None:
                msg.error(
                    "Couldn't find style file %s. Looked for it here:\n%s"
                    % (font_filename, filenames)
                )

            try:
                fs = self._shape_dict["font-size"]
            except:
                msg.error("A 'font-size' attribute must be specified for a 'text' type")

            ls = self._shape_dict.get("letter-spacing") or "0mm"
            lh = self._shape_dict.get("line-height") or fs

            font_size, letter_spacing, line_height = utils.getTextParams(fs, ls, lh)

            # With the units-per-em we can figure out the scale factor
            # to use for the desired font size
            units_per_em = (
                float(
                    font_data.find(
                        "//n:font-face", namespaces={"n": config.cfg["ns"]["svg"]}
                    ).get("units-per-em")
                )
                or 1000
            )
            self._scale = font_size / units_per_em

            # Get the path to use. This returns the path without
            # scaling, which will be applied later, in the same manner
            # as to the other shape types
            path, gerber_lp = utils.textToPath(
                font_data, self._text, letter_spacing, line_height, self._scale
            )

            # In the case where the text is an outline/stroke instead
            # of a fill we get rid of the gerber_lp
            if self._shape_dict.get("style") == "stroke":
                gerber_lp = None

            self._rotate += 180

        elif self._type in ["path"]:
            path = self._shape_dict.get("value")
        else:
            msg.error("'%s' is not a recongnised shape type" % self._type)

        self._path = SvgPath(path, gerber_lp)

        self._path.transform(
            scale=self._scale,
            rotate_angle=self._rotate,
            rotate_point=self._rotate_point,
            mirror=self._place_mirrored,
        )

        self._gerber_lp = (
            shape.get("gerber-lp") or shape.get("gerber_lp") or gerber_lp or None
        )

        self._location = utils.toPoint(shape.get("location", [0, 0]))

    def _get_shape_type(self):
        """
        Get the shape type. There are some equivalent options available, so define one for the rest of the processing.
        """

        try:
            self._type = self._shape_dict.get("type")
        except:
            msg.error("Shapes must have a 'type' defined")

        if self._type in ["rect", "rectangle"]:
            self._type = "rect"
        elif self._type in ["circ", "circle", "round"]:
            self._type = "circ"
        elif self._type in ["text", "string"]:
            self._type = "text"

    def transformPath(
        self, scale=1, rotate=0, rotate_point=Point(), mirror=False, add=False
    ):
        if add == False:
            self._path.transform(scale, rotate * self._inv_rotate, rotate_point, mirror)
        else:
            self._path.transform(
                scale * self._scale,
                rotate * self._inv_rotate + self._rotate,
                rotate_point + self._rotate_point,
                mirror,
            )

    def rotateLocation(self, angle, point=Point()):
        """
        """
        self._location.rotate(angle, point)

    def getRotation(self):
        return self._rotate

    def setRotation(self, rotate):
        self._rotate = rotate

    def getOriginalPath(self):
        """
        Returns that original, unmodified path
        """
        return self._path.getOriginal()

    def getTransformedPath(self, mirrored=False):
        if mirrored == True:
            return self._path.getTransformedMirrored()
        else:
            return self._path.getTransformed()

    def getWidth(self):
        return self._path.getWidth()

    def getHeight(self):
        return self._path.getHeight()

    def getGerberLP(self):
        return self._gerber_lp

    def setStyle(self, style):
        """
        style: Style object
        """
        self._style = style

    def getStyle(self):
        """
        Return the shape's style Style object
        """
        return self._style

    def getStyleString(self):
        style = self._style.getStyleString()
        return style

    def getStyleType(self):
        style = self._style.getStyleType()
        return style

    def getScale(self):
        return self._scale

    def getLocation(self):
        return self._location

    def setLocation(self, location):
        self._location = location

    def getParsedPath(self):
        return self._parsed

    def getPourBuffer(self):
        return self._pour_buffer

    def getType(self):
        return self._type

    def getText(self):
        return self._text

    def getDiameter(self):
        return self._diameter

    def setLabel(self, label):
        self._label = label

    def getLabel(self):
        return self._label

    def getMirrorPlacement(self):
        return self._place_mirrored
