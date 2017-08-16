#!/usr/bin/python
# coding=utf-8

from __future__ import absolute_import

import pcbmode.config as config
from pcbmode.utils.module import Module


class Board(object):
    """
    """

    def __init__(self):
        self._module_dict = config.brd
        self._module_routing = config.rte
        module = Module(self._module_dict,
                        self._module_routing)
