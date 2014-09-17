######
Shapes
######

Overview
========

Shapes are the basic building blocks of *PCBmodE*, and are defined in JSON format. Here's an example of a 'path' shape:

.. code-block:: json

    {
      "type": "path", 
      "layer": "bottom", 
      "location": [3.1, 5.667],
      "stroke-width": 1.2, 
      "style": "stroke", 
      "value": "m -48.3,0 0,-5.75 c 0,-1.104569 0.895431,-2 2,-2 0,0 11.530272,-0.555504 17.300001,-0.5644445 10.235557,-0.015861 20.4577816,0.925558 30.6933324,0.9062128 C 10.767237,-7.4253814 19.826085,-8.3105055 28.900004,-8.3144445 34.703053,-8.3169636 46.3,-7.75 46.3,-7.75 c 1.103988,0.035813 2,0.895431 2,2 l 0,5.75 0,5.75 c 0,1.104569 -0.895431,2 -2,2 0,0 -11.596947,0.5669636 -17.399996,0.5644445 C 19.826085,8.3105055 10.767237,7.4253814 1.6933334,7.4082317 -8.5422174,7.3888865 -18.764442,8.3303051 -28.999999,8.3144445 -34.769728,8.305504 -46.3,7.75 -46.3,7.75 c -1.103982,-0.036019 -2,-0.895431 -2,-2 l 0,-5.75"
    }


This will place an SVG path as a stroke with width 1.2 mm at location x=3.1 and y=5.667. The shape will be placed on the bottom layer of the PCB.

Shape types
===========

Each shape must be defined with a ``type``; for each ``type`` there are some mandatory fields.

Rectangle
---------

.. code-block:: json

    {
      "type": "rect",
      "layer": ["top"],
      "width": 1.7, 
      "height": 1.7,
      "radii": {"tl": 0, 
                "tr": 0.3, 
                "bl": 0.3, 
                "br": 0.3},
      "rotate": 15,
      "style": "fill"
    }

type
  Place a rectangle
layer
  A list of layers to place the shape on
width
  The width of the rectangle
height
  The height of the rectangle
radii
  The radius of round corners
    tl: top left, 
    tr: top right, 
    bl: bottom left, 
    br: bottom right,
rotate
  Rotation in clock-wise angles
style
  Define the style of the shape, can be one of the two
    fill: filled shape
    stroke: apply a stroke




Circle
------


Path
----
