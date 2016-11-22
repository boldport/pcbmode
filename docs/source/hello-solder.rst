######################
Tutorial: hello-solder
######################

The 'hello-solder' is a fun design for learn how *PCBmodE* by example.

.. image:: images/hello-solder/board.png

Setup
=====

Get the boards repository from `here <https://github.com/boldport/boards>`_ and follow the instructions :doc:`setup` to 'compile' the board. This command should do it

    ``pcbmode -b hello-solder -m``


.. info:: *PCBmodE* caches some of the heavy computations in a file in the ``build`` directory, so subsequent invocations will run much faster.

Then open the SVG you produced with Inkscape

    ``inkscape path/to/project/boards/hello-solder/build/hello-solder.svg``

Once opened, open the layers pane by pressing ``CTRL+SHIFT+L`` and get familiar with the layers of the board by making some hidden and visible.


Outline
=======

Using the layer pane hide all layers except for ``outline``. This shape is defined by an SVG path. In SVG (actually XML) is looks like this

.. code-block:: XML

    <path  
    d="m -16.699260,-6.454745 c -2.780854,0.8264621 -4.806955,3.3959901 -4.806955,6.44592474 0.0,3.04953526 2.025571,5.63383146 4.805863,6.46294446 0.373502,0.1206099 0.541906,0.3377362 0.36641,0.7166985 -0.537601,0.9664023 -0.841925,2.0765939 -0.841925,3.2625791 0.0,3.718159 3.019899,6.738056 6.738055,6.738056 1.1862717,0.0 2.2968105,-0.30644 3.2633909,-0.844923 0.2779016,-0.144746 0.6338321,-0.09921 0.7184502,0.343724 0.8185077,2.79334 3.3927864,4.831546 6.45156129,4.831546 3.06962611,0.0 5.66024241,-2.052348 6.47040841,-4.860911 0.097465,-0.315553 0.453736,-0.434303 0.7700817,-0.273567 0.9522855,0.514048 2.0438307,0.804131 3.2017325,0.804131 3.718159,0.0 6.729236,-3.019897 6.729236,-6.738056 0.0,-1.1177297 -0.269937,-2.1676049 -0.750914,-3.0935477 -0.277868,-0.520065 0.07101,-0.817639 0.379848,-0.9166584 2.730845,-0.859225 4.710233,-3.4176958 4.710233,-6.43201596 0.0,-2.98855014 -1.945688,-5.51459174 -4.640357,-6.39242304 -0.362382,-0.1152866 -0.660925,-0.5371332 -0.411209,-1.0139163 0.45685,-0.9074068 0.712399,-1.9307068 0.712399,-3.0182436 0.0,-3.718158 -3.011077,-6.746875 -6.729236,-6.746875 -0.165351,0.02476 -0.410376,-0.219946 -0.219238,-0.595553 0.129165,-0.314741 0.201599,-0.658879 0.201599,-1.018404 0.0,-1.496699 -1.2196914,-2.707569 -2.7163892,-2.707569 -1.0789126,0.0 -2.0094311,0.629927 -2.4450348,1.542338 -0.119881,0.280927 -0.5068697,0.412753 -0.8079468,0.144495 -1.1862758,-1.048846 -2.7462918,-1.686833 -4.45521281,-1.686833 -3.12285319,0.0 -5.73997179,2.120433 -6.49986279,5.003566 -0.079222,0.219391 -0.1844607,0.406694 -0.6008463,0.210249 -0.9826557,-0.564791 -2.1176191,-0.892287 -3.3326933,-0.892287 -3.718156,0.0 -6.738055,3.028717 -6.738055,6.746875 0.0,1.0923431 0.258164,2.1203908 0.718982,3.0310127 0.257646,0.4766398 0.146527,0.778116 -0.242375,0.9476435 z"  
    style="stroke-width:0.05;"  
    pcbmode:style="stroke"  
    transform="translate(0, 0)"  
    />

You can view this by clicking on the outline and pressing ``SHIFT+CTRL+X`` to invoke Inkscape's built-in XML editor. This shows you the group the outline belongs to, so collapse the list on the left and choose the single element in the group. This should show you something like the above.

.. tip:: Can't select the outline? That's because the layer is locked. On the layer pane click the lock next to the ``outline`` layer.

Now open ``hello-solder.json`` in the project directory with a text editor. The shape above was created using the following definition

.. code-block:: json

    {    
      "outline": {
        "shape": {
          "type": "path", 
          "value": "m -16.698952,-6.4545028 c -2.780854,0.8264621 -4.806955,3.3959901 -4.806955,6.44592474 0,3.04953526 2.025571,5.63383146 4.805863,6.46294446 0.373502,0.1206099 0.541906,0.3377362 0.36641,0.7166985 -0.537601,0.9664023 -0.841925,2.0765939 -0.841925,3.2625791 0,3.718159 3.019899,6.738056 6.738055,6.738056 1.1862717,0 2.2968105,-0.30644 3.2633909,-0.844923 0.2779016,-0.144746 0.6338321,-0.09921 0.7184502,0.343724 0.8185077,2.79334 3.3927864,4.831546 6.45156129,4.831546 3.06962611,0 5.66024241,-2.052348 6.47040841,-4.860911 0.097465,-0.315553 0.453736,-0.434303 0.7700817,-0.273567 0.9522855,0.514048 2.0438307,0.804131 3.2017325,0.804131 3.718159,0 6.729236,-3.019897 6.729236,-6.738056 0,-1.1177297 -0.269937,-2.1676049 -0.750914,-3.0935477 -0.277868,-0.520065 0.07101,-0.817639 0.379848,-0.9166584 2.730845,-0.859225 4.710233,-3.4176958 4.710233,-6.43201596 0,-2.98855014 -1.945688,-5.51459174 -4.640357,-6.39242304 -0.362382,-0.1152866 -0.660925,-0.5371332 -0.411209,-1.0139163 0.45685,-0.9074068 0.712399,-1.9307068 0.712399,-3.0182436 0,-3.718158 -3.011077,-6.746875 -6.729236,-6.746875 -0.165351,0.02476 -0.410376,-0.219946 -0.219238,-0.595553 0.129165,-0.314741 0.201599,-0.658879 0.201599,-1.018404 0,-1.496699 -1.2196914,-2.707569 -2.7163892,-2.707569 -1.0789126,0 -2.0094311,0.629927 -2.4450348,1.542338 -0.119881,0.280927 -0.5068697,0.412753 -0.8079468,0.144495 -1.1862758,-1.048846 -2.7462918,-1.686833 -4.45521281,-1.686833 -3.12285319,0 -5.73997179,2.120433 -6.49986279,5.003566 -0.079222,0.219391 -0.1844607,0.406694 -0.6008463,0.210249 -0.9826557,-0.564791 -2.1176191,-0.892287 -3.3326933,-0.892287 -3.718156,0 -6.738055,3.028717 -6.738055,6.746875 0,1.0923431 0.258164,2.1203908 0.718982,3.0310127 0.257646,0.4766398 0.146527,0.778116 -0.242375,0.9476435 z"
        }
      }  
    }

Since this is the board's outline *PCBmodE* assumes that its placement is at the center (that is ``location: [0,0]``) and that the style is an ``outline``.

Let's try something. In Inkscape, modify the path using the node tool (press ``F2``). Using the XML editor cut-and-paste the path into the board's JSON file, replacing the existing outline path. Now recompile the board using the same command as above.

When it's done, back in Inkscape, press ``ALT+F`` and then ``V`` to reload. Click ``yes`` and see your shape used as an outline. Notice that the shape is centered -- it's always like that with *PCBmodE*, all coordinates are relative to the center of the board. Also, the dimensions for the new outline are calculated and added automatically.


Components
==========

Placing components is done by "instantiating" a component that is defined in another JSON file in the ``components`` directory within the project. Here's an example from ``hello-solder.json`` for reference designator ``R2``

.. code-block:: json

    {
      "R2": {
        "footprint": "0805", 
        "layer": "top", 
        "location": [
          5.3, 
          5.3
        ], 
        "rotate": 45, 
        "show": true
      }
    }

``R2`` is the unique name for this instantiation of footprint ``0805``. It can be any unique (for the design) name, but convention is to keep it short, one or two letters followed by a number.

.. tip:: There are no hard rules about reference designator format and prefixes, so they vary depending on the context. Wikipedia has a `list <http://en.wikipedia.org/wiki/Reference_designator>`_ that you can follow in the absence of other guidelines. 
 
The footprint for ``0805`` is defined in the file

    components/0805.json

Open it with a text editor.

.. code-block:: json

    {
    "pins":
      {
      "1":
        {	
          "layout": 
          {
            "pad": "pad", 
            "location": [-1.143, 0]
          }
        },
      "2":
        {	
          "layout": 
          {
            "pad": "pad", 
            "location": [1.143, 0],
            "rotate": 180
          }
        }
      }
    }

We define two pins (we'll also call surface mount pads "pins") called ``1`` and ``2``. For each of these we instantiate ``pad`` as the shape and place it at the coordinate defined in ``location`` (remember, placement is always relative to the center). We rotate pin ``2`` by 180 degrees.

.. tip:: Pin names can be any text, and a label can be added too. See :doc:`components` for more detail.

The pad is defined in the same file, like so

.. code-block:: json

    {
      "pads":
      {
        "pad":
        {
          "shapes":
          [
            {
              "type": "rect",
     	      "layers": ["top"],
     	      "width": 1.542,
     	      "height": 1.143,
     	      "radii": {"tl": 0.25, "tr": 0, "bl": 0.25, "br": 0}
     	    }
          ]
        }
      }
    }

Of course it's possible to define more than one pad, and it's even possible to have multiple shapes as part of a single pad in order to create complex shapes. See :doc:`shapes` for more on defining shapes.

We would like to now add a silkscreen shape and assembly drawing. Here's how we do that

.. code-block:: json

    {
      "layout":
      {
        "silkscreen":
        {
       	  "shapes":
       	  [
       	    {
       	      "type": "rect",
       	      "width": 0.3, 
       	      "height": 1,
       	      "location": [0, 0],
       	      "style": "fill"
       	    }
       	  ]
        },
        "assembly":
        {
       	  "shapes":
       	  [
       	    {
       	      "type": "rect",
       	      "width": 2.55,
       	      "height": 1.4
       	    }
          ]
        }
      }
    }

Here's an exercise: instead a small silkscreen square, draw an outline rectangle with rounded corners around the component's pads. For a bonus, add a tiny silkscreen dot next to one of the pads.


Shapes
======


Routing
=======


Documentation and indexes
=========================


Extraction
==========


Production
==========

..  LocalWords:  PCBmodE Inkscape inkscape
