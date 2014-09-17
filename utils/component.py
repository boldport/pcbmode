#!/usr/bin/python

import os

import config
import messages as msg

# pcbmode modules
import utils
import messages as msg
from shape import Shape
from style import Style
from footprint import Footprint



class Component():
    """
    """

    def __init__(self, refdef, component):
        """
        """

        self._refdef = refdef
        self._layer = component.get('layer') or 'top'

        self._rotate = component.get('rotate') or 0
        self._rotate_point = utils.toPoint(component.get('rotate-point') or [0, 0])
        self._scale = component.get('scale') or 1
        self._location = component.get('location') or [0, 0]

        # Get footprint definition and shapes
        try:
            self._footprint_name = component['footprint']
        except:
            msg.error("Cannot find a 'footprint' name for refdef %s." % refdef)

        fname = os.path.join(config.cfg['base-dir'],
                             config.cfg['locations']['components'],
                             self._footprint_name + '.json')
        footprint_dict = utils.dictFromJsonFile(fname)
        footprint = Footprint(footprint_dict)
        footprint_shapes = footprint.getShapes()

        #------------------------------------------------        
        # Apply component-specific modifiers to footprint
        #------------------------------------------------
        for sheet in ['copper', 'soldermask', 'solderpaste', 'silkscreen', 'assembly', 'drills']:
            for layer in utils.getSurfaceLayers() + utils.getInternalLayers():
                for shape in footprint_shapes[sheet][layer]:
                    # In order to apply the rotation we need to adust the location
                    # of each element
                    shape.rotateLocation(self._rotate, self._rotate_point)

                    shape.transformPath(self._scale,
                                        self._rotate,
                                        self._rotate_point,
                                        False,
                                        True)


        #--------------------------------------
        # Remove silkscreen and assembly shapes
        #--------------------------------------
        for sheet in ['silkscreen','assembly']:
            
            try:
                shapes_dict = component[sheet].get('shapes') or {}
            except:
                shapes_dict = {}

            # If the setting is to not show silkscreen shapes for the
            # component, delete the shapes from the shapes' dictionary
            if shapes_dict.get('show') == False:
                for pcb_layer in utils.getSurfaceLayers():
                    footprint_shapes[sheet][pcb_layer] = []



        #----------------------------------------------------------
        # Add silkscreen and assembly reference designator (refdef)
        #----------------------------------------------------------
        for sheet in ['silkscreen','assembly']:
            
            try:
                refdef_dict = component[sheet].get('refdef') or {}
            except:
                refdef_dict = {}
     
            if refdef_dict.get('show') != False:
                layer = refdef_dict.get('layer') or 'top'
         
                # Rotate the refdef; if unspecified the rotation is the same as
                # the rotation of the component
                refdef_dict['rotate'] = refdef_dict.get('rotate') or 0
 
                # Sometimes you'd want to keep all refdefs at the same angle
                # and not rotated with the component
                if refdef_dict.get('rotate-with-component') != False:
                    refdef_dict['rotate'] += self._rotate

                refdef_dict['rotate-point'] = utils.toPoint(refdef_dict.get('rotate-point')) or self._rotate_point
     
                refdef_dict['location'] = refdef_dict.get('location') or [0, 0]
                refdef_dict['type'] = 'text'
                refdef_dict['value'] = refdef
                refdef_dict['font-family'] = (config.stl['layout'][sheet]['refdef'].get('font-family') or 
                                              config.stl['defaults']['font-family'])
                refdef_dict['font-size'] = (config.stl['layout'][sheet]['refdef'].get('font-size') or 
                                              "2mm")
                refdef_shape = Shape(refdef_dict)
                refdef_shape.is_refdef = True
                refdef_shape.rotateLocation(self._rotate, self._rotate_point)
                style = Style(refdef_dict, sheet, 'refdef')
                refdef_shape.setStyle(style)

                # Add the refdef to the silkscreen/assembly list. It's
                # important that this is added at the very end since the
                # plcament process assumes the refdef is that very 
                footprint_shapes[sheet][layer].append(refdef_shape)


        #------------------------------------------------------
        # Invert 'top' and 'bottom' if layer is on the 'bottom'
        #------------------------------------------------------
        if self._layer == 'bottom':
            layers = utils.getSurfaceLayers()
            layers_reversed = reversed(utils.getSurfaceLayers())
           
            for sheet in ['copper', 'soldermask', 'solderpaste', 'silkscreen', 'assembly']:
                sheet_dict = footprint_shapes[sheet]
                # TODO: this nasty hack won't work for more than two
                # layers, so when 2+ are supported this needs to be
                # revisited
                for i in range(0,len(layers)-1):
                    sheet_dict['temp'] = sheet_dict.pop(layers[i])
                    sheet_dict[layers[i]] = sheet_dict.pop(layers[len(layers)-1-i])
                    sheet_dict[layers[len(layers)-1-i]] = sheet_dict.pop('temp')

        self._footprint_shapes = footprint_shapes





    def getShapes(self):
        """
        """
        return self._footprint_shapes


    def getLocation(self):
        """
        """
        return self._location


    def getRefdef(self):
        return self._refdef


    def getPlacementLayer(self):
        return self._layer


    def getFootprintName(self):
        return self._footprint_name


    def getRotation(self):
        return self._rotate
