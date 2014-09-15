##########
Extraction
##########

One of the common steps of the *PCBmodE* workflow is extracting information from the SVG and storing it in primary JSON files.

The following will be extracted from the SVG:

* Routing shapes and location
* Vias' location
* Components' location and rotation
* Documentation elements' location
* Drill index location

That's it. 

.. note:: It's quite likely that more information will be extracted in the future to make the design process require fewer steps. Architecturally, however, the use of a GUI is meant only to assist the textual design process, not replace it.

Other information needs to be entered manually with a text editor. A great tool in this process is Inkscape's built-in XML editor (open with ``SHIFT+CTRL+F``) which allows you to see the path definition of shape (the ``d`` property) and copy it over to the JSON file.

.. tip:: Since some shapes (pours, silkscreen, etc.) are not extracted, it's sometimes a bit of a guesswork to get the location just right. To do that in a single iteration, use the XML editor to change the transform of the shape (press ``CTRL+ENTER`` to apply) until the position is right. Then copy over the coordinates for that shape to the JSON file. **Note** that Inkscape inverts the y-axis coordinate, so when entering it into the JSON invert it back.


