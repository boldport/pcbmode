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

        # Invert rotation so it's clock-wise. Inkscape is counter-clockwise and
        # it's unclear to me what's the "right" direction. clockwise makes more
        # sense to me. This should be the only place to make the change.
        self._inv_rotate = -1

        # A general purpose label field
        self._label = None

        self._shape_dict = shape
        self._gerber_lp = shape.get("gerber-lp") or shape.get("gerber_lp") or None
        self._place_mirrored = shape.get("mirror") or False
        self._rotate = shape.get("rotate") or 0
        self._rotate *= self._inv_rotate
        self._rotate_point = shape.get("rotate-point") or Point(0, 0)
        self._scale = shape.get("scale") or 1
        self._pour_buffer = shape.get("buffer-to-pour")
        self._location = utils.toPoint(shape.get("location", [0, 0]))

        self._style_class = self._shape_dict.get("style_class", None)
        self._style = self._shape_dict.get("style", None)
        if self._style is not None:
            self._style = utils.process_style(self._style)
        else:
            self._style = "stroke:none;"

        # Create the SVG path for the shape
        self._get_path_from_shape_type()

        # Convert the path to an object
        self._path = SvgPath(self._path, self._gerber_lp)

        self._path.transform(
            scale=self._scale,
            rotate_angle=self._rotate,
            rotate_point=self._rotate_point,
            mirror=self._place_mirrored,
        )

    def _get_path_from_shape_type(self):
        """
        There are various shape types. Here we create an SVG path from the shape type and parameters provided by the shape dict.
        """

        try:
            self._type = self._shape_dict.get("type")
        except:
            msg.error("Shapes must have a 'type' definition.")

        # A 'layer' shape type is a shape that covers the entire board. So here we copy
        # the outline shape and continue with processing
        if self._type == "layer":
            self._shape_dict = config.brd["outline"].get("shape").copy()
            self._type = self._shape_dict.get("type")

        if self._type in ["rect", "rectangle"]:
            self._type = "rect"
            self._process_rect()
        elif self._type in ["circ", "circle", "round"]:
            self._type = "circ"
            self._process_circ()
        elif self._type == "drill":
            self._process_drill()
        elif self._type in ["text", "string"]:
            self._type == "text"
            self._process_text()
        elif self._type == "path":
            self._process_path()
        else:
            msg.error("'%s' is not a recongnised shape type" % self._type)

    def _process_rect(self):
        try:
            width = self._shape_dict["width"]
        except KeyError:
            msg.error("A 'rect' shape requires a 'width' definition")

        try:
            height = self._shape_dict["height"]
        except KeyError:
            msg.error("A 'rect' shape requires a 'height' definition")

        self._path = svg.width_and_height_to_path(
            width, height, self._shape_dict.get("radii")
        )

    def _process_circ(self):
        try:
            self._diameter = self._shape_dict["diameter"]
        except KeyError:
            msg.error("A 'circle' shape requires a 'diameter' definition")
        self._path = svg.circle_diameter_to_path(self._diameter)

    def _process_drill(self):
        try:
            self._diameter = self._shape_dict["diameter"]
        except KeyError:
            msg.error("A 'drill' shape requires a 'diameter' definition")
        self._path = svg.drillPath(self._diameter)

    def _process_text(self):
        try:
            self._text = self._shape_dict["value"] or self._shape_dict["text"]
        except KeyError:
            msg.error(
                "A 'text' shape type must have a 'value' or 'text' definition with the text to display."
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
        except KeyError:
            msg.error(
                "A 'font-size' attribute must be specified for a 'text' shape type"
            )
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
        self._path, self._gerber_lp = utils.textToPath(
            font_data, self._text, letter_spacing, line_height, self._scale
        )
        # In the case where the text is an outline/stroke instead
        # of a fill we get rid of the gerber_lp
        if self._shape_dict.get("style") == "stroke":
            self._gerber_lp = None

        # For some reason SVG fonts are rotated by 180 degrees. This undos that
        self._rotate += 180

    def _process_path(self):
        try:
            self._path = self._shape_dict.get("value") or self._shape_dict.get("d")
        except KeyError:
            msg.error(
                "A 'path' shape requires a 'value' or 'd' definition with a valid SVG path."
            )

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
        self._location.rotate(angle, point)

    def get_style_class(self):
        return self._style_class

    def set_style_class(self, new_class):
        self._style_class = new_class

    def set_style(self, new_style):
        self._style = new_style

    def get_style(self):
        return self._style

    def getRotation(self):
        return self._rotate

    def setRotation(self, rotate):
        self._rotate = rotate

    def getOriginalPath(self):
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

    def set_label(self, label):
        self._label = label

    def set_label_style_class(self, new_style_class):
        self._label_style_class = new_style_class

    def get_label(self):
        return self._label

    def getMirrorPlacement(self):
        return self._place_mirrored
