![PCBmodE logo](/images/pcbmode-logo.png)

# A circuit board design software with a twist

PCBmodE is a circuit board design software written in Python. Its main advantage is allowing the design to create and use arbitrary shapes for any element of the board. Using stock [Inkscape](http://inkscape.org) as the GUI provides all the features of a drawing tool. This, in contrast to traditional PCB design tools that restrict visual freedom and don't have the full feature set of a vector editing software.

## Workflow

PCBmodE folows a layout-driven design flow. There's no schematic functionality or DRC other than the designer's eyes. It's essentiallya script that runs from commandline generating files depending on the stage of the design.

1. Text editor: edit input [JSON](http://en.wikipedia.org/wiki/JSON) files
2. PCBmodE: convert JSON files to Inkscape SVG
3. Inkscape: edit SVG (component movement, routing, etc.)
4. PCBmodE: extract changes and apply them back to input JSON files

Iterate the above until the design is ready, and then

1. PCBmodE: create [Gerber](http://en.wikipedia.org/wiki/Gerber_format) files from SVG
2. Send to fab
3. Get lovely boards back and impress people on Twitter

## Requirements

* Python 2.7
* [PyParsing](http://pyparsing.wikispaces.com/)
* [lxml](http://lxml.de/)
* [Inkscape](http://inkscape.org)

PCBmodE is developed and tested under Linux, so it might or might not work under other OSs.

### Resources
* [Documentation](http://pcbmode.readthedocs.org) (needs serious updating!)
* Boldport Club Discord [#pcbmode](https://discordapp.com/channels/422844882315640832/422881024796786708) (you need to be a [Boldport Club](https://boldport.com/club) member to have access)

## Roadmap

PCBmodE was written and is maintained by Saar Drimer of [Boldport](https://boldport.com). It has been used to design all of Boldport's [products](https://boldport.com/shop) since 2013. It is, therefore, very functional but sadly not that well documented and development happens in bursts.

The next version of PCBmodE is v5, codename 'cinco'. For this release I'd like to get the following done:
* Package PCBmodE so it's easy to install
* Update and maintain the documentation
* Migrate to Python3 (drop support for Python2)
* Work with Inkscape 1.x (drop support for previous versions)
* Improve performance and do better than the current simple caching method
* Implement the latest Gerber X2 standard
* Automatic 'gerber-lp' generation from SVG shapes
* Support any font form Google Fonts
* Fully support SVG paths (currently 'l' is buggy and 'a' isn't supported)

New desired extensions:
* Footprint creation wizard
* New project wizard
* Browser viewer of PCBmodE SVGs
* Inkscape add-on to invoke PCBmodE functions from within Inkscape

## Contributing

For contributing code, see the CONTRIBUTE.md included in this repository.

If you'd like to contribute _towards_ development in the form of hard cold electronic money, see the end of [this](https://boldport.com/pcbmode) page.

## The name
The 'mod' in PCBmodE has a double meaning. The first is short for 'modern' (in contrast to tired old EDA tools). The second is a play on the familiar 'modifications' or 'mods' done to imperfect PCBs. Call it 'PCB mode' or 'PCB mod E', whichever you prefer. 

## License
PCBmodE is licensed under the [MIT License](http://opensource.org/licenses/MIT).
