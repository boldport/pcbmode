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


import os
from pathlib import Path
import re
from lxml import etree as et
import pyparsing as pyp

from pcbmode.config import config
from pcbmode.utils import messages as msg
from pcbmode.utils import svg
from pcbmode.utils import utils
from pcbmode.utils.svgpath import SvgPath
from pcbmode.utils.point import Point


def gerberise(manufacturer="default"):
    """
    Generate Gerbers for one or more layers
    """

    # Open the board's SVG
    svg_in = utils.open_board_svg()

    # Get Gerber generation settings
    gcd = config.cfg["gerber"]
    decimals = gcd["decimals"]
    digits = gcd["digits"]
    steps = gcd["steps-per-segment"]
    length = gcd["min-segment-length"]

    # Get layer data
    xpath_regex = ""
    ns = {"pcbmode": config.cfg["ns"]["pcbmode"], "svg": config.cfg["ns"]["svg"]}

    prod_dir = Path(
        config.tmp["project-path"]
        / config.brd["project-params"]["output"]["gerber-preamble"]
    ).parent
    gerber_preamble = Path(
        config.brd["project-params"]["output"]["gerber-preamble"]
    ).name

    prod_dir.mkdir(parents=True, exist_ok=True)

    filename_info = config.cfg["manufacturers"][manufacturer]["filenames"]["gerbers"]

    # Process Gerbers for PCB layers and sheets
    # for pcb_layer in utils.getSurfaceLayers():
    for pcb_layer in config.stk["layer-names"]:

        # Get the SVG layer corresponding to the PCB layer
        svg_layer = svg_in.find(
            "//svg:g[@pcbmode:pcb-layer='%s']" % (pcb_layer), namespaces=ns
        )

        # Get masks (must be placed right after pours)
        mask_paths = svg_in.findall(
            ".//svg:defs//svg:mask[@pcbmode:pcb-layer='%s']//svg:path" % pcb_layer,
            namespaces=ns,
        )

        sheets = ["conductor", "soldermask", "solderpaste", "silkscreen"]
        for sheet in sheets:
            # Get the SVG layer corresponding to the 'sheet'
            sheet_layer = svg_layer.find(
                ".//svg:g[@pcbmode:sheet='%s']" % (sheet), namespaces=ns
            )

            if sheet == "conductor":
                mask_paths_to_pass = mask_paths
            else:
                mask_paths_to_pass = []

            if sheet_layer != None:
                # Create a Gerber object
                gerber = Gerber(
                    sheet_layer, mask_paths_to_pass, decimals, digits, steps, length
                )

                # Default to .ger extension if undefined
                try:
                    ext = filename_info[pcb_layer.split("-")[0]][sheet].get("ext")
                except KeyError:
                    ext = "ger"

                add = "_%s_%s.%s" % (pcb_layer, sheet, ext)

                filename = os.path.join(base_dir, base_name + add)

                with open(filename, "w") as f:
                    for line in gerber.getGerber():
                        f.write(line)

    # Process module sheets
    sheets = ["outline", "documentation"]
    for sheet in sheets:
        # Get the SVG layer corresponding to the 'sheet'
        sheet_layer = svg_in.find(
            ".//svg:g[@pcbmode:sheet='%s']" % (sheet), namespaces=ns
        )

        # Create a Gerber object
        gerber = Gerber(sheet_layer, [], decimals, digits, steps, length)

        add = "_%s.%s" % (sheet, filename_info["other"][sheet].get("ext") or "ger")
        filename = os.path.join(base_dir, base_name + add)

        with open(filename, "w") as f:
            for line in gerber.getGerber(False):
                f.write(line)

    return ["bullshit"]


class Gerber:
    """
    """

    def __init__(self, svg, mask_paths, decimals, digits, steps, length):
        """
        """

        self._ns = {
            "pcbmode": config.cfg["ns"]["pcbmode"],
            "svg": config.cfg["ns"]["svg"],
        }

        self._svg = svg
        self._mask_paths = mask_paths
        self._decimals = decimals
        self._digits = digits
        self._steps = steps
        self._length = length
        self._grammar = self._getGerberGrammar()

        self._aperture_list = []

        # Gerber apertures are defined at the begining of the file and
        # then refered to by number. 1--10 are reserved and cannot be
        # used, so wer start the design's apersute number at 20,
        # leaving 10 to define fixed apertures for closed shapesm
        # flashes, wtc.lets us have
        self._aperture_num = 20

        self._closed_shape_aperture_num = 10
        self._pad_flashes_aperture_num = 11

        self._commands = []
        self._apertures = {}

        self._paths = self._getPaths()

        for path in self._paths:
            tmp = {}

            style_string = path.get("style")
            tmp["style"] = path.get("{" + config.cfg["ns"]["pcbmode"] + "}style")
            if tmp["style"] == "stroke":
                tmp["stroke-width"] = css_utils.get_style_value(
                    style_string, "stroke-width"
                )
                # Build aperture list
                if tmp["stroke-width"] not in self._apertures:
                    self._apertures[tmp["stroke-width"]] = self._aperture_num
                    self._aperture_num += 1

            tmp["gerber-lp"] = path.get(
                "{" + config.cfg["ns"]["pcbmode"] + "}gerber-lp"
            )

            # Get the absolute location
            location = self._getLocation(path)

            # Get path coordinates; each path segment as a list item
            tmp["coords"] = self._getCommandListOfPath(path, location)

            self._commands.append(tmp)

        self._flattenCoords()
        self._flashes = self._getFlashes()
        self._preamble = self._createPreamble()
        self._postamble = self._createPostamble()

    def _getFlashes(self):
        """
        Manufacturers use the coordinate of a flash of pads as coordinates
        for continuity tests when boards are testes. Typically, a pad
        is created using a flash. Since PCBmodE doesn't flash a pad,
        we add tiny dots in the center of the pads.
        """

        fc = []
        fc.append("\n")
        fc.append("G04 Pad flashes *\n")
        fc.append("%LPD*%\n")
        fc.append("D%d*\n" % self._pad_flashes_aperture_num)

        # Get pads
        pad_paths = self._svg.findall(
            ".//svg:g[@pcbmode:sheet='pads']//svg:path", namespaces=self._ns
        )

        for pad_path in pad_paths:
            location = self._getLocation(pad_path)
            text = self._getGerberisedPoint(location, Point())
            fc.append("%sD03*\n" % text)

        fc.append("\n")

        return fc

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
            transform = ancestor.get("transform")
            transform_data = utils.parseTransform(transform)
            # Add them up
            location += transform_data["location"]

        # Add the transform of the path itself
        transform = path.get("transform")
        if transform != None:
            transform_data = utils.parseTransform(transform)
            location += transform_data["location"]

        return location

    def _getPaths(self):
        """
        Return all paths in the input SVG layer.  This function also
        captures pours and masks and orders them in the right order so
        the 'dark' and 'clear' areas show up correctly
        """

        paths = []

        # Get pours (must be placed first! Applies to copper,
        # otherwise empty list)
        paths += self._svg.findall(
            ".//svg:g[@pcbmode:sheet='pours']//svg:path", namespaces=self._ns
        )

        # Get mask paths (must follow pours!)
        for path in self._mask_paths:
            # Add the path
            paths.append(path)
            # If the path is a fill we must also stroke it in order to
            # create the buffer to the pour
            style = path.get("{" + config.cfg["ns"]["pcbmode"] + "}style")
            if style == "fill":
                path.set("{" + config.cfg["ns"]["pcbmode"] + "}style", "stroke")
                paths.append(path)

        # Get routing (applies to copper only, otherwise empty list)
        paths += self._svg.findall(
            ".//svg:g[@pcbmode:sheet='routing']//svg:path", namespaces=self._ns
        )

        # Get pads (applies to copper only, otherwise empty list)
        paths += self._svg.findall(
            ".//svg:g[@pcbmode:sheet='pads']//svg:path", namespaces=self._ns
        )

        # Get component shapes
        paths += self._svg.findall(
            ".//svg:g[@pcbmode:type='component-shapes']//svg:path", namespaces=self._ns
        )

        # Get refdefs
        paths += self._svg.findall(
            ".//svg:g[@pcbmode:type='refdef']//svg:path", namespaces=self._ns
        )

        # Get component shapes
        paths += self._svg.findall(
            ".//svg:g[@pcbmode:type='layer-index']//svg:path", namespaces=self._ns
        )

        # Get module shapes
        paths += self._svg.findall(
            ".//svg:g[@pcbmode:type='module-shapes']//svg:path", namespaces=self._ns
        )

        return paths

    def getGerber(self, flashes=True):
        """
        Return the complete Gerber
        """
        if flashes == True:
            gerber = (
                self._preamble
                + self._flattened_commands
                + self._flashes
                + self._postamble
            )
        else:
            gerber = self._preamble + self._flattened_commands + self._postamble

        return gerber

    def _flattenCoords(self):
        """
        """

        # This is left intentionally 'empty' in order for it to be
        # set the first time
        current_polarity = ""

        commands = []
        for cmd_set in self._commands:
            gerber_lp = cmd_set.get("gerber-lp")

            for i, cmd_list in enumerate(cmd_set["coords"]):

                # Get the polarity setting character from the string,
                # corresponding to the current path segment being
                # processed
                try:
                    polarity = gerber_lp[i].upper()
                except:
                    polarity = "D"

                # Change the polarity of neccessary
                if polarity != current_polarity:
                    commands.append("%%LP%s*%%\n" % polarity)
                    current_polarity = polarity

                if cmd_set["style"] == "fill":
                    # Start of a closed shape
                    commands.append("G36*\n")
                else:
                    # Chahge aperture to match stroke width
                    commands.append("D%d*\n" % self._apertures[cmd_set["stroke-width"]])

                # Add the path segment's commands
                commands += cmd_list

                if cmd_set["style"] == "fill":
                    # Close the 'closed' shape
                    commands.append("G37*\n")

        self._flattened_commands = commands

    def _getParamCommand(self, param, comment=None):
        """
        Returns a list of Gerber parameter command with an optional
        comment
        """
        commands = []
        if comment != None:
            commands.append("G04 " + comment + " *\n")
        commands.append("%" + param + "*%\n")

        return commands

    def _pathToPoints(self, path):
        """
        Converts a path into points
        """
        path = SvgPath(path.get("d"))
        coords = path.getCoordList(self._steps, self._length)

        return coords

    def _getCommandListOfPath(self, path, offset=None):
        """
        Linearises a path into Gerber points. The 'offset' Point() is
        added to the location.
        Returns a list of Gerber 'commands'.
        """

        if offset is None:
            offset = Point()

        # store the Gerber commands in this list
        commands = {}

        polarity_sequence = ""
        order = ""

        # Create a list of lineat points from the input path
        coords = self._pathToPoints(path)

        coord_list = []

        # Each 'segment' correspond to a shape within the complete
        # poth.
        for segment in coords:

            segment_coord_list = []

            text = self._getGerberisedPoint(segment[0], offset)
            segment_coord_list.append("G01%sD02*\n" % text)

            for coord in segment[1:]:
                text = self._getGerberisedPoint(coord, offset)
                segment_coord_list.append("G01%sD01*\n" % text)

            coord_list.append(segment_coord_list)

        return coord_list

    def _getGerberisedPoint(self, coord, offset):
        """
        Convert a float to the ridiculous Gerber format 
        """

        # Add offset to coordinate
        coord += offset

        # Split to integer and decimal content; the reformatting is required
        # for floats coming in represented in scientific notation
        xi, xd = str("%f" % coord.x).split(".")
        yi, yd = str("%f" % -coord.y).split(".")

        # Pad decimals to required number of digits for Gerber (yuck!)
        xd = xd.ljust(self._decimals, "0")
        yd = yd.ljust(self._decimals, "0")

        return "X%s%sY%s%s" % (xi, xd[: self._decimals], yi, yd[: self._decimals])

    def _createPostamble(self):
        """
        This goes at the end of the Gerber
        """
        pa = []
        pa.append("G04 end of program *\n")
        pa.append("M02*\n")
        return pa

    def _createPreamble(self):
        """
        """
        pa = []
        pa.append("G04                                                      *\n")
        pa.append("G04 Greetings!                                           *\n")
        pa.append("G04 This Gerber was generated by PCBmodE, an open source *\n")
        pa.append("G04 PCB design software. Get it here:                    *\n")
        pa.append("G04                                                      *\n")
        pa.append("G04   http://pcbmode.com                                 *\n")
        pa.append("G04                                                      *\n")
        pa.append("G04 Also visit                                           *\n")
        pa.append("G04                                                      *\n")
        pa.append("G04   http://boldport.com                                *\n")
        pa.append("G04                                                      *\n")
        pa.append("G04 and follow @boldport / @pcbmode for updates!         *\n")
        pa.append("G04                                                      *\n")
        pa.append("\n")
        # version %s on %s GMT; *\n" % (config.cfg['version'], datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

        # Define figure format
        pa += self._getParamCommand(
            "FSLAX%d%dY%d%d"
            % (self._digits, self._decimals, self._digits, self._decimals),
            "leading zeros omitted (L); absolute data (A); %s integer digits and %s fractional digits"
            % (self._digits, self._decimals),
        )
        pa.append("\n")

        # Define units
        pa += self._getParamCommand("MOMM", "mode (MO): millimeters (MM)")
        pa.append("\n")

        pa.append("G04 Aperture definitions *\n")

        # Fixed circular aperture used for closed shapes
        pa.append("%%ADD%dC,%.3fX*%%\n" % (self._closed_shape_aperture_num, 0.001))
        pa.append("%%ADD%dC,%.3fX*%%\n" % (self._pad_flashes_aperture_num, 0.001))

        # List all apertures captured for this sheet
        for aperture in self._apertures:
            pa.append(
                "%%ADD%dC,%.2fX*%%\n" % (self._apertures[aperture], float(aperture))
            )
        pa.append("\n")

        return pa

    def _getGerberGrammar(self):
        """
       Returns the grammar of Gerber
       """

        gerber_dictionary = {
            "G04": {"text": "comment"},
            "G36": {"text": "closed-shape-start"},
            "G37": {"text": "closed-shape-end"},
            "MO": {"text": "units", "MM": {"text": "mm"}, "IN": {"text": "inch"}},
            "AD": {
                "text": "aperture-definition",
                "C": {"text": "circle"},
                "R": {"text": "rectangle"},
            },
            "FS": {
                "text": "format",
                "L": {"text": "leading-zeros"},
                "A": {"text": "absolute"},
            },
            "D01": {"text": "draw"},
            "D02": {"text": "move"},
            "D03": {"text": "flash"},
        }

        # Define grammar using pyparsing
        space = pyp.Literal(" ")
        comma = pyp.Literal(",").suppress()

        # Capture a float string and cast to float
        floatnum = pyp.Regex(r"([\d\.]+)").setParseAction(lambda t: float(t[0]))

        # Capture integer string and cast to int
        integer = pyp.Regex(r"(-?\d+)").setParseAction(lambda t: int(t[0]))

        # Capture single digit string and cast to int
        single_digit = pyp.Regex(r"(\d)").setParseAction(lambda t: int(t[0]))

        aperture = pyp.Literal("D").setParseAction(pyp.replaceWith("aperture"))
        coord_x = pyp.Literal("X").setParseAction(pyp.replaceWith("x"))
        coord_y = pyp.Literal("Y").setParseAction(pyp.replaceWith("y"))
        gcoord = pyp.Regex(r"(-?\d+)")
        coord_dict = pyp.dictOf((coord_x | coord_y), gcoord)
        coord_xy = pyp.Group(coord_dict + coord_dict)

        inst_del = pyp.Literal("%").suppress()  # instruction delimeter
        inst_end = pyp.Literal("*").suppress()  # ending suffix

        cmd_comment = pyp.Literal("G04").setParseAction(pyp.replaceWith("comment"))

        cmd_closed_shape_start = pyp.Literal("G36")
        cmd_closed_shape_end = pyp.Literal("G37")

        cmd_units = pyp.Literal("MO")("gerber-command")
        cmd_units_opt_mm = pyp.Literal("MM").setParseAction(pyp.replaceWith("mm"))
        cmd_units_opt_inch = pyp.Literal("IN").setParseAction(pyp.replaceWith("inch"))

        cmd_format = pyp.Literal("FS")("gerber-command")
        cmd_format_opt_leading_zeros = pyp.Literal("L").setParseAction(
            pyp.replaceWith("leading")
        )
        cmd_format_opt_trailing_zeros = pyp.Literal("T").setParseAction(
            pyp.replaceWith("trailing")
        )

        cmd_format_opt_absolute = pyp.Literal("A").setParseAction(
            pyp.replaceWith("absolute")
        )
        cmd_format_opt_incremental = pyp.Literal("I").setParseAction(
            pyp.replaceWith("incremental")
        )

        # Aperture definition
        cmd_ap_def = pyp.Literal("AD")("gerber-command")
        cmd_ap_def_num = "D" + integer.setResultsName("number")
        cmd_ap_def_opt_circ = pyp.Literal("C").setParseAction(pyp.replaceWith("circle"))
        cmd_ap_def_opt_rect = pyp.Literal("R").setParseAction(pyp.replaceWith("rect"))

        cmd_polarity = pyp.Literal("LP")("gerber-command")
        cmd_polarity_opt_dark = pyp.Literal("D").setParseAction(pyp.replaceWith("dark"))
        cmd_polarity_opt_clear = pyp.Literal("C").setParseAction(
            pyp.replaceWith("clear")
        )

        cmd_linear_int = pyp.Literal("G01").suppress()  # lineal interpolation
        cmd_circ_int_cw = pyp.Literal("G02").suppress()  # circular int. clockwise
        cmd_circ_int_ccw = pyp.Literal(
            "G03"
        ).suppress()  # circular int. counter-clockwise

        aperture_type = (
            (cmd_ap_def_opt_circ("type") + comma) + (floatnum)("diameter") + "X"
        ) | (
            (cmd_ap_def_opt_rect("type") + comma)
            + (floatnum)("width")
            + "X"
            + (floatnum)("height")
        )

        polarity_type = (cmd_polarity_opt_clear | cmd_polarity_opt_dark)("polarity")

        units_type = (cmd_units_opt_mm | cmd_units_opt_inch)("units")

        format_zeros = (cmd_format_opt_leading_zeros("zeros")) | (
            cmd_format_opt_trailing_zeros("zeros")
        )

        format_notation = (cmd_format_opt_absolute("notation")) | (
            cmd_format_opt_incremental("notation")
        )

        format_data = (single_digit)("integer") + single_digit("decimal")

        # comments (suppress)
        comment = (
            cmd_comment
            + pyp.Optional(space)
            + pyp.Regex(r"([^\*]+)?")
            + pyp.Optional(space)
            + inst_end
        ).suppress()

        units = (
            inst_del + pyp.Group(cmd_units + units_type)("units") + inst_end + inst_del
        )

        gformat = (
            inst_del
            + pyp.Group(
                cmd_format
                + format_zeros
                + format_notation
                + "X"
                + pyp.Group(format_data)("x")
                + "Y"
                + pyp.Group(format_data)("y")
            )("format")
            + inst_end
            + inst_del
        )

        ap_def = (
            inst_del
            + pyp.Group(cmd_ap_def + cmd_ap_def_num + aperture_type)(
                "aperture_definition"
            )
            + inst_end
            + inst_del
        )

        polarity = (
            inst_del
            + pyp.Group(cmd_polarity + polarity_type)("polarity_change")
            + inst_end
            + inst_del
        )

        closed_shape_start = cmd_closed_shape_start("start_closed_shape") + inst_end
        closed_shape_end = cmd_closed_shape_end("end_closed_shape") + inst_end

        draw = pyp.Group(
            pyp.Optional(cmd_linear_int)
            + "X"
            + (integer)("x")
            + "Y"
            + (integer)("y")
            + pyp.Literal("D01").suppress()
            + inst_end
        )("draw")

        move = pyp.Group(
            pyp.Optional(cmd_linear_int)
            + "X"
            + (integer)("x")
            + "Y"
            + (integer)("y")
            + pyp.Literal("D02").suppress()
            + inst_end
        )("move")

        flash = pyp.Group(
            pyp.Optional(cmd_linear_int)
            + "X"
            + (integer)("x")
            + "Y"
            + (integer)("y")
            + pyp.Literal("D03").suppress()
            + inst_end
        )("flash")

        aperture_change = pyp.Literal("D").suppress() + pyp.Group(
            integer("number") + inst_end
        )("aperture_change")

        # end of file (suppress)
        the_end = (pyp.Literal("M02") + inst_end)("end_of_gerber")

        grammar = (
            comment
            | units
            | gformat
            | ap_def
            | aperture_change
            | draw
            | move
            | flash
            | polarity
            | closed_shape_start
            | closed_shape_end
            | the_end
        )

        return pyp.OneOrMore(pyp.Group(grammar))


def gerbers_to_svg(manufacturer="default"):
    """
    Takes Gerber files as input and generates an SVG of them
    """

    def normalise_gerber_number(gerber_number, axis, form):
        """
        Takes a Gerber number and converts it into a float using
        the formatting defined in the Gerber header
        """

        # TODO: actually support anything other than leading zeros
        number = gerber_number / pow(10.0, form[axis]["decimal"])

        return number

    def parsed_grammar_to_dict(parsed_grammar):
        """
        Converts the Gerber parsing results to an SVG.
        """

        gerber_dict = {}
        current_aperture = None
        new_shape = True

        for line in parsed_grammar:
            if line.dump():
                if line.format:
                    if gerber_dict.get("format") is None:
                        gerber_dict["format"] = {}
                    tmp = gerber_dict["format"]

                    tmp["notation"] = line["format"]["notation"]
                    tmp["zeros"] = line["format"]["zeros"]
                    tmp["x"] = {}
                    tmp["x"]["integer"] = line["format"]["x"]["integer"]
                    tmp["x"]["decimal"] = line["format"]["x"]["decimal"]
                    tmp["y"] = {}
                    tmp["y"]["integer"] = line["format"]["x"]["integer"]
                    tmp["y"]["decimal"] = line["format"]["x"]["decimal"]

                elif line.units:
                    gerber_dict["units"] = line["units"]["units"]

                elif line.aperture_definition:
                    tmp = {}
                    if line["aperture_definition"]["type"] == "circle":
                        tmp["type"] = "circle"
                        tmp["diameter"] = line["aperture_definition"]["diameter"]
                        tmp["number"] = line["aperture_definition"]["number"]
                    elif line["aperture_definition"]["type"] == "rect":
                        tmp["type"] = "rect"
                        tmp["width"] = line["aperture_definition"]["width"]
                        tmp["height"] = line["aperture_definition"]["height"]
                        tmp["number"] = line["aperture_definition"]["number"]
                    else:
                        print("ERROR: cannot recognise aperture definition type")

                    if gerber_dict.get("aperture-definitions") is None:
                        gerber_dict["aperture-definitions"] = []

                    gerber_dict["aperture-definitions"].append(tmp)

                elif line.polarity_change:

                    if gerber_dict.get("features") is None:
                        gerber_dict["features"] = []

                    polarity = line["polarity_change"]["polarity"]
                    polarity_dict = {}
                    polarity_dict["polarity"] = polarity
                    polarity_dict["shapes"] = []
                    gerber_dict["features"].append(polarity_dict)

                elif line.aperture_change:
                    tmp = {}
                    tmp["type"] = "aperture-change"
                    tmp["number"] = line.aperture_change["number"]
                    # if len(gerber_dict['features'][-1]['shapes'] == 0):
                    gerber_dict["features"][-1]["shapes"].append(tmp)
                    # else:
                    #    gerber_dict['features'][-1]['shapes'].append(tmp)

                    tmp = {}
                    tmp["type"] = "stroke"
                    tmp["segments"] = []
                    gerber_dict["features"][-1]["shapes"].append(tmp)

                elif line.start_closed_shape:
                    tmp = {}
                    tmp["type"] = "fill"
                    tmp["segments"] = []
                    gerber_dict["features"][-1]["shapes"].append(tmp)

                elif line.move or line.draw or line.flash:

                    # TODO: hack alert! (Got to get shit done, you know? Don't judge me!)
                    if line.move:
                        command_name = "move"
                        item = line.move
                    if line.draw:
                        command_name = "draw"
                        item = line.draw
                    if line.flash:
                        command_name = "flash"
                        item = line.flash

                    point = Point(
                        normalise_gerber_number(item["x"], "x", gerber_dict["format"]),
                        normalise_gerber_number(item["y"], "y", gerber_dict["format"]),
                    )
                    tmp = {}
                    tmp["type"] = command_name
                    tmp["coord"] = point
                    gerber_dict["features"][-1]["shapes"][-1]["segments"].append(tmp)

                elif line.end_closed_shape:
                    new_shape = True

        return gerber_dict

    def create_gerber_svg_data(gerber_data):
        """
        Returns an SVG element of the input Gerber data
        """
        gerber_data_parsed = gerber_grammar.parseString(gerber_data)
        gerber_data_dict = parsed_grammar_to_dict(gerber_data_parsed)
        gerber_data_svg = svg.generate_svg_from_gerber_dict(gerber_data_dict)

        return gerber_data_svg

    # get the board's shape / outline
    board_shape_gerber_lp = None
    shape = config.brd["board_outline"]["shape"]
    board_shape_type = shape.get("type")

    if board_shape_type in ["rect", "rectangle"]:
        offset = utils.to_Point(shape.get("offset") or [0, 0])
        board_shape_path = svg.rect_to_path(shape)

    elif board_shape_type == "path":
        board_shape_path = shape.get("value")
        board_shape_gerber_lp = shape.get("gerber_lp")
        if board_shape_path is None:
            print("ERROR: couldn't find a path under key 'value' for board outline")

    else:
        print(
            "ERROR: unrecognised board shape type: %s. Possible options are 'rect' or 'path'"
            % board_shape_type
        )

    # convert path to relative
    board_shape_path_relative = svg.absolute_to_relative_path(board_shape_path)

    # this will return a path having an origin at the center of the shape
    # defined by the path
    board_width, board_height, board_outline = svg.transform_path(
        board_shape_path_relative, True
    )

    display_width = board_width
    display_height = board_height

    # transform = 'translate(' + str(round((board_width)/2, SD)) + ' ' + str(round((board_height)/2, SD)) + ')'
    sig_dig = config.cfg["params"]["significant-digits"]
    # transform = 'translate(%s %s)' % (round(board_width/2, sig_dig),
    #                                  round(board_height/2, sig_dig))

    # extra buffer for display frame
    display_frame_buffer = config.cfg["params"]["display-frame-buffer"]

    gerber = et.Element(
        "svg",
        width=str(display_width) + config.brd["config"]["units"],
        height=str(display_height) + config.brd["config"]["units"],
        viewBox=str(-display_frame_buffer / 2)
        + " "
        + str(-display_frame_buffer / 2)
        + " "
        + str(board_width + display_frame_buffer)
        + " "
        + str(board_height + display_frame_buffer),
        version="1.1",
        nsmap=cfg["namespace"],
        fill="black",
    )

    doc = et.ElementTree(gerber)

    gerber_layers = svg.create_layers_for_gerber_svg(gerber)

    # directory for where to expect the Gerbers within the build path
    # regardless of the source of the Gerbers, the PCBmodE directory
    # structure is assumed
    production_path = os.path.join(
        config.cfg["base-dir"], config.cfg["locations"]["build"], "production"
    )

    # get board information from configuration file
    pcbmode_version = config.cfg["version"]
    board_name = config.cfg["name"]
    board_revision = config.brd["config"].get("rev")

    base_name = "%s_rev_%s" % (board_name, board_revision)

    gerber_grammar = gerber_grammar_generator()

    for foil in ["outline"]:  # , 'documentation']:
        gerber_file = os.path.join(production_path, base_name + "_%s.ger" % (foil))
        gerber_data = open(gerber_file, "r").read()
        gerber_svg = create_gerber_svg_data(gerber_data)
        gerber_svg_layer = gerber_layers[foil]["layer"]
        gerber_svg_layer.append(gerber_svg)
        print(foil)

    # for pcb_layer in utils.getSurfaceLayers():
    for pcb_layer in config.stk["layer-names"]:
        for foil in ["conductor", "silkscreen", "soldermask"]:
            gerber_file = os.path.join(
                production_path, base_name + "_%s_%s.ger" % (pcb_layer, foil)
            )
            gerber_data = open(gerber_file, "r").read()
            gerber_svg = create_gerber_svg_data(gerber_data)
            gerber_svg_layer = gerber_layers[pcb_layer][foil]["layer"]
            gerber_svg_layer.append(gerber_svg)
            print(foil)

    output_file = os.path.join(
        config.cfg["base-dir"],
        config.cfg["locations"]["build"],
        cfg["board_name"] + "_gerber.svg",
    )

    try:
        f = open(output_file, "wb")
    except IOError as e:
        print("I/O error({0}): {1}".format(e.errno, e.strerror))

    f.write(et.tostring(doc, pretty_print=True))
    f.close()

    return
