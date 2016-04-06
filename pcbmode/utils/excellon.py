#!/usr/bin/python

import os
import re
from lxml import etree as et

import pcbmode.config as config
from . import messages as msg

# pcbmode modules
from . import utils
from .point import Point



def makeExcellon(manufacturer='default'):
    """
    """

    ns = {'pcbmode':config.cfg['ns']['pcbmode'],
          'svg':config.cfg['ns']['svg']} 

    # Open the board's SVG
    svg_in = utils.openBoardSVG()
    drills_layer = svg_in.find("//svg:g[@pcbmode:sheet='drills']",
                               namespaces=ns)

    excellon = Excellon(drills_layer)

    # Save to file
    base_dir = os.path.join(config.cfg['base-dir'], 
                            config.cfg['locations']['build'], 
                            'production')
    base_name = "%s_rev_%s" % (config.brd['config']['name'],
                               config.brd['config']['rev'])

    filename_info = config.cfg['manufacturers'][manufacturer]['filenames']['drills']

    add = '_%s.%s' % ('drills',
                      filename_info['plated'].get('ext') or 'txt')
    filename = os.path.join(base_dir, base_name + add)

    with open(filename, "wb") as f:
        for line in excellon.getExcellon():
            f.write(line)





class Excellon():
    """
    """

    def __init__(self, svg):
        """
        """

        self._svg = svg

        self._ns = {'pcbmode':config.cfg['ns']['pcbmode'],
                    'svg':config.cfg['ns']['svg']} 

        # Get all drill paths except for the ones used in the
        # drill-index
        drill_paths = self._svg.findall(".//svg:g[@pcbmode:type='component-shapes']//svg:path",
                                     namespaces=self._ns)

        drills_dict = {}
        for drill_path in drill_paths:
            diameter = drill_path.get('{'+config.cfg['ns']['pcbmode']+'}diameter')
            location = self._getLocation(drill_path)
            if diameter not in drills_dict:
                drills_dict[diameter] = {}
                drills_dict[diameter]['locations'] = []
            drills_dict[diameter]['locations'].append(location)

        self._preamble = self._createPreamble()
        self._content = self._createContent(drills_dict)
        self._postamble = self._createPostamble()


    def getExcellon(self):
        return (self._preamble+
                self._content+
                self._postamble)



    def _createContent(self, drills):
        """
        """
        ex = []
        for i, diameter in enumerate(drills):
            # This is probably not necessary, but I'm not 100% certain
            # that if the item order of a dict is gurenteed. If not
            # the result can be quite devastating where drill
            # diameters are wrong!
            # Drill index must be greater than 0
            drills[diameter]['index'] = i+1
            ex.append("T%dC%s\n" % (i+1, diameter)) 

        ex.append('M95\n') # End of a part program header

        for diameter in drills:
            ex.append("T%s\n" % drills[diameter]['index'])
            for coord in drills[diameter]['locations']:
                ex.append(self._getPoint(coord))

        return ex



    def _createPreamble(self):
        """
        """
        ex = []
        ex.append('M48\n') # Beginning of a part program header
        ex.append('METRIC,TZ\n') # Metric, trailing zeros
        ex.append('G90\n') # Absolute mode
        ex.append('M71\n') # Metric measuring mode        
        return ex



    def _createPostamble(self):
        """
        """
        ex = []
        ex.append('M30\n') # End of Program, rewind
        return ex



    def _getLocation(self, path):
        """
        Returns the location of a path, factoring in all the transforms of
        its ancestors, and its own transform
        """

        location = Point()

        # We need to get the transforms of all ancestors that have
        # one in order to get the location correctly
        ancestors = path.xpath("ancestor::*[@transform]")
        for ancestor in ancestors:
            transform = ancestor.get('transform')
            transform_data = utils.parseTransform(transform)
            # Add them up
            location += transform_data['location']

        # Add the transform of the path itself
        transform = path.get('transform')
        if transform != None:
            transform_data = utils.parseTransform(transform)
            location += transform_data['location']        

        return location




    def _getPoint(self, point):
        """
        Converts a Point type into an Excellon coordinate
        """
        return "X%.6fY%.6f\n" % (point.x, -point.y)



