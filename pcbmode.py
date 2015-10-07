#!/usr/bin/python

import os
import json
import argparse

# PCBmodE modules
import config
import utils.utils as utils
import utils.gerber as gerber
import utils.extract as extract
import utils.excellon as excellon
import utils.messages as msg
import utils.bom as bom
from utils.board import Board


def cmdArgSetup(pcbmode_version):
    """
    Sets up the commandline arguments form and variables
    """

    description = "PCBmodE is a script-based PCB design tool that generates SVG files from JSON inpus files. It can then convert the SVG into Gerbers. Viewing and (some) editing is done with Inkscape. "

    epilog = """
    """
    
    # commandline argument settings and parsing
    argp = argparse.ArgumentParser(description=description, 
                      add_help=True, version=pcbmode_version, epilog=epilog)
     
    argp.add_argument('-b', '--board-name',
                      dest='boards', required=True, nargs=1,
                      help='The name of the board. The location of the files should be specified in the configuration file, otherwise defaults are used')
     
    argp.add_argument('-f', '--filein', required=False,
                      dest='filein',
                      help='Input file name')
     
    argp.add_argument('-o', '--fileout',
                      dest='fileout',
                      help='Output file name')
     
    argp.add_argument('-c', '--config-file', default='pcbmode_config.json',
                      dest='config_file',
                      help='Configuration file name (default=pcbmode_config.json)')
     
    argp.add_argument('-m', '--make-board',
                      action='store_true', dest='make', default=False,
                      help="Create SVG for the board specified with the '-b'/'--board_name' switch. The output's location can be specified in the configuration file")
     
    argp.add_argument('-e', '--extract',
                      action='store_true', dest='extract', default=False,
                      help="Extract data from the generated SVG")
     
    argp.add_argument('--fab', nargs='?',
                      dest='fab', default=False,
                      help='Generate manufacturing files (Gerbers, Excellon, etc.) An optional argument specifies the fab for custom filenames')

    argp.add_argument('-p', '--make-pngs',
                      action='store_true', dest='pngs', default=False,
                      help='Generate a PNG of the board (requires Inkscape)')

    argp.add_argument('--no-layer-index',
                      action='store_true', dest='no_layer_index', default=False,
                      help='Do not add a layer index to SVG')

    argp.add_argument('--no-drill-index',
                      action='store_true', dest='no_drill_index', default=False,
                      help='Do not add a drill index to SVG')

    argp.add_argument('--no-flashes',
                      action='store_true', dest='no_flashes', default=False,
                      help='Do not add pad flashes to Gerbers')

    argp.add_argument('--no-docs',
                      action='store_true', dest='no_docs', default=False,
                      help='Do not add documentation')

    argp.add_argument('--renumber-refdefs', nargs='?',
                      dest='renumber', default=False,
                      help="Renumber refdefs (valid options are 'top-to-bottom' (default), 'bottom-to-top', 'left-to-right', 'right-to-left'")

    argp.add_argument('--make-bom', nargs='?',
                      dest='make_bom', default=False, 
                      help='Create a bill of materials')

    return argp






def makeConfig(name, version, cmdline_args):
    """
    """

    # Read in PCBmodE's configuration file. Look for it in the
    # calling directory, and then where the script is
    msg.info("Processing PCBmodE's configuration file")
    paths = [os.path.join(os.getcwdu()), # project dir
             os.path.join(os.path.dirname(os.path.realpath(__file__)))] # script dir

    filenames = ''
    for path in paths:
        filename = os.path.join(path, cmdline_args.config_file)
        filenames += "  %s \n" % filename
        if os.path.isfile(filename):
            config.cfg = utils.dictFromJsonFile(filename)
            break

    if config.cfg == {}:
        msg.error("Couldn't open PCBmodE's configuration file %s. Looked for it here:\n%s" % (cmdline_args.config_file, filenames))

    # add stuff
    config.cfg['name'] = name
    config.cfg['version'] = version
    config.cfg['base-dir'] = os.path.join(config.cfg['locations']['boards'], name)

    config.cfg['digest-digits'] = 10

    # Read in the board's configuration data
    msg.info("Processing board's configuration file")
    filename = os.path.join(config.cfg['locations']['boards'], 
                            config.cfg['name'], 
                            config.cfg['name'] + '.json')
    config.brd = utils.dictFromJsonFile(filename)

    tmp_dict = config.brd.get('config')
    if tmp_dict != None:
        config.brd['config']['units'] = tmp_dict.get('units', 'mm') or 'mm'
        config.brd['config']['style-layout'] = tmp_dict.get('style-layout', 'default') or 'default'
    else:
        config.brd['config'] = {}
        config.brd['config']['units'] = 'mm'
        config.brd['config']['style-layout'] = 'default'

    # Get style file; search for it in the project directory and 
    # where the script it
    layout_style = config.brd['config']['style-layout']
    layout_style_filename = 'layout.json'
    paths = [os.path.join(config.cfg['base-dir']), # project dir
             os.path.join(os.path.dirname(os.path.realpath(__file__)))] # script dir

    filenames = ''
    for path in paths:
        filename = os.path.join(path, config.cfg['locations']['styles'],
                                layout_style, 
                                layout_style_filename)
        filenames += "  %s \n" % filename
        if os.path.isfile(filename):
            config.stl['layout'] = utils.dictFromJsonFile(filename)
            break

    if config.stl['layout'] == {}:
        msg.error("Couldn't find style file %s. Looked for it here:\n%s" % (layout_style_filename, filenames))

    #=================================
    # Path database
    #=================================
    filename = os.path.join(config.cfg['locations']['boards'], 
                            config.cfg['name'],
                            config.cfg['locations']['build'],
                            'paths_db.json')

    # Open database file. If it doesn't exist, leave the database in
    # ots initial state of {}
    if os.path.isfile(filename):
        config.pth = utils.dictFromJsonFile(filename)


    #=================================
    # Routing
    #=================================
    filename = os.path.join(config.cfg['base-dir'], 
                            config.brd['files'].get('routing-json') or config.cfg['name'] + '_routing.json')

    # Open database file. If it doesn't exist, leave the database in
    # ots initial state of {}
    if os.path.isfile(filename):
        config.rte = utils.dictFromJsonFile(filename)
    else:
        config.rte = {}


    # namespace URLs
    config.cfg['ns'] = {
        None       : "http://www.w3.org/2000/svg",
        "dc"       : "http://purl.org/dc/elements/1.1/",
        "cc"       : "http://creativecommons.org/ns#",
        "rdf"      : "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "svg"      : "http://www.w3.org/2000/svg",
        "sodipodi" : "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
        "inkscape" : "http://www.inkscape.org/namespaces/inkscape",
        # Namespace URI are strings; they don't need to be URLs. See:
        #  http://en.wikipedia.org/wiki/XML_namespace
        "pcbmode"  : "pcbmode"
    }

    config.cfg['namespace'] = config.cfg['ns']

    # significant digits to use for floats
    config.cfg['significant-digits'] = config.cfg.get('significant-digits', 8)

    # buffer from board outline to display block edge 
    config.cfg['display-frame-buffer'] = config.cfg.get('display_frame_buffer', 1.0)

    # the style for masks used for copper pours
    config.cfg['mask-style'] = "fill:#000;stroke:#000;stroke-linejoin:round;stroke-width:%s;"

    # Sort out distances
    distances = {
      "from-pour-to": {
        "outline": 0.5,
        "drill": 0.3, 
        "pad": 0.2, 
        "route": 0.25
       }
    }

    config.brd['distances'] = (config.brd.get('distances') or 
                               distances)
    config.brd['distances']['from-pour-to'] = (config.brd['distances'].get('from-pour-to') or
                                               distances['from-pour-to'])
    dcfg = config.brd['distances']['from-pour-to']
    for key in distances['from-pour-to'].keys():
        dcfg[key] = (dcfg[key] or distances[key])

    # Commandline overrides. These are stored in a temporary dictionary
    # so that they are not written to the config file when the board's
    # configuration is dumped, with extraction, for example
    config.tmp = {}
    config.tmp['no-layer-index'] = (cmdline_args.no_layer_index or
                                    config.brd['config'].get('no-layer-index') or
                                    False)
    config.tmp['no-flashes'] = (cmdline_args.no_flashes or
                                config.brd['config'].get('no-flashes') or
                                False)
    config.tmp['no-docs'] = (cmdline_args.no_docs or
                             config.brd['config'].get('no-docs') or
                             False)
    config.tmp['no-drill-index'] = (cmdline_args.no_drill_index or
                                    config.brd['config'].get('no-drill-index') or
                                    False)


    # Define Gerber setting from board's config or defaults
    try:
        tmp = config.brd['gerber']
    except:
        config.brd['gerber'] = {}
    gd = config.brd['gerber']    
    gd['decimals'] = config.brd['gerber'].get('decimals') or 6
    gd['digits'] = config.brd['gerber'].get('digits') or 6
    gd['steps-per-segment'] = config.brd['gerber'].get('steps-per-segment') or 100
    gd['min-segment-length'] = config.brd['gerber'].get('min-segment-length') or 0.05

    # Inkscape inverts the 'y' axis for some historical reasons.
    # This means that we need to invert it as well. This should
    # be the only place this inversion happens so it's easy to
    # control if things change.
    config.cfg['invert-y'] = -1

    # Applying a scale factor to a rectanle can look bad if the height
    # and width are different. For paths, since they are typically
    # irregular, we apply a scale, but for rectangles and circles we
    # apply a buffer

    # Soldemask scales and buffers
    soldermask_dict = {
      "path-scale": 1.05,
      "rect-buffer": 0.05,
      "circle-buffer": 0.05
    }
    config.brd['soldermask'] = config.brd.get('soldermask') or {}
    for key in soldermask_dict:
        value = config.brd['soldermask'].get(key)
        if value == None:
            config.brd['soldermask'][key] = soldermask_dict[key]

    # Solderpaste scale
    solderpaste_dict = {
      "path-scale": 0.9,
      "rect-buffer": -0.1,
      "circle-buffer": -0.1
    }
    config.brd['solderpaste'] = config.brd.get('solderpaste') or {}
    for key in solderpaste_dict:
        value = config.brd['solderpaste'].get(key)
        if value == None:
            config.brd['solderpaste'][key] = solderpaste_dict[key]


    return





def main():

    # get PCBmodE version
    version = utils.get_git_revision()

    # setup and parse commandline arguments
    argp = cmdArgSetup(version)
    cmdline_args = argp.parse_args()

    # Might support running multiple boards in the future,
    # for now get the first onw
    board_name = cmdline_args.boards[0]
    makeConfig(board_name, version, cmdline_args)

    # check if build directory exists; if not, create
    build_dir = os.path.join(config.cfg['base-dir'], config.cfg['locations']['build'])
    utils.create_dir(build_dir)

    # renumber refdefs and dump board config file
    if cmdline_args.renumber is not False:
        msg.info("Renumbering refdefs")
        if cmdline_args.renumber is None:
            order = 'top-to-bottom'
        else:
            order = cmdline_args.renumber.lower()    

        utils.renumberRefdefs(order)

    # Extract routing from input SVG file
    elif cmdline_args.extract is True:
        extract.extract()

    # Create a BoM
    elif cmdline_args.make_bom is not False:
        bom.make_bom(cmdline_args.make_bom)

    else:
        # make the board
        if cmdline_args.make is True:
            msg.info("Creating board")
            board = Board()

        # Create production files (Gerbers, Excellon, etc.)
        if cmdline_args.fab is not False:
            if cmdline_args.fab is None:
                manufacturer = 'default'
            else:
                manufacturer = cmdline_args.fab.lower()
     
            msg.info("Creating Gerbers")
            gerber.gerberise(manufacturer)

            msg.info("Creating excellon drill file")
            excellon.makeExcellon(manufacturer)
     
        if cmdline_args.pngs is True:
            msg.info("Creating PNGs")
            utils.makePngs()
   
    
    filename = os.path.join(config.cfg['locations']['boards'], 
                            config.cfg['name'],
                            config.cfg['locations']['build'],
                            'paths_db.json')

    try:
        f = open(filename, 'wb')
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
 
    f.write(json.dumps(config.pth, sort_keys=True, indent=2))
    f.close()

    msg.info("Done!")



if __name__ == "__main__":
    main()
