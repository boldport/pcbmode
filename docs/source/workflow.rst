########
Workflow
########

*PCBmodE* is a script that uses Inkscaoe as a graphical interface. So
 you can think of *PCBmodE* as a wrapper around Inkscape.

To get a feel for how to work with *PCBmodE*, here's a typical design workflow:

1) Edit JSON files with a text editor for adding components, placing them, etc.
2) Run *PCBmodE* to generate the board's Inkscape SVG
3) Open the generated SVG in Inkscape
4) Make modifications in Inkscape, such as routing, vias, and component positioning
5) Run *PCBmodE* to extract these changes; this will put those changes back to the input JSON files

During development you'd go through many iterations of steps 1 to 5. Then when you're ready,

6) Run *PCBmodE* to generate Gerbers from the board's SVG

It is possible to design a complete circuit board in a text editor
without using Inkscape at all! The most challanging part would be
generating (using scripts), or hand crafting SVG paths for the
routing.

.. tip:: Inkscape does not reload SVGs when they change on the disc
         after *PCBmodE* regenerated them. To reload quickly, press
         ``ALT+f`` and the ``v``.

.. tip:: Until you get used to it the extraction process may not do
         what you'd expect. One trick is to extract and then run
         *PCBmodE* with also generating Gerbers (``--fab``
         switch). Then review the Gerbers instead of reloading the SVG
         to notice that your changed are gone. It might also be
         practical to design in a separate Inkscape window and then
         copy over the shapes to the design's SVG.

