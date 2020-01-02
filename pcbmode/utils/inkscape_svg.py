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


import datetime
from lxml import etree as et

from pcbmode.config import config

def create(width, height):
    """
    Create a skelaton of an Inkscape SVG element
    """
    module = et.Element(
        "svg",
        width="%s%s" % (width, config.cfg["params"]["units"]),
        height="%s%s" % (height, config.cfg["params"]["units"]),
        viewBox="%s, %s, %s, %s" % (0, 0, width, height),
        version="1.1",
        nsmap=config.cfg["ns"],
        fill="black",
    )

    title = config.brd["metadata"].get("title", None)
    if title not in [None, ""]:
        title_element = et.SubElement(
            module,
            "{" + config.cfg["ns"]["svg"] + "}%s" % ("title"),
            id="title",
        )
        title_element.text = title
        module.append(title_element)

    # Set Inkscape options tag
    inkscape_opt = et.SubElement(
        module,
        "{" + config.cfg["ns"]["sodipodi"] + "}%s" % "namedview",
        id="namedview-pcbmode",
        showgrid="true",
    )

    # Add units definition (only 'mm' is supported)
    inkscape_opt.set(
        "{" + config.cfg["ns"]["inkscape"] + "}%s" % "document-units",
        config.cfg["params"]["units"],
    )

    # Open window maximised
    inkscape_opt.set(
        "{" + config.cfg["ns"]["inkscape"] + "}%s" % "window-maximized", "1"
    )

    # Define a grid
    et.SubElement(
        inkscape_opt,
        "{" + config.cfg["ns"]["inkscape"] + "}%s" % "grid",
        type="xygrid",
        id="pcbmode-grid",
        visible="true",
        enabled="false",
        units="mm",
        emspacing="5",
        spacingx="0.1mm",
        spacingy="0.1mm",
    )

    # Add a welcome message as a comment in the SVG
    welcome_message = """
Hello! This SVG file was generated using PCBmodE on %s GMT. 
PCBmodE is open source software

  https://pcbmode.com

and is maintained by Boldport

  https://boldport.com

""" % (
        datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )
    module.append(et.Comment(welcome_message))

    return module
