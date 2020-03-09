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

from pcbmode.config import config
from pcbmode.utils import place
from pcbmode.utils import utils
from pcbmode.utils.shape import Shape
from pcbmode.utils.point import Point


def place_docs(layer):

    ns_pcm = config.cfg["ns"]["pcbmode"]

    try:
        docs_dict = config.brd["documentation"]
    except:
        return

    for key in docs_dict:
        location = Point(docs_dict[key]["location"])
        docs_dict[key]["location"] = [0, 0]
        shape_group = et.SubElement(layer, "g")
        shape_group.set(f"{{{ns_pcm}}}type", "module-shapes")
        shape_group.set(f"{{{ns_pcm}}}doc-key", key)
        shape_group.set(
            "transform", f"translate({location.px()},{config.cfg['iya']*location.py()})"
        )
        location = docs_dict[key]["location"]
        docs_dict[key]["location"] = Point() #[0, 0]
        shape = Shape(docs_dict[key])
        place.place_shape(shape, shape_group)
