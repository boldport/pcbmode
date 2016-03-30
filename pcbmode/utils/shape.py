#!/usr/bin/python

import os
import copy
from lxml import etree as et

from pkg_resources import resource_exists, resource_filename

import pcbmode.config as config
import messages as msg

# import pcbmode modules
import utils as utils
import svg
from point import Point
from svgpath import SvgPath




class Shape():
    """
    """

    def __init__(self, shape):

        gerber_lp = None
        mirror = False

        self._shape_dict = shape

        # Invert rotation so it's clock-wise. Inkscape is counter-clockwise and
        # it's unclear to ma what's the "right" direction. clockwise makse more
        # sense to me. This should be the only place to make the change.
        self._inv_rotate = -1

        try:
            self._type = shape.get('type')
        except:
            msg.error("Shapes must have a 'type' defined")

        # A 'layer' type is a copy of the outline. Here we copy the
        # outline shape and override the type
        if self._type in ['layer']:
            self._shape_dict = config.brd['outline'].get('shape').copy()
            self._type = self._shape_dict.get('type')

        self._place_mirrored = shape.get('mirror') or False

        self._rotate = shape.get('rotate') or 0
        self._rotate *= self._inv_rotate
        self._rotate_point = shape.get('rotate-point') or Point(0,0)
        self._scale = shape.get('scale') or 1
        self._pour_buffer = shape.get('buffer-to-pour')

        # A general purpose label field; intended for use for pad
        # labels
        self._label = None

        if self._type in ['rect', 'rectangle']:
            path = svg.width_and_height_to_path(self._shape_dict['width'],
                                                self._shape_dict['height'],
                                                self._shape_dict.get('radii'))
        elif self._type in ['circ', 'circle', 'round']:
            path = svg.circle_diameter_to_path(self._shape_dict['diameter'])
        elif self._type in ['drill']:
            self._diameter = self._shape_dict['diameter']
            path = svg.drillPath(self._diameter)
        elif self._type in ['text', 'string']:
            try:
                self._text = self._shape_dict['value']
            except KeyError:
                msg.error("Could not find the text to display. The text to be displayed should be defined in the 'value' field, for example, 'value': 'DEADBEEF\\nhar\\nhar'")

            # Get the font's name
            font = self._shape_dict.get('font-family') or config.stl['layout']['defaults']['font-family']
            font_filename = "%s.svg" % font

            # Search for the font SVG in these paths
            paths = [os.path.join(config.cfg['base-dir'],
                                  config.cfg['locations']['fonts'],
                                  font_filename)]

            font_resource = ('pcbmode', '/'.join(['fonts',font_filename]))
            if resource_exists(*font_resource):
                paths.append(resource_filename(*font_resource))

            filenames = ''
            font_data = None
            for path in paths:
                filename = path
                filenames += "  %s \n" % filename
                if os.path.isfile(filename):
                    font_data = et.ElementTree(file=filename)
                    break

            if font_data == None:
                msg.error("Couldn't find style file %s. Looked for it here:\n%s" % (font_filename, filenames))

            try:
                fs = self._shape_dict['font-size']
            except:
                msg.error("A 'font-size' attribute must be specified for a 'text' type")

            ls = self._shape_dict.get('letter-spacing') or '0mm'
            lh = self._shape_dict.get('line-height') or fs

            font_size, letter_spacing, line_height = utils.getTextParams(fs,
                                                                         ls, 
                                                                         lh)

            # With the units-per-em we can figure out the scale factor
            # to use for the desired font size
            units_per_em = float(font_data.find("//n:font-face", namespaces={'n': config.cfg['namespace']['svg']}).get('units-per-em')) or 1000
            self._scale = font_size/units_per_em

            # Get the path to use. This returns the path without
            # scaling, which will be applied later, in the same manner
            # as to the other shape types
            path, gerber_lp = utils.textToPath(font_data,
                                               self._text,
                                               letter_spacing,
                                               line_height,
                                               self._scale)
           
            # In the case where the text is an outline/stroke instead
            # of a fill we get rid of the gerber_lp
            if self._shape_dict.get('style') == 'stroke':
                gerber_lp = None

            self._rotate += 180

        elif self._type in ['path']:
            path = self._shape_dict.get('value')
        else:
            msg.error("'%s' is not a recongnised shape type" % self._type)


        self._path = SvgPath(path, gerber_lp)

        self._path.transform(scale=self._scale, 
                             rotate_angle=self._rotate, 
                             rotate_point=self._rotate_point, 
                             mirror=self._place_mirrored)

        self._gerber_lp = (shape.get('gerber-lp') or 
                           shape.get('gerber_lp') or 
                           gerber_lp or 
                           None)

        self._location = utils.toPoint(shape.get('location', [0, 0]))




    def transformPath(self, scale=1, rotate=0, rotate_point=Point(), mirror=False, add=False):
        if add == False:
            self._path.transform(scale,
                                 rotate*self._inv_rotate,
                                 rotate_point,
                                 mirror)
        else:
            self._path.transform(scale*self._scale,
                                 rotate*self._inv_rotate+self._rotate,
                                 rotate_point+self._rotate_point,
                                 mirror)



    def rotateLocation(self, angle, point=Point()):
        """
        """
        self._location.rotate(angle, point)


    def getRotation(self):
        return self._rotate



    def setRotation(self, rotate):
        self._rotate = rotate



    def getOriginalPath(self):
        """
        Returns that original, unmodified path
        """
        return self._path.getOriginal()



    def getTransformedPath(self, mirrored=False):
        if mirrored == True:
            return self._path.getTransformedMirrored()
        else:
            return self._path.getTransformed()



    def getWidth(self):
        return self._path.getWidth()



    def getHeight(self):
        return self._path.getHeight()



    def getGerberLP(self):
        return self._gerber_lp



    def setStyle(self, style):
        """
        style: Style object
        """
        self._style = style


    def getStyle(self):
        """
        Return the shape's style Style object
        """
        return self._style


    def getStyleString(self):
        style = self._style.getStyleString()
        return style


    def getStyleType(self):
        style = self._style.getStyleType()
        return style


    def getScale(self):
        return self._scale


    def getLocation(self):
        return self._location

  
    def setLocation(self, location):
        self._location = location


    def getParsedPath(self):
        return self._parsed


    def getPourBuffer(self):
        return self._pour_buffer

     
    def getType(self):
        return self._type


    def getText(self):
        return self._text


    def getDiameter(self):
        return self._diameter


    def setLabel(self, label):
        self._label = label


    def getLabel(self):
        return self._label


    def getMirrorPlacement(self):
        return self._place_mirrored
