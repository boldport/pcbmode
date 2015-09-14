#!/usr/bin/python

import os
import re
import json
from lxml import etree as et

import config
import messages as msg

# pcbmode modules
import svg 
import utils
import place
import copy
from style import Style
from point import Point
from shape import Shape



class Footprint():
    """
    """

    def __init__(self, footprint):

        self._footprint = footprint

        

        self._shapes = {'conductor': {},
                        'pours': {},
                        'soldermask': {},
                        'silkscreen': {},
                        'assembly': {},
                        'solderpaste': {},
                        'drills': {}}

        self._processPins()
        self._processPours()
        self._processSilkscreenShapes()
        self._processAssemblyShapes()




    def getShapes(self):
        return self._shapes



    def _processPins(self):
        """
        Converts pins into 'shapes'
        """

        pins = self._footprint.get('pins') or {}

        for pin in pins:

            pin_location = pins[pin]['layout']['location'] or [0, 0]

            try:
                pad_name = pins[pin]['layout']['pad']
            except:
                msg.error("Each defined 'pin' must have a 'pad' name that is defined in the 'pads' dection of the footprint.")

            try:
                pad_dict = self._footprint['pads'][pad_name]
            except:
                msg.error("There doesn't seem to be a pad definition for pad '%s'." % pad_name)

            # Get the pin's rotation, if any
            pin_rotate = pins[pin]['layout'].get('rotate') or 0

            shapes = pad_dict.get('shapes') or []

            for shape_dict in shapes:

                shape_dict = shape_dict.copy()

                # Which layer(s) to place the shape on
                layers = utils.getExtendedLayerList(shape_dict.get('layers') or ['top'])

                # Add the pin's location to the pad's location
                shape_location = shape_dict.get('location') or [0, 0]
                shape_dict['location'] = [shape_location[0] + pin_location[0],
                                          shape_location[1] + pin_location[1]]

                # Add the pin's rotation to the pad's rotation
                shape_dict['rotate'] = (shape_dict.get('rotate') or 0) + pin_rotate

                # Determine if and which label to show
                show_name = pins[pin]['layout'].get('show-label') or True
                if show_name == True:
                    pin_label = pins[pin]['layout'].get('label') or pin

                for layer in layers:
                    
                    shape = Shape(shape_dict)
                    style = Style(shape_dict, 'conductor')
                    shape.setStyle(style)
                    try:
                        self._shapes['conductor'][layer].append(shape)
                    except:
                        self._shapes['conductor'][layer] = []
                        self._shapes['conductor'][layer].append(shape)
                        
                    for stype in ['soldermask', 'solderpaste']:

                        # Get a custom shape specification if it exists
                        sdict_list = shape_dict.get(stype) 

                        # No defined; default
                        if sdict_list == None:
                            # Use default settings for shape based on
                            # the pad shape
                            sdict = shape_dict.copy()

                            # Which shape type is the pad?
                            shape_type = shape.getType()

                            # Apply modifier based on shape type
                            if shape_type == 'path':
                                sdict['scale'] = shape.getScale()*config.brd[stype]['path-scale']
                            elif shape_type in ['rect', 'rectangle']:
                                sdict['width'] += config.brd[stype]['rect-buffer']
                                sdict['height'] += config.brd[stype]['rect-buffer']
                            elif shape_type in ['circ', 'circle']:
                                sdict['diameter'] += config.brd[stype]['circle-buffer']
                            else:
                                pass
     
                            # Create shape based on new dictionary
                            sshape = Shape(sdict)

                            # Define style
                            sstyle = Style(sdict, stype)

                            # Aplpy style
                            sshape.setStyle(sstyle)

                            # Add shape to footprint's shape dictionary
                            #self._shapes[stype][layer].append(sshape)
                            try:
                                self._shapes[stype][layer].append(shape)
                            except:
                                self._shapes[stype][layer] = []
                                self._shapes[stype][layer].append(shape)


                        # Do not place shape
                        elif (sdict_list == {}) or (sdict_list == []):
                            pass

                        # Custom shape definition
                        else:

                            # If dict (as before support of multiple
                            # shapes) then append to a single element
                            # list
                            if type(sdict_list) is dict:
                                sdict_list = [sdict_list]

                            # Process list of shapes
                            for sdict in sdict_list:
                                sdict = sdict.copy()
                                shape_loc = utils.toPoint(sdict.get('location') or [0, 0])

                                # Apply rotation
                                sdict['rotate'] = (sdict.get('rotate') or 0) + pin_rotate

                                # Rotate location
                                shape_loc.rotate(pin_rotate, Point())

                                sdict['location'] = [shape_loc.x + pin_location[0],
                                                     shape_loc.y + pin_location[1]]

                                # Create new shape
                                sshape = Shape(sdict)
     
                                # Create new style
                                sstyle = Style(sdict, stype)
                                
                                # Apply style
                                sshape.setStyle(sstyle)
     
                                # Add shape to footprint's shape dictionary
                                #self._shapes[stype][layer].append(sshape)
                                try:
                                    self._shapes[stype][layer].append(shape)
                                except:
                                    self._shapes[stype][layer] = []
                                    self._shapes[stype][layer].append(shape)

     
                    # Add pin label
                    if (pin_label != None):
                        shape.setLabel(pin_label)




            drills = pad_dict.get('drills') or []
            for drill_dict in drills:
                drill_dict = drill_dict.copy()
                drill_dict['type'] = drill_dict.get('type') or 'drill'
                drill_location = drill_dict.get('location') or [0, 0]
                drill_dict['location'] = [drill_location[0] + pin_location[0],
                                          drill_location[1] + pin_location[1]]
                shape = Shape(drill_dict)
                style = Style(drill_dict, 'drills')
                shape.setStyle(style)
                try:
                    self._shapes['drills']['top'].append(shape)
                except:
                    self._shapes['drills']['top'] = []
                    self._shapes['drills']['top'].append(shape)
                        




    def _processPours(self):
        """
        """

        try:
            shapes = self._footprint['layout']['pours']['shapes']
        except:
            return        

        for shape_dict in shapes:
            layers = utils.getExtendedLayerList(shape_dict.get('layers') or ['top'])
            for layer in layers:
                shape = Shape(shape_dict)
                style = Style(shape_dict, 'conductor', 'pours')
                shape.setStyle(style)

                try:
                    self._shapes['pours'][layer].append(shape)
                except:
                    self._shapes['pours'][layer] = []
                    self._shapes['pours'][layer].append(shape)





    def _processSilkscreenShapes(self):
        """
        """
        try:
            shapes = self._footprint['layout']['silkscreen']['shapes']
        except:
            return

        for shape_dict in shapes:
            layers = utils.getExtendedLayerList(shape_dict.get('layers') or ['top'])
            for layer in layers:
                shape = Shape(shape_dict)
                style = Style(shape_dict, 'silkscreen')
                shape.setStyle(style)
                try:
                    self._shapes['silkscreen'][layer].append(shape)
                except:
                    self._shapes['silkscreen'][layer] = []
                    self._shapes['silkscreen'][layer].append(shape)





    def _processAssemblyShapes(self):
        """
        """
        try:
            shapes = self._footprint['layout']['assembly']['shapes']
        except:
            return

        for shape_dict in shapes:
            layers = utils.getExtendedLayerList(shape_dict.get('layer') or ['top'])
            for layer in layers:
                shape = Shape(shape_dict)
                style = Style(shape_dict, 'assembly')
                shape.setStyle(style)
                try:
                    self._shapes['assembly'][layer].append(shape)
                except:
                    self._shapes['assembly'][layer] = []
                    self._shapes['assembly'][layer].append(shape)



