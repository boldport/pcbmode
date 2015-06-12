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


    # Output header
    length = 20
    for item in bom_content:
        if item['field'] == 'suppliers':
            for supplier in item['suppliers']:
                print "%s" % (supplier['text']).ljust(length),
        else:
            print "%s" % (item['text']).ljust(length),
    print

    for i, desc in enumerate(bom_dict):
        for item in bom_content:
            if item['field'] == 'line-item':
                print i+1,
            elif item['field'] == 'suppliers':
                for supplier in item['suppliers']:
                    try:
                        print bom_dict[desc][item['field']][supplier['field']].ljust(length),
                    except:
                        print "".ljust(length),
            elif item['field'] == 'quantity':
                print "%s" % (str(len(bom_dict[desc]['refdefs']))).ljust(length),
            elif item['field'] == 'designators':
                for refdef in bom_dict[desc]['refdefs']:
                    print "%s " % refdef,
            elif item['field'] == 'description':
                print "%s " % desc,
            else:
                try:
                    print bom_dict[desc][item['field']].ljust(length),
                except:
                    print "".ljust(length),
        print

    print
    
    #print bom_dict


