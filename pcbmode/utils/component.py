#!/usr/bin/python

import os

import pcbmode.config as config
import copy

# pcbmode modules
from . import utils
from . import messages as msg
from .shape import Shape
from .style import Style
from .footprint import Footprint



class Component():
    """
    """

    def __init__(self, refdef, component):
        """
        """

        self._refdef = refdef
        self._layer = component.get('layer') or 'top'

        self._rotate = component.get('rotate') or 0
        if self._layer=='bottom':
            self._rotate *= -1

        self._rotate_point = utils.toPoint(component.get('rotate-point') or [0, 0])
        self._scale = component.get('scale') or 1
        self._location = component.get('location') or [0, 0]

        # Get footprint definition and shapes
        try:
            self._footprint_name = component['footprint']
        except:
            msg.error("Cannot find a 'footprint' name for refdef %s." % refdef)

        filename = self._footprint_name + '.json'

        paths = [os.path.join(config.cfg['base-dir'],
                             config.cfg['locations']['shapes'],
                             filename),
                   os.path.join(config.cfg['base-dir'],
                             config.cfg['locations']['components'],
                             filename)]

        footprint_dict = None
        for path in paths:
            if os.path.isfile(path):
                footprint_dict = utils.dictFromJsonFile(path)
                break

        if footprint_dict == None:
            fname_list = ""
            for path in paths:
                fname_list += " %s" % path
            msg.error("Couldn't find shape file. Looked for it here:\n%s" % (fname_list))

        footprint = Footprint(footprint_dict)
        footprint_shapes = footprint.getShapes()

        #------------------------------------------------        
        # Apply component-specific modifiers to footprint
        #------------------------------------------------
        for sheet in ['conductor', 'soldermask', 'solderpaste', 'pours', 'silkscreen', 'assembly', 'drills']:
            for layer in config.stk['layer-names']:
                for shape in footprint_shapes[sheet].get(layer) or []:

                    # In order to apply the rotation we need to adust the location
                    shape.rotateLocation(self._rotate, self._rotate_point)

                    shape.transformPath(scale=self._scale,
                                        rotate=self._rotate,
                                        rotate_point=self._rotate_point,
                                        mirror=shape.getMirrorPlacement(),
                                        add=True)

        #-------------------------------------------------------------- 
        # Remove silkscreen and assembly shapes if instructed 
        #-------------------------------------------------------------- 
        # If the 'show' flag is 'false then remove these items from the
        # shapes dictionary 
        #--------------------------------------------------------------
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
                refdef_dict['value'] = refdef_dict.get('value') or refdef
                refdef_dict['font-family'] = (refdef_dict.get('font-family') or
                                              config.stl['layout'][sheet]['refdef'].get('font-family') or 
                                              config.stl['defaults']['font-family'])
                refdef_dict['font-size'] = (refdef_dict.get('font-size') or 
                                            config.stl['layout'][sheet]['refdef'].get('font-size') or 
                                            "2mm")
                refdef_shape = Shape(refdef_dict)

                refdef_shape.is_refdef = True
                refdef_shape.rotateLocation(self._rotate, self._rotate_point)
                style = Style(refdef_dict, sheet, 'refdef')
                refdef_shape.setStyle(style)

                # Add the refdef to the silkscreen/assembly list. It's
                # important that this is added at the very end since the
                # placement process assumes the refdef is last
                try:
                    footprint_shapes[sheet][layer]
                except:
                    footprint_shapes[sheet][layer] = []

                footprint_shapes[sheet][layer].append(refdef_shape)
                    

        #------------------------------------------------------
        # Invert layers
        #------------------------------------------------------
        # If the placement is on the bottom of the baord then we need
        # to invert the placement of all components. This affects the
        # surface laters but also internal layers

        if self._layer == 'bottom':
            layers = config.stk['layer-names']
           
            for sheet in ['conductor', 'pours', 'soldermask', 'solderpaste', 'silkscreen', 'assembly']:
                sheet_dict = footprint_shapes[sheet]
                sheet_dict_new = {}
                for i, pcb_layer in enumerate(layers):
                    try:
                        sheet_dict_new[layers[len(layers)-i-1]] = copy.copy(sheet_dict[pcb_layer])
                    except:
                        continue

                footprint_shapes[sheet] = copy.copy(sheet_dict_new)    

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
