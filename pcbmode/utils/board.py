#!/usr/bin/python

import pcbmode.config as config
from . import messages as msg
from .module import Module



class Board():
    """
    """

    def __init__(self):

        self._module_dict = config.brd
        self._module_routing = config.rte
        module = Module(self._module_dict,
                        self._module_routing)



