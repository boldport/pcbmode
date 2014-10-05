######
Shapes
######

Shapes are the basic building blocks of *PCBmodE*. Here's an example of a shape type ``path``:

.. code-block:: json

    {
      "type": "path", 
      "layers": ["bottom"], 
      "location": [3.1, -5.667],
      "stroke-width": 1.2, 
      "style": "stroke",
      "value": "m -48.3,0 0,-5.75 c 0,-1.104569 0.895431,-2 2,-2 0,0 11.530272,-0.555504 17.300001,-0.5644445 10.235557,-0.015861 20.4577816,0.925558 30.6933324,0.9062128 C 10.767237,-7.4253814 19.826085,-8.3105055 28.900004,-8.3144445 34.703053,-8.3169636 46.3,-7.75 46.3,-7.75 c 1.103988,0.035813 2,0.895431 2,2 l 0,5.75 0,5.75 c 0,1.104569 -0.895431,2 -2,2 0,0 -11.596947,0.5669636 -17.399996,0.5644445 C 19.826085,8.3105055 10.767237,7.4253814 1.6933334,7.4082317 -8.5422174,7.3888865 -18.764442,8.3303051 -28.999999,8.3144445 -34.769728,8.305504 -46.3,7.75 -46.3,7.75 c -1.103982,-0.036019 -2,-0.895431 -2,-2 l 0,-5.75"
    }

This will place an SVG path as a ``stroke`` with width ``1.2 mm`` at location ``x=3.1`` and ``y=5.667``. The shape will be placed on the bottom layer of the PCB.

Shape types
===========

For each shape a ``type`` must be defined. Below are the available shapes.

Rectangle
---------

Below is an example of a filled rectangle with rounded corners except for the top left corner.

.. code-block:: json

    {
      "type": "rect",
      "layers": ["top"],
      "width": 1.7, 
      "height": 1.7,
      "location": [6, 7.2],
      "radii": {"tl": 0, 
                "tr": 0.3, 
                "bl": 0.3, 
                "br": 0.3},
      "rotate": 15,
      "style": "fill"
    }

type
  ``rect``: place a rectangle
layers (optional; default ``["top"]``)
  list: layers to place the shape on (even if placing on a single layer, the definition needs to be in a form of a list)
width 
  float: width of the rectangle
height
  float: height of the rectangle
location (optional; default ``[0,0]``)
  list: ``x`` and ``y`` coordinates for where to place the shape
radii (optional)
  dict: radius of round corners 
  ``tl``: top left radius,   
  ``tr``: top right radius,   
  ``bl``: bottom left radius,   
  ``br``: bottom right radius,  
rotate (optional; default ``0``)
  float: rotation, clock-wise degrees
style (optional; default depends on sheet)
  ``stroke`` or ``fill``: style of the shape
stroke-width (optional; default depends on sheet; ignored unless ``style`` is ``stroke``)
  float: stroke width



Circle
------

Below is an example of a circle outline of diameter 1.7 mm and stroke width of 0.23 mm

.. code-block:: json

    {
      "type": "circle",
      "layers": ["bottom"],
      "location": [-3.2, -6],
      "diameter": 1.7, 
      "style": "stroke"
      "stroke-width": 0.23
    }

type
  ``circle``: place a circle
layers (optional; default ``["top"]``)
  list: layers to place the shape on (even if placing on a single layer, the definition needs to be in a form of a list)
location (optional; default ``[0,0]``)
  list: ``x`` and ``y`` coordinates for where to place the shape
diameter 
  float: diameter of circle
style (optional; default depends on sheet)
  ``stroke`` or ``fill``: style of the shape
stroke-width (optional; default depends on sheet; ignored unless ``style`` is ``stroke``)
  float: stroke width


Path
----

Other than simple shapes above, and SVG path can be placed.

.. code-block:: json

    {
      "type": "path", 
      "layers": ["top","bottom"], 
      "location": [3.1, 5.667],
      "stroke-width": 1.2, 
      "style": "stroke",
      "rotate": 23,
      "scale": 1.2,
      "value": "m -48.3,0 0,-5.75 c 0,-1.104569 0.895431,-2 2,-2 0,0 11.530272,-0.555504 17.300001,-0.5644445 10.235557,-0.015861 20.4577816,0.925558 30.6933324,0.9062128 C 10.767237,-7.4253814 19.826085,-8.3105055 28.900004,-8.3144445 34.703053,-8.3169636 46.3,-7.75 46.3,-7.75 c 1.103988,0.035813 2,0.895431 2,2 l 0,5.75 0,5.75 c 0,1.104569 -0.895431,2 -2,2 0,0 -11.596947,0.5669636 -17.399996,0.5644445 C 19.826085,8.3105055 10.767237,7.4253814 1.6933334,7.4082317 -8.5422174,7.3888865 -18.764442,8.3303051 -28.999999,8.3144445 -34.769728,8.305504 -46.3,7.75 -46.3,7.75 c -1.103982,-0.036019 -2,-0.895431 -2,-2 l 0,-5.75"
    }

type
  ``path``: place an SVG path
value
  path: in SVG this is the ``d`` property of a ``<path>``
layers (optional; default ``["top"]``)
  list: layers to place the shape on (even if placing on a single layer, the definition needs to be in a form of a list)
location (optional; default ``[0,0]``)
  list: ``x`` and ``y`` coordinates for where to place the shape
diameter 
  float: diameter of circle
style (optional; default depends on sheet)
  ``stroke`` or ``fill``: style of the shape
stroke-width (optional; default depends on sheet; ignored unless ``style`` is ``stroke``)
  float: stroke width
rotate (optional; default ``0``)
  float: rotation, clock-wise degrees
scale (optional; default ``1``)
  float: scale factor to apply to the path


Text
----

Placing a text shape is covered in :doc:`text`.
