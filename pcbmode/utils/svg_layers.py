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
    Includes the default style definition from the stylesheet.
    Returns a dictionary of layer instantiations.
    """

    ns_pcm = config.cfg["ns"]["pcbmode"]
    ns_sp = config.cfg["ns"]["sodipodi"]

    # Contains whether to show, place, or lock each layer
    layer_control = config.cfg["layer-control"]

    layers = {}

    # Create layers for the PCB according to the stackup. We need to reverse the
    # order so that Inkscape shows them in the 'correct' order.
    for layer_dict in reversed(config.stk["layers-dict"]):

        layer_name = layer_dict["name"]       
        layers[layer_name] = {}

        # Create the primary layers ('top', 'bottom', etc.)
        # These have no 'style_class' or 'style'
        el = layers[layer_name]["layer"] = create_layer(
            parent=parent_el,
            name=layer_name,
            transform=transform,
            style_class=None,
            refdef=refdef,
        )
        el.set(f"{{{ns_pcm}}}pcb-layer", layer_name)

        # Each PCB layer is composed of 'sheets' (silkscreen, soldermask, etc.)
        # but also 'solderpaste' and 'assembly' and even 'placement' are part of
        # the stackup, which is defined in the chosen stack JSON.
        sheets = layer_dict["stack"]

        for sheet in reversed(sheets):

            sheet_type = sheet["type"]
 
            if layer_control[sheet_type]["hide"] == True:
                style = "display:none;"
            else:
                style = None

            print(f"{layer_name} {sheet_type}")

            tmp = layers[layer_name]
            tmp[sheet_type] = {}
 
            el = tmp[sheet_type]["layer"] = create_layer(
                parent=tmp["layer"],
                name=sheet["name"],
                transform=None,
                style_class=f"{layer_name}-{sheet_type}",
                refdef=refdef,
            )

            el.set(f"{{{ns_pcm}}}sheet", sheet_type)
 
            if layer_control[sheet_type]["lock"] == True:
                el.set(f"{{{ns_sp}}}insensitive", "true")

            # A PCB layer of type 'conductor' is best presented in
            # seperate sub-layers of 'pours', 'pads', and
            # 'routing'. The following generates those sub-layers
            if sheet_type == "conductor":
                tmp2 = layers[layer_name]["conductor"]
                conductor_types = ["routing", "pads", "pours"]

                for cond_type in conductor_types:
                    if layer_control["conductor"][cond_type]["hide"] == True:
                        style = "display:none;"
                    else:
                        style = None

                    tmp2[cond_type] = {}
                    el = tmp2[cond_type]["layer"] = create_layer(
                        parent=tmp2["layer"],
                        name=cond_type,
                        transform=None,
                        style_class=layer_name,
                        refdef=refdef,
                    )

                    el.set(f"{{{ns_pcm}}}sheet", cond_type)

                    if layer_control["conductor"][cond_type]["lock"] == True:
                        el.set(f"{{{ns_sp}}}insensitive", "true")

    for info_layer in ["origin", "dimensions", "outline", "drills", "documentation"]:
        # style = utils.dictToStyleText(config.stl["layout"][info_layer].get("default"))
        if layer_control[info_layer]["hide"] == True:
            style = "display:none;"
        else:
            style = None

        layers[info_layer] = {}
        el = layers[info_layer]["layer"] = create_layer(
            parent=parent_el,
            name=info_layer,
            transform=transform,
            style_class=info_layer,
            refdef=refdef,
        )
        el.set(f"{{{ns_pcm}}}sheet", info_layer)
        if layer_control[info_layer]["lock"] == True:
            el.set(f"{{{ns_sp}}}insensitive", "true")

    return layers


def create_layer(parent, name, transform=None, style_class=None, refdef=None):
    """
    Create and return an Inkscape SVG layer 
    """

    ns_ink = config.cfg["ns"]["inkscape"]

    new_layer = et.SubElement(parent, "g")
    new_layer.set(f"{{{ns_ink}}}groupmode", "layer")
    new_layer.set(f"{{{ns_ink}}}label", name)
    if transform is not None:
        new_layer.set("transform", transform)
    if style_class is not None:
        new_layer.set("class", style_class)
    if refdef is not None:
        new_layer.set("refdef", refdef)

    return new_layer
