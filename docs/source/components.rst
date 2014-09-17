##########
Components
##########

Components are an essential part of every design. Here you'll find how to define a component, and how to place it on the board.

Defining components
===================

Components are defined in their own JSON file. The skeleton of this file is the following

.. code-block:: json

    {
      "pins":
      {
      },
      "layout":
      {
        "silkscreen":
        {
        },
        "assembly":
        {
        }
      },
      "pads":
      {
      }
    }

In ``pins`` the pins of the components are "declared" by instantiating one of the pads defined in ``pads``. In ``layout`` shapes for assembly and silkscreen are added.

pins
----

The ``pins`` block is where pins are instantiated. Here's what a 2-pin footprint would look like

.. code-block:: json

    {
      "pins":
      {
      "1":
        {	
          "layout": 
          {
            "pad": "pad", 
            "location": [-1.27, 0],
     	    "show-label": false
          }
        },
      "2-TH":
        {	
          "layout": 
          {
            "pad": "pad", 
            "location": [1.27, 0]
            "label": "PWR",
            "show-label": true
          }
        }
      }
    }

Each pin has a unique key -- ``1`` and ``2-TH`` above -- which do not necessarily need to be numbers. ``pad`` instantiates the type of landing pad to use, which is defined later. ``location`` is the position of the pin relative to the *centre of the component*.

*PCBmodE* can discreetly place a label at center of the pin (this is viewable when zooming in on the pin). The label can be defined using ``label``, or if ``label`` is missing, the key will be used instead. Labels will be shown by default, and ``"show-label": false`` will disable this functionality. 


pads
----



layout shapes
-------------






Placing components
==================

.. code-block:: json

    {
      "locations":
      {
        "boards": "boards/",
        "components": "components/",
        "fonts": "fonts/",
        "build": "build/",
        "styles": "styles/"
      }
    }


.. code-block:: json

    "J2": {
      "footprint": "1x2_smd_pin", 
      "layer": "top", 
      "location": [
        36.7, 
        0
      ], 
      "rotate": -90, 
      "show": true, 
      "silkscreen": {
        "refdef": {
          "location": [
            -7.2, 
            2.16
          ], 
          "rotate": 0, 
          "rotate-with-component": false, 
          "show": true
        }, 
        "shapes": {
          "show": true
        }
      }
    }, 

SVG fonts have an SVG path for every glyph, and other useful information about how to place the font so the glyphs align. *PCBmodE* uses that information to place text on the board's layers.

The folder in which *PCBmodE* looks for a font is defined in the the configuration file ``pcbmode_config.json``.

.. code-block:: json

    {
      "locations":
      {
        "boards": "boards/",
        "components": "components/",
        "fonts": "fonts/",
        "build": "build/",
        "styles": "styles/"
      }
    }

When looking for a font file, *PCBmodE* will first look at the local project folder and then where ``pcbmode.py`` is. 

.. tip:: When you find a font that you'd like to use, search for an SVG version of it. Many fonts at http://www.fontsquirrel.com have an SVG version for download.


Defining text
-------------

A text definition looks like the following

.. code-block:: json

    {
      "type": "text", 
      "font-family": "Overlock-Regular-OTF-webfont", 
      "font-size": "1.5mm", 
      "letter-spacing": "0mm", 
      "line-height": "1.5mm", 
      "location": [
        -32.39372, 
        -33.739699
      ], 
      "rotate": 0, 
      "style": "fill", 
      "value": "Your text\nhere!"
    }

type
  ``text``
font-family
  The name of the font file, without the ``.svg``
font-size
  Font size in mm (the ``mm`` must be present)
letter-spacing
  ``0mm`` maintains the natural spacing defined by the font. A positive/negative value will increase/decrease the spacing
line-height
  Controls the distance between lines; a negative value is allowed
location
  The *center* of the text object will be placed at coordinates ``x`` and ``y`` 
rotate
  Clock-wise rotation in degrees
style
  ``fill`` or ``stroke``
value
  The text to display; use ``\n`` for newline

When defining text for placement on a particular PCB layer, add a list of layers where the shape is to be placed

.. code-block:: json

    {
      "layers": [
        "bottom"
      ] 
    }






