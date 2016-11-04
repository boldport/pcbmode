#####
Setup
#####

*PCBmodE* is written and tested with Python 2.7 under Linux. It may or may not work on other operating systems or later versions of Python. With time 'official' support for Windows/MAC will be added.

It comes in the form of a installable tool called `pcbmode` which is
run from the command line.

What you'll need
================

* Python 2.7
* Inkscape
* Text editor

Installation from Source with Virtualenv
========================================

Virualenv is a Python tool that makes it easy to keep applications in
their own isolated environments. As a bonus, root permissions are not
required. This can come useful when running experimental versions of
PCBmodE.

These instructions describe how to build PCBmodE for use in a
virtualenv. To be able to build python-lxml (one of PCBmodE's
dependencies) you need to install some system-level development
packages. On Debian based systems these are installed like this:

.. code-block:: bash

                sudo apt-get install libxml2-dev libxslt1-dev python-dev

Fetch the *PCBModE* source. Stable snapshots are available at
`https://github.com/boldport/pcbmode/releases
<https://github.com/boldport/pcbmode/releases>`_. The latest
development sources are available via git:

.. code-block:: bash

                git clone https://github.com/boldport/pcbmode.git

After putting PCBmodE in a directory called `pcbmode`, run these
commands to create a virtualenv in the directory `pcbmode-env/` next
to it, and install PCBmodE in the virtualenv.

.. code-block:: bash

                virtualenv pcbmode-env
                source pcbmode-env/bin/activate
		cd pcbmode
		python setup.py install

After installation, PCBmodE will be available in your path as
``pcbmode``. But since it was installed in a virtualenv, the
``pcbmode`` command will only be available in your path after running
``pcbmode-env/bin/activate`` and will no longer be in your path after
running ``deactivate``. You will need to activate the virtualenv each
time you want to run `pcbmode` from a new terminal window.

Nothing is installed globally, so to start from scratch you can just follow these steps:

.. code-block:: bash

                deactivate         # skip if pcbmode-env is not active
                rm -r pcbmode-env
                cd pcbmode
                git clean -dfX     # erases any untracked files (build files etc). save your work!


Installation on Windows
========================================

Only Linux is officially supported, so consider this experimental,
and prone to breaking at any time.

Start with the dependencies:

Make sure you have Python 2.7.9 or later, this is the first Windows
version with pip bundled. It's also assumed that Python has been
added to the system path.

Install Lxml:
Download an appropriate binary `here <http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml>`_.

Confusingly enough, the default Python install is a 32-bit version,
even when installed on a 64-bit version, so you probably want
*lxml-3.6.4-cp27-cp27m-win32.whl*

Then upgrade pip and install the Lxml wheel:

.. code-block:: bash

                cd path\to\downloads
                python -m pip install --upgrade pip
                python -m pip install lxml-3.6.4-cp27-cp27m-win32.whl


Fetch the *PCBModE* source. Stable snapshots are available at
`https://github.com/boldport/pcbmode/releases
<https://github.com/boldport/pcbmode/releases>`_. The latest
development sources are available via git:

.. code-block:: bash

                git clone https://github.com/boldport/pcbmode.git
                cd pcbmode
                python setup.py install

                
There will now be a ``pcbmode.exe`` in your ``C:\Python27\Scripts`` directory.
Add this to the system path, or use the whole path whenever you call PCBmodE.
                
Running PCBmodE
===============

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


