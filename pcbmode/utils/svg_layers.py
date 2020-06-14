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


def create_layers(parent_el, transform=None, refdef=None):
    """
    Creates Inkscape SVG layers that correspond to a board's layers.
    Includes the default style definition from the stylesheet as a 'class'.
    Returns a dictionary of layer instantiations.
    """
    layers_d = {}

    # Create layers for the PCB according to the stackup. We need to reverse the
    # order so that Inkscape shows them in the 'correct' order.
    #    for layer_dict in reversed(config.stk["layers-dict"]):
    for l_name, l_d in reversed(config.stk["stackup"].items()):
        if l_d.get("place", True) == False:
            continue
        style_class = l_d.get("name", l_name)
        layers_d[l_name] = {}
        layers_d[l_name]["layer"] = create_layer(
            parent=parent_el,
            name=l_d.get("name", l_name),
            transform=transform,
            style_class=style_class,
            refdef=refdef,
            pcbmode_type=l_d["type"],
            pcbmode_value=l_name,
            lock=l_d.get("lock", False),
            hide=l_d.get("hide", False),
        )

        process_foils(
            d=l_d, 
            layers_d=layers_d, 
            parent_layer=layers_d[l_name]["layer"],
            refdef=refdef,
            style_class_base=style_class
        )

    return layers_d


def process_foils(d, layers_d, parent_layer, refdef, style_class_base):
    """
    """
    for f_d in reversed(d.get("foils", [])):
        if f_d.get("place", True) == False:
            continue
        foil_type = f_d["type"]
        style_class = f"{style_class_base}-{foil_type}"
        layer_name = f_d["name"]
        layers_d[foil_type] = {}
        layers_d[foil_type]["layer"] = create_layer(
            parent=parent_layer,
            name=f_d["name"],
            transform=None,
            style_class=style_class,
            refdef=refdef,
            pcbmode_type="sheet",
            pcbmode_value=f_d["type"],
            lock=f_d.get("lock", False),
            hide=f_d.get("hide", False),
        )

        process_foils(
            d=f_d,
            layers_d=layers_d, 
            parent_layer=layers_d[foil_type]["layer"], 
            refdef=refdef, 
            style_class_base=style_class,
        )

    return


def create_layer(
    parent,
    name,
    transform=None,
    style_class=None,
    refdef=None,
    pcbmode_type=None,
    pcbmode_value="",
    lock=False,
    hide=False,
):
    """
    Create and return an Inkscape SVG layer 
    """

    ns_ink = config.cfg["ns"]["inkscape"]
    ns_pcm = config.cfg["ns"]["pcbmode"]
    ns_sp = config.cfg["ns"]["sodipodi"]

    new_layer = et.SubElement(parent, "g")
    new_layer.set(f"{{{ns_ink}}}groupmode", "layer")
    new_layer.set(f"{{{ns_ink}}}label", name)
    if pcbmode_type is not None:
        new_layer.set(f"{{{ns_pcm}}}{pcbmode_type}", pcbmode_value)
    if transform is not None:
        new_layer.set("transform", transform)
    if style_class is not None:
        new_layer.set("class", style_class)
    if refdef is not None:
        new_layer.set("refdef", refdef)
    if lock == True:
        new_layer.set(f"{{{ns_sp}}}insensitive", "true")
    if hide == True:
        new_layer.set("style", "display:none;")

    return new_layer
