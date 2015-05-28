#!/usr/bin/python

from lxml import etree as et

import config
import messages as msg

# pcbmode modules
import utils
import svg
from point import Point





def placeShape(shape, svg_layer, invert=False, original=False):
    """
    Places a shape or type 'Shape' onto SVG layer 'svg_layer'.
    'invert'  : placed path should be mirrored
    'original': use the original path, not the transformed one
    """

    sig_dig = config.cfg['significant-digits']

    style_string = shape.getStyleString()
    style_type = shape.getStyleType()
    gerber_lp = shape.getGerberLP()
    location = shape.getLocation()

    if original == False:
        translate = 'translate(%s,%s)' % (round((((1,-1)[invert])*location.x), sig_dig),
                                          round(location.y*config.cfg['invert-y'], sig_dig))
        transform = translate
    else:
        transform = None

    if invert == True:
        path = shape.getTransformedPath(True)
    else:
        if original == True:
            path = shape.getOriginalPath()
        else:
            path = shape.getTransformedPath()

    element = et.SubElement(svg_layer, 
                            'path',
                            d=path)
    # Set style string
    element.set('style', style_string)

    # Set style type in pcbmode namespace. This is later used to easliy
    # identify the type when the path is converted to Gerber format
    element.set('{'+config.cfg['ns']['pcbmode']+'}style', style_type)

    if transform != None:
        element.set('transform', transform)

    if gerber_lp != None:
        element.set('{'+config.cfg['ns']['pcbmode']+'}gerber-lp', gerber_lp)

    if shape.getType() == 'text':
        element.set('{'+config.cfg['ns']['pcbmode']+'}text', shape.getText())

    return element






def placeDrill(drill, 
               layer, 
               location, 
               scale, 
               soldermask_layers={}, 
               mask_groups={}):
    """
    Places the drilling point
    """

    diameter = drill.get('diameter')
    offset = utils.to_Point(drill.get('offset') or [0, 0]) 
    path = svg.drill_diameter_to_path(diameter)
    mask_path = svg.circle_diameter_to_path(diameter)

    sig_dig = config.cfg['significant-digits']
    #translate = str(round((location.x + offset.x)*scale, sig_dig))+' '+str(round((-location.y - offset.y)*scale, sig_dig))
    transform = 'translate(%s %s)' % (round((location.x + offset.x)*scale, sig_dig),
                                      round((-location.y - offset.y)*scale, sig_dig))

    drill_element = et.SubElement(layer, 'path',
                                  transform=transform,
                                  d=path,
                                  id='pad_drill',
                                  diameter=str(diameter))

    pour_buffer = 1.0
    try:
        pour_buffer = board_cfg['distances']['buffer_from_pour_to'].get('drill') or 1.0
    except:
        pass

    # add a mask buffer between pour and board outline
    if mask_groups != {}:
        for pcb_layer in surface_layers:
            mask_group = et.SubElement(mask_groups[pcb_layer], 'g',
                                            id="drill_masks")
            pour_mask = et.SubElement(mask_group, 'path',
                                      transform=transform,
                                      style=MASK_STYLE % str(pour_buffer*2),
                                      gerber_lp="c",
                                      d=mask_path)



    # place the size of the drill; id the drill element has a
    # "show_diameter": "no", then this can be suppressed
    # default to 'yes'
    show_diameter = drill.get('show_diameter') or 'yes'
    if show_diameter.lower() != 'no':
        text = "%s mm" % (str(diameter))
        text_style = config.stl['layout']['drills'].get('text') or None
        if text_style is not None:
            text_style['font-size'] = str(diameter/10.0)+'px'
            text_style = utils.dict_to_style(text_style)
            t = et.SubElement(layer, 'text',
                x=str(location.x),
                # TODO: get rid of this hack
                y=str(-location.y-(diameter/4)),
                style=text_style)
            t.text = text

    # place soldermask unless specified otherwise
    # default is 'yes'
    add_soldermask = drill.get('add_soldermask') or 'yes'
    style = utils.dict_to_style(config.stl['layout']['soldermask'].get('fill'))
    possible_answers = ['yes', 'top', 'top only', 'bottom', 'bottom only', 'top and bottom']
    if (add_soldermask.lower() in possible_answers) and (soldermask_layers != {}):
        # TODO: get this into a configuration parameter
        drill_soldermask_scale_factors = drill.get('soldermask_scale_factors') or {'top':1.2, 'bottom':1.2}
        path_top = svg.circle_diameter_to_path(diameter * drill_soldermask_scale_factors['top'])
        path_bottom = svg.circle_diameter_to_path(diameter * drill_soldermask_scale_factors['bottom'])

        if add_soldermask.lower() == 'yes' or add_soldermask.lower() == 'top and bottom':
            drill_element = et.SubElement(soldermask_layers['top'], 
                                          'path',
                                          transform=transform,
                                          style=style,
                                          d=path_top)
            drill_element = et.SubElement(soldermask_layers['bottom'], 
                                          'path',
                                          transform=transform,
                                          style=style,
                                          d=path_bottom)
        elif add_soldermask.lower() == 'top only' or add_soldermask.lower() == 'top':
            drill_element = et.SubElement(soldermask_layers['top'], 
                                          'path',
                                          transform=transform,
                                          style=style,
                                          d=path_top)
        elif add_soldermask.lower() == 'bottom only' or add_soldermask.lower() == 'bottom':
            drill_element = et.SubElement(soldermask_layers['bottom'], 
                                          'path',
                                          transform=transform,
                                          style=style,
                                          d=path_bottom)
        else:
            print "ERROR: unrecognised drills soldermask option"

    return






def place_text(cfg, text_element, layer, layer_name, mirror=False, additional_rotate=0):
    """
    Places a dict text element in the specified layer
    """

    sig_dig = cfg['pcbmode']['significant_digits']
    text_list = text_element.get('value')

    # Check if text is a string. Text fields used to be only a single line
    # are not a list of lines. So if the input is a string, we need to convert
    # into a single item list.
    # TODO: check if this can be removed after all designs have text input as a list
    if isinstance(text_list, basestring):
        text_list = [text_list]
        
    font = text_element.get('font')
    scale = text_element.get('scale') or text_element.get('scale') or 0.0009
    rotate = text_element.get('rotate') or 0
    rotate += additional_rotate
    location = utils.to_Point(text_element.get('location') or [0, 0])
    offset = utils.to_Point(text_element.get('offset') or [0, 0])
    location += offset
    if mirror is True:
        location.x = -location.x

    add_space = text_element.get('additional_space_between_glyphs') or 0
    style = text_element.get('style')
    gerber_lp = (text_element.get('gerber-lp') or 
                text_element.get('gerber_lp') or '')


    # create a group for the entire string
    string_group = et.SubElement(layer, 'g')
 
    # add the right style
    if style is not None:
        if style == 'outline':
            style = utils.dict_to_style(cfg['layout_style'][layer_name].get('outline'))
        elif style == 'fill':
            style = utils.dict_to_style(cfg['layout_style'][layer_name].get('fill'))
        else:
            print "ERROR: unrecognised style '%s' for text element" % style
    else:
        # default to fill
        style = utils.dict_to_style(cfg['layout_style'][layer_name].get('fill'))
 
    if style is not None:
        string_group.set('style', style)
 
    # place the glyphs' paths 


    line_number = 0

    for text in text_list:

        line_number += 1

        # get the slyphs for the text
        paths, text_width, text_height = glyphs.get_glyphs(cfg,
                                                           text, 
                                                           font, 
                                                           location,
                                                           scale,
                                                           line_number, # line number
                                                           rotate,
                                                           add_space)
     
   
        origin = utils.to_Point(paths[0]['location'])
     
        for path in paths:
     
            # TODO: hack?
            place = utils.to_Point(path['location'])
            d = place - origin
            d.rotate(rotate, Point())
            place = origin + d
     
            if mirror is True:
                path['d'] = svg.mirror_path_over_axis(path['d'], 'x', 0)
                place.x = -place.x
     
            transform = 'translate(%s %s)' % (round(place.x, sig_dig),
                                              round(-place.y, sig_dig))
            
            # add glyph
            subelement = et.SubElement(string_group,
                                       'path', 
                                       transform=transform, 
                                       d=path['d'],
                                       letter=path['symbol'],
                                       gerber_lp=path['gerber-lp'])

    return


def place_path_shape(cfg, shape, layer, layer_name, mirror=False):
    """
    Places a dict path shape definition in the specified layer
    """

    sig_dig = cfg['pcbmode']['significant_digits']

    path = shape.get('value')
    rotation = shape.get('rotate') or 0
    location = shape.get('location')
    scale = shape.get('scale') or 1
    style = shape.get('style')
    stroke_width = shape.get('stroke_width')
    gerber_lp = (shape.get('gerber_lp') or 
                 shape.get('gerber-lp'))

    translate = 'translate(' + str(round(location[0], sig_dig)) + ' ' + str(round(-location[1], sig_dig)) + ')'
    transform = translate

    # convert path to relative commands
    path = svg.absolute_to_relative_path(path)

    # get a path having an origin at the center of the shape
    # defined by the path
    d_width, d_height, path = svg.transform_path(path, True, scale, rotation, Point())

    if mirror is True:
        path = svg.mirror_path_over_axis(path, 'x', 0)

    subelement = et.SubElement(layer, 
                               'path', 
                               transform=transform, 
                               d=path)
    if gerber_lp is not None:
        subelement.set('{'+config.cfg['ns']['pcbmode']+'}gerber-lp', gerber_lp)


    # add the right style
    if style is not None:
        if style == 'outline':
            style = cfg['layout_style'][layer_name].get('outline')
            # if there's a stroke-width definition, then override the default
            if stroke_width is not None:
                style['stroke-width'] = str(stroke_width)
            style = utils.dict_to_style(style)
        elif style == 'fill':
            style = utils.dict_to_style(cfg['layout_style'][layer_name].get('fill'))
        else:
            print "ERROR: unrecognised style"
    else:
        # default to outline
        style = utils.dict_to_style(cfg['layout_style'][layer_name].get('outline'))
 
    if style is not None:
        subelement.set('style', style)

    return
