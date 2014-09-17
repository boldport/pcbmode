############
Copper pours
############

A `copper pour <http://en.wikipedia.org/wiki/Copper_pour>`_ covers the surface area of a board with copper while maintaining a certain buffer from other copper features, such as routes and pads. A 'bridge' can connect between a copper feature and a pour.

Defining pours
--------------

Pours are defined in their own section in the board's JSON under ``shapes``


.. code-block:: json
        
    {
      "shapes": {
        "pours": 
        [
          {
            "layers": [
              "bottom", 
              "top"
            ], 
            "type": "layer"
          }
        ]
      }
    } 


The above will place a pour over the entire top and bottom layer of the board. It's possible to pour a specific shape, and that's done just like any other shape definition. 

.. warning:: Since *PCBmodE* does not have a netlist, those bridges need to be added manually, and careful attention needs to be paid to prevent shorts -- there's no DRC!

.. info:: Even if you're pouring over a single layer, the ``layers`` definition only accepts a list, so you'd use ``["bottom"]``, not ``"bottom"``.


Defining buffers
----------------

The global settings for the buffer size between the pour and a feature is defined in the board's JSON file, as follows:

.. code-block:: json

    "distances": {
      "from-pour-to": {
        "drill": 0.4, 
        "outline": 0.25, 
        "pad": 0.4, 
        "route": 0.25
      }
    } 

If this block, or any of its definitions, is missing, defaults will be used.

These global settings can be overridden for every shape and route. For routes, it's done using the ``pcbmode:buffer-to-pour`` definition, as described in :doc:`routing`. For shapes it's done using the ``buffer-to-pour`` definition, as described in :doc:`shapes`.


