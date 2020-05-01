#!/usr/bin/python

# PCBmodE, a printed circuit design software with a twist
# Copyright (C) 2020 Saar Drimer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from pcbmode.config import config


def create():
    """
    Create the SVG defined by the input files. This requires two primary steps.
    1. Combine all the input files into a single dict while applying global and local
       settings
    2. Create the SVG based on this dict.
    """ 

    # These two statement assume that there's a single module. When we start working
    # on multiple modules per board/panel those will need to be named and seperated
    module_d = config.brd
    routing_d = config.rte
    