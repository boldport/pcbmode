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
from pcbmode.utils import svg_path_create
from pcbmode.utils.point import Point
from pcbmode.utils.svgpath import SvgPath


class Shape:
    """
    """

    def __init__(self, shape_dict, rel_to_dim="itself"):
        """
        'rel_to_dim': if a Point() is given, shape will be centered relative to the
        dimensions specified. Otherwise it'll be centered around the dimentsions of the
        shape itself (routing shapes are placed relative to the outline, not themselves) 
        """
        self._shape_dict = self._process_shape_dict(shape_dict)
        self._p_r_path = self._path_from_shape_type()
        trans_dict = {  # transform dictionary
            "scale": self._shape_dict["scale"],
            "rotate": self._shape_dict["rotate"],
            "rotate_p": self._shape_dict["rotate_p"],
            "mirror_y": self._shape_dict["mirror-y"],
            "mirror_x": self._shape_dict["mirror-x"],
            "rel_to_dim": rel_to_dim,
        }
        self._path_obj = SvgPath(self._p_r_path, trans_dict)

    def _process_shape_dict(self, sd):
        """ 
        Read in parameters and set defaults
        """
        sd["label"] = sd.get("label", None)
        sd["label_style_class"] = sd.get("label-style-class", None)
        sd["gerber-lp"] = sd.get("gerber-lp", None)
        sd["mirror-y"] = sd.get("mirror-y", False)
        sd["mirror-x"] = sd.get("mirror-x", False)
        sd["rotate"] = sd.get("rotate", 0)
        sd["rotate_p"] = sd.get("rotate_p", Point([0, 0]))
        sd["scale"] = sd.get("scale", 1)
        sd["buffer-to-pour"] = sd.get("buffer-to-pour")
        sd["location"] = sd.get("location", Point([0, 0]))

        # Somewhere the location input isn't being converted to Point()
        # This checks.
        # TODO: remove this check eventually
        if isinstance(sd["location"], Point) is False:
            sd["location"] = Point(sd["location"])

        sd["style-class"] = sd.get("style_class", None)
        sd["style"] = sd.get("style", None)

        if sd["style"] in [None, ""]:
            sd["style"] = "stroke:none;"
        else:
            sd["style"] = utils.process_style(sd["style"])

        return sd

    def _path_from_shape_type(self):
        """
        There are various shape types. Here we create an SVG path from the shape type
        and parameters provided by the shape dict.
        """

        try:
            self._type = self._shape_dict.get("type")
        except:
            msg.error("Shapes must have a 'type' definition.")

        if self._type == "layer":
            # A 'layer' shape type is a shape that covers the entire board. So we copy
            # the board's outline shape and and change the style so that there's no
            # stroke
            self._shape_dict = config.brd["outline"].get("shape").copy()
            self._shape_dict["style"] = "stroke:none;"
            self._type = self._shape_dict.get("type")

        if self._type == "rect":
            p_r_path = self._process_rect()
        elif self._type == "circle":
            p_r_path = self._process_circ()
        elif self._type == "drill":
            p_r_path = self._process_drill()
        elif self._type == "text":
            # path = self._process_text()
            # TODO: remove when dealing with text properly
            p_r_path = "m 0,0"
        elif self._type == "path":
            p_r_path = self._process_path()
        else:
            msg.error("'%s' is not a recongnised shape type" % self._type)

        return p_r_path

    def _process_rect(self):
        try:
            width = self._shape_dict["width"]
            height = self._shape_dict["height"]
        except KeyError:
            msg.error("A 'rect' shape requires 'width' and 'height' definitions")

        border_radius = self._shape_dict.get("border-radius", [])
        return svg_path_create.rect(width, height, border_radius)

    def _process_circ(self):
        try:
            self._diameter = self._shape_dict["diameter"]
        except KeyError:
            msg.error("A 'circle' shape requires a 'diameter' definition")

        return svg_path_create.circle(self._diameter)

    def _process_drill(self):
        try:
            self._diameter = self._shape_dict["diameter"]
        except KeyError:
            msg.error("A 'drill' shape requires a 'diameter' definition")

        # Keep track of drill diameters for index
        try:
            config.tmp["drill-count"].append(self._diameter)
        except:
            config.tmp["drill-count"] = [self._diameter]

        return svg_path_create.drill(self._diameter)

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
        font_filename = f"{font}.svg"
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
                f"Couldn't find style file {font_filename}. Looked for it here:\n{filenames}"
            )
        try:
            fs = self._shape_dict["font-size"]
        except KeyError:
            msg.error(
                "A 'font-size' attribute must be specified for a 'text' shape type"
            )
        ls = self._shape_dict.get("letter-spacing", "0mm")
        lh = self._shape_dict.get("line-height", fs)

        font_size, letter_spacing, line_height = utils.get_text_params(fs, ls, lh)

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
        path, self._gerber_lp = utils.textToPath(
            font_data, self._text, letter_spacing, line_height, self._scale
        )
        # In the case where the text is an outline/stroke instead
        # of a fill we get rid of the gerber_lp
        if self._shape_dict.get("style") == "stroke":
            self._gerber_lp = None

        # For some reason SVG fonts are rotated by 180 degrees. This undos that
        self._rotate += 180

        return path

    def _process_path(self):
        try:
            return self._shape_dict.get("value") or self._shape_dict.get("d")
        except KeyError:
            msg.error(
                "A 'path' shape requires a 'value' or 'd' definition with a valid SVG path."
            )

    def transform_path(self, t_dict):
        """ 
        Transform the path of this object by taking the existing path and tranforming
        it into a new SvgPath given 't_dict' transform dictionary
        """
        p_r_path = self._path_obj.get_relative_parsed()
        self._path_obj = SvgPath(p_r_path, t_dict)

    def get_style_class(self):
        return self._shape_dict["style-class"]

    def set_style_class(self, new_class):
        self._shape_dict["style-class"] = new_class

    def get_style(self):
        return self._shape_dict.get("style", None)

    def set_style(self, new_style):
        self._shape_dict["style"] = new_style

    def get_label(self):
        return self._shape_dict["label"]

    def set_label(self, label):
        self._shape_dict["label"] = label

    def get_label_style_class(self):
        return self._shape_dict["label-style-class"]

    def set_label_style_class(self, new_style_class):
        self._shape_dict["label-style-class"] = new_style_class

    def rotate_location(self, deg, rotate_p=None):
        if rotate_p is None:
            rotate_p = Point([0, 0])
        self._shape_dict["location"].rotate(deg, rotate_p)

    def get_rotate(self):
        return self._shape_dict["rotate"]

    def set_rotate(self, rotate):
        self._shape_dict["rotate"] = rotate

    def getOriginalPath(self):
        return self._path_obj.get_input_path()

    def get_path_str(self):
        return self._path_obj.get_path_str()

    def get_orig_path_str(self):
        return self._path_obj.get_orig_path_str()

    def get_dims(self):
        return self._path_obj.get_dims()

    def get_width(self):
        return self._path_obj.get_width()

    def get_height(self):
        return self._path_obj.get_height()

    def getGerberLP(self):
        return self._shape_dict["gerber-lp"]

    def getScale(self):
        return self._shape_dict["scale"]

    def get_location(self):
        return self._shape_dict["location"]

    def set_location(self, location_point):
        self._shape_dict["location"] = location_point

    def getPourBuffer(self):
        return self._shape_dict["buffer-to-pour"]

    def get_type(self):
        return self._shape_dict["type"]

    def getText(self):
        # TODO: need to look into making this better
        return self._shape_dict.get("text", "")

    def getDiameter(self):
        return self._diameter

    def get_mirror_y(self):
        return self._shape_dict["mirror-y"]

    def get_mirror_x(self):
        return self._shape_dict["mirror-x"]

    def get_path_obj_num_of_segs(self):
        return self._path_obj.get_num_of_segments()
