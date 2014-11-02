#!/usr/bin/python

import os
import datetime
from lxml import etree as et

import config
import messages as msg

import svg
import utils
import place

from shape import Shape
from style import Style
from component import Component



class Module():
    """
    """

    def __init__(self, 
                 module_dict, 
                 routing_dict, 
                 asmodule=False):
        """
        """

        self._module_dict = module_dict
        self._routing_dict = routing_dict

        self._outline = self._getOutline()
        self._width = self._outline.getWidth()
        self._height = self._outline.getHeight()

        # Get dictionary of component definitions
        components_dict = self._module_dict.get('components') or {}
        self._components = self._getComponents(components_dict)

        # Get dictionary of component definitions
        vias_dict = self._routing_dict.get('vias') or {}
        self._vias = self._getComponents(vias_dict)

        sig_dig = config.cfg['significant-digits']
        self._transform = 'translate(%s %s)' % (round(self._width/2, sig_dig),
                                                round(self._height/2, sig_dig))

        # Create the Inkscape SVG document
        self._module = self._getModuleElement()
        svg_doc = et.ElementTree(self._module)

        # Get a dictionary of SVG layers
        self._layers = svg.makeSvgLayers(self._module, self._transform)

        # Add a 'defs' element:
        #   http://www.w3.org/TR/SVG/struct.html#Head
        # This is where masking elements that are used for pours are stored
        defs = et.SubElement(self._module, 'defs')
        self._masks = {}
        for pcb_layer in utils.getSurfaceLayers():
             element = et.SubElement(defs, 'mask',
                                     id="mask-%s" % pcb_layer,
                                     transform=self._transform)
             # This will identify the masks for each PCB layer when
             # the layer is converted to Gerber
             element.set('{'+config.cfg['ns']['pcbmode']+'}pcb-layer', pcb_layer)
             self._masks[pcb_layer] = element

        self._placeOutline()
        self._placeOutlineDimensions()

        msg.subInfo('Placing components:', newline=False)
        self._placeComponents(self._components, 'components', print_refdef=True)
        print

        msg.subInfo('Placing routes')
        self._placeRouting()

        msg.subInfo('Placing vias')
        self._placeComponents(self._vias, 'vias')

        msg.subInfo('Placing shapes')
        self._placeShapes()

        msg.subInfo('Placing pours')
        self._placePours()

        if config.tmp['no-docs'] == False:
            msg.subInfo('Placing documentation')
            self._placeDocs()

        if config.tmp['no-drill-index'] == False:
            msg.subInfo('Placing drill index')
            self._placeDrillIndex()

        if config.tmp['no-layer-index'] == False:
            msg.subInfo('Placing layer index')
            self._placeLayerIndex()


        # This 'cover' "enables" the mask shapes defined in the mask are
        # shown. It *must* be the last element in the mask definition;
        # any mask element after it won't show
        for pcb_layer in utils.getSurfaceLayers():
            if utils.checkForPoursInLayer(pcb_layer) is True:
                mask_cover = et.SubElement(self._masks[pcb_layer], 'rect',
                                           x="%s" % str(-self._width/2), 
                                           y="%s" % str(-self._height/2),
                                           width="%s" % self._width,
                                           height="%s" % self._height,
                                           style="fill:#fff;")
                # This tells the Gerber conversion to ignore this shape
                mask_cover.set('{'+config.cfg['ns']['pcbmode']+'}type', 'mask-cover')

        output_file = os.path.join(config.cfg['base-dir'],
                                   config.cfg['locations']['build'],
                                   config.cfg['name'] + '.svg')
     
        try:
            f = open(output_file, 'wb')
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
     
        f.write(et.tostring(svg_doc, pretty_print=True))
        f.close()





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
            path = "m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s m %s,%s %s,%s" % (-gap/2,0, -width/2+gap/2,0, 0,base_length/2, 0,-base_length, arrow_height,(base_length-arrow_base)/2, -arrow_height,arrow_base/2, arrow_height,arrow_base/2, -arrow_height,-arrow_base/2, width/2,0, gap/2,0, width/2-gap/2,0, 0,base_length/2, 0,-base_length, -arrow_height,(base_length-arrow_base)/2, arrow_height,arrow_base/2, -arrow_height,arrow_base/2, arrow_height,-arrow_base/2,) 
            
            return path



 
        # Create text shapes
        shape_dict = {}
        shape_dict['type'] = 'text'
        style_dict = config.stl['layout']['dimensions'].get('text') or {}
        shape_dict['font-family'] = style_dict.get('font-family') or "UbuntuMono-R-webfont"
        shape_dict['font-size'] = style_dict.get('font-size') or "1.5mm"
        shape_dict['line-height'] = style_dict.get('line-height') or "1mm"
        shape_dict['letter-spacing'] = style_dict.get('letter-spacing') or "0mm"

        # Locations
        arrow_gap = 1.5
        width_loc = [0, self._height/2+arrow_gap]
        height_loc = [-(self._width/2+arrow_gap), 0]

        # Width text
        width_text_dict = shape_dict.copy()
        width_text_dict['value'] = "%s mm" % round(self._width,2)
        width_text_dict['location'] = width_loc
        width_text = Shape(width_text_dict)
        style = Style(width_text_dict, 'dimensions')
        width_text.setStyle(style)

        # Height text
        height_text_dict = shape_dict.copy()
        height_text_dict['value'] = "%s mm" % round(self._height,2)
        height_text_dict['rotate'] = -90
        height_text_dict['location'] = height_loc
        height_text = Shape(height_text_dict)
        style = Style(height_text_dict, 'dimensions')
        height_text.setStyle(style)
 
        # Width arrow
        shape_dict = {}
        shape_dict['type'] = 'path'
        shape_dict['value'] = makeArrow(self._width, width_text.getWidth()*1.2)
        shape_dict['location'] = width_loc
        width_arrow = Shape(shape_dict)
        style = Style(shape_dict, 'dimensions')
        width_arrow.setStyle(style)
 
        # Height arrow
        shape_dict = {}
        shape_dict['type'] = 'path'
        shape_dict['value'] = makeArrow(self._height, height_text.getHeight()*1.2)
        shape_dict['rotate'] = -90
        shape_dict['location'] = height_loc
        height_arrow = Shape(shape_dict)
        style = Style(shape_dict, 'dimensions')
        height_arrow.setStyle(style)

        svg_layer = self._layers['dimensions']['layer']
        group = et.SubElement(svg_layer, 'g')
        group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'module-shapes')
        place.placeShape(width_text, group)
        place.placeShape(height_text, group)
        place.placeShape(width_arrow, group)
        place.placeShape(height_arrow, group)
        





    def _placePours(self):
        """
        """

        try:
            pours = self._module_dict['shapes']['pours']
        except:
            return

        shape_group = {}
        for pcb_layer in utils.getSurfaceLayers():
            svg_layer = self._layers[pcb_layer]['copper']['pours']['layer']
            shape_group[pcb_layer] = et.SubElement(svg_layer, 'g',
                                                   mask='url(#mask-%s)' % pcb_layer)

        for pour_dict in pours:
            try:
                pour_type = pour_dict['type']
            except:
                msg.error("Can't find a 'type' for a pour shape. Pours can be any 'shape', or simply 'type':'layer' to cover the entire layer.")

            layers = pour_dict.get('layers') or ['top']

            if pour_type == 'layer':
                # Get the outline shape dict
                new_pour_dict = self._module_dict['outline'].get('shape').copy()
                new_pour_dict['style'] = 'fill'
                shape = Shape(new_pour_dict)
                style = Style(new_pour_dict, 'outline')
                shape.setStyle(style)
            else:
                shape = Shape(pour_dict)
                style = Style(pour_dict, 'outline')
                shape.setStyle(style)

            # Place on all specified layers
            for layer in layers:
                place.placeShape(shape, shape_group[layer])





    def _placeShapes(self):
        """
        """

        mirror = False

        try:
            shapes_dict = self._module_dict['shapes']
        except:
            return


        for sheet in ['copper','soldermask','solderpaste','silkscreen']:
            try:
                shapes = shapes_dict[sheet]
            except KeyError:
                continue

            there_are_pours = {}
            shape_groups = {}
            for pcb_layer in utils.getSurfaceLayers():
                there_are_pours[pcb_layer] = utils.checkForPoursInLayer(pcb_layer)
                shape_groups[pcb_layer] = et.SubElement(self._layers[pcb_layer][sheet]['layer'], 'g')
                shape_groups[pcb_layer].set('{'+config.cfg['ns']['pcbmode']+'}type', 'module-shapes')


            for shape_dict in shapes:

                pcb_layers = shape_dict.get('layers') or ['top']

                for pcb_layer in pcb_layers:

                    # Shapes placed on the bottom layer are not mirrored
                    # unless they are text, in which case, it's the
                    # expected behaviour and so it is mirrored by default
                    # unless otherwise instructed.
                    try:
                        shape_mirror = shape_dict.get['mirror']
                    except:
                        if shape_dict['type'] == 'text':
                            shape_mirror = True
                        else:
                            shape_mirror = False
                        
                    if (pcb_layer == 'bottom') and (shape_mirror != False):
                        mirror = True
                    else:
                        mirror = False
                    shape = Shape(shape_dict)
                    style = Style(shape_dict, sheet)
                    shape.setStyle(style)
                    place.placeShape(shape, shape_groups[pcb_layer], mirror)
     
                    # Place mask for pour if copper shape
                    if (sheet == 'copper') and (there_are_pours[pcb_layer] == True):
                        location = shape.getLocation()
                        transform = "translate(%s,%s)" % (location.x, location.y)
                        mask_group = et.SubElement(self._masks[pcb_layer], 'g')
                                                   #id="routing_masks") 
                                                   #transform=transform)
                        self._placeMask(mask_group, 
                                        shape,
                                        'pad',
                                        False,
                                        mirror)


     
     
     
     
    def _placeComponents(self, components, component_type, print_refdef=False):
        """
        """
        for component in components:
            shapes_dict = component.getShapes()
            location = component.getLocation()

            # If the component is placed on the bottom layer we need
            # to invert the shapes AND their 'x' coordinate.  This is
            # sone using the 'invert' indicator set below
            refdef = component.getRefdef()

            if print_refdef == True:
                print refdef,

            placement_layer = component.getPlacementLayer()
            if placement_layer == 'bottom':
                invert = True
            else:
                invert = False

            for pcb_layer in utils.getSurfaceLayers():

                there_are_pours = utils.checkForPoursInLayer(pcb_layer)

                # Copper
                shapes = shapes_dict['copper'][pcb_layer]
                if len(shapes) > 0:
                    svg_layer = self._layers[pcb_layer]['copper']['pads']['layer']
     
                    transform = "translate(%s,%s)" % (location[0],
                                                      config.cfg['invert-y']*location[1])
                    group = et.SubElement(svg_layer, 'g', 
                                          transform=transform)

                    if component_type == 'components':
                        group.set('{'+config.cfg['ns']['pcbmode']+'}refdef', component.getRefdef())
                    elif component_type == 'vias':
                        group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'via')
                        group.set('{'+config.cfg['ns']['pcbmode']+'}via', component.getFootprintName())
                    else:
                        pass

                    for shape in shapes:
                        place.placeShape(shape, group, invert)
                        if there_are_pours == True:
                            mask_group = et.SubElement(self._masks[pcb_layer], 'g', 
                                                       transform=transform)
                            self._placeMask(mask_group, 
                                            shape,
                                            'pad')
                    # Add pin labels
                    labels = shapes_dict['pin-labels'][pcb_layer]
                    if labels != []:
                        style = utils.dictToStyleText(config.stl['layout']['board']['pad-labels'])
                        label_group = et.SubElement(group, 'g', 
                                                    transform="rotate(%s)" % component.getRotation(),
                                                    style=style)
                        for label in labels:
                            t = et.SubElement(label_group, 'text',
                                              x=str(label['location'][0]),
                                              # TODO: get rid of this hack
                                              y=str(-label['location'][1]))
                                              #y=str(-pin_location.y + pad_numbers_font_size/3),
                                              #refdef=self._refdef)
                            t.text = label['text']





                # Soldermask
                shapes = shapes_dict['soldermask'][pcb_layer]
                if len(shapes) > 0:
                    svg_layer = self._layers[pcb_layer]['soldermask']['layer']
                    transform = "translate(%s,%s)" % (location[0],
                                                      config.cfg['invert-y']*location[1])
                    group = et.SubElement(svg_layer, 'g', transform=transform)
                    group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'component-shapes')
                    for shape in shapes:
                        placed_element = place.placeShape(shape, group, invert)
     
                    # Solderpaste
                    shapes = shapes_dict['solderpaste'][pcb_layer]
                    svg_layer = self._layers[pcb_layer]['solderpaste']['layer']
                    transform = "translate(%s,%s)" % (location[0],
                                                      config.cfg['invert-y']*location[1])
                    group = et.SubElement(svg_layer, 'g', transform=transform)
                    group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'component-shapes')
                    for shape in shapes:
                        placed_element = place.placeShape(shape, group, invert)


                # Silkscreen
                shapes = shapes_dict['silkscreen'][pcb_layer]
                if len(shapes) > 0:
                    svg_layer = self._layers[pcb_layer]['silkscreen']['layer']
                    transform = "translate(%s,%s)" % (location[0],
                                                      config.cfg['invert-y']*location[1])
                    shape_group = et.SubElement(svg_layer, 'g', transform=transform)
                    shape_group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'component-shapes')
     
                    for shape in shapes:
                        # Refdefs need to be in their own groups so that their
                        # location can later be extracted, hence this...
                        try:
                            is_refdef = getattr(shape, 'is_refdef')
                        except:
                            is_refdef = False

                        if is_refdef == True:
                            refdef_group = et.SubElement(svg_layer, 'g', transform=transform)
                            refdef_group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'refdef')
                            refdef_group.set('{'+config.cfg['ns']['pcbmode']+'}refdef', refdef)
                            placed_element = place.placeShape(shape, refdef_group, invert)
                        else:
                            placed_element = place.placeShape(shape, shape_group, invert)


                # Assembly
                shapes = shapes_dict['assembly'][pcb_layer]
                if len(shapes) > 0: 
                    svg_layer = self._layers[pcb_layer]['assembly']['layer']
                    transform = "translate(%s,%s)" % (location[0],
                                                      config.cfg['invert-y']*location[1])
                    group = et.SubElement(svg_layer, 'g', transform=transform)
                    for shape in shapes:
                        placed_element = place.placeShape(shape, group, invert)

                # Drills
                shapes = shapes_dict['drills'][pcb_layer]
                if len(shapes) > 0:
                    svg_layer = self._layers['drills']['layer']
                    transform = "translate(%s,%s)" % (location[0],
                                                      config.cfg['invert-y']*location[1])
                    group = et.SubElement(svg_layer, 'g', transform=transform)
                    group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'component-shapes')
                    for shape in shapes:
                        placed_element = place.placeShape(shape, group, invert)
                        placed_element.set('{'+config.cfg['ns']['pcbmode']+'}diameter',
                                           str(shape.getDiameter()))






    def _placeRouting(self):
        """
        """

        routing = config.rte
        routes = routing.get('routes') or {}
        vias = routing.get('vias') 

        # Path effects are used for meandering paths, for example
        path_effects = routes.get('path_effects')
 
        xpath_expr = "//g[@inkscape:label='%s']//g[@inkscape:label='%s']"
        extra_attributes = ['inkscape:connector-curvature', 'inkscape:original-d', 'inkscape:path-effect']
 
        for pcb_layer in utils.getSurfaceLayers():
 
            # Are there pours in the layer? This makes a difference for whether to place
            # masks
            there_are_pours = utils.checkForPoursInLayer(pcb_layer)

            # Define a group where masks are stored
            mask_group = et.SubElement(self._masks[pcb_layer], 'g')

            # Place defined routes on this SVG layer
            sheet = self._layers[pcb_layer]['copper']['routing']['layer']

            for route_key in (routes.get(pcb_layer) or {}):
                shape_dict = routes[pcb_layer][route_key]
                shape = Shape(shape_dict)
                style = Style(shape_dict, 'copper')
                shape.setStyle(style)

                # Routes are a special case where they are used as-is
                # counting on Inkscapes 'optimised' setting to modify
                # the path such that placement is refleced in
                # it. Therefor we use the original path, not the
                # transformed one as usual
                use_original_path = True
                mirror_path = False
                route_element = place.placeShape(shape,
                                                 sheet,
                                                 mirror_path,
                                                 use_original_path)

                route_element.set('style', shape.getStyleString())

                # Set the key as pcbmode:id of the route. This is used
                # when extracting routing to offset the location of a
                # modified route
                route_element.set('{'+config.cfg['ns']['pcbmode']+'}%s' % ('id'),
                                  route_key)

                # Add a custom buffer definition if it exists
                custom_buffer = shape_dict.get('buffer-to-pour')
                if custom_buffer != None:
                    route_element.set('{'+config.cfg['namespace']['pcbmode']+'}%s' % "buffer-to-pour", str(custom_buffer))

                # TODO: can this be done more elegantly, and "general purpose"?
                for extra_attrib in extra_attributes:
                    ea = shape_dict.get(extra_attrib)
                    if ea is not None:
                        route_element.set('{'+config.cfg['namespace']['inkscape']+'}%s' % (extra_attrib[extra_attrib.index(':')+1:], ea))


                # TODO: this needs to eventually go away or be done properly
                pcbmode_params = shape_dict.get('pcbmode')
                if pcbmode_params is not None:
                    route_element.set('pcbmode', pcbmode_params)                

                if ((there_are_pours == True) and (custom_buffer != "0")):
                    self._placeMask(self._masks[pcb_layer], 
                                    shape, 
                                    'route',
                                    use_original_path)

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
            try:
                pour_buffer = self._module_dict['distances']['from-pour-to'][kind]
            except:
                pour_buffer = config.brd['distances']['from-pour-to'][kind]

        style_template = "fill:%s;stroke:#000;stroke-linejoin:round;stroke-width:%s;stroke-linecap:round;"

        style = shape.getStyle()

        if (pour_buffer > 0):
            mask_element = place.placeShape(shape, svg_layer, mirror, original)
            if style.getStyleType() == 'fill':
                mask_element.set('style', style_template % ('#000', pour_buffer*2))
            else:
                # This width provides a distance of 'pour_buffer' from the
                # edge of the trace to a pour
                width = style.getStrokeWidth() + pour_buffer*2
                mask_element.set('style', style_template % ('none', width))        

            path = shape.getOriginalPath().lower()
            segments = path.count('m')
            mask_element.set('{'+config.cfg['ns']['pcbmode']+'}gerber-lp', 'c'*segments)
            



    def _placeOutline(self):
        """
        """
        # Place shape
        shape_group = et.SubElement(self._layers['outline']['layer'], 'g')
        shape_group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'module-shapes')
        place.placeShape(self._outline, shape_group)

        # Place a mask for the board's outline. This creates a buffer between 
        # the board's edge and pours
        try:
            pour_buffer = self._module['distances']['from-pour-to']['outline']
        except:
            pour_buffer = config.brd['distances']['from-pour-to']['outline']

        for pcb_layer in utils.getSurfaceLayers():
            if utils.checkForPoursInLayer(pcb_layer) is True:
                mask_element = place.placeShape(self._outline, self._masks[pcb_layer])
                # Override style so that we get the desired effect
                # We stroke the outline with twice the size of the buffer, so
                # we get the actual distance between the outline and board
                style = "fill:none;stroke:#000;stroke-linejoin:round;stroke-width:%s;" % str(pour_buffer*2)
                mask_element.set('style', style)

                # Also override mask's gerber-lp and set to all clear
                path = self._outline.getOriginalPath().lower()
                segments = path.count('m')
                mask_element.set('{'+config.cfg['ns']['pcbmode']+'}gerber-lp', 'c'*segments)



    def _placeDocs(self):
        """
        Places documentation blocks on the documentation layer
        """
        try:
            docs_dict = config.brd['documentation']
        except:
            return

        for key in docs_dict:

            location = utils.toPoint(docs_dict[key]['location'])
            docs_dict[key]['location'] = [0, 0]

            shape_group = et.SubElement(self._layers['documentation']['layer'], 'g')
            shape_group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'module-shapes')            
            shape_group.set('{'+config.cfg['ns']['pcbmode']+'}doc-key', key)
            shape_group.set('transform', "translate(%s,%s)" % (location.x, config.cfg['invert-y']*location.y))

            location = docs_dict[key]['location']
            docs_dict[key]['location'] = [0, 0]

            shape = Shape(docs_dict[key])
            style = Style(docs_dict[key], 'documentation')
            shape.setStyle(style)
            element = place.placeShape(shape, shape_group)



    def _placeLayerIndex(self):
        """
        Adds a drill index
        """

        text_dict = config.stl['layout']['layer-index']['text']
        text_dict['type'] = 'text'

        # Set the height (and width) of the rectangle (square) to the
        # size of the text
        rect_width = utils.parseDimension(text_dict['font-size'])[0]
        rect_height = rect_width
        rect_gap = 0.25

        # Get location, or generate one
        try:
            location = config.brd['layer-index']['location']
        except:
            # If not location is specified, put the drill index at the
            # top right of the board. The 'gap' defines the extra
            # spcae between the top of the largest drill and the
            # board's edge
            gap = 2
            location = [self._width/2+gap, self._height/2-rect_height/2]
        location = utils.toPoint(location)        

        rect_dict = {}
        rect_dict['type'] = 'rect'
        rect_dict['style'] = 'fill'
        rect_dict['width'] = rect_width
        rect_dict['height'] = rect_height

        # Create group for placing index
        for pcb_layer in utils.getSurfaceLayers():
            for sheet in ['copper', 'soldermask', 'silkscreen', 'assembly', 'solderpaste']:
                layer = self._layers[pcb_layer][sheet]['layer']
                transform = "translate(%s,%s)" % (location.x, config.cfg['invert-y']*location.y)
                group = et.SubElement(layer, 'g',
                                      transform=transform)
                group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'layer-index')

                rect_shape = Shape(rect_dict)
                style = Style(rect_dict, sheet)
                rect_shape.setStyle(style)
                place.placeShape(rect_shape, group)

                text_dict['value'] = "%s %s" % (pcb_layer, sheet)
                #text_dict['location'] = [rect_width+rect_gap+text_width, 0]
                text_shape = Shape(text_dict)
                text_width = text_shape.getWidth()
                style = Style(text_dict, sheet)
                text_shape.setStyle(style)
                element = place.placeShape(text_shape, group)
                element.set("transform", "translate(%s,%s)" % (rect_width/2+rect_gap+text_width/2, 0))

                location.y += config.cfg['invert-y']*(rect_height+rect_gap)

            location.y += config.cfg['invert-y']*(rect_height+rect_gap*2)
                




    def _placeDrillIndex(self):
        """
        Adds a drill index
        """

        # Get the drills sheet / SVG layer
        drill_layer = self._layers['drills']['layer']
        ns = {'pcbmode':config.cfg['ns']['pcbmode'],
              'svg':config.cfg['ns']['svg']}
        drills = drill_layer.findall(".//*[@pcbmode:diameter]", namespaces=ns)

        drills_dict = {}
        largest_drill = 0
        drill_count = 0
        for drill in drills:
            diameter = drill.get('{'+config.cfg['ns']['pcbmode']+'}diameter')
            diameter = round(float(diameter), 2)
            if diameter not in drills_dict:
                drills_dict[diameter] = 1
            else:
                drills_dict[diameter] += 1
            if diameter > largest_drill:
                largest_drill = diameter
            drill_count += 1


        # Get location, or generate one
        try:
            location = config.brd['drill-index']['location']
        except:
            # If not location is specified, put the drill index at the
            # bottom left of the board. The 'gap' defines the extra
            # spcae between the top of the largest drill and the
            # board's edge
            gap = 2
            location = [-self._width/2, -(self._height/2+gap)]
        location = utils.toPoint(location)        

        # Create group for placing index
        transform = "translate(%s,%s)" % (location.x, config.cfg['invert-y']*location.y)
        group = et.SubElement(drill_layer, 'g',
                              transform=transform)
        group.set('{'+config.cfg['ns']['pcbmode']+'}type', 'drill-index')
        

        text_style_dict = config.stl['layout']['drill-index'].get('text')
        text_style = utils.dict_to_style(text_style_dict)
 
        count_style_dict = config.stl['layout']['drill-index'].get('count-text')
        count_style = utils.dict_to_style(count_style_dict)        

        count_style_dict['font-size'] /= 2
        drill_size_style = utils.dict_to_style(count_style_dict)

        if drill_count == 0:
            text = 'No drills'
        elif drill_count == 1:
            text = '1 drill: '
        else:
            text = '%s drills: ' % drill_count
        t = et.SubElement(group, 'text',
                          x=str(0),
                          y=str(0),
                          style=text_style)
        t.text = text

        # "new line"
        location.y = -(largest_drill/2 + 0.5)
        location.x = largest_drill/2

        gap = 2

        for diameter in reversed(sorted(drills_dict)):
            path = svg.drillPath(diameter)
            transform = "translate(%s,%s)" % (location.x, config.cfg['invert-y']*location.y)
            element = et.SubElement(group, 'path',
                                    d=path,
                                    transform=transform)
            element.set("fill-rule", "evenodd")

            t = et.SubElement(group, 'text',
                              x=str(location.x),
                              y=str(-location.y),
                              dy="%s" % (config.cfg['invert-y']*0.25),
                              style=count_style)
            t.text = str(drills_dict[diameter])

            t = et.SubElement(group, 'text',
                              x=str(location.x),
                              y=str(-location.y),
                              dy="%s" % (config.cfg['invert-y']*-0.5),
                              style=drill_size_style)
            t.text = "%s mm" % diameter

            location.x += max(diameter, 2.5) 






    def _getModuleElement(self):
        """
        Returns the skelaton of an Inkscape SVG element
        """
        module = et.Element('svg',
                            width="%s%s" % (self._width, config.brd['config']['units']),
                            height="%s%s" % (self._height, config.brd['config']['units']),
                            viewBox='%s, %s, %s, %s' % (0, 0, self._width, self._height),
                            version='1.1',
                            nsmap=config.cfg['ns'],
                            fill='black')
        
        # Set Inkscape options tag
        inkscape_opt = et.SubElement(module,
                                     '{'+config.cfg['ns']['sodipodi']+'}%s' % 'namedview',
                                     id="namedview-pcbmode",
                                     showgrid="true")
       
        # Add units definition (only 'mm' is supported)
        inkscape_opt.set('{'+config.cfg['ns']['inkscape']+'}%s' % 'document-units',
                         config.brd['config']['units'])
       
        # Open window maximised
        inkscape_opt.set('{'+config.cfg['ns']['inkscape']+'}%s' % 'window-maximized',
                         '1')
       
        # Define a grid 
        et.SubElement(inkscape_opt, '{'+config.cfg['ns']['inkscape']+'}%s' % 'grid',
                      type="xygrid",
                      id="pcbmode-grid",
                      visible="true",
                      enabled="false",
                      units="mm",
                      emspacing="5",
                      spacingx="0.1mm",
                      spacingy="0.1mm")
       
        # Add a welcome message as a comment in the SVG
        welcome_message = """
Hello! This SVG file was generated using PCBmodE version %s on %s GMT. 
PCBmodE is open source software, found here:

  http://bitbucket.org/boldport/pcbmode

and is maintained by Boldport:

  http://boldport.com

""" % (config.cfg['version'], datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")) 
        module.append(et.Comment(welcome_message))

        return module





    def _getComponents(self, components_dict):
        """
        Create the components for this module.
        Return a list of items of class 'component'
        """

        # Store components here
        components = []

        # Get shapes for each component definition
        for refdef in components_dict:
            component_dict = components_dict[refdef]
            show = component_dict.get('show', True)
            if show == True:
                component = Component(refdef, component_dict)
                components.append(component)
        
        return components





    def _getOutline(self):
        """
        Process the module's outline shape. Modules don't have to have an outline
        defined, so in that case return None.
        """
        shape = None

        outline_dict = self._module_dict.get('outline')
        if outline_dict != None:
            shape_dict = outline_dict.get('shape')
            if shape_dict != None:
                shape = Shape(shape_dict)
                style = Style(shape_dict, 'outline')
                shape.setStyle(style)

        return shape




