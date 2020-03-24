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
from pcbmode.utils import utils
from pcbmode.utils import svg
from pcbmode.utils import svg_path_create
from pcbmode.utils.svgpath import SvgPath
from pcbmode.utils.point import Point


def place(layer, width, height):
    """
    """

    try:
        drill_count_d = config.tmp["drill-count"]
    except:
        return

    ns_pcm = config.cfg["ns"]["pcbmode"]

    drills_dict = {}
    longest_text = 0
    largest_drill = 0
    for diameter in drill_count_d:
        if diameter not in drills_dict:
            drills_dict[diameter] = 1
        else:
            drills_dict[diameter] += 1
        if diameter > largest_drill:
            largest_drill = diameter
        if len(str(diameter)) > longest_text:
            longest_text = len(str(diameter))

    # Location of index
    default_loc = [-width / 2, -(height / 2 + 2)]
    drill_index = config.brd.get("drill-index", {"location": default_loc})
    location = Point(drill_index.get("location", default_loc))

    # Element
    transform = f"translate({location.px()},{config.cfg['iya']*location.py()})"
    group = et.SubElement(layer, "g", transform=transform)
    group.set(f"{{{ns_pcm}}}type", "drill-index")

    # Headline text
    drill_count = len(drill_count_d)
    if drill_count == 0:
        text = "No drills"
    elif drill_count == 1:
        text = "1 drill: "
    else:
        text = f"{drill_count} drills: "

    text_el = et.SubElement(group, "text", x="0", y="0")
    text_el.set("class", "drill-index")
    text_el.text = text

    location.y = 0
    location.x = 0

    for diameter in reversed(sorted(drills_dict)):
        location.x = diameter / 2
        location.y += config.cfg["iya"] * max(diameter / 2, 2)
        path_obj = SvgPath(svg_path_create.drill(diameter))
        path_str = path_obj.get_path_str()
        transform = f"translate({location.px()},{config.cfg['iya']*location.py()})"
        symbol_el = et.SubElement(group, "path", d=path_str, transform=transform)
        symbol_el.set("fill-rule", "evenodd")
        symbol_el.set("class", "drill-index-symbol")

        t = et.SubElement(
            group,
            "text",
            x=f"{location.x + diameter*2}",
            y=f"{config.cfg['iya']*(location.y-diameter/2)}",
        )
        t.set("class", "drill-index-symbol-text")
        t.text = f"x{drills_dict[diameter]} {diameter} mm"
