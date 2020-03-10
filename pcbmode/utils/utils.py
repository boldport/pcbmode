#!/usr/bin/python

# PCBmodE, a printed circuit design software with a twist
# Copyright (C) 2020 Saar Drimer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import json
import os
from pathlib import Path
import re
import subprocess as subp  # for shell commands
import math
from operator import itemgetter  # for sorting lists by dict value
import html.parser as HTMLParser
import hashlib

from pcbmode.config import config
from pcbmode.utils import css_utils
from pcbmode.utils.point import Point
from pcbmode.utils import messages as msg


def dictToStyleText(style_dict):
    """
    Convert a dictionary into an SVG/CSS style attribute
    """

    style = ""
    for key in style_dict:
        style += f"{key}:{style_dict[key]};"

    return style


def open_board_svg():
    """
    Opens the built PCBmodE board SVG.
    Returns an ElementTree object
    """

    filename = Path(
        config.tmp["project-path"] / config.brd["project-params"]["input"]["svg-file"]
    )

    try:
        data = et.ElementTree(file=str(filename))
    except IOError as e:
        msg.error(f"Cannot open {filename}; has the board SVG been created?")

    return data


def makePngs():
    """
    Creates a PNG of the board using Inkscape
    """

    # Directory for storing the Gerbers within the build path
    images_path = os.path.join(
        config.cfg["base-dir"], config.cfg["locations"]["build"], "images"
    )
    # Create it if it doesn't exist
    create_dir(images_path)

    # create individual PNG files for layers
    png_dpi = 600
    msg.subInfo("Generating PNGs for each layer of the board")

    command = [
        "inkscape",
        "--without-gui",
        "--file=%s"
        % os.path.join(
            config.cfg["base-dir"],
            config.cfg["locations"]["build"],
            config.cfg["name"] + ".svg",
        ),
        "--export-png=%s"
        % os.path.join(
            images_path,
            config.cfg["name"] + "_rev_" + config.brd["config"]["rev"] + ".png",
        ),
        "--export-dpi=%s" % str(png_dpi),
        "--export-area-drawing",
        "--export-background=#FFFFFF",
    ]

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
        for key, value in pairs:
            if key in result:
                msg.error(f"duplicate key ('{key}') specified in {filename}", KeyError)
            result[key] = value
        return result

    try:
        with open(filename, "r") as f:
            json_data = json.load(f, object_pairs_hook=checking_for_unique_keys)
    except ValueError as e:
        msg.error("Couldn't parse JSON file %s:\n-- %s" % (filename, e), ValueError)
    except (IOError, OSError):
        if error == True:
            msg.error("Couldn't open JSON file: %s" % filename, IOError)
        else:
            msg.info("Couldn't open JSON file: %s" % filename, IOError)

    return json_data


def getLayerList():
    """
    """
    layer_list = []
    for record in config.stk["stackup"]:
        if (
            record["type"] == "signal-layer-surface"
            or record["type"] == "signal-layer-internal"
        ):
            layer_list.append(record)

    layer_names = []
    for record in layer_list:
        layer_names.append(record["name"])

    return layer_list, layer_names


def getSurfaceLayers():
    """
    Returns a list of surface layer names
    Only here until this function is purged from the
    codebase
    """
    return config.stk["surface-layer-names"]


def getInternalLayers():
    """
    Returns a list of internal layer names
    Only here until this function is purged from the
    codebase
    """
    return config.stk["internal-layer-names"]


def getExtendedLayerList(layers):
    """
    For the list of layers we may get a list of all internal layers ('internal-1', 
    'internal-2, etc.) or simply 'internal', meaning that that shape is meant to go 
    into all internal layers, which is the most common case. The following 'expands'
    the layer list
    """
    if "internal" in layers:
        layers.remove("internal")
        layers.extend(config.stk["internal-layer-names"])
    return layers


def getExtendedSheetList(layer, sheet):
    """
    We may want multiple sheets of the same type, such as two
    soldermask layers on the same physical layer. This function
    expands the list if such layers are defined in the stackup
    """

    for layer_dict in config.stk["layers-dict"]:
        if layer_dict["name"] == layer:
            break
    stack_sheets = layer_dict["stack"]

    sheet_names = []
    for stack_sheet in stack_sheets:
        sheet_names.append(stack_sheet["name"])

    new_list = []
    for sheet_name in sheet_names:
        if sheet_name.startswith(sheet):
            new_list.append(sheet_name)

    return new_list


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
            print(f"ERROR: couldn't create build path {path}")
            raise

    return


def add_dict_values(d1, d2):
    """
    Add the values of two dicts
    Helpful code here:
      http://stackoverflow.com/questions/1031199/adding-dictionaries-in-python
    """

    return dict((n, d1.get(n, 0) + d2.get(n, 0)) for n in set(d1) | set(d2))


def process_meander_type(type_string, meander_type):
    """
    Extract meander path type parameters and return them as a dict
    """

    if meander_type == "meander-round":
        look_for = ["radius", "theta", "bus-width", "pitch"]
    elif meander_type == "meander-sawtooth":
        look_for = ["base-length", "amplitude", "bus-width", "pitch"]
    else:
        print("ERROR: unrecognised meander type")
        reaise

    meander = {}

    regex = "\s*%s\s*:\s*(?P<v>[^;]*)"

    for param in look_for:
        tmp = re.search(regex % param, type_string)
        if tmp is not None:
            meander[param] = float(tmp.group("v"))

    # add optional fields as 'None'
    for param in look_for:
        if meander.get(param) is None:
            meander[param] = None

    return meander


def checkForPoursInLayer(layer):
    """
    Returns True or False if there are pours in the specified layer
    """

    # In case there are no 'shapes' defined
    try:
        pours = config.brd["shapes"].get("pours")
    except:
        pours = {}

    if pours is not None:
        for pour_dict in pours:
            layers = getExtendedLayerList(pour_dict.get("layers"))
            if layer in layers:
                return True

    # return False
    return True


def interpret_svg_matrix(matrix_data):
    """
    Takes an array for six SVG parameters and returns angle, scale 
    and placement coordinate

    This SO answer was helpful here:
      http://stackoverflow.com/questions/15546273/svg-matrix-to-rotation-degrees
    """

    # apply float() to all elements, just in case
    matrix_data = [float(x) for x in matrix_data]

    coord = Point(matrix_data[4], -matrix_data[5])
    if matrix_data[0] == 0:
        angle = math.degrees(0)
    else:
        angle = math.atan(matrix_data[2] / matrix_data[0])

    scale = Point(
        math.fabs(matrix_data[0] / math.cos(angle)),
        math.fabs(matrix_data[3] / math.cos(angle)),
    )

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

    regex = r"^(?P<t>[a-zA-z\D]+?)(?P<n>\d+)(?P<e>[\-\s].*)?"
    parse = re.match(regex, refdef)

    # TODO: there has to be a more elegant way for doing this!
    if parse == None:
        return None, None, None
    else:
        t = parse.group("t")
        n = int(parse.group("n"))
        e = parse.group("e")
        return t, n, e


def renumberRefdefs(order):
    """
    Renumber the refdefs in the specified order
    """

    components = config.brd["components"]
    comp_dict = {}
    new_dict = {}

    for refdef in components:

        rd_type, rd_number, rd_extra = parse_refdef(refdef)
        location = to_Point(components[refdef].get("location", [0, 0]))
        tmp = {}
        tmp["record"] = components[refdef]
        tmp["type"] = rd_type
        tmp["number"] = rd_number
        tmp["extra"] = rd_extra
        tmp["coord-x"] = location.x
        tmp["coord-y"] = location.y

        if comp_dict.get(rd_type) == None:
            comp_dict[rd_type] = []
        comp_dict[rd_type].append(tmp)

        # Sort list according to 'order'
        for comp_type in comp_dict:
            if order == "left-to-right":
                reverse = False
                itemget_param = "coord_x"
            elif order == "right-to-left":
                reverse = True
                itemget_param = "coord_x"
            elif order == "top-to-bottom":
                reverse = True
                itemget_param = "coord-y"
            elif order == "bottom-to-top":
                reverse = False
                itemget_param = "coord-y"
            else:
                msg.error("Unrecognised renumbering order %s" % (order))

            sorted_list = sorted(
                comp_dict[comp_type], key=itemgetter(itemget_param), reverse=reverse
            )

            for i, record in enumerate(sorted_list):
                new_refdef = f"{record['type']}{i+1}"
                if record["extra"] is not None:
                    new_refdef += f"record['extra']"
                new_dict[new_refdef] = record["record"]

    config.brd["components"] = new_dict

    # Save board config to file (everything is saved, not only the
    # component data)
    filename = os.path.join(
        config.cfg["locations"]["boards"],
        config.cfg["name"],
        config.cfg["name"] + ".json",
    )
    try:
        with open(filename, "wb") as f:
            f.write(json.dumps(config.brd, sort_keys=True, indent=2))
    except:
        msg.error("Cannot save file %s" % filename)

    return


def parse_dimension(string):
    """
    Parses a dimention recieved from the source files, separating the units,
    if specified, from the value
    """
    if string != None:
        result = re.match("(-?\d*\.?\d+)\s?(\w+)?", string)
        value = float(result.group(1))
        unit = result.group(2)
    else:
        value = None
        unit = None
    return value, unit


def get_text_params(font_size, letter_spacing, line_height):
    try:
        letter_spacing, letter_spacing_unit = parse_dimension(letter_spacing)
    except:
        msg.error(
            f"There's a problem with parsing the 'letter-spacing' property with value '{letter_spacing}'. The format should be an integer or float followed by 'mm' (the only unit supported). For example, '0.3mm' or '-2 mm' should work."
        )

    if letter_spacing_unit == None:
        letter_spacing_unit = "mm"

    try:
        line_height, line_height_unit = parse_dimension(line_height)
    except:
        msg.error(
            f"There's a problem parsing the 'line-height' property with value '{line_height}'. The format should be an integer or float followed by 'mm' (the only unit supported). For example, '0.3mm' or '-2 mm' should work."
        )

    if line_height_unit == None:
        line_height_unit = "mm"

    try:
        font_size, font_size_unit = parse_dimension(font_size)
    except:
        throw(
            "There's a problem parsing the 'font-size'. It's most likely missing. The format should be an integer or float followed by 'mm' (the only unit supported). For example, '0.3mm' or '2 mm' should work. Of course, it needs to be a positive figure."
        )

    if font_size_unit == None:
        font_size_unit = "mm"

    return float(font_size), float(letter_spacing), float(line_height)


def textToPath(font_data, text, letter_spacing, line_height, scale_factor):
    from .svgpath import SvgPath

    """
    Convert a text string (unicode and newlines allowed) to a path.
    The 'scale_factor' is needed in order to scale rp 'letter_spacing' and 'line_height'
    to the original scale of the font.
    """

    ns_svg = config.cfg["ns"]["svg"]

    # This the horizontal advance that applied to all glyphs unless there's a specification for
    # for the glyph itself
    font_horiz_adv_x = float(
        font_data.find("//n:font", namespaces={"n": ns_svg}).get("horiz-adv-x")
    )

    # This is the number if 'units' per 'em'. The default, in the absence of a definition is 1000
    # according to the SVG spec
    units_per_em = (
        float(
            font_data.find("//n:font-face", namespaces={"n": ns_svg}).get(
                "units-per-em"
            )
        )
        or 1000
    )

    glyph_ascent = float(
        font_data.find("//n:font-face", namespaces={"n": ns_svg}).get("ascent")
    )
    glyph_decent = float(
        font_data.find("//n:font-face", namespaces={"n": ns_svg}).get("descent")
    )

    text_width = 0
    text_path = ""

    # split text into charcters and find unicade chars
    try:
        text = re.findall(r"(\&#x[0-9abcdef]*;|.|\n)", text)
    except:
        throw(
            f"There's a problem parsing the text '{text}'. Unicode and \\n newline should be fine, by the way."
        )

    # instantiate HTML parser
    htmlpar = HTMLParser.HTMLParser()
    gerber_lp = ""
    text_height = 0

    if line_height == None:
        line_height = units_per_em

    for i, symbol in enumerate(text[:]):

        symbol = htmlpar.unescape(symbol)
        # get the glyph definition from the file
        if symbol == "\n":
            text_width = 0
            text_height += units_per_em + (line_height / scale_factor - units_per_em)
        else:
            glyph = font_data.find(
                f'//n:glyph[@unicode="{symbol}"]', namespaces={"n": ns_svg},
            )
            if glyph == None:
                utils.throw(
                    f"There's no glyph definition for '{symbol}' in the '{font}' font."
                )
            else:
                # Unless the glyph has its own width, use the global font width
                glyph_width = float(glyph.get("horiz-adv-x") or font_horiz_adv_x)
                if symbol != " ":
                    glyph_path = SvgPath(glyph.get("d"))
                    first_point = glyph_path.get_first_point()
                    offset_x = float(first_point[0])
                    offset_y = float(first_point[1])
                    path = glyph_path.get_path_str()
                    path = re.sub(
                        "^(m\s?[-\d\.]+\s?,\s?[-\d\.]+)",
                        f"M {str(text_width + offset_x)},{str(offset_y - text_height)}",
                        path,
                    )
                    gerber_lp += (
                        glyph.get("gerber-lp")
                        or glyph.get("gerber_lp")
                        or "%s" % "d" * glyph_path.get_num_of_segments()
                    )
                    text_path += "%s " % (path)

            text_width += glyph_width + letter_spacing / scale_factor

    # Mirror text
#    text_path = SvgPath(text_path)
#    text_path.transform()
#    text_path = text_path.getTransformedMirrored()

    return "m 0,0", ""


def digest(string):
    """
    """
    digits = config.cfg["params"]["num-of-digest-digits"]
    return hashlib.md5(string.encode()).hexdigest()[: digits - 1]


def pn(num_in, sd=None):
    """
    Create a pretty number from a float.
    'round()' returns '0.0' and that's ugly. So this takes care of that.
    If the amount of digits isn't defined then use the global settings. 
    """
    if sd is None:
        num = round(num_in, config.cfg["params"]["significant-digits"])
    else:
        num = round(num_in, sd)
    if float(num).is_integer():
        num = int(num)
    return num

def parseTransform(transform):
    """
    Returns a Point() for the input transform
    """
    data = {}

    if transform == None:
        data["type"] = "translate"
        data["location"] = Point()
    elif "translate" in transform.lower():
        regex = r".*?translate\s?\(\s?(?P<x>[+-]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)(\s?[\s,]\s?)?(?P<y>[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)?\s?\).*"
        coord = re.match(regex, transform)
        data["type"] = "translate"
        x = coord.group("x")
        y = coord.group("y")
        if coord.group("y") != None:
            y = coord.group("y")
        else:
            y = 0
        data["location"] = Point(x, y)
    elif "matrix" in transform.lower():
        data["type"] = "matrix"
        data["location"], data["rotate"], data["scale"] = parseSvgMatrix(transform)
    elif "rotate" in transform.lower():
        data["type"] = "rotate"
        data["location"], data["rotate"] = parseSvgRotate(transform)
    else:
        msg.error(
            "Found a path transform that cannot be handled, %s. SVG stansforms should be in the form of 'translate(num,num)' or 'matrix(num,num,num,num,num,num)"
            % transform
        )

    return data


def parseSvgRotate(rotate):
    """
    """
    regex = r".*?rotate\((?P<m>.*?)\).*"
    rotate = re.match(regex, rotate)
    rotate = rotate.group("m")
    rotate = rotate.split(",")

    # Apply float() to all elements
    rotate = [float(x) for x in rotate]

    location = Point(rotate[1], rotate[2])

    angle = rotate[0]

    return location, angle


def parseSvgMatrix(matrix):
    """
    Takes an array for six SVG parameters and returns angle, scale 
    and placement coordinate

    This SO answer was helpful here:
      http://stackoverflow.com/questions/15546273/svg-matrix-to-rotation-degrees
    """
    regex = r".*?matrix\((?P<m>.*?)\).*"
    matrix = re.match(regex, matrix)
    matrix = matrix.group("m")
    matrix = matrix.split(",")

    # Apply float() to all elements
    matrix = [float(x) for x in matrix]

    coord = Point(matrix[4], matrix[5])
    if matrix[0] == 0:
        angle = math.degrees(0)
    else:
        angle = math.atan(matrix[2] / matrix[0])

    scale_x = (math.sqrt(matrix[0] * matrix[0] + matrix[1] * matrix[1]),)
    scale_y = (math.sqrt(matrix[2] * matrix[2] + matrix[3] * matrix[3]),)

    scale = max(scale_x, scale_y)[0]

    # convert angle to degrees
    angle = math.degrees(angle)

    # Inkscape rotates anti-clockwise, PCBmodE "thinks" clockwise. The following
    # adjusts these two views, although at some point we'd
    # need to have the same view, or make it configurable
    angle = -angle

    return coord, angle, scale


def process_style(style):
    """
    Keep only relevant style properties. Plus, add 'fill:none' if a
    'stroke-width' is captured, otherwise Inkscape still displays the
    shape as a stroke+fill. This means that we don't require an additional
    'fill:none' after every 'stroke-width' in the shape definitions.
    """

    keep = ["stroke-width"]
    add_if_stroke = "fill:none;"

    pattern = "^\s*?%s\s*:\s*(.*?)\s*;?\s*$"

    new_style = ""
    for k in keep:
        result = re.findall(pattern % k, style)
        if result != []:
            new_style += f"{k}:{result[0]};"
            if k == "stroke-width":
                new_style += add_if_stroke

    return new_style
