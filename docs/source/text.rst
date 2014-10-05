####
Text
####

One of the unique features of *PCBmodE* is that any font -- as long as it is in SVG form -- can be used for any text on the board.

Fonts
-----

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
      "layers": ["bottom"],
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
  ``text``: place a text element
layers (optional; default ``["top"]``)
  list: layers to place the shape on (even if placing on a single layer, the definition needs to be in a form of a list)
font-family
  text: The name of the font file, without the ``.svg``
font-size
  float: font size in mm (the ``mm`` must be present)
value
  text: the text to display; use ``\n`` for newline
letter-spacing (optional; default ``0mm``)
  float: positive/negative value increases/decreases the spacing. ``0mm`` maintains the natural spacing defined by the font
line-height (optional; defaults to ``font-size``)
  float: the distance between lines; a negative value is allowed
location (optional; default ``[0, 0]``)
  list: ``x`` and ``y`` to place the *center* of the text object  
rotate (optional; default ``0``)
  float: rotation, clock-wise degrees
style (optional; default depends on sheet)
  ``stroke`` or ``fill``: style of the shape
stroke-width (optional; default depends on sheet; ignored unless ``style`` is ``stroke``)
  float: stroke width






