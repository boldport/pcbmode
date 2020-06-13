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

        print(l_d)

        # Maybe we don't want to place this layer?
        if l_d.get("place", True) == False:
            continue

        l_type = l_d.get('type', None)
        if l_type == 'signal':
            style_class = None
            #pcbmode_type = "pcb-layer"
        else:
            style_class = l_d.get("type", None)
            #pcbmode_type = "other-layer"

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
            hide=l_d.get("hide", False)
        )

        for s_d in reversed(l_d.get('foils', [])):
            print(s_d) 

    #     layer_name = layer_dict["name"]

    #     # Each PCB layer is composed of 'foils' (silkscreen, soldermask, etc.)
    #     # but also 'solderpaste' and 'assembly' and even 'placement' are part of
    #     # the stackup, which is defined in the chosen stack JSON.
    #     sheets = layer_dict["stack"]

    #     for sheet in reversed(sheets):
    #         sheet_type = sheet["type"]

    #         layers_d[layer_name][sheet_type] = {}
    #         layers_d[layer_name][sheet_type]["layer"] = create_layer(
    #             parent=layers_d[layer_name]["layer"],
    #             name=sheet["name"],
    #             transform=None,
    #             style_class=f"{layer_name}-{sheet_type}",
    #             refdef=refdef,
    #             pcbmode_prop="sheet",
    #             pcbmode_value=sheet["type"],
    #             lock=config.cfg["layer-control"][sheet["type"]].get("lock", False),
    #             hide=config.cfg["layer-control"][sheet["type"]].get("hide", False),
    #         )

    #         # Sheet 'conductor' also gets sub-layers 'pours', 'pads', and 'routing'.
    #         if sheet_type == "conductor":
    #             conductor_types = ["routing", "pads", "pours"]
    #             for cond_type in conductor_types:
    #                 layers_d[layer_name]["conductor"][cond_type] = {}
    #                 layers_d[layer_name]["conductor"][cond_type][
    #                     "layer"
    #                 ] = create_layer(
    #                     parent=layers_d[layer_name]["conductor"]["layer"],
    #                     name=cond_type,
    #                     transform=None,
    #                     style_class=f"{layer_name}-{sheet_type}-{cond_type}",
    #                     refdef=refdef,
    #                     pcbmode_prop="sheet",
    #                     pcbmode_value=cond_type,
    #                     lock=config.cfg["layer-control"]["conductor"][cond_type].get(
    #                         "lock", False
    #                     ),
    #                     hide=config.cfg["layer-control"]["conductor"][cond_type].get(
    #                         "hide", False
    #                     ),
    #                 )

    # info_layers = ["drills", "outline", "origin", "dimensions", "documentation"]
    # for info_layer in info_layers:
    #     layers_d[info_layer] = {}
    #     layers_d[info_layer]["layer"] = create_layer(
    #         parent=parent_el,
    #         name=info_layer,
    #         transform=transform,
    #         style_class=info_layer,
    #         refdef=refdef,
    #         pcbmode_prop="sheet",
    #         pcbmode_value=info_layer,
    #         lock=config.cfg["layer-control"][info_layer].get("lock", False),
    #         hide=config.cfg["layer-control"][info_layer].get("hide", False),
    #     )

    return layers_d


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
