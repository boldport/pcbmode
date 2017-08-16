#!/usr/bin/python
# coding=utf-8

from lxml import etree as et

import pcbmode.config as config
from pcbmode.utils import svg, utils


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
        translate = 'translate(%s,%s)' % (round((((1, -1)[invert]) * location.x), sig_dig),
                                          round(location.y * config.cfg['invert-y'], sig_dig))
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
    element.set('{' + config.cfg['ns']['pcbmode'] + '}style', style_type)

    if transform != None:
        element.set('transform', transform)

    if gerber_lp != None:
        element.set('{' + config.cfg['ns']['pcbmode'] + '}gerber-lp', gerber_lp)

    if shape.getType() == 'text':
        element.set('{' + config.cfg['ns']['pcbmode'] + '}text', shape.getText())

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
    transform = 'translate(%s %s)' % (round((location.x + offset.x) * scale, sig_dig),
                                      round((-location.y - offset.y) * scale, sig_dig))

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
                                      style=MASK_STYLE % str(pour_buffer * 2),
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
            text_style['font-size'] = str(diameter / 10.0) + 'px'
            text_style = utils.dict_to_style(text_style)
            t = et.SubElement(layer, 'text',
                              x=str(location.x),
                              # TODO: get rid of this hack
                              y=str(-location.y - (diameter / 4)),
                              style=text_style)
            t.text = text

    # place soldermask unless specified otherwise
    # default is 'yes'
    add_soldermask = drill.get('add_soldermask') or 'yes'
    style = utils.dict_to_style(config.stl['layout']['soldermask'].get('fill'))
    possible_answers = ['yes', 'top', 'top only', 'bottom', 'bottom only', 'top and bottom']
    if (add_soldermask.lower() in possible_answers) and (soldermask_layers != {}):
        # TODO: get this into a configuration parameter
        drill_soldermask_scale_factors = drill.get('soldermask_scale_factors') or {'top': 1.2, 'bottom': 1.2}
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
            print("ERROR: unrecognised drills soldermask option")

    return
