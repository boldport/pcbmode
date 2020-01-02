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


import sys


def info(info, newline=True):
    """
    """
    if newline == True:
        print("-- %s" % info)
    else:
        sys.stdout.write("-- %s" % info)


def note(note, newline=True):
    """
    """
    if newline == True:
        print("-- NOTE: %s" % note)
    else:
        sys.stdout.write("-- NOTE: %s" % note)


def subInfo(info, newline=True):
    """
    """
    if newline == True:
        print(" * %s" % info)
    else:
        sys.stdout.write(" * %s" % info)


def error(info, error_type=None):
    """
    Print a message and then raise
    """

    print("")
    print("-----------------------------")
    print("Yikes, ERROR!")
    print("")
    print("* %s" % info)
    print("")
    print("Solder on!")
    print("-----------------------------")
    print("")

    if error_type != None:
        raise error_type
    else:
        raise Exception
