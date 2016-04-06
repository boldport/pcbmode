#####
Setup
#####

*PCBmodE* is written and tested with Python 2.7 under Linux. It may or may not work on other operating systems or later versions of Python. With time 'official' support for Windows/MAC will be added.

What you'll need
================

* Python 2.7
* Inkscape
* Text editor

Installation with ``pip``
=========================

System packages for `python-parsing` and `python-lxml` are
required. If they aren't already installed, pip will attempt to build
them. See `Installation with virtualenv` for information on the
required development packages.

.. tip:: You'll need root permissions to install pcbmode
	 system-wide. Be sure to use sudo/su as needed.

.. code-block:: bash

		pip install pcbmode

`or`

.. code-block:: bash

		easy_install pcbmode

Often it's helpful to segregate applications to their own virtual
environments. As a bonus, root permissions are not required.

.. tip:: To use virtualenv you will need to build the python-lxml
	 package. For this to succeed, you'll need to install the
	 development packages for several programs and libraries. On
	 Ubuntu, this looks like: ``apt-get install libxml2-dev
	 libxslt1-dev python-dev``

.. code-block:: bash

		virtualenv pcbmode-env
		. pcbmode-env/bin/activate
		pip install pcbmode

Installation from Source
========================

Fetch the *PCBModE* source. Stable snapshots are available at `https://github.com/boldport/pcbmode/releases
<https://github.com/boldport/pcbmode/releases>`_. The latest
development sources are available via git:

``git clone https://github.com/boldport/pcbmode.git``

.. code-block:: bash

		cd pcbmode
		virtualenv env          # Virtualenv is
		. env/bin/activate      # Optional
		python setup.py install # Use sudo/su if needed (e.g. not using virtualenv)

After installation, PCBmodE will be available in your path as
``pcbmode``. If you are using `virtualenv`, the ``pcbmode`` command
will only be available in your path after ``. env/bin/activate`` and
will no longer be in your path after running ``deactivate``.

Setup
=====

.. tip:: To see all the options that *PCBmodE* supports, use ``pcbmode --help``

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

    pcbmode -b hello-solder -m

Then open the SVG with Inkscape

    inkscape cool-pcbs/boards/hello-solder/build/hello-solder.svg

If the SVG opens you're good to go!

.. note:: *PCBmodE* processes a lot of shapes on the first time it is run, so it will take a noticeable time. This time will be dramatically reduced on subsequent invocations since *PCBmodE* caches the shapes in a datafile within the project's build directory.


