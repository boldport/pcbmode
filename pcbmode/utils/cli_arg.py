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


import argparse


def setup():
    """
    Sets up the commandline arguments form and variables
    """

    description = """
    PCBmodE is a script-based PCB design tool that generates SVG files
    from JSON inpus files. It can then convert the SVG into
    Gerbers. Viewing and (some) editing is done with Inkscape. You can
    support this project here: https://github.com/sponsors/saardrimer
    """

    epilog = """
    """

    # commandline argument settings and parsing
    argp = argparse.ArgumentParser(
        description=description, add_help=True, epilog=epilog
    )

    argp.add_argument(
        "-b",
        "--board-name",
        dest="boards",
        required=True,
        nargs=1,
        help="The name of the board. The location of the files should \
                            be specified in the configuration file, otherwise defaults \
                            are used",
    )

    argp.add_argument(
        "-f", "--filein", required=False, dest="filein", help="Input file name"
    )

    argp.add_argument("-o", "--fileout", dest="fileout", help="Output file name")

    argp.add_argument(
        "-c",
        "--config-file",
        default="pcbmode_config.json",
        dest="config_file",
        help="Configuration file name (default=pcbmode_config.json)",
    )

    argp.add_argument(
        "-m",
        "--make-board",
        action="store_true",
        dest="make",
        help="Create SVG for the board specified with the '-b'/'--board_name' \
                            switch. The output's location can be specified in the \
                            configuration file",
    )

    argp.add_argument(
        "-e",
        "--extract",
        action="store_true",
        dest="extract",
        help="Extract routing and component placement from board's SVG",
    )

    argp.add_argument(
        "--extract-refdefs",
        action="store_true",
        dest="extract_refdefs",
        help="Extract components' reference designator location and rotation \
                            from board's SVG",
    )

    argp.add_argument(
        "--fab",
        nargs="?",
        dest="fab",
        default=False,
        help="Generate manufacturing files (Gerbers, Excellon, etc.) An optional \
                            argument specifies the fab for custom filenames",
    )

    argp.add_argument(
        "-p",
        "--make-pngs",
        action="store_true",
        dest="pngs",
        help="Generate a PNG of the board (requires Inkscape)",
    )

    argp.add_argument(
        "--no-cache",
        action="store_true",
        dest="no_cache",
        help="Do not create a cache file (use for testing)",
    )

    argp.add_argument(
        "--renumber-refdefs",
        nargs="?",
        dest="renumber",
        default=False,
        help="Renumber refdefs (valid options are 'top-to-bottom' (default), \
                            'bottom-to-top', 'left-to-right', 'right-to-left'",
    )

    argp.add_argument(
        "--make-coord-file",
        nargs="?",
        dest="coord_file",
        default=False,
        help="Create a simple placement coordinate CSV file",
    )

    argp.add_argument(
        "--make-bom",
        nargs="?",
        dest="make_bom",
        default=False,
        help="Create a bill of materials",
    )

    # Mutually exclusive optional overrides
    layer_index = argp.add_mutually_exclusive_group(required=False)
    layer_index.add_argument(
        "--layer-index",
        action="store_true",
        dest="show_layer_index",
        help="Create a layer index to the SVG",
    )
    layer_index.add_argument(
        "--no-layer-index",
        action="store_false",
        dest="show_layer_index",
        help="Do not create a layer index to SVG",
    )
    argp.set_defaults(show_layer_index=None)

    drill_index = argp.add_mutually_exclusive_group(required=False)
    drill_index.add_argument(
        "--drill-index",
        action="store_true",
        dest="show_drill_index",
        help="Create a drill index to the SVG",
    )
    drill_index.add_argument(
        "--no-drill-index",
        action="store_false",
        dest="show_drill_index",
        help="Do not create a drill index to SVG",
    )
    argp.set_defaults(show_drill_index=None)

    docs = argp.add_mutually_exclusive_group(required=False)
    docs.add_argument(
        "--docs",
        action="store_true",
        dest="show_docs",
        help="Create the document text on SVG",
    )
    docs.add_argument(
        "--no-docs",
        action="store_false",
        dest="show_docs",
        help="Do not create document text on SVG",
    )
    argp.set_defaults(show_docs=None)

    flashes = argp.add_mutually_exclusive_group(required=False)
    flashes.add_argument(
        "--flashes",
        action="store_true",
        dest="show_flashes",
        help="Place flashes in Gerbers",
    )
    flashes.add_argument(
        "--no-flashes",
        action="store_false",
        dest="show_flashes",
        help="Do not place flashes in Gerbers",
    )
    argp.set_defaults(show_flashes=None)

    return argp
