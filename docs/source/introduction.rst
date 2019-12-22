############
Introduction
############

What is PCBmodE?
----------------

*PCBmodE* is a Python script that takes input JSON files and converts them into an Inkscape SVG that represents a printed circuit board. *PCBmodE* can then convert the SVG it generated into Gerber and Excellon files for manufacturing.


How is PCBmodE different?
-------------------------

*PCBmodE* was conceived as a circuit design tool that allows the designer freedom to put any arbitrary shape on any layer of the board. While it is possible to add graphical elements to other PCB design tools by additional scripts and general arm-twisting, *PCBmodE* is purposefully designed and architected for that purpose.

*PCBmodE* uses open and widely used formats (SVG, JSON) together with open source tools (Python, Inkscape) without proprietary elements (Gerber is an exception, although the standard is public). It also provides a fresh take on circuit design and opens new uses for the circuit board manufacturing medium.

*PCBmodE* is free and open source under the GPL 3 license.


What PCBmodE isn't
------------------

*PCBmodE* isn't a general-purpose replacement for other PCB design tools like KiCad, EAGLE, Altium, etc. For example, it does not currently have a notion of a netlist or schematics, have design rule checks.
