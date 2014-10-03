#####
Setup
#####

*PCBmodE* is written and tested with Python 2.7 under Linux. It may or may not work on other operating systems or later versions of Python. With time 'official' support for Windows/MAC will be added.

What you'll need
================

* Linux
* Python 2.7 + PyParsing package
* Inkscape
* Text editor

Setup
=====

By default *PCBmodE* expects to find the board files under

    boards/<board-name>

relative to the place where it is invoked. 

.. tip:: Paths where *PCBmodE* looks for thing can be changed in the config file ``pcbmode_config.json``

Here's one way to organise the build environment

    cool-pcbs/
      PCBmodE/
      boards/
        hello-solder/
          hello-solder.json
          hello-solder_routing.json
          components/
            ...
        cordwood/
          ...


To make the ``hello-solder`` board, run *PCBmodE* within ``cool-pcbs``

    python PCBmodeE/pcbmode.py -b hello-solder -m

Then open the SVG with Inkscape

    inkscape cool-pcbs/boards/hello-solder/build/hello-solder.svg

If the SVG opens you're good to go!

.. note:: *PCBmodE* processes a lot of shapes on the first time it is run, so it will take a noticeable time. This time will be dramatically reduced on subsequent invocations since *PCBmodE* caches the shapes in a datafile within the project's build directory.
