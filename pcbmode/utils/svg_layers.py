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


def create_layers(top_layer, transform=None, refdef=None):
    """
    Creates Inkscape SVG layers that correspond to a board's layers.
    Includes the default style definition from the stylesheet.
    Returns a dictionary of layer instantiations.
    """

    layer_control = config.cfg["layer-control"]

    # Holds SVG layers
    layers = {}

    # Create layers for top and bottom PCB layers
    for layer_dict in reversed(config.stk["layers-dict"]):

        layer_type = layer_dict["type"]
        layer_name = layer_dict["name"]

        # create SVG layer for PCB layer
        layers[layer_name] = {}
        element = layers[layer_name]["layer"] = create_layer(
            top_layer, layer_name, transform, None, refdef
        )
        element.set(
            "{" + config.cfg["ns"]["pcbmode"] + "}%s" % ("pcb-layer"), layer_name
        )

        sheets = layer_dict["stack"]
        if layer_type == "signal-layer-surface":
            placement_dict = [{"name": "placement", "type": "placement"}]
            assembly_dict = [{"name": "assembly", "type": "assembly"}]
            solderpaste_dict = [{"name": "solderpaste", "type": "solderpaste"}]

            # Layer appear in Inkscape first/top to bottom/last
            sheets = placement_dict + assembly_dict + solderpaste_dict + sheets

        for sheet in reversed(sheets):

            sheet_type = sheet["type"]
            sheet_name = sheet["name"]

            # # Set default style for this sheet
            # try:
            #     style = utils.dictToStyleText(
            #         config.stl["layout"][sheet_type]["default"][layer_name]
            #     )
            # except:
            #     # A stylesheet may define one style for any sheet type
            #     # or a specific style for multiple layers of the same
            #     # type. If, for example, a specific style for
            #     # 'internal-2' cannot be found, PCBmodE will default
            #     # to the general definition for this type of sheet
            #     style = utils.dictToStyleText(
            #         config.stl["layout"][sheet_type]["default"][
            #             layer_name.split("-")[0]
            #         ]
            #     )

            if layer_control[sheet_type]["hide"] == True:
                style = "display:none;"
            else:
                style = None

            print(f"{layer_name} {sheet_type}")

            tmp = layers[layer_name]
            tmp[sheet_type] = {}
            element = tmp[sheet_type]["layer"] = create_layer(
                parent_layer=tmp["layer"],
                layer_name=sheet_name,
                transform=None,
                style_class=f"{layer_name}-{sheet_type}",
                refdef=refdef,
            )

            element.set(
                "{" + config.cfg["ns"]["pcbmode"] + "}%s" % ("sheet"), sheet_type
            )
            if layer_control[sheet_type]["lock"] == True:
                element.set("{" + config.cfg["ns"]["sodipodi"] + "}insensitive", "true")

            # A PCB layer of type 'conductor' is best presented in
            # seperate sub-layers of 'pours', 'pads', and
            # 'routing'. The following generates those sub-layers
            if sheet_type == "conductor":
                tmp2 = layers[layer_name]["conductor"]
                conductor_types = ["routing", "pads", "pours"]

                for cond_type in conductor_types:

                    # try:
                    #     style = utils.dictToStyle(
                    #         config.stl["layout"]["conductor"][cond_type].get(layer_name)
                    #     )
                    # except:
                    #     # See comment above for rationalle
                    #     style = utils.dictToStyleText(
                    #         config.stl["layout"]["conductor"][cond_type][
                    #             layer_name.split("-")[0]
                    #         ]
                    #     )

                    if layer_control["conductor"][cond_type]["hide"] == True:
                        style = "display:none;"
                    else:
                        style = None

                    tmp2[cond_type] = {}
                    element = tmp2[cond_type]["layer"] = create_layer(
                        parent_layer=tmp2["layer"],
                        layer_name=cond_type,
                        transform=None,
                        style_class=layer_name,
                        refdef=refdef,
                    )

                    element.set(
                        "{" + config.cfg["ns"]["pcbmode"] + "}%s" % ("sheet"), cond_type
                    )

                    if layer_control["conductor"][cond_type]["lock"] == True:
                        element.set(
                            "{" + config.cfg["ns"]["sodipodi"] + "}insensitive", "true"
                        )

    for info_layer in ["origin", "dimensions", "outline", "drills", "documentation"]:
        # style = utils.dictToStyleText(config.stl["layout"][info_layer].get("default"))
        if layer_control[info_layer]["hide"] == True:
            style = "display:none;"
        else:
            style = None
        layers[info_layer] = {}
        element = layers[info_layer]["layer"] = create_layer(
            parent_layer=top_layer,
            layer_name=info_layer,
            transform=transform,
            style_class=info_layer,
            refdef=refdef,
        )
        element.set("{" + config.cfg["ns"]["pcbmode"] + "}%s" % ("sheet"), info_layer)
        if layer_control[info_layer]["lock"] == True:
            element.set("{" + config.cfg["ns"]["sodipodi"] + "}insensitive", "true")

    return layers


def create_layer(
    parent_layer, layer_name, transform=None, style_class=None, refdef=None
):
    """
    Create and return an Inkscape SVG layer 
    """

    ns_ink = config.cfg["ns"]["inkscape"]

    new_layer = et.SubElement(parent_layer, "g")
    new_layer.set(f"{{{ns_ink}}}groupmode", "layer")
    new_layer.set(f"{{{ns_ink}}}label", layer_name)
    if transform is not None:
        new_layer.set("transform", transform)
    if style_class is not None:
        new_layer.set("class", style_class)
    if refdef is not None:
        new_layer.set("refdef", refdef)

    return new_layer
