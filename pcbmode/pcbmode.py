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
import argparse

from pathlib import Path

from pkg_resources import resource_filename, resource_exists

from pcbmode.config import config
from pcbmode.utils import cli_arg
from pcbmode.utils import utils
from pcbmode.utils import gerber
from pcbmode.utils import extract
from pcbmode.utils import excellon
from pcbmode.utils import messages as msg
from pcbmode.utils import bom
from pcbmode.utils import coord_file
from pcbmode.utils import css_utils
from pcbmode.utils.board import Board


def load_pcbmode_config():
    """
    Load the default configuration.  If a local 'pcbmode_config'
    exists in 'config/' then override the settings in there.
    """
    config_path = "config"
    config_filename = "pcbmode_config.json"

    config_file = config.tmp["pcbmode-path"] / config_path / config_filename
    config.cfg = utils.dictFromJsonFile(config_file)

    # Override with local settings, if any
    project_config_file = config.tmp["project-path"] / config_path / config_filename
    if project_config_file.exists():
        project_config = utils.dictFromJsonFile(project_config_file)
        for key in project_config:
            config.cfg[key] = {**config.cfg[key], **project_config[key]}


def load_board_file():
    """
    Load the board's configuration data
    """

    filename = config.tmp["project-path"] / config.tmp["project-file"]
    config.brd = utils.dictFromJsonFile(filename)


def load_stylesheet():
    """
    Load the layout CSS stylesheets.
    """
    filename = Path(config.cfg["styles"]["stylesheet-for-layout"])
    fn = config.tmp["project-path"] / filename
    if fn.exists():
        raw_css = (fn / filename).read_text()
    else:
        fn = Path(__file__).parent / filename
        raw_css = fn.read_text()

    config.stl["layout"] = raw_css


def load_stackup():
    """
    Load and process the stackup for the board
    """
    filename = Path(config.cfg["stackup"]["definition-file"])

    if (config.tmp["project-path"] / filename).exists():
        config.stk = utils.dictFromJsonFile(config.tmp["project-path"] / filename)
    else:
        config.stk = utils.dictFromJsonFile(Path(__file__).parent / filename)

    config.stk["layers-dict"], config.stk["layer-names"] = utils.getLayerList()
    config.stk["surface-layers"] = [
        config.stk["layers-dict"][0],
        config.stk["layers-dict"][-1],
    ]
    config.stk["internal-layers"] = config.stk["layers-dict"][1:-1]
    config.stk["surface-layer-names"] = [
        config.stk["layer-names"][0],
        config.stk["layer-names"][-1],
    ]
    config.stk["internal-layer-names"] = config.stk["layer-names"][1:-1]


def load_cache():
    """
    Load cache file if it exists
    """
    filename = config.tmp["project-path"] / config.cfg["cache"]["file"]
    if filename.is_file():
        config.pth = utils.dictFromJsonFile(filename)


def load_routing():
    """
    """
    filename = Path(
        config.tmp["project-path"]
        / config.brd["project-params"]["input"]["routing-file"]
    )
    config.rte = utils.dictFromJsonFile(filename)


def set_y_axis_invert():
    """
    Inkscape inverts the 'y' axis for some historical reasons. This
    means that we need to invert it as well. Use 'iya' whenever processing
    outputting or reading the y-axis. Inkscape 1.0+ should have an option
    to not invert the y-axis.
    """
    config.cfg["iya"] = -1 if config.cfg["params"]["invert-y-axis"] else 1


def apply_overrides(cli_args):
    """
    Apply commandline switches's overrides 
    """
    if cli_args.show_layer_index is not None:
        config.cfg["create"]["layer-index"] = cli_args.show_layer_index
    if cli_args.show_docs is not None:
        config.cfg["create"]["docs"] = cli_args.show_layer_index
    if cli_args.show_drill_index is not None:
        config.cfg["create"]["drill-index"] = cli_args.show_layer_index
    if cli_args.show_flashes is not None:
        config.cfg["create"]["flashes"] = cli_args.show_layer_index


def main():
    # License information
    print("PCBmodE, Copyright (C) 2020 Saar Drimer")
    print("This program comes with ABSOLUTELY NO WARRANTY. This is free software,")
    print("and you are welcome to redistribute it under certain conditions.")
    print("See the LICENSE file that came with this software for details.")
    print()

    # Info while in development
    print("Important!")
    print("This version of PCBmodE ('cinco') is actively under development.")
    print("Support this project at https://github.com/sponsors/saardrimer")
    print()

    print("Running... ", end="", flush=True)

    argp = cli_arg.setup()  # setup cli arguments
    cmdline_args = argp.parse_args()  # parse arguments

    # Get the path to PCBmodE
    config.tmp["pcbmode-path"] = Path(__file__).parent

    # Might support running multiple boards in the future,
    # for now get the first one
    project_path = cmdline_args.boards[0]
    config.tmp["project-file"] = Path(project_path).name
    config.tmp["project-path"] = Path(project_path).parent

    load_pcbmode_config()
    load_board_file()
    load_stylesheet()
    load_stackup()
    load_routing()
    set_y_axis_invert()
    apply_overrides(cmdline_args)

    # Extract information from SVG file
    if cmdline_args.extract is True or cmdline_args.extract_refdefs is True:
        extract.extract(
            extract=cmdline_args.extract, extract_refdefs=cmdline_args.extract_refdefs
        )

    # Renumber refdefs and dump board config file
    elif cmdline_args.renumber is not False:
        if cmdline_args.renumber is None:
            order = "top-to-bottom"
        else:
            order = cmdline_args.renumber.lower()

        utils.renumberRefdefs(order)

    # Create a BoM
    elif cmdline_args.make_bom is not False:
        bom.make_bom(cmdline_args.make_bom)

    elif cmdline_args.coord_file is not False:
        coord_file.makeCoordFile(cmdline_args.coord_file)

    else:

        # Load the cache file
        if cmdline_args.no_cache is False:
            load_cache()

        # Make the board
        if cmdline_args.make is True:
            board = Board()

        # Create production files (Gerbers, Excellon, etc.)
        if cmdline_args.fab is not False:
            if cmdline_args.fab is None:
                manufacturer = "default"
            else:
                manufacturer = cmdline_args.fab.lower()

            gerber.gerberise(manufacturer)
            excellon.makeExcellon(manufacturer)

        if cmdline_args.pngs is True:
            utils.makePngs()

    # Save cache to file if cache isn't disabled
    if cmdline_args.no_cache is False:
        filename = config.tmp["project-path"] / config.cfg["cache"]["file"]
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_text(json.dumps(config.pth, sort_keys=True, indent=2))

    print("done!")


if __name__ == "__main__":
    main()
