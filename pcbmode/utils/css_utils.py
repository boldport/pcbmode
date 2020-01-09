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

import re


def get_prop(css, class_name, prop_name):
    """
    Capture and return the property value from the specified class in the given CSS  
    """

    pattern = '\.%s\s*{[\s\S]*?%s:\s+"?([-\w]*)"?;[\s\S]*?' % (class_name, prop_name)
    result = re.findall(pattern, css)
    return result[0]

def get_style_value(attrib, style):
    """
    """
    regex = r".*?%s:\s?(?P<s>[^;]*)(?:;|$)"
    match = re.match(regex % attrib, style)
    if match == None:
        return None
    else:
        return match.group("s")
