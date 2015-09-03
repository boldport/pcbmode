#!/usr/bin/python

import json
import os
import re
import subprocess as subp # for shell commands
import math
from operator import itemgetter # for sorting lists by dict value
import HTMLParser # required for HTML to unicode translation
from lxml import etree as et

import config

# pcbmode modules
from point import Point
from svgpath import SvgPath
import messages as msg
import hashlib



def dict_to_style(style_dict):
    """
    Convert a dictionary into an SVG/CSS style attribute
    """

    style = None

    if style_dict is not None:
        style = ''
        for key in style_dict:
            style += "%s:%s;" % (key, style_dict[key])

    return style




def dictToStyleText(style_dict):
    """
    Convert a dictionary into an SVG/CSS style attribute
    """

    style = None

    if style_dict is not None:
        style = ''
        for key in style_dict:
            style += "%s:%s;" % (key, style_dict[key])

    return style




def openBoardSVG():
    """
    Opens the built PCBmodE board SVG.
    Returns an ElementTree object
    """

    filename = os.path.join(config.cfg['base-dir'],
                            config.cfg['locations']['build'],
                            config.cfg['name'] + '.svg')
    try:
        data = et.ElementTree(file=filename) 
    except IOError as e:
        msg.error("Cannot open %s; has the board been made using the '-m' option yet?" % filename)

    return data






def parseDimension(string):
    """
    Parses a dimention recieved from the source files, separating the units,
    if specified, from the value
    """
    if string != None:
        result = re.match('(-?\d*\.?\d+)\s?(\w+)?', string)
        value = float(result.group(1))
        unit = result.group(2)
    else:
        value = None
        unit = None
    return value, unit




def to_Point(coord=[0, 0]):
    """
    Takes a coordinate in the form of [x,y] and
    returns a Point type
    """
    return Point(coord[0], coord[1])




def toPoint(coord=[0, 0]):
    """
    Takes a coordinate in the form of [x,y] and
    returns a Point type
    """
    if coord == None:
        return None
    else:
        return Point(coord[0], coord[1])





def get_git_revision():

    path = os.path.dirname(os.path.realpath(__file__))
    command = [path, 'git', 'describe', '--tags', '--long']

    try:
        rev = subp.check_output(command)
    except:
        rev = 'unknown'

    return rev






def makePngs():
    """
    Creates a PNG of the board using Inkscape
    """

    # Directory for storing the Gerbers within the build path
    images_path = os.path.join(config.cfg['base-dir'], 
                               config.cfg['locations']['build'], 
                               'images')
    # Create it if it doesn't exist
    create_dir(images_path)

    # create individual PNG files for layers
    png_dpi = 600
    msg.subInfo("Generating PNGs for each layer of the board")

    command = ['inkscape', 
               '--without-gui', 
               '--file=%s' % os.path.join(config.cfg['base-dir'], 
                                          config.cfg['locations']['build'], 
                                          config.cfg['name'] + '.svg'), 
               '--export-png=%s' % os.path.join(images_path, config.cfg['name'] + '_rev_' + 
                                                config.brd['config']['rev'] +
                                                '.png'),
               '--export-dpi=%s' % str(png_dpi),
               '--export-area-drawing',
               '--export-background=#FFFFFF']
    
    try:
        subp.call(command)
    except OSError as e:
        msg.error("Cannot find, or run, Inkscape in commandline mode")

    return





# get_json_data_from_file
def dictFromJsonFile(filename, error=True):
    """
    Open a json file and returns its content as a dict
    """

    def checking_for_unique_keys(pairs):
        """
        Check if there are duplicate keys defined; this is useful
        for any hand-edited file
  
        This SO answer was useful here:
          http://stackoverflow.com/questions/16172011/json-in-python-receive-check-duplicate-key-error
        """
        result = dict()
        for key,value in pairs:
            if key in result:
                msg.error("duplicate key ('%s') specified in %s" % (key, filename), KeyError)
            result[key] = value
        return result

    try:
        with open(filename, 'rb') as f:
            json_data = json.load(f, object_pairs_hook=checking_for_unique_keys)
    except IOError, OSError:
        if error == True:
            msg.error("Couldn't open JSON file: %s" % filename, IOError)
        else:
            msg.info("Couldn't open JSON file: %s" % filename, IOError)

    return json_data




def getLayerList():
    """
    """
    layer_list = []
    for record in config.stk['stackup']:
        if record['type'] == 'signal-layer-surface' or record['type'] == 'signal-layer-internal':
            layer_list.append(record)

    layer_names = []
    for record in layer_list:
        layer_names.append(record['name'])

    return layer_list, layer_names



def getSurfaceLayers():
    """
    Returns a list of surface layer names
    Only here until this function is purged from the
    codebase
    """    
    return config.stk['surface-layers-names']




def getInternalLayers():
    """
    Returns a list of internal layer names
    Only here until this function is purged from the
    codebase
    """    
    return config.stk['internal-layers-names']





def create_dir(path):
    """
    Checks if a directory exists, and creates one if not
    """
    
    try:
        # try to create directory first; this prevents TOCTTOU-type race condition
        os.makedirs(path)
    except OSError:
        # if the dir exists, pass
        if os.path.isdir(path):
            pass
        else:
            print "ERROR: couldn't create build path %s" % path
            raise

    return





def add_dict_values(d1, d2):
    """
    Add the values of two dicts
    Helpful code here:
      http://stackoverflow.com/questions/1031199/adding-dictionaries-in-python
    """

    return dict((n, d1.get(n, 0)+d2.get(n, 0)) for n in set(d1)|set(d2) )






def process_meander_type(type_string, meander_type):
    """
    Extract meander path type parameters and return them as a dict
    """

    if (meander_type == 'meander-round'):
        look_for = ['radius', 'theta', 'bus-width', 'pitch']
    elif (meander_type == 'meander-sawtooth'):
        look_for = ['base-length', 'amplitude', 'bus-width', 'pitch']
    else:
        print "ERROR: unrecognised meander type"
        reaise

    meander = {}

    regex = '\s*%s\s*:\s*(?P<v>[^;]*)'

    for param in look_for:
        tmp = re.search(regex % param, type_string)
        if tmp is not None:
            meander[param] = float(tmp.group('v'))

    # add optional fields as 'None'
    for param in look_for:    
        if meander.get(param) is None:
            meander[param] = None

    return meander





# there_are_pours_in_this_layer
def checkForPoursInLayer(layer):
    """
    Returns True or False if there are pours in the specified layer
    """

    # In case there are no 'shapes' defined
    try:
        pours = config.brd['shapes'].get('pours')
    except:
        pours = {}

    if pours is not None:
        for pour_dict in pours:
            layers = pour_dict.get('layers')
            if layer in layers:
                return True
 
    return False
  




def interpret_svg_matrix(matrix_data):
    """
    Takes an array for six SVG parameters and returns angle, scale 
    and placement coordinate

    This SO answer was helpful here:
      http://stackoverflow.com/questions/15546273/svg-matrix-to-rotation-degrees
    """

    # apply float() to all elements, just in case
    matrix_data = [ float(x) for x in matrix_data ]

    coord = Point(matrix_data[4], -matrix_data[5])
    if matrix_data[0] == 0:
        angle = math.degrees(0)
    else:
        angle = math.atan(matrix_data[2] / matrix_data[0])
    
    scale = Point(math.fabs(matrix_data[0] / math.cos(angle)), 
                  math.fabs(matrix_data[3] / math.cos(angle)))

    # convert angle to degrees
    angle = math.degrees(angle)

    # Inkscape rotates anti-clockwise, PCBmodE "thinks" clockwise. The following 
    # adjusts these two views, although at some point we'd
    # need to have the same view, or make it configurable
    angle = -angle

    return coord, angle, scale






def parse_refdef(refdef):
    """
    Parses a reference designator and returns the refdef categoty,
    number, and extra characters
    """

    regex = r'^(?P<t>[a-zA-z\D]+?)(?P<n>\d+)(?P<e>[\-\s].*)?'
    parse = re.match(regex, refdef)

    # TODO: there has to be a more elegant way for doing this!
    if parse == None:
        return None, None, None
    else:
        t = parse.group('t')
        n = int(parse.group('n'))
        e = parse.group('e')
        return t, n, e
    





#def renumber_refdefs(cfg, order):
def renumberRefdefs(order):
    """
    Renumber the refdefs in the specified order
    """

    components = config.brd['components']
    comp_dict = {}
    new_dict = {}

    for refdef in components:

        rd_type, rd_number, rd_extra = parse_refdef(refdef)
        location = to_Point(components[refdef].get('location') or [0, 0])
        tmp = {}
        tmp['record'] = components[refdef]
        tmp['type'] = rd_type
        tmp['number'] = rd_number
        tmp['extra'] = rd_extra
        tmp['coord-x'] = location.x
        tmp['coord-y'] = location.y

        if comp_dict.get(rd_type) == None:
            comp_dict[rd_type] = []
        comp_dict[rd_type].append(tmp)

        # Sort list according to 'order'
        for comp_type in comp_dict:
           if order == 'left-to-right':
               reverse = False
               itemget_param = 'coord_x'
           elif order == 'right-to-left':
               reverse = True
               itemget_param = 'coord_x'
           elif order == 'top-to-bottom':
               reverse = True
               itemget_param = 'coord-y'
           elif order == 'bottom-to-top':
               reverse = False
               itemget_param = 'coord-y'
           else:
               msg.error('Unrecognised renumbering order %s' % (order)) 
 
           sorted_list = sorted(comp_dict[comp_type], 
                                key=itemgetter(itemget_param), 
                                reverse=reverse)


           for i, record in enumerate(sorted_list):
               new_refdef = "%s%s" % (record['type'], i+1)
               if record['extra'] is not None:
                   new_refdef += "%s" % (record['extra'])
               new_dict[new_refdef] = record['record']
 
    config.brd['components'] = new_dict

    # Save board config to file (everything is saved, not only the
    # component data)
    filename = os.path.join(config.cfg['locations']['boards'], 
                            config.cfg['name'], 
                            config.cfg['name'] + '.json')
    try:
        with open(filename, 'wb') as f:
            f.write(json.dumps(config.brd, sort_keys=True, indent=2))
    except:
        msg.error("Cannot save file %s" % filename)
 
 
    return






def getTextParams(font_size, letter_spacing, line_height):
    try:
        letter_spacing, letter_spacing_unit = parseDimension(letter_spacing)
    except:
        msg.error("There's a problem with parsing the 'letter-spacing' property with value '%s'. The format should be an integer or float followed by 'mm' (the only unit supported). For example, '0.3mm' or '-2 mm' should work." % letter_spacing)

    if letter_spacing_unit == None:
        letter_spacing_unit = 'mm'

    try:
        line_height, line_height_unit = parseDimension(line_height)
    except:
        msg.error("There's a problem parsing the 'line-height' property with value '%s'. The format should be an integer or float followed by 'mm' (the only unit supported). For example, '0.3mm' or '-2 mm' should work." % line_height)

    if line_height_unit == None:
        line_height_unit = 'mm'
    
    try:
        font_size, font_size_unit = parseDimension(font_size)
    except:
        throw("There's a problem parsing the 'font-size'. It's most likely missing. The format should be an integer or float followed by 'mm' (the only unit supported). For example, '0.3mm' or '2 mm' should work. Of course, it needs to be a positive figure.")

    if font_size_unit == None:
        font_size_unit = 'mm'

    return float(font_size), float(letter_spacing), float(line_height)




def textToPath(font_data, text, letter_spacing, line_height, scale_factor):
    """
    Convert a text string (unicode and newlines allowed) to a path.
    The 'scale_factor' is needed in order to scale rp 'letter_spacing' and 'line_height'
    to the original scale of the font.
    """

    # This the horizontal advance that applied to all glyphs unless there's a specification for
    # for the glyph itself
    font_horiz_adv_x = float(font_data.find("//n:font", namespaces={'n': config.cfg['namespace']['svg']}).get('horiz-adv-x'))
    
    # This is the number if 'units' per 'em'. The default, in the absence of a definition is 1000
    # according to the SVG spec
    units_per_em = float(font_data.find("//n:font-face", namespaces={'n': config.cfg['namespace']['svg']}).get('units-per-em')) or 1000

    glyph_ascent = float(font_data.find("//n:font-face", namespaces={'n': config.cfg['namespace']['svg']}).get('ascent'))
    glyph_decent = float(font_data.find("//n:font-face", namespaces={'n': config.cfg['namespace']['svg']}).get('descent'))
 
    text_width = 0
    text_path = ''

    # split text into charcters and find unicade chars
    try:
        text = re.findall(r'(\&#x[0-9abcdef]*;|.|\n)', text)
    except:
        throw("There's a problem parsing the text '%s'. Unicode and \\n newline should be fine, by the way." % text)
 

    # instantiate HTML parser
    htmlpar = HTMLParser.HTMLParser()
    gerber_lp = ''
    text_height = 0

    if line_height == None:
        line_height = units_per_em

    for i, symbol in enumerate(text[:]):

        symbol = htmlpar.unescape(symbol)
        # get the glyph definition from the file
        if symbol == '\n':
            text_width = 0
            text_height += units_per_em + (line_height/scale_factor-units_per_em)
        else:
            glyph = font_data.find(u'//n:glyph[@unicode="%s"]' % symbol, namespaces={'n': config.cfg['namespace']['svg']})
            if glyph == None:
                utils.throw("Damn, there's no glyph definition for '%s' in the '%s' font :(" % (symbol, font))
            else:
                # Unless the glyph has its own width, use the global font width
                glyph_width = float(glyph.get('horiz-adv-x') or font_horiz_adv_x)
                if symbol != ' ':
                    glyph_path = SvgPath(glyph.get('d'))
                    first_point = glyph_path.getFirstPoint()
                    offset_x = float(first_point[0])
                    offset_y = float(first_point[1])
                    path = glyph_path.getRelative()
                    path = re.sub('^(m\s?[-\d\.]+\s?,\s?[-\d\.]+)', 'M %s,%s' % (str(text_width+offset_x), str(offset_y-text_height)), path)
                    gerber_lp += (glyph.get('gerber-lp') or 
                                  glyph.get('gerber_lp') or 
                                  "%s" % 'd'*glyph_path.getNumberOfSegments())
                    text_path += "%s " % (path)

            text_width += glyph_width+letter_spacing/scale_factor


    # Mirror text 
    text_path = SvgPath(text_path)
    text_path.transform()
    text_path = text_path.getTransformedMirrored()

    return text_path, gerber_lp





def digest(string):
    digits = config.cfg['digest-digits']
    return hashlib.md5(string).hexdigest()[:digits-1]







def getStyleAttrib(style, attrib):
    """
    """
    regex = r".*?%s:\s?(?P<s>[^;]*)(?:;|$)"
    match = re.match(regex % attrib, style)
    if match == None:
        return None
    else:
        return match.group('s')





def parseTransform(transform):
    """
    Returns a Point() for the input transform
    """
    data = {}
    if 'translate' in transform.lower():
        regex = r".*?translate\s?\(\s?(?P<x>-?[0-9]*\.?[0-9]+)\s?[\s,]\s?(?P<y>-?[0-9]*\.?[0-9]+\s?)\s?\).*"
        coord = re.match(regex, transform)
        data['type'] = 'translate'
        data['location'] = Point(coord.group('x'),coord.group('y'))
    elif 'matrix' in transform.lower():
        data['type'] = 'matrix'
        data['location'], data['rotate'], data['scale'] = parseSvgMatrix(transform)
    else:
        msg.error("Found a path transform that cannot be handled, %s. SVG stansforms shouls be in the form of 'translate(num,num)' or 'matric(num,num,num,num,num,num)" % transform)

    return data 





def parseSvgMatrix(matrix):
    """
    Takes an array for six SVG parameters and returns angle, scale 
    and placement coordinate

    This SO answer was helpful here:
      http://stackoverflow.com/questions/15546273/svg-matrix-to-rotation-degrees
    """
    regex = r".*?matrix\((?P<m>.*?)\).*"
    matrix = re.match(regex, matrix)
    matrix = matrix.group('m')
    matrix = matrix.split(',')

    # Apply float() to all elements
    matrix = [ float(x) for x in matrix ]

    coord = Point(matrix[4], matrix[5])
    if matrix[0] == 0:
        angle = math.degrees(0)
    else:
        angle = math.atan(matrix[2] / matrix[0])
    
    #scale = Point(math.fabs(matrix[0] / math.cos(angle)), 
    #              math.fabs(matrix[3] / math.cos(angle)))
    scale_x = math.sqrt(matrix[0]*matrix[0] + matrix[1]*matrix[1]),
    scale_y = math.sqrt(matrix[2]*matrix[2] + matrix[3]*matrix[3]),    

    scale = max(scale_x, scale_y)[0]

    # convert angle to degrees
    angle = math.degrees(angle)

    # Inkscape rotates anti-clockwise, PCBmodE "thinks" clockwise. The following 
    # adjusts these two views, although at some point we'd
    # need to have the same view, or make it configurable
    angle = -angle

    return coord, angle, scale






