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

from pcbmode.config import config
from pcbmode.utils import messages as msg
from pcbmode.utils import svg
from pcbmode.utils import utils
from pcbmode.utils import place
from pcbmode.utils import inkscape_svg
from pcbmode.utils import css_utils
from pcbmode.utils import svg_layers
from pcbmode.utils import drill_index
from pcbmode.utils import layer_index
from pcbmode.utils import documentation
from pcbmode.utils import svg_path_create
from pcbmode.utils.shape import Shape
from pcbmode.utils.component import Component
from pcbmode.utils.svgpath import SvgPath
from pcbmode.utils.point import Point


class Module:
    """
    """

    def __init__(self, module_name, asmodule=False):
        """
        """

        ns_pcm = config.cfg["ns"]["pcbmode"]

        # These two statement assume that there's a single module. When we start working
        # on multiple modules per board/panel those will need to be named and seperated
        self._module_dict = config.brd
        self._routing_dict = config.rte

        self._outline_shape = self._get_outline_shape()
        self._dims = self._outline_shape.get_dims()
        self._center = self._dims.copy()
        self._center.mult(0.5)  # Center point

        comps_dict = self._module_dict.get("components", {})
        self._comp_objs = self._get_comp_objs(comps_dict, "components")

        vias_dict = self._routing_dict.get("vias", {})
        self._via_objs = self._get_comp_objs(vias_dict, "vias")

        shapes_dict = self._module_dict.get("shapes", {})
        self._shape_objs = self._get_comp_objs(shapes_dict, "shapes")

        # Create the Inkscape SVG document
        self._module = inkscape_svg.create(self._dims.px(), self._dims.py())
        svg_doc = et.ElementTree(self._module)
        # Create a dictionary of SVG layers
        self._transform = f"translate({self._center.px()} {self._center.py()})"
        self._layers = svg_layers.create_layers(self._module, self._transform)

        # Add a 'defs' element:
        #   http://www.w3.org/TR/SVG/struct.html#Head
        # This is where masking elements that are used for pours are stored
        defs = et.SubElement(self._module, "defs")
        self._masks = {}

        for pcb_layer in config.stk["layer-names"]:
            el = et.SubElement(
                defs, "mask", id=f"mask-{pcb_layer}", transform=self._transform
            )
            # This will identify the masks for each PCB layer when
            # the layer is converted to Gerber
            el.set(f"{{{ns_pcm}}}pcb-layer", pcb_layer)
            self._masks[pcb_layer] = el

        self._place_outline()
        self._place_outline_dims()
        self._place_comps(comp_objs=self._comp_objs, comp_type="component")
        self._place_routing()
        self._place_comps(comp_objs=self._via_objs, comp_type="via")
        self._place_comps(comp_objs=self._shape_objs, comp_type="shape")

        if config.cfg["create"]["docs"] == True:
            docs_layer = self._layers["documentation"]["layer"]
            documentation.place_docs(docs_layer)
        if config.cfg["create"]["drill-index"] == True:
            drills_layer = self._layers["drills"]["layer"]
            drill_index.place(drills_layer, self._dims.px(), self._dims.py())
        if config.cfg["create"]["layer-index"] == True:
            layer_index.place_index(self._layers, self._dims.px(), self._dims.py())

        # This 'cover' "enables" the mask shapes defined in the mask are
        # shown. It *must* be the last element in the mask definition;
        # any mask element after it won't show
        for pcb_layer in config.stk["layer-names"]:
            if utils.checkForPoursInLayer(pcb_layer) is True:
                mask_cover = et.SubElement(
                    self._masks[pcb_layer],
                    "rect",
                    x=f"{-self._center.px()}",
                    y=f"{-self._center.py()}",
                    width=f"{self._dims.px()}",
                    height=f"{self._dims.py()}",
                    style="fill:#fff;",
                )
                # This tells the Gerber conversion to ignore this shape
                mask_cover.set(f"{{{ns_pcm}}}type", "mask-cover")

        # Output module SVG
        output_file = Path(
            config.tmp["project-path"]
            / config.brd["project-params"]["output"]["svg-file"]
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            et.tostring(svg_doc, encoding="unicode", pretty_print=True)
        )

    def _get_comp_objs(self, comps_dict, comp_type):
        """ Returna a list of Component objects """
        comp_objs = []
        for refdef in comps_dict:
            comp_dict = comps_dict[refdef]
            show = comp_dict.get("show", True)
            place = comp_dict.get("place", True)
            if (show == True) and (place == True):
                comp_obj = Component(refdef, comp_dict, comp_type)
                comp_objs.append(comp_obj)
        return comp_objs

    def _get_outline_shape(self):
        """
        Get the (optional) module's outline.
        """
        shape = None
        outline_dict = self._module_dict.get("outline", None)
        if outline_dict != None:
            shape_dict = outline_dict.get("shape", None)
            if shape_dict != None:
                shape = Shape(shape_dict)
        return shape

    def _place_outline(self):
        """
        """
        ns_pcm = config.cfg["ns"]["pcbmode"]

        shape_group = et.SubElement(self._layers["outline"]["layer"], "g")
        shape_group.set(f"{{{ns_pcm}}}type", "module-shapes")
        place.place_shape(self._outline_shape, shape_group)

        pour_buffer = config.cfg["distances"]["from-pour-to"]["outline"]

        for pcb_layer in config.stk["layer-names"]:
            if utils.checkForPoursInLayer(pcb_layer) is True:
                mask_element = place.place_shape(
                    self._outline_shape, self._masks[pcb_layer]
                )
                # Override style so that we get the desired effect
                # We stroke the outline with twice the size of the buffer, so
                # we get the actual distance between the outline and board
                style = (
                    "fill:none;stroke:#000;stroke-linejoin:round;stroke-width:%s;"
                    % str(pour_buffer * 2)
                )
                mask_element.set("style", style)

                # Also override mask's gerber-lp and set to all clear
                path = self._outline_shape.get_path_str()
                segments = path.count("m")
                mask_element.set(f"{{{ns_pcm}}}gerber-lp", "c" * segments)

    def _place_outline_dims(self):
        """
        Places outline dimension arrows
        """

        # Create text shapes
        shape_dict = {}
        shape_dict["type"] = "text"

        # Where to get properties from
        style_class = "dimensions"

        shape_dict["font-family"] = css_utils.get_prop(
            config.stl["layout"], style_class, "font-family"
        )
        shape_dict["font-size"] = css_utils.get_prop(
            config.stl["layout"], style_class, "font-size"
        )
        shape_dict["line-height"] = css_utils.get_prop(
            config.stl["layout"], style_class, "line-height"
        )
        shape_dict["letter-spacing"] = css_utils.get_prop(
            config.stl["layout"], style_class, "letter-spacing"
        )

        # Dimension arrow properties
        arrow_gap = 1.5
        arrow_bar_length = 1.6  # bar against arrow head
        arrow_height = 2.2  # height of arrow's head
        arrow_base = 1.2  # width of arrow's head

        width_loc = [0, self._center.py() + arrow_gap]
        height_loc = [-(self._center.px() + arrow_gap), 0]

        # Width text
        width_text_dict = shape_dict.copy()
        width_text_dict["value"] = f"{self._center.px()} mm"
        width_text_dict["location"] = width_loc
        width_text = Shape(width_text_dict)

        # Height text
        height_text_dict = shape_dict.copy()
        height_text_dict["value"] = f"{self._center.py()} mm"
        height_text_dict["rotate"] = -90
        height_text_dict["location"] = height_loc
        height_text = Shape(height_text_dict)

        # Width arrow
        shape_dict = {}
        shape_dict["type"] = "path"
        shape_dict["value"] = SvgPath(
            svg_path_create.arrow(
                width=self._dims.px(),
                height=arrow_height,
                base=arrow_base,
                bar=arrow_bar_length,
                gap=width_text.get_width() * 1.5,
            )
        ).get_path_str()
        shape_dict["location"] = width_loc
        shape_dict["style"] = "stroke-width:0.2;"
        width_arrow = Shape(shape_dict)

        # Height arrow
        shape_dict = {}
        shape_dict["type"] = "path"
        shape_dict["value"] = SvgPath(
            svg_path_create.arrow(
                width=self._dims.py(),
                height=arrow_height,
                base=arrow_base,
                bar=arrow_bar_length,
                gap=height_text.get_height() * 1.5,
            )
        ).get_path_str()
        shape_dict["rotate"] = -90
        shape_dict["location"] = height_loc
        shape_dict["style"] = "stroke-width:0.2;"
        height_arrow = Shape(shape_dict)

        svg_layer = self._layers["dimensions"]["layer"]
        group = et.SubElement(svg_layer, "g")
        group.set(f"{{{config.cfg['ns']['pcbmode']}}}type", "module-shapes")
        place.place_shape(width_text, group)
        place.place_shape(height_text, group)
        place.place_shape(width_arrow, group)
        place.place_shape(height_arrow, group)

    def _place_comps(self, comp_objs, comp_type):
        """
        Places the component on the board.

        'component_type' is the content of the 'type' fiels of the
        placed group. This is used by the extractor to identify the
        type of component ('component', 'via', 'shape')
        """

        ns_pcm = config.cfg["ns"]["pcbmode"]

        for comp_obj in comp_objs:
            shapes_dict = comp_obj.get_shapes()
            location = comp_obj.get_location()
            refdef = comp_obj.get_refdef()

            if location.is_not_00():
                lx = location.px()
                ly = location.py() * config.cfg["iya"]
                transform = f"translate({lx},{ly})"
            else:
                transform = None

            # If the component is placed on the bottom layer we need
            # to invert the shapes AND their 'x' coordinate.  This is
            # done using the 'invert' indicator set below
            placement_layer = comp_obj.get_placement_layer()
            if placement_layer == "bottom":
                invert = True
            else:
                invert = False

            for pcb_layer in config.stk["layer-names"]:

                there_are_pours = utils.checkForPoursInLayer(pcb_layer)

                # Conductor
                shapes = shapes_dict["conductor"].get(pcb_layer, [])

                if len(shapes) > 0:

                    svg_layer = self._layers[pcb_layer]["conductor"]["pads"]["layer"]

                    shape_group = et.SubElement(svg_layer, "g")
                    if transform != None:
                        shape_group.set("transform", transform)

                    shape_group.set(f"{{{ns_pcm}}}type", comp_type)
                    # Add the reference designator as well if it's a
                    # 'component'
                    if comp_type == "component":
                        shape_group.set(
                            f"{{{ns_pcm}}}refdef", comp_obj.get_refdef(),
                        )

                    for shape in shapes:
                        place.place_shape(shape, shape_group, invert)

                        if there_are_pours == True:
                            mask_grp_el = et.SubElement(self._masks[pcb_layer], "g")
                            if transform != None:
                                mask_grp_el.set("transform", transform)
                            self._place_mask(
                                layer=mask_grp_el,
                                shape=shape,
                                feature_kind="pad",
                                original=False,
                                mirror=invert,
                            )

                # Pours
                shapes = shapes_dict["pours"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["conductor"]["pours"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    shape_group = et.SubElement(
                        svg_layer, "g", mask=f"url(#mask-{pcb_layer})"
                    )
                    group = et.SubElement(shape_group, "g")
                    if transform != None:
                        group.set("transform", transform)

                    group.set(f"{{{ns_pcm}}}type", "pours")
                    for shape in shapes:
                        placed_element = place.place_shape(shape, group, invert)

                # Soldermask
                shapes = shapes_dict["soldermask"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["soldermask"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    group = et.SubElement(svg_layer, "g")
                    if transform != None:
                        group.set("transform", transform)
                    group.set(f"{{{ns_pcm}}}type", "component-shapes")
                    for shape in shapes:
                        placed_element = place.place_shape(shape, group, invert)

                # Solderpaste
                shapes = shapes_dict["solderpaste"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["solderpaste"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    group = et.SubElement(svg_layer, "g")
                    if transform != None:
                        group.set("transform", transform)
                    group.set(f"{{{ns_pcm}}}type", "component-shapes")
                    for shape in shapes:
                        placed_element = place.place_shape(shape, group, invert)

                # Silkscreen
                shapes = shapes_dict["silkscreen"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["silkscreen"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    shape_group = et.SubElement(svg_layer, "g")
                    shape_group.set(f"{{{ns_pcm}}}type", "component-shapes")
                    if transform != None:
                        shape_group.set("transform", transform)

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
                            if comp_type != "shape":
                                refdef_group = et.SubElement(
                                    svg_layer, "g", transform=transform
                                )
                                refdef_group.set(f"{{{ns_pcm}}}type", "refdef")
                                refdef_group.set(f"{{{ns_pcm}}}refdef", refdef)
                                placed_element = place.place_shape(
                                    shape, refdef_group, invert
                                )
                        else:
                            placed_element = place.place_shape(
                                shape, shape_group, invert
                            )

                # Assembly
                shapes = shapes_dict["assembly"].get(pcb_layer, [])
                try:
                    svg_layer = self._layers[pcb_layer]["assembly"]["layer"]
                except:
                    svg_layer = None

                if len(shapes) > 0 and svg_layer != None:
                    transform = (
                        f"translate({location.px()},{config.cfg['iya']*location.py()})"
                    )
                    group = et.SubElement(svg_layer, "g")
                    if transform != None:
                        group.set("transform", transform)
                    for shape in shapes:
                        placed_element = place.place_shape(shape, group, invert)

                # Drills
                shapes = shapes_dict["drills"].get(pcb_layer, [])
                if len(shapes) > 0:
                    svg_layer = self._layers["drills"]["layer"]
                    group = et.SubElement(svg_layer, "g")
                    if transform != None:
                        group.set("transform", transform)
                    group.set(f"{{{ns_pcm}}}type", "component-shapes")
                    for shape in shapes:
                        placed_element = place.place_shape(shape, group, invert)
                        placed_element.set(
                            f"{{{ns_pcm}}}diameter", str(shape.getDiameter())
                        )

            # Place component origin marker
            svg_layer = self._layers[placement_layer]["placement"]["layer"]

            # Here pcb_layer may not exist for components that define
            # shapes for internal layers but only surface layers are
            # defined in the stackup
            try:
                group = et.SubElement(svg_layer, "g")
            except:
                return

            if transform != None:
                group.set("transform", transform)

            # Add PCBmodE information, used when extracting
            group.set(f"{{{ns_pcm}}}type", comp_type)
            group.set(f"{{{ns_pcm}}}footprint", comp_obj.getFootprintName())
            if comp_type in ["component", "shape"]:
                group.set(f"{{{ns_pcm}}}refdef", refdef)
            elif comp_type == "via":
                group.set(f"{{{ns_pcm}}}id", refdef)
            else:
                pass

            # Place the placement marker
            # The information included in the marker is:
            # refdef (for components), rotation, location (2 sig digs) 
            marker_obj = SvgPath(svg_path_create.placement_marker())
            marker_el = et.SubElement(group, "path", d=marker_obj.get_path_str())
            rotate = comp_obj.get_rotate()
            if rotate != 0:
                if placement_layer == "bottom":
                    rotate *= -1
                marker_el.set("transform", f"rotate({rotate})")  # rotate marker

            # Place marker text
            style_class = "placement-text"
            if comp_type in ["component", "shape"]:
                t = et.SubElement(group, "text", x="0", y="-0.17")
                t.set("class", style_class)
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = f"{refdef}"
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = f"{rotate}\u00B0"
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = f"[{location.px(2)},{location.py(2)}]"
            elif comp_type == "via":
                t = et.SubElement(group, "text", x="0", y="-0.11")
                t.set("class", style_class)
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = f"{rotate}\u00B0"
                ts = et.SubElement(t, "tspan", x="0", dy="0.1")
                ts.text = f"[{location.px(2)},{location.py(2)}]"
            else:
                pass

    def _place_routing(self):
        """
        """

        ns_pcm = config.cfg["ns"]["pcbmode"]
        ns_ink = config.cfg["ns"]["inkscape"]

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
                # Make the shape relative to outline dims
                shape = Shape(shape_dict=shape_dict, rel_to_dim=self._dims)

                route_el = place.place_shape(
                    shape=shape, svg_layer=sheet, orig_path=True,
                )
                # Set the key as pcbmode:id of the route. This is used
                # when extracting routing to offset the location of a
                # modified route
                route_el.set(f"{{{ns_pcm}}}id", route_key)

                # Add a custom buffer definition if it exists
                custom_buffer = shape_dict.get("buffer-to-pour")
                if custom_buffer != None:
                    route_el.set(
                        f"{{{ns_pcm}}}buffer-to-pour", str(custom_buffer),
                    )
                if (there_are_pours == True) and (custom_buffer != "0"):
                    self._place_mask(
                        layer=self._masks[pcb_layer],
                        shape=shape,
                        feature_kind="route",
                        original=True,
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

    def _place_mask(self, layer, shape, feature_kind, original=False, mirror=False):
        """
        Places a mask of a shape of type 'Shape' on SVG layer 'layer'.
        'feature_kind'    : type of shape; used to fetch the correct distance to pour
        'original': use the original path, not the transformed one
        """

        ns_pcm = config.cfg["ns"]["pcbmode"]

        # Get the desired distance based on 'kind' 'outline', 'drill',
        # 'pad', 'route' unless 'pour_buffer' is specified
        pour_buffer = shape.getPourBuffer()
        if pour_buffer == None:
            pour_buffer = config.cfg["distances"]["from-pour-to"][feature_kind]

        # TODO: replace this with a class... might not be possible!
        style_template = "fill:%s;stroke:#000;stroke-linejoin:round;stroke-width:%s;stroke-linecap:round;"

        style = shape.get_style()

        if pour_buffer > 0:
            mask_el = place.place_shape(shape, layer, mirror, original)

            stroke_width = css_utils.get_style_value("stroke-width", style)

            if stroke_width is not None:
                # This width provides a distance of 'pour_buffer' from the
                # edge of the trace to a pour
                width = float(stroke_width) + pour_buffer * 2
                mask_el.set("style", style_template % ("none", width))
            else:
                mask_el.set("style", style_template % ("#000", pour_buffer * 2))

            c_string = "c" * shape.get_path_obj_num_of_segs()
            mask_el.set(f"{{{ns_pcm}}}gerber-lp", c_string)
