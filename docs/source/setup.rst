#####
Setup
#####

We test *PCBmodE* with Python 3.7 under Linux, but it may or may not
work on other operating systems.

It comes in the form of a installable tool called ``pcbmode`` which is
run from the command line.

What you'll need
================

* Python 3.7+
* Inkscape 1.0+
* Text editor

Installation in a virtual environment 
=====================================

Use a virtual environment to keep *PCBmodE* in its own isolated
environments, for example Python3's ``venv``. If you don't have
``venv``, get it like this:

.. code-block:: bash

                sudo apt-get install python3-venv

These instructions describe how to build *PCBmodE* for use in a
virtual environment. To be able to build python-lxml (one of
*PCBmodE*'s dependencies) you need to install some system-level
development packages. On Debian based systems these are installed like
this:

.. code-block:: bash

                sudo apt-get install libxml2-dev libxslt1-dev python-dev

.. note:: You're reading the documentation for version 5 of *PCBmodE*,
          'Cinco'. The link below will get you that branch while we're
          working on it, and before its release.

Get the *PCBModE* source from GitHub. 

.. code-block:: bash

                git clone https://github.com/boldport/pcbmode/tree/cinco-master

Now run these commands to create a virtual environment, for example in
the directory ``pcbmode-env/`` next to ``pcbmode/``. Then create the
virtual environment like this:

.. code-block:: bash

                python3 -m venv pcbmode-env
                source pcbmode-env/bin/activate
		cd pcbmode

where you can replace ``pcbmode-env`` with a name of your chooseing. If you want
to install *PCBmodE*, run

.. code-block:: bash

		pip install .

but if you want to develop it, run

.. code-block:: bash

		pip install --editable . 

After installation, *PCBmodE* will be available in your path as an
executable ``pcbmode``. But since it was installed in a virtual environment,
the ``pcbmode`` command will only be available in your path after
running ``source pcbmode-env/bin/activate`` and will no longer be in
your path after running ``deactivate``, which gets you out of the
virtual environment. You will need to activate the virtual environment each
time you want to run ``pcbmode`` from a new terminal window.

Packages are not installed globally, so to start from scratch you can just
follow these steps:

.. code-block:: bash

  deactivate	     # skip if pcbmode-env is not active
  rm -r pcbmode-env
  cd pcbmode
  git clean -dfX     # erases any untracked files (build files etc). Save your work!

Running PCBmodE
===============

.. tip:: To see all the options that *PCBmodE* supports, use ``pcbmode
         --help``

To make a create an SVG of your board you'd use a command like this: 

.. code-block:: bash

                pcbmode -b <board-name>.json -m

where ``board-name.json`` is your board file. If you're nor running ``pcbmode``
at the path where ``board.json`` is, you'll need to specify the path to it,
like this for example:

.. code-block:: bash

                boards/<project-name>/<board-name>.json

Youre ``board-name.json`` will tell *PCBmodE* where the rest of the file are,
for example

.. code-block:: json

                "project-params":
                {
                "input":
                  {
                    "routing-file": "board-routing.json",
                    "svg-file": "build/gent-pcbmode-v5-test.svg"
                  },
                  "output":
                  {
                    "svg-file": "build/gent-pcbmode-v5-test.svg",
                    "gerber-preamble": "build/prod/gent-pcbmode-v5-test_"
                  }
                }

Again, you'll need to specify the path where *PCBmodE* should expect file and
place files relative to the path where ``board-name.json`` is.

Where component and shape files are are defined in ``pcbmode_config.json``.
*PCBmodE* will load its default settings and override it with settings in a
local ``config/pcbmode_config.json`` if it exists.

The defaults for where to find component and shape files are the following:

.. code-block:: bash

                "shapes":
                {
                  "path": "shapes"
                },
                "components":
                {
                  "path": "components"
                }


So here's one way to organise the build environment

.. code-block:: bash

                beautiful-pcbs/
                  pcbmode-env/
                  pcbmode/
                  boards/
                    my-board/                # a PCB project
                      my-board.json
                      my-board_routing.json
                      components/
                      shapes/
                      docs/
                        ...
                    cordwood/                # another PCB project
                      ...


To make the ``my-board`` board from the ``beautiful-pcbs`` path, run

.. code-block:: bash

                pcbmode -b boards/my-board/my-board.json -m

and then open the SVG with Inkscape

.. code-block:: bash

                inkscape beautiful-pcbs/boards/my-board/build/my-board.svg

If the SVG opens you're good to go!

.. note:: *PCBmodE* processes a lot of shapes on the first time it is
          run, so it will take a noticeable amount. This time will be
          dramatically reduced on subsequent invocations since
          *PCBmodE* caches the shapes in a datafile within the
          project's build directory.
