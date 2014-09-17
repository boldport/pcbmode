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
            "location": [1.27, 0],
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

    {
      "J2": 
      {
        "footprint": "my-part", 
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
      }
    } 





