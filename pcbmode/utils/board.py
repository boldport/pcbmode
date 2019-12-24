#!/usr/bin/python

from pcbmode.config import config
from pcbmode.utils import messages as msg
from pcbmode.utils.module import Module



class Board():
    """
    """

    def __init__(self):

        self._module_dict = config.brd
        self._module_routing = config.rte
        module = Module(self._module_dict,
                        self._module_routing)



