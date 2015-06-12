#!/usr/bin/python

#import json
import os
#import re
#import subprocess as subp # for shell commands
#import math
#from operator import itemgetter # for sorting lists by dict value
#import HTMLParser # required for HTML to unicode translation
#from lxml import etree as et

import config

# pcbmode modules
#from point import Point
#from svgpath import SvgPath
import utils as utils
import messages as msg
#import hashlib



def create_bom():
    """
    
    """

    components_dict = config.brd['components']
    
    bom_dict = {}

    for refdef in components_dict:
        place = components_dict.get('place', True)

        # If component isn't placed, ignore it
        if place == True:

            # Get footprint definition and shapes
            try:
                footprint_name = components_dict[refdef]['footprint']
            except:
                msg.error("Cannot find a 'footprint' name for refdef %s." % refdef)
            
            # Open footprint file
            fname = os.path.join(config.cfg['base-dir'],
                                 config.cfg['locations']['components'],
                                 footprint_name + '.json')
            footprint_dict = utils.dictFromJsonFile(fname)

            info_dict = footprint_dict.get('info') or {}

            try: 
                comp_bom_dict = components_dict[refdef]['bom']
            except:
                comp_bom_dict = {}

            try: 
                fp_bom_dict = footprint_dict['info']
            except:
                fp_bom_dict = {}


            # Override component BoM info on top of footprint info
            for key in comp_bom_dict:
                fp_bom_dict[key] = comp_bom_dict[key]

            description = fp_bom_dict.get('description') or 'Uncategorised'

            if description not in bom_dict:
                bom_dict[description] = fp_bom_dict
                bom_dict[description]['refdefs'] = []
            bom_dict[description]['refdefs'].append(refdef)
            
            bom_dict[description]['placement'] = components_dict[refdef]['layer']
    

    try:
        bom_content = config.brd['bom']
    except:
        bom_content = [
            {
              "field": "line-item",
              "text": "#"
            },
            {
              "field": "quantity",
              "text": "qty"
            },
            {
              "field": "designators",
               "text": "designators"
            }, 
            {
              "field": "description",
              "text": "description"
            }, 
            {
              "field": "package",
              "text": "package"
            }, 
            {
              "field": "manufacturer",
              "text": "manuf."
            }, 
            {
              "field": "manufacturer-part-number",
              "text": "manuf. part #"
            },
            {
              "field": "suppliers",
              "text": "suppliers",
              "suppliers": 
              [
                {
                  "field": "farnell",
                  "text": "Farnell"
                },
                { 
                  "field": "mouser",
                  "text": "Mouser"
                }
              ]
            }, 
            {
              "field": "placement",
              "text": "layer"
            }, 
            {
              "field": "notes",
              "text": "notes"
            }
          ]



    # Set up the BoM file name
    bom_path = os.path.join(config.cfg['base-dir'],
                            config.cfg['locations']['build'],
                            'bom')
    # Create path if it doesn't exist already
    utils.create_dir(bom_path)

    board_name = config.cfg['name']
    board_revision = config.brd['config'].get('rev')
    base_name = "%s_rev_%s" % (board_name, board_revision)

    bom_html = os.path.join(bom_path, base_name + '_%s.html'% 'bom')
    bom_csv = os.path.join(bom_path, base_name + '_%s.csv'% 'bom')


    html = []
    csv = []


    html.append('<html>')
    html.append('<style type="text/css">')
    try:
        css = config.stl['layout']['bom']['css']
    except:
        css = []
    for line in css:
        html.append(line)
    html.append('</style>')
    html.append('<table class="tg">')

    header = []
    for item in bom_content:
        if item['field'] == 'suppliers':
            for supplier in item['suppliers']:
                header.append("%s" % supplier['text'])
        else:
            header.append("%s" % item['text'])

    html.append('  <tr>')
    html.append('    <th class="tg-title" colspan="%s">Bill of materials -- %s rev %s</th>' % (len(header), board_name, board_revision))
    html.append('  </tr>') 
    html.append('  <tr>')
    for item in header:
        html.append('    <th class="tg-header">%s</th>' % item)
    html.append('  </tr>')
    

    for i, desc in enumerate(bom_dict):
        content = []
        for item in bom_content:
            if item['field'] == 'line-item':
                content.append(str(i+1))
            elif item['field'] == 'suppliers':
                for supplier in item['suppliers']:
                    try:
                        content.append(bom_dict[desc][item['field']][supplier['field']])
                    except:
                        content.append("")
            elif item['field'] == 'quantity':
                content.append("%s" % (str(len(bom_dict[desc]['refdefs']))))
            elif item['field'] == 'designators':
                refdefs = ''
                for refdef in bom_dict[desc]['refdefs'][:-1]:
                    refdefs += "%s " % refdef
                refdefs += "%s" % bom_dict[desc]['refdefs'][-1]
                content.append("%s " % refdefs)
            elif item['field'] == 'description':
                content.append("%s " % desc)
            else:
                try:
                    content.append(bom_dict[desc][item['field']])
                except:
                    content.append("")

        html.append('  <tr>')
        for item in content:
            html.append('    <td class="tg-item-%s">%s</td>' % (('odd','even')[i%2==0], item))
        html.append('  </tr>')

    html.append('</table>')
    html.append('</html>')

    with open(bom_html, "wb") as f:
        for line in html:
            f.write(line+'\n')

    
    #print bom_dict


