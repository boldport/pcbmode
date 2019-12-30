#!/usr/bin/python

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


def load_style():
    """
    Load the stylesheets. (For now only for 'layout')
    First look for the file in the project path (assuming the default was overriden),
    then load the default from PCBmodE.
    """

    filename = Path(config.cfg["styles"]["stylesheet-for-layout"])

    if (config.tmp["project-path"] / filename).exists():
        config.stl["layout"] = utils.dictFromJsonFile(
            config.tmp["project-path"] / filename
        )
    else:
        config.stl["layout"] = utils.dictFromJsonFile(Path(__file__).parent / filename)


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

    if config.cfg["params"]["invert-y-axis"]:
        config.cfg["iya"] = -1
    else:
        config.cfg["iya"] = 1


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

    # Info while in development
    msg.info("Important!")
    msg.info(
        "You are using a version of PCBmodE ('cinco') that's actively under development."
    )
    msg.info("Please support this project at https://github.com/sponsors/saardrimer.\n")

    # Setup and parse commandline arguments
    argp = cli_arg.setup()
    cmdline_args = argp.parse_args()

    config.tmp["pcbmode-path"] = Path(__file__).parent

    # Might support running multiple boards in the future,
    # for now get the first one
    project_path = cmdline_args.boards[0]
    config.tmp["project-file"] = Path(project_path).name
    config.tmp["project-path"] = Path(project_path).parent

    msg.info("Loading PCBmodE's configuration data")
    load_pcbmode_config()
    msg.info("Loading board's configuration data")
    load_board_file()
    load_style()
    load_stackup()
    load_cache()
    load_routing()
    set_y_axis_invert()
    apply_overrides(cmdline_args)

    # Renumber refdefs and dump board config file
    if cmdline_args.renumber is not False:
        msg.info("Renumbering refdefs")
        if cmdline_args.renumber is None:
            order = "top-to-bottom"
        else:
            order = cmdline_args.renumber.lower()

        utils.renumberRefdefs(order)

    # Extract information from SVG file
    elif cmdline_args.extract is True or cmdline_args.extract_refdefs is True:
        extract.extract(
            extract=cmdline_args.extract, extract_refdefs=cmdline_args.extract_refdefs
        )

    # Create a BoM
    elif cmdline_args.make_bom is not False:
        bom.make_bom(cmdline_args.make_bom)

    elif cmdline_args.coord_file is not False:
        coord_file.makeCoordFile(cmdline_args.coord_file)

    else:
        # Make the board
        if cmdline_args.make is True:
            msg.info("Creating board")
            board = Board()

        # Create production files (Gerbers, Excellon, etc.)
        if cmdline_args.fab is not False:
            if cmdline_args.fab is None:
                manufacturer = "default"
            else:
                manufacturer = cmdline_args.fab.lower()

            msg.info("Creating Gerbers")
            gerber.gerberise(manufacturer)

            msg.info("Creating excellon drill file")
            excellon.makeExcellon(manufacturer)

        if cmdline_args.pngs is True:
            msg.info("Creating PNGs")
            utils.makePngs()

    filename = config.tmp["project-path"] / config.cfg["cache"]["file"]
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_text(json.dumps(config.pth, sort_keys=True, indent=2))

    msg.info("Done!")


if __name__ == "__main__":
    main()
