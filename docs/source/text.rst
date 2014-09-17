####
Text
####

One of the unique features of *PCBmodE* is that any font can be used for any text on the board. Well, as long as it is in SVG form.

Fonts
-----

SVG fonts have an SVG path for every glyph, and other useful information about how to place the font so the glyphs align. *PCBmodE* uses that information to place text on the board's layers.

The folder in which *PCBmodE* looks for a font is defined in the the configuration file ``pcbmode_config.json``

.. code-block:: json
    "locations":
    {
      "boards": "boards/",
      "components": "components/",
      "fonts": "fonts/",
      "build": "build/",
      "styles": "styles/"
    }

When looking for a font file, *PCBmodE* will first look at the local project folder and then where ``pcbmode.py`` is. 

.. tip:: When you find a font that you'd like to use, search for an SVG version of it. Many fonts at `http://www.fontsquirrel.com`_ have an SVG version for download.


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
  Controls the distance between lines. A negative value is allowed
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






