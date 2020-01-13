Shapes
######

Shapes are the building blocks of *PCBmodE*. Here's an example of how a definition of
a ``path`` type looks like:

.. code-block:: json

    {
      "type": "path", 
      "layers": ["top, "bottom"], 
      "location": [3.1, -5.667],
      "style": "stroke-width:1.2;", 
      "d": "m -48.3,0 0,-5.75 c 0,-1.104569 0.895431,-2 2,-2 0,0 11.530272,-0.555504 17.300001,-0.5644445 10.235557,-0.015861 20.4577816,0.925558 30.6933324,0.9062128 C 10.767237,-7.4253814 19.826085,-8.3105055 28.900004,-8.3144445 34.703053,-8.3169636 46.3,-7.75 46.3,-7.75 c 1.103988,0.035813 2,0.895431 2,2 l 0,5.75 0,5.75 c 0,1.104569 -0.895431,2 -2,2 0,0 -11.596947,0.5669636 -17.399996,0.5644445 C 19.826085,8.3105055 10.767237,7.4253814 1.6933334,7.4082317 -8.5422174,7.3888865 -18.764442,8.3303051 -28.999999,8.3144445 -34.769728,8.305504 -46.3,7.75 -46.3,7.75 c -1.103982,-0.036019 -2,-0.895431 -2,-2 l 0,-5.75"
    }

This will place the SVG path defined in ``d`` shown as stroke with width ``1.2 mm`` at
location ``[3.1,5.667]``. The shape will be placed on the top and bottom layers of the PCB.

Shape properties
================

Fills and strokes
-----------------

By default *PCBmodE* assumes that a shape is a 'fill' without a 'stroke'. If the shape
you want to place is a 'fill' there's no need to tell *PCBmodE* that. But if you'd like
to place a 'stroked' shape, then you need to add:

.. code-block:: json

     "style": "stroke-width:<width>;"

just like adding a CSS property. *PCBmodE* will only pay attention to ``stroke-width`` 
in the ``style`` property; all the others will be discarded when the SVG is `extracted`.

Buffer to pour
--------------

``buffer-to-pour`` defines the distance from the edge of the filled or stroked shape to 
a pour. This overrides global settings defined in the board's JSON, or *PCBmodE*'s
defaults if those are not defined locally.

Location
--------

Location is defined as an ``x``, ``y`` coordinate

.. code-block:: json

     "location": [<x>m <y>]

The location definition is relative to the hierarchy. So if you're defining a pad, the
location is relative to the footprint's center.

Default: ``[0,0]``.

Layers
------

A list of which layers to put the shape in

.. code-block:: json

     "layers": ["top", "bottom"]

Even if the shape is placed in a single layer, it needs to be defined as a list

.. code-block:: json

     "layers": ["bottom"]

Default: ``["top"]``.


Rotation
--------

Default: `0`.

Scale
-----

Default: `1`.


Shape types
===========

You must define a shape ``type`` with each shape definition.


Rectangle
---------

.. code-block:: json

    {
      "type": "rect",
      "width": 1.7, 
      "height": 1.7,
      "radii": {"tl": 0, 
                "tr": 0.3, 
                "bl": 0.3, 
                "br": 0.3}
    }

type
  ``rect``: place a rectangle
width 
  int/float: width of the rectangle
height
  int/float: height of the rectangle
radii (optional)
  dict: radius of round corners 
  ``tl``: top left radius,   
  ``tr``: top right radius,   
  ``bl``: bottom left radius,   
  ``br``: bottom right radius,  


Circle
------

.. code-block:: json

    {
      "type": "circle",
      "diameter": 1.7, 
    }

type
  ``circle``: place a circle
diameter 
  float: diameter of circle


Path
----

.. code-block:: json

    {
      "type": "path", 
      "d": "m -48.3,0 0,-5.75 c 0,-1.104569 0.895431,-2 2,-2 0,0 11.530272,-0.555504 17.300001,-0.5644445 10.235557,-0.015861 20.4577816,0.925558 30.6933324,0.9062128 C 10.767237,-7.4253814 19.826085,-8.3105055 28.900004,-8.3144445 34.703053,-8.3169636 46.3,-7.75 46.3,-7.75 c 1.103988,0.035813 2,0.895431 2,2 l 0,5.75 0,5.75 c 0,1.104569 -0.895431,2 -2,2 0,0 -11.596947,0.5669636 -17.399996,0.5644445 C 19.826085,8.3105055 10.767237,7.4253814 1.6933334,7.4082317 -8.5422174,7.3888865 -18.764442,8.3303051 -28.999999,8.3144445 -34.769728,8.305504 -46.3,7.75 -46.3,7.75 c -1.103982,-0.036019 -2,-0.895431 -2,-2 l 0,-5.75"
    }

type
  ``path``: place an SVG path
d
  path: in SVG this is the ``d`` property of a ``<path>``


Text
----

Covered in :doc:`text`.
