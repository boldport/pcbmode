############
Introduction
############

What is PCBmodE?
----------------

**PCBmodE** is a Python script that takes input JSON files and converts them into an Inkscape SVG that represents a printed circuit board. **PCBmodE** can then convert the SVG it generated into Gerber and Excellon files for manufacturing.


How is PCBmodE different?
-------------------------

**PCBmodE** was conceived as a circuit design tool that allows the designer to put any arbitrary shape on any layer of the board; it is natively vector-based. **PCBmodE** uses open and widely used formats (SVG, JSON) together with open source tools (Python, Inkscape) without proprietary elements (Gerber is an exception). It also provides a fresh take on circuit design and opens new uses for the circuit board manufacturing medium.

**PCBmodE** uses stylesheets with CSS-like syntax. This seperates 'style' from 'content', similarly to the relationship of HTML and CSS.

**PCBmodE** is free and open source (MIT license).


What PCBmodE isn't
------------------

**PCBmodE** is not a complete circuit design tool. It does not (currently) have a notion of schematics, have design rule checks, or support more than two layers.
