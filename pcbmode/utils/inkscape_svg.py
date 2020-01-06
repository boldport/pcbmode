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
from pcbmode.utils import lxml_utils as lxu


def create(width, height):
    """
    Create a skelaton of an Inkscape SVG element
    """

    module = et.Element(
        "svg",
        width=f"{width}{config.cfg['params']['units']}",
        height=f"{height}{config.cfg['params']['units']}",
        viewBox=f"0, 0, {width}, {height}",
        version="1.1",
        nsmap=config.cfg["ns"],
        fill="black",
    )

    # Short namespaces
    ns_svg = config.cfg["ns"]["svg"]
    ns_rdf = config.cfg["ns"]["rdf"]
    ns_ink = config.cfg["ns"]["inkscape"]
    ns_cc = config.cfg["ns"]["cc"]
    ns_dc = config.cfg["ns"]["dc"]
    ns_sp = config.cfg["ns"]["sodipodi"]

    # CSS classes
    classes = config.stl.get("layout", None)
    if classes not in [None, ""]:
        lxu.addch(parent=module, ns=ns_svg, name="style", id="pcbmode-classes", text=classes)

    # Title
    title = config.brd["metadata"].get("title", None)
    if title not in [None, ""]:
        lxu.addch(parent=module, ns=ns_svg, name="title", id="title", text=title)

    # Set Inkscape options tag
    inkscape_opt = lxu.addch(module, ns_sp, "namedview", "namedview-pcbmode")
    inkscape_opt.set(f"{{{ns_ink}}}window-maximized", "1")
    inkscape_opt.set(f"{{{ns_ink}}}document-units", config.cfg["params"]["units"])
    # Create grid
    et.SubElement(
        inkscape_opt,
        f"{{{ns_ink}}}grid",
        type="xygrid",
        id="pcbmode-grid",
        visible="true",
        enabled="false",  # Change to enable by default
        units="mm",
        emspacing="5",
        spacingx="0.1mm",
        spacingy="0.1mm",
    )

    # Metadata - rdf - work
    md_el = lxu.addch(module, ns_svg, "metadata", "metadata-by-pcbmode")
    rdf_el = lxu.addch(md_el, ns_rdf, "RDF")
    work_el = lxu.addch(rdf_el, ns_cc, "Work")

    # Format
    lxu.addch(work_el, ns_dc, "format", None, "image/svg+xml")

    # Creator
    creator = config.brd["metadata"].get("creator", None)
    if creator not in [None, ""]:
        work_c_el = lxu.addch(work_el, ns_dc, "creator")
        work_ca_el = lxu.addch(work_c_el, ns_cc, "Agent")
        lxu.addch(work_ca_el, ns_dc, "title", None, creator)

    # Identifier
    identifier = config.brd["metadata"].get("project-id", None)
    if identifier not in [None, ""]:
        lxu.addch(work_el, ns_dc, "identifier", None, identifier)

    # Source
    source = config.brd["metadata"].get("sourcecode-url", None)
    if source not in [None, ""]:
        lxu.addch(work_el, ns_dc, "source", None, source)

    # Description
    desc = config.brd["metadata"].get("description", None)
    if desc not in [None, ""]:
        work_d = lxu.addch(work_el, ns_dc, "description", None, desc)

    # Contributors
    contrib = config.brd["metadata"].get("contributors", None)
    if contrib not in [None, ""]:
        work_c_el = lxu.addch(work_el, ns_dc, "contributor")
        work_ca_el = lxu.addch(work_c_el, ns_cc, "Agent")
        lxu.addch(work_ca_el, ns_dc, "title", None, contrib)

    # Rights - license
    license_name = config.brd["metadata"].get("license-name", None)
    if license_name not in [None, ""]:
        work_c_el = lxu.addch(work_el, ns_dc, "rights")
        work_ca_el = lxu.addch(work_c_el, ns_cc, "Agent")
        lxu.addch(work_ca_el, ns_dc, "title", None, f"License: {license_name}")

    # License - url
    license_url = config.brd["metadata"].get("license-url", None)
    if desc not in [None, ""]:
        work_d = lxu.addch(work_el, ns_cc, "license")
        work_d.set(f"{{{ns_rdf}}}resource", license_url)

    # Keywords
    keywords = config.brd["metadata"].get("keywords", None)
    if keywords not in [None, ""]:
        work_c_el = lxu.addch(work_el, ns_dc, "subject")
        work_ca_el = lxu.addch(work_c_el, ns_rdf, "Bag")
        lxu.addch(work_ca_el, ns_rdf, "li", None, keywords)

    # Date
    now = config.brd["metadata"].get("date", None)
    if now not in [None, ""]:
        if now.lower() == "now":
            now = datetime.datetime.now().isoformat(" ", "seconds")
        lxu.addch(work_el, ns_dc, "date", None, now)

    return module
