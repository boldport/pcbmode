############
Layers and stackup
############

The layering of a PCB is defined by a "stackup", a lit of layers and their properties, like thickness and copper lamination. "Layers" can be quite ambiguous because it can mean a physical layer, but also a logical layer (like for assembly, or "keep-out"). 

With *PCBmodE* we'll use "layer" to mean a physical or logical top-level layer of a certain type, and "foil" to mean a sub-layer of a top-level layer. Layers and foils are defined in a json file that's called by the project's configuration json file. 

Our stackup defines the physical and logical layers of the design and is used by *PCBmodE* to create the layers that are displayed by Inkscape. This means that it is here that we also control the order in which the layers are shown and weather they are hidden or locked when the SVG is created. 

We can also extend or reduce the layer-foil structure to our needs. (Every foil definition can have its own foil list, so any depth of hierarchy can be created.) All we need to do is add that layer or foil to the stackup JSON and assign shapes to it.

When opening a *PCBmodE* SVG in Inkscape, the board's layers can be manipulated by opening the layer pane (``CTRL+SHIFT+L``). Each layer can then be set to be hidden/visible or editable/locked. The default for each layer is defined in ``utils/svg.py``

Here's an example of logical layer for 'info', divided into three sub-foils.

.. code-block:: json

  {
    "info": {
      "name": "info",
      "type": "info",
      "place": true,
      "hide": false,
      "lock": true,
      "foils": [
        {
          "type": "documentation",
          "name": "documentation",
          "place": true,
          "hide": false,
          "lock": false
        },
        {
          "type": "dimensions",
          "name": "dimensions",
          "place": true,
          "hide": false,
          "lock": false
        },
        {
          "type": "origin",
          "name": "origin",
          "place": true,
          "hide": true,
          "lock": false
        }
      ]
    }
  }

Each layer or foil can have these directives:

``place``:``<true|false>``, create and place the layer in the SVG
``hide``:``<true|false>``, hide the layer
``lock``:``<true|false>``, lock the layer

The ``type`` property is used by *PCBmodE* to know how to process the shapes. The ``name`` property can by customised.

Here's an example of a physical layer with ``place``, ``hide``, and ``lock`` removed.

.. code-block:: json

  {    
    "top": {
      "name": "top",
      "type": "signal",
      "surface": true,
      "foils": [
        {
          "type": "placement",
          "name": "placement",
        },
        {
          "type": "assembly",
          "name": "assembly",
        },
        {
          "type": "solderpaste",
          "name": "solderpaste",
          "place": true,
          "hide": true,
          "lock": false
        },
        {
          "type": "silkscreen",
          "name": "silkscreen",
        },
        {
          "type": "soldermask",
          "name": "soldermask",
        },
        {
          "type": "conductor",
          "name": "conductor",
          "foils": [
            {
              "type": "pours",
              "name": "pours",
            },
            {
              "type": "pads",
              "name": "pads",
            },
            {
              "type": "routing",
              "name": "routing",
            }
          ]
        }
      ]
    }
  }  

A layer of ``type`` ``signal`` tells *PCBmodE* that this is a physical layer of the PCB while ``surface``:``<true|false>`` indicates that this is a surface layer because those require special consideration. Of course, normally we'd have only two surface layers in a PCB design. 

We can also see that the ``conductor`` foil has three sub-foils: ``pours``, ``pads``, and ``routing``. If we wanted to extend this, we could do the following:

.. code-block:: json

        {
          "type": "conductor",
          "name": "conductor",
          "foils": [
            {
              "type": "pours",
              "name": "pours",
            },
            {
              "type": "pads",
              "name": "pads",
              "foils": [
                {
                  "type": "pads",
                  "name": "smd",
                },
                {
                  "type": "pads",
                  "name": "th",
                }
              ]
            },
            {
              "type": "routing",
              "name": "routing",
            }
          ]
        }

where we have two sub-foils for ``pads``: ``smd`` and ``th``. When *PCBmodE* generates the PCB, it will create these foils as Inkscape layers, but it is up to the designer to assign shapes to them.

.. tip:: Locking layers and foils prevent moving them by mistake while editing the SVG. Use this feature for layers that are not edited regularly.

