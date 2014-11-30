############
Layer control
############

When opening a *PCBmodE* SVG in Inkscape, the board's layers can be manipulated by opening the layer pane (``CTRL+SHIFT+L``). Each layer can then be set to be hidden/visible or editable/locked. The default for each layer is defined in ``utils/svg.py``

.. code-block:: python

    layer_control = {
      "copper": { 
        "hidden": False, "locked": False, 
        "pours": { "hidden": False, "locked": True },
        "pads": { "hidden": False, "locked": False },
        "routing": { "hidden": False, "locked": False }
      },
      "soldermask": { "hidden": False, "locked": False },
      "solderpaste": { "hidden": True, "locked": True },
      "silkscreen": { "hidden": False, "locked": False },
      "assembly": { "hidden": False, "locked": False },
      "documentation": { "hidden": False, "locked": False },
      "dimensions": { "hidden": False, "locked": True },
      "origin": { "hidden": False, "locked": True },
      "drills": { "hidden": False, "locked": False },
      "outline": { "hidden": False, "locked": True }
    }

but can be overridden in the board's configuration file. So, for example, if we wish to have the solderpaste layers visible when the SVG is generated, we'd add 

 
.. code-block:: json

    {
      "layer-control": 
      {
        "solderpaste": { "hidden": false, "locked": true }
      }
    }

Or if we'd like the outline to be editable (instead of the default 'locked') we'd add 

.. code-block:: json

    {
      "layer-control": 
      {
        "solderpaste": { "hidden": false, "locked": true },
        "outline": { "hidden": false, "locked": false }
      }
    }

.. info:: The reason that some layers are locked by default -- 'outline' is a good example -- is because they are not edited regularly, but span the entire board so very often take focus when slecting objects. Locking them puts them out of the way until an edit is required.

