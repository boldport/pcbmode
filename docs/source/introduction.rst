############
Introduction
############

What is PCBmodE?
================

**PCBmodE** is a Python script that takes input JSON files and converts them into an Inkscape SVG that represents a printed circuit board. **PCBmodE** can then convert the SVG it generated into Gerber and Excellon files for manufacturing.


How is PCBmodE different?
-------------------------

**PCBmodE** was conceived as a circuit design tool that allows the designer to put any arbitrary shape on any layer of the board; it is natively vector-based. **PCBmodE** uses open and widely used formats (SVG and JSON) together with open source tools (Inkscape) without proprietary elements. (Gerber is an exception, but there is no other alternative, unfortunately.) It also provides a fresh take on circuit design, and open up new uses of the circuit board manufacturing medium.

**PCBmodE** is free and open source (MIT license).


What PCBmodE isn't
------------------

**PCBmodE** is not a complete circuit design tool. It does not (currently) have a notion of schematics, have design rule checks, or support more than two layers.
