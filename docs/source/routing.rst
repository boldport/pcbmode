#######
Routing
#######

Routing, of course, is an essential part of a circuit board. **PCBmodE** does not have an auto-router, and routing is typically done in Inkscape, although theoretically, routing can be added manually in a text editor. All routing shapes reside in the routing SVG layer of each PCB layer. 

.. important:: Make sure that you place the routes and vias on the routing SVG layer of the desired PCB layer. To choose that layer either click on an element in the layer or open the layer pane by pressing ``CTRL+SHIFT+L``.


.. important:: In order to place routes, make sure that Inkscape is set to 'optimise' paths by going to ``File->Inkscape Preferences->Transforms`` and choosing ``optimised`` under ``Store transformation``.


Adding routes
-------------

Choose the desired routing SVG layer. Using the Bezier tool (``SHIFT+F6``) to draw a shape. 

For a filled shape, make sure that it is a closed path and in the ``Fill and stroke`` pane (``SHIFT+CTRL+F``) click on the ``flat color`` button on the ``Fill`` tab, and the ``No paint`` (marked with an ``X``) on the ``Stroke point`` tab.

For a stroke, in the ``Fill and stroke`` pane (``SHIFT+CTRL+F``) click on the ``No paint`` button on the ``Fill`` tab, and the ``Flat color`` on the ``Stroke point`` tab. Adjust the stroke thickness on the ``Stroke style`` tab.

.. note:: Shapes can be either stroke or fill, not both. If you'd like a filled and stroked shape, you'll need to create two shapes. 

Finally, you ***must*** move the shape with the mouse or with the arrows.

.. note:: When creating a new shape Inkscape adds a matrix transform, which is removed when the shape is moved because of the ``optimise`` settings as described above. This minor inconvenience is a compromise that greatly simplifies the extraction process.

If the route is placed where there is a copper pour, it will automatically have a buffer around it that's defined in the board's configuration. Sometimes, it is desirable to reduce or increase this buffer, or eliminate it completely in order to create a bridge (for example when connecting a via to a pour). This is how it is done:

1) Choose the route
2) Open Inkscape's XML editor (``SHIFT+CTRL+X``)
3) On the bottom right, next to ``set`` remove what's there and type in ``pcbmode:buffer-to-pour``
4) In the box below type in the buffer in millimeters (don't add 'mm') that you'd like, or ``0`` for none
5) Press ``set`` or ``CTRL+ENTER`` to save that property 

.. tip:: Once you've created one route, you can simply cut-and-paste it and edit it using the node tool without an additional settings. You can even cut-and-paste routes from a different design.


Adding vias
-----------

Vias are defined just like any other component, but are placed differently.

1) Choose the routing layer
2) Choose the ``Draw`` tool (``F6``)
3) Press ``CTRL`` and click with the left button where you'd like the via (size and color doesn't matter)
4) Open Inkscape's XML editor (``SHIFT+CTRL+X``)
5) Next to ``set`` enter ``pcbmode:type`` and below enter ``via``
6) Press ``set`` or ``CTRL+ENTER``
7) Next to ``set`` enter ``pcbmode:via`` and below enter the component to be placed as a via. So if your via definition is in ``via.json`` (in the component directory) then enter ``via`` (without the ``.json``)
8) Press ``set`` or ``CTRL+ENTER``

.. note:: Since vias are components, anything could be a via, so if it makes sense to place a 2x2 0.1" header as a "via", that's possible.

.. note:: This somewhat cumbersome procedure is a compromise between usability and the need to modify Inkscape or adding vias manually.

.. important:: Don't forget to extract the changes!
