Style
#####

*PCBmodE* seperates the shapes and their visual apperance in the SVG. This means that
visual changes can be applied to the entore design without touching the shapes themselves, unless they
differ from the overall setting. The styles are defined in CSS stylesheet classes.

Classes
-------

``.board`` 

Sets the global look of the SVG.

``.origin``

``.outline``, ``.dimensions``

Converted to paths

``.drills``

``.pad-labels``

Unless disabled, PCBmodE will put a small pad label under each component pad. This is 
an SVG text element.

``<pcb-layer>-<sheet>``

Where ``<pcb-layer>`` are PCB layers such as ``top``, ``bottom``, or ``internal-<num>``.
``<sheet>`` is an additional 'layer' associated with a pcb-layer: ``placement``, ``assembly``,
``conductor``, ``silkscreen``, ``soldermask``, and ``solderpaste``.

``<pcb-layer>-conductor-<type>``

An additional level applies to ``conductor`` layers where ``type`` is: ``routing``,
``pads``, and ``pours``.


``.drill-index``, ``.drill-index-symbol``, ``.drill-index-symbol-text``

Defined the look of the drill index


``.layer-index``

Defined the look of the layer index
