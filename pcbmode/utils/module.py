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
import copy
import sys
from pathlib import Path
from lxml import etree as et
import html.parser as HTMLParser

from pcbmode.config import config
from pcbmode.utils import messages as msg
from pcbmode.utils import svg
from pcbmode.utils import utils
from pcbmode.utils import place
from pcbmode.utils import inkscape_svg
from pcbmode.utils.shape import Shape
from pcbmode.utils.style import Style
from pcbmode.utils.component import Component
from pcbmode.utils.point import Point


class Module:
    """
    """

    def __init__(self, module_dict, routing_dict, asmodule=False):
        """
        """

        ns = {"pcbmode": config.cfg["ns"]["pcbmode"], "svg": config.cfg["ns"]["svg"]}

        self._module_dict = module_dict
        self._routing_dict = routing_dict

        self._outline = self._get_outline()
        self._width = self._outline.getWidth()
        self._height = self._outline.getHeight()

        # Get dictionaries of component/via/shape definitions
        components_dict = self._module_dict.get("components", {})
        self._components = self._get_components(components_dict)
        vias_dict = self._routing_dict.get("vias", {})
        self._vias = self._get_components(vias_dict)
        shapes_dict = self._module_dict.get("shapes", {})
        self._shapes = self._get_components(shapes_dict)

        sig_dig = config.cfg["params"]["significant-digits"]
        self._transform = "translate(%s %s)" % (
            round(self._width / 2, sig_dig),
            round(self._height / 2, sig_dig),
        )

        # Create the Inkscape SVG document
        self._module = inkscape_svg.create(self._width, self._height)
        svg_doc = et.ElementTree(self._module)

        # Get a dictionary of SVG layers
        self._layers = svg.makeSvgLayers(self._module, self._transform)

        # Add a 'defs' element:
        #   http://www.w3.org/TR/SVG/struct.html#Head
        # This is where masking elements that are used for pours are stored
        defs = et.SubElement(self._module, "defs")
        self._masks = {}

        for pcb_layer in config.stk["layer-names"]:
            element = et.SubElement(
                defs, "mask", id="mask-%s" % pcb_layer, transform=self._transform
            )
            # This will identify the masks for each PCB layer when
            # the layer is converted to Gerber
            element.set("{" + config.cfg["ns"]["pcbmode"] + "}pcb-layer", pcb_layer)
            self._masks[pcb_layer] = element

        self._placeOutline()
        self._placeOutlineDimensions()

        self._placeComponents(components=self._components, component_type="component")
        sys.stdout.write("\n")

        self._placeRouting()

        self._placeComponents(components=self._vias, component_type="via")

        self._placeComponents(components=self._shapes, component_type="shape")

        if config.cfg["create"]["docs"] == True:
            self._placeDocs()

        if config.cfg["create"]["drill-index"] == True:
            self._placeDrillIndex()

        if config.cfg["create"]["layer-index"] == True:
            self._placeLayerIndex()

        # This 'cover' "enables" the mask shapes defined in the mask are
        # shown. It *must* be the last element in the mask definition;
        # any mask element after it won't show
        for pcb_layer in config.stk["layer-names"]:
            if utils.checkForPoursInLayer(pcb_layer) is True:
                mask_cover = et.SubElement(
                    self._masks[pcb_layer],
                    "rect",
                    x="%s" % str(-self._width / 2),
                    y="%s" % str(-self._height / 2),
                    width="%s" % self._width,
                    height="%s" % self._height,
                    style="fill:#fff;",
                )
                # This tells the Gerber conversion to ignore this shape
                mask_cover.set(
                    "{" + config.cfg["ns"]["pcbmode"] + "}type", "mask-cover"
                )

        # Remove layers that were not made to be 'placed'. This
        # is a bit of a cheat, but it works for now.
        # TODO ;)

        # Output SVG
        output_file = Path(
            config.tmp["project-path"]
            / config.brd["project-params"]["output"]["svg-file"]
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(et.tostring(svg_doc, pretty_print=True))

    def _get_components(self, components_dict):
        """
        Create the components for this module.
        Return a list of items of class 'component'
        """
        components = []
        for refdef in components_dict:
            component_dict = components_dict[refdef]
            show = component_dict.get("show", True)
            place = component_dict.get("place", True)
            if (show == True) and (place == True):
                component = Component(refdef, component_dict)
                components.append(component)

        return components

    def _get_outline(self):
        """
        Get the (optional) module's outline.
        """
        outline_dict = self._module_dict.get("outline")
        if outline_dict != None:
            shape_dict = outline_dict.get("shape")
            if shape_dict != None:
                shape = Shape(shape_dict)
                style = Style(shape_dict, "outline")
                shape.setStyle(style)
        else:
            shape = None

        return shape

    def _placeOutlineDimensions(self):
        """
        Places outline dimension arrows
        """

        def makeArrow(width, gap):
            """
            Returns a path for an arrow of width 'width' with a center gap of
            width 'gap'
            """

            # Length of bar perpendicular to the arrow's shaft
            base_length = 1.8

            # Height of arrow's head
            arrow_height = 2.5

            # Width of arrow's head
            arrow_base = 1.2

            # Create path
            path = (
                "m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s"
                % (
                    -gap / 2,
                    0,
                    -width / 2 + gap / 2,
                    0,
                    0,
                    base_length / 2,
                    0,
                    -base_length,
                    arrow_height,
                    (base_length - arrow_base) / 2,
                    -arrow_height,
                    arrow_base / 2,
                    arrow_height,
                    arrow_base / 2,
                    -arrow_height,
                    -arrow_base / 2,
                    width / 2,
                    0,
                    gap / 2,
                    0,
                    width / 2 - gap / 2,
                    0,
                    0,
                    base_length / 2,
                    0,
                    -base_length,
                    -arrow_height,
                    (base_length - arrow_base) / 2,
                    arrow_height,
                    arrow_base / 2,
                    -arrow_height,
                    arrow_base / 2,
                    arrow_height,
                    -arrow_base / 2,
                )
            )

            return path

        # Create text shapes
        shape_dict = {}
        shape_dict["type"] = "text"
        style_dict = config.stl["layout"]["dimensions"].get("text", {})
        shape_dict["font-family"] = style_dict.get(
            "font-family", "UbuntuMono-R-webfont"
        )
        shape_dict["font-size"] = style_dict.get("font-size", "1.5mm")
        shape_dict["line-height"] = style_dict.get("line-height", "1mm")
        shape_dict["letter-spacing"] = style_dict.get("letter-spacing", "0mm")

        # Locations
        arrow_gap = 1.5
        width_loc = [0, self._height / 2 + arrow_gap]
        height_loc = [-(self._width / 2 + arrow_gap), 0]

        # Width text
        width_text_dict = shape_dict.copy()
        width_text_dict["value"] = "%s mm" % round(self._width, 2)
        width_text_dict["location"] = width_loc
        width_text = Shape(width_text_dict)
        style = Style(width_text_dict, "dimensions")
        width_text.setStyle(style)

        # Height text
        height_text_dict = shape_dict.copy()
        height_text_dict["value"] = "%s mm" % round(self._height, 2)
        height_text_dict["rotate"] = -90
        height_text_dict["location"] = height_loc
        height_text = Shape(height_text_dict)
        style = Style(height_text_dict, "dimensions")
        height_text.setStyle(style)

        # Width arrow
        shape_dict = {}
        shape_dict["type"] = "path"
        shape_dict["value"] = makeArrow(self._width, width_text.getWidth() * 1.2)
        shape_dict["location"] = width_loc
        width_arrow = Shape(shape_dict)
        style = Style(shape_dict, "dimensions")
        width_arrow.setStyle(style)

        # Height arrow
        shape_dict = {}
        shape_dict["type"] = "path"
        shape_dict["value"] = makeArrow(self._height, height_text.getHeight() * 1.2)
        shape_dict["rotate"] = -90
        shape_dict["location"] = height_loc
        height_arrow = Shape(shape_dict)
        style = Style(shape_dict, "dimensions")
        height_arrow.setStyle(style)

        svg_layer = self._layers["dimensions"]["layer"]
        group = et.SubElement(svg_layer, "g")
        group.set("{" + config.cfg["ns"]["pcbmode"] + "}type", "module-shapes")
        place.placeShape(width_text, group)
        place.placeShape(height_text, group)
        place.placeShape(width_arrow, group)
        place.placeShape(height_arrow, group)

    def _placeComponents(self, components, component_type):
        """
        Places the component on the board.

        'component_type' is the content of the 'type' fiels of the
        placed group. This is used by the extractor to identify the
        type of component ('component', 'via', 'shape')
        """

        htmlpar = HTMLParser.HTMLParser()

        for component in components:
            shapes_dict = component.getShapes()
            location = component.getLocation()
            rotation = component.getRotation()
            refdef = component.getRefdef()

            # If the component is placed on the bottom layer we need
            # to invert the shapes AND their 'x' coordinate.  This is
            # done using the 'invert' indicator set below
            placement_layer = component.getPlacementLayer()
            if placement_layer == "bottom":
                invert = True
            else:
                invert = False

            for pcb_layer in config.stk["layer-names"]:

                there_are_pours = utils.checkForPoursInLayer(pcb_layer)

                # Copper
                shapes = shapes_dict["conductor"].get(pcb_layer, [])

                if len(shapes) > 0:

                    svg_layer = self._layers[pcb_layer]["conductor"]["pads"]["layer"]

                    transform = "translate(%s,%s)" % (
                        location[0],
                        config.cfg["iya"] * location[1],
                    )

                    shape_group = et.SubElement(svg_layer, "g", transform=transform)

                    shape_group.set(
                        "{" + config.cfg["ns"]["pcbmode"] + "}type", component_type
                    )
                    # Add the reference designator as well if it's a
                    # 'component'
                    if component_type == "component":
                        shape_group.set(
                            "{" + config.cfg["ns"]["pcbmode"] + "}refdef",
                            component.getRefdef(),
                        )

                    style = utils.dictToStyleText(
                        config.stl["layout"]["conductor"]["pads"]["labels"]
                    )
                    label_group = et.SubElement(shape_group, "g", style=style)

                    for shape in shapes:
                        place.placeShape(shape, shape_group, invert)

                        # Add pin labels
                        # TODO: This isn't perfect, but good enough for now
                        label = shape.getLabel()
                        if label != None:
                            label_location = shape.getLocation()
                            label_rotation = shape.getRotation()
                            label_transform = "rotate(%s)" % label_rotation
                            t = et.SubElement(
                                label_group,
                                "text",
                                x=str(((1, -1)[invert]) * label_location.x),
                                y=str(config.cfg["iya"] * label_location.y),
                                transform=label_transform,
                            )
                            t.text = label

                        if there_are_pours == True:
                            mask_group = et.SubElement(
                                self._masks[pcb_layer], "g", transform=transform
                            )
                            self._placeMask(
                                mask_group, shape, "pad", original=False, mirror=invert
                            )

                # Pours
                shapes = shapes_dict["pours"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["conductor"]["pours"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    shape_group = et.SubElement(
                        svg_layer, "g", mask="url(#mask-%s)" % pcb_layer
                    )
                    transform = "translate(%s,%s)" % (
                        location[0],
                        config.cfg["iya"] * location[1],
                    )
                    group = et.SubElement(shape_group, "g", transform=transform)
                    group.set("{" + config.cfg["ns"]["pcbmode"] + "}type", "pours")
                    for shape in shapes:
                        placed_element = place.placeShape(shape, group, invert)

                # Soldermask
                shapes = shapes_dict["soldermask"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["soldermask"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    transform = "translate(%s,%s)" % (
                        location[0],
                        config.cfg["iya"] * location[1],
                    )
                    group = et.SubElement(svg_layer, "g", transform=transform)
                    group.set(
                        "{" + config.cfg["ns"]["pcbmode"] + "}type", "component-shapes"
                    )
                    for shape in shapes:
                        placed_element = place.placeShape(shape, group, invert)

                # Solderpaste
                shapes = shapes_dict["solderpaste"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["solderpaste"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    transform = "translate(%s,%s)" % (
                        location[0],
                        config.cfg["iya"] * location[1],
                    )
                    group = et.SubElement(svg_layer, "g", transform=transform)
                    group.set(
                        "{" + config.cfg["ns"]["pcbmode"] + "}type", "component-shapes"
                    )
                    for shape in shapes:
                        placed_element = place.placeShape(shape, group, invert)

                # Silkscreen
                shapes = shapes_dict["silkscreen"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["silkscreen"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    transform = "translate(%s,%s)" % (
                        location[0],
                        config.cfg["iya"] * location[1],
                    )
                    shape_group = et.SubElement(svg_layer, "g", transform=transform)
                    shape_group.set(
                        "{" + config.cfg["ns"]["pcbmode"] + "}type", "component-shapes"
                    )

                    for shape in shapes:
                        # Refdefs need to be in their own groups so that their
                        # location can later be extracted, hence this...
                        try:
                            is_refdef = getattr(shape, "is_refdef")
                        except:
                            is_refdef = False

                        if is_refdef == True:
                            # Shapes don't need to have silkscreen
                            # reference designators
                            if component_type != "shape":
                                refdef_group = et.SubElement(
                                    svg_layer, "g", transform=transform
                                )
                                refdef_group.set(
                                    "{" + config.cfg["ns"]["pcbmode"] + "}type",
                                    "refdef",
                                )
                                refdef_group.set(
                                    "{" + config.cfg["ns"]["pcbmode"] + "}refdef",
                                    refdef,
                                )
                                placed_element = place.placeShape(
                                    shape, refdef_group, invert
                                )
                        else:
                            placed_element = place.placeShape(
                                shape, shape_group, invert
                            )

                # Assembly
                shapes = shapes_dict["assembly"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["assembly"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    transform = "translate(%s,%s)" % (
                        location[0],
                        config.cfg["iya"] * location[1],
                    )
                    group = et.SubElement(svg_layer, "g", transform=transform)
                    for shape in shapes:
                        placed_element = place.placeShape(shape, group, invert)

                # Drills
                shapes = shapes_dict["drills"].get(pcb_layer, [])
                if len(shapes) > 0:
                    svg_layer = self._layers["drills"]["layer"]
                    transform = "translate(%s,%s)" % (
                        location[0],
                        config.cfg["iya"] * location[1],
                    )
                    group = et.SubElement(svg_layer, "g", transform=transform)
                    group.set(
                        "{" + config.cfg["ns"]["pcbmode"] + "}type", "component-shapes"
                    )
                    for shape in shapes:
                        placed_element = place.placeShape(shape, group, invert)
                        placed_element.set(
                            "{" + config.cfg["ns"]["pcbmode"] + "}diameter",
                            str(shape.getDiameter()),
                        )

            # Place component origin marker
            svg_layer = self._layers[placement_layer]["placement"]["layer"]

            # Here pcb_layer may not exist for components that define
            # shapes for internal layers but only surface layers are
            # defined in the stackup
            try:
                group = et.SubElement(svg_layer, "g", transform=transform)
            except:
                return

            # Add PCBmodE information, useful for when extracting
            group.set("{" + config.cfg["ns"]["pcbmode"] + "}type", component_type)
            group.set(
                "{" + config.cfg["ns"]["pcbmode"] + "}footprint",
                component.getFootprintName(),
            )
            if (component_type == "component") or (component_type == "shape"):
                group.set("{" + config.cfg["ns"]["pcbmode"] + "}refdef", refdef)
            elif component_type == "via":
                group.set("{" + config.cfg["ns"]["pcbmode"] + "}id", refdef)
            else:
                pass

            path = svg.placementMarkerPath()
            transform = "translate(%s,%s)" % (
                location[0],
                config.cfg["iya"] * location[1],
            )

            if placement_layer == "bottom":
                rotation *= -1

            marker_element = et.SubElement(
                group, "path", d=path, transform="rotate(%s)" % rotation
            )

            if component_type == "component":
                style = utils.dictToStyleText(config.stl["layout"]["placement"]["text"])
                t = et.SubElement(group, "text", x="0", y="-0.17", style=style)
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = "%s" % (refdef)
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = htmlpar.unescape("%s&#176;" % (rotation))
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = "[%.2f,%.2f]" % (location[0], location[1])
            elif component_type == "shape":
                style = utils.dictToStyleText(config.stl["layout"]["placement"]["text"])
                t = et.SubElement(group, "text", x="0", y="-0.17", style=style)
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = "%s" % (refdef)
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = htmlpar.unescape("%s&#176;" % (rotation))
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = "[%.2f,%.2f]" % (location[0], location[1])
            elif component_type == "via":
                style = utils.dictToStyleText(config.stl["layout"]["placement"]["text"])
                t = et.SubElement(group, "text", x="0", y="-0.11", style=style)
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = htmlpar.unescape("%s&#176;" % (rotation))
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = "[%.2f,%.2f]" % (location[0], location[1])
            else:
                continue

    def _placeRouting(self):
        """
        """

        routing = config.rte
        routes = routing.get("routes", {})

        # Path effects are used for meandering paths, for example
        path_effects = routes.get("path_effects")

        xpath_expr = "//g[@inkscape:label='%s']//g[@inkscape:label='%s']"
        extra_attributes = [
            "inkscape:connector-curvature",
            "inkscape:original-d",
            "inkscape:path-effect",
        ]

        for pcb_layer in config.stk["layer-names"]:

            # Are there pours in the layer? This makes a difference for whether to place
            # masks
            there_are_pours = utils.checkForPoursInLayer(pcb_layer)

            # Define a group where masks are stored
            mask_group = et.SubElement(self._masks[pcb_layer], "g")

            # Place defined routes on this SVG layer
            sheet = self._layers[pcb_layer]["conductor"]["routing"]["layer"]

            for route_key in routes.get(pcb_layer, {}):
                shape_dict = routes[pcb_layer][route_key]
                shape = Shape(shape_dict)
                style = Style(shape_dict, "conductor")
                shape.setStyle(style)

                # Routes are a special case where they are used as-is
                # counting on Inkscapes 'optimised' setting to modify
                # the path such that placement is refleced in
                # it. Therefor we use the original path, not the
                # transformed one as usual
                use_original_path = True
                mirror_path = False
                route_element = place.placeShape(
                    shape, sheet, mirror_path, use_original_path
                )

                route_element.set("style", shape.getStyleString())

                # Set the key as pcbmode:id of the route. This is used
                # when extracting routing to offset the location of a
                # modified route
                route_element.set(
                    "{" + config.cfg["ns"]["pcbmode"] + "}%s" % ("id"), route_key
                )

                # Add a custom buffer definition if it exists
                custom_buffer = shape_dict.get("buffer-to-pour")
                if custom_buffer != None:
                    route_element.set(
                        "{" + config.cfg["ns"]["pcbmode"] + "}%s" % "buffer-to-pour",
                        str(custom_buffer),
                    )

                # TODO: can this be done more elegantly, and "general purpose"?
                for extra_attrib in extra_attributes:
                    ea = shape_dict.get(extra_attrib)
                    if ea is not None:
                        route_element.set(
                            "{"
                            + config.cfg["namespace"]["inkscape"]
                            + "}%s" % (extra_attrib[extra_attrib.index(":") + 1 :], ea)
                        )

                # TODO: this needs to eventually go away or be done properly
                pcbmode_params = shape_dict.get("pcbmode")
                if pcbmode_params is not None:
                    route_element.set("pcbmode", pcbmode_params)

                if (there_are_pours == True) and (custom_buffer != "0"):
                    self._placeMask(
                        self._masks[pcb_layer], shape, "route", use_original_path
                    )

    #                # Due to the limitation of the Gerber format, and the method chosen
    #                # for applying masks onto pours, it is not possible to have copper
    #                # pour material inside of paths that have more than a single segment.
    #                # In order to make the apperance in the SVG and Gerbers consistent,
    #                # each path segment is added with a 'fill'. In the future, when the
    #                # *actual* shape is calculated, it may be possible to avoid this
    #                # hack. On the other hand, one can argue that having pours inside of
    #                # shapes doesn't make sense anyway, because it alters its apperance,
    #                # and such shapes are stylistic anyway. OK, back to code now...
    #                gerber_lp = shape.getGerberLP()
    #                if gerber_lp is not None:
    #                    if len(gerber_lp) > 1:
    #                        path_segments = path.split('m')
    #                        i = 0
    #                        for path_segment in path_segments[1:]:
    #                            # only mask dark bits
    #                            if gerber_lp[i] == 'd':
    #                                mask_element = et.SubElement(mask_group, 'path',
    #                                                             type="mask_shape",
    #                                                             style="fill:#000;stroke:none;",
    #                                                             d='m '+path_segment)
    #
    #                            i += 1

    def _placeMask(self, svg_layer, shape, kind, original=False, mirror=False):
        """
        Places a mask of a shape of type 'Shape' on SVG layer 'svg_layer'.
        'kind'    : type of shape; used to fetch the correct distance to pour
        'original': use the original path, not the transformed one
        """

        # Get the desired distance based on 'kind' 'outline', 'drill',
        # 'pad', 'route' unless 'pour_buffer' is specified
        pour_buffer = shape.getPourBuffer()
        if pour_buffer == None:
            pour_buffer = config.cfg["distances"]["from-pour-to"][kind]

        style_template = "fill:%s;stroke:#000;stroke-linejoin:round;stroke-width:%s;stroke-linecap:round;"

        style = shape.getStyle()

        if pour_buffer > 0:
            mask_element = place.placeShape(shape, svg_layer, mirror, original)
            if style.getStyleType() == "fill":
                mask_element.set("style", style_template % ("#000", pour_buffer * 2))
            else:
                # This width provides a distance of 'pour_buffer' from the
                # edge of the trace to a pour
                width = style.getStrokeWidth() + pour_buffer * 2
                mask_element.set("style", style_template % ("none", width))

            path = shape.getOriginalPath().lower()
            segments = path.count("m")
            mask_element.set(
                "{" + config.cfg["ns"]["pcbmode"] + "}gerber-lp", "c" * segments
            )

    def _placeOutline(self):
        """
        """
        # Place shape
        shape_group = et.SubElement(self._layers["outline"]["layer"], "g")
        shape_group.set("{" + config.cfg["ns"]["pcbmode"] + "}type", "module-shapes")
        place.placeShape(self._outline, shape_group)

        pour_buffer = config.cfg["distances"]["from-pour-to"]["outline"]

        for pcb_layer in config.stk["layer-names"]:
            if utils.checkForPoursInLayer(pcb_layer) is True:
                mask_element = place.placeShape(self._outline, self._masks[pcb_layer])
                # Override style so that we get the desired effect
                # We stroke the outline with twice the size of the buffer, so
                # we get the actual distance between the outline and board
                style = (
                    "fill:none;stroke:#000;stroke-linejoin:round;stroke-width:%s;"
                    % str(pour_buffer * 2)
                )
                mask_element.set("style", style)

                # Also override mask's gerber-lp and set to all clear
                path = self._outline.getOriginalPath().lower()
                segments = path.count("m")
                mask_element.set(
                    "{" + config.cfg["ns"]["pcbmode"] + "}gerber-lp", "c" * segments
                )

    def _placeDocs(self):
        """
        Places documentation blocks on the documentation layer
        """
        try:
            docs_dict = config.brd["documentation"]
        except:
            return

        for key in docs_dict:

            location = utils.toPoint(docs_dict[key]["location"])
            docs_dict[key]["location"] = [0, 0]

            shape_group = et.SubElement(self._layers["documentation"]["layer"], "g")
            shape_group.set(
                "{" + config.cfg["ns"]["pcbmode"] + "}type", "module-shapes"
            )
            shape_group.set("{" + config.cfg["ns"]["pcbmode"] + "}doc-key", key)
            shape_group.set(
                "transform",
                "translate(%s,%s)" % (location.x, config.cfg["iya"] * location.y),
            )

            location = docs_dict[key]["location"]
            docs_dict[key]["location"] = [0, 0]

            shape = Shape(docs_dict[key])
            style = Style(docs_dict[key], "documentation")
            shape.setStyle(style)
            element = place.placeShape(shape, shape_group)

    def _placeLayerIndex(self):
        """
        Adds a layer index
        """

        text_dict = config.stl["layout"]["layer-index"]["text"]
        text_dict["type"] = "text"

        # Set the height (and width) of the rectangle (square) to the
        # size of the text
        rect_width = utils.parseDimension(text_dict["font-size"])[0]
        rect_height = rect_width
        rect_gap = 0.25

        # Get location, or generate one
        try:
            location = config.brd["layer-index"]["location"]
        except:
            # If not location is specified, put the drill index at the
            # top right of the board. The 'gap' defines the extra
            # spcae between the top of the largest drill and the
            # board's edge
            gap = 2
            location = [self._width / 2 + gap, self._height / 2 - rect_height / 2]
        location = utils.toPoint(location)

        rect_dict = {}
        rect_dict["type"] = "rect"
        rect_dict["style"] = "fill"
        rect_dict["width"] = rect_width
        rect_dict["height"] = rect_height

        # Create group for placing index
        for pcb_layer in config.stk["layer-names"]:

            if pcb_layer in config.stk["surface-layer-names"]:
                sheets = [
                    "conductor",
                    "soldermask",
                    "silkscreen",
                    "assembly",
                    "solderpaste",
                ]
            else:
                sheets = ["conductor"]

            for sheet in sheets:
                layer = self._layers[pcb_layer][sheet]["layer"]
                transform = "translate(%s,%s)" % (
                    location.x,
                    config.cfg["iya"] * location.y,
                )
                group = et.SubElement(layer, "g", transform=transform)
                group.set("{" + config.cfg["ns"]["pcbmode"] + "}type", "layer-index")

                rect_shape = Shape(rect_dict)
                style = Style(rect_dict, sheet)
                rect_shape.setStyle(style)
                place.placeShape(rect_shape, group)

                text_dict["value"] = "%s %s" % (pcb_layer, sheet)
                text_shape = Shape(text_dict)
                text_width = text_shape.getWidth()
                style = Style(text_dict, sheet)
                text_shape.setStyle(style)
                element = place.placeShape(text_shape, group)
                element.set(
                    "transform",
                    "translate(%s,%s)"
                    % (rect_width / 2 + rect_gap + text_width / 2, 0),
                )

                location.y += config.cfg["iya"] * (rect_height + rect_gap)

            location.y += config.cfg["iya"] * (rect_height + rect_gap * 1.5)

    def _placeDrillIndex(self):
        """
        Adds a drill index
        """

        # Get the drills sheet / SVG layer
        drill_layer = self._layers["drills"]["layer"]
        ns = {"pcbmode": config.cfg["ns"]["pcbmode"], "svg": config.cfg["ns"]["svg"]}
        drills = drill_layer.findall(".//*[@pcbmode:diameter]", namespaces=ns)

        drills_dict = {}
        longest_text = 0
        largest_drill = 0
        drill_count = 0
        for drill in drills:
            diameter = drill.get("{" + config.cfg["ns"]["pcbmode"] + "}diameter")
            diameter = round(float(diameter), 2)
            if diameter not in drills_dict:
                drills_dict[diameter] = 1
            else:
                drills_dict[diameter] += 1
            if diameter > largest_drill:
                largest_drill = diameter
            drill_count += 1

            if len(str(diameter)) > longest_text:
                longest_text = len(str(diameter))

        # Get location, or generate one
        try:
            location = config.brd["drill-index"]["location"]
        except:
            # If no location is specified, put the drill index at the
            # bottom left of the board. The 'gap' defines the extra
            # spcae between the top of the largest drill and the
            # board's edge
            gap = 2
            location = [-self._width / 2, -(self._height / 2 + gap)]
        location = utils.toPoint(location)

        # Create group for placing index
        transform = "translate(%s,%s)" % (location.x, config.cfg["iya"] * location.y)
        group = et.SubElement(drill_layer, "g", transform=transform)
        group.set("{" + config.cfg["ns"]["pcbmode"] + "}type", "drill-index")

        text_style_dict = config.stl["layout"]["drill-index"].get("text")
        text_style = utils.dictToStyleText(text_style_dict)

        count_style_dict = config.stl["layout"]["drill-index"].get("count-text")
        count_style = utils.dictToStyleText(count_style_dict)

        count_style_dict["font-size"] /= 2
        drill_size_style = utils.dictToStyleText(count_style_dict)

        if drill_count == 0:
            text = "No drills"
        elif drill_count == 1:
            text = "1 drill: "
        else:
            text = "%s drills: " % drill_count
        t = et.SubElement(group, "text", x=str(0), y=str(0), style=text_style)
        t.text = text

        # "new line"
        location.y = -(largest_drill / 2 + 1.5)

        # TODO: this hack'ish thing for aligning the text isn't going
        # to work when the font is changed in the stylesheet
        if float(longest_text * 0.5) > largest_drill:
            location.x = longest_text * 0.3
        else:
            location.x = largest_drill / 2

        gap = 2

        for diameter in reversed(sorted(drills_dict)):
            path = svg.drillPath(diameter)
            transform = "translate(%s,%s)" % (
                location.x,
                config.cfg["iya"] * location.y,
            )
            element = et.SubElement(group, "path", d=path, transform=transform)
            element.set("fill-rule", "evenodd")

            t = et.SubElement(
                group,
                "text",
                x=str(location.x),
                y=str(-location.y),
                dy="%s" % (config.cfg["iya"] * 0.25),
                style=count_style,
            )
            t.text = str(drills_dict[diameter])

            t = et.SubElement(
                group,
                "text",
                x=str(location.x),
                y=str(-location.y),
                dy="%s" % (config.cfg["iya"] * -0.5),
                style=drill_size_style,
            )
            t.text = "%s mm" % diameter

            location.x += max(diameter, 2.5)
