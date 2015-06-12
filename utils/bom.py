#!/usr/bin/python

import json
import os
import re
import subprocess as subp # for shell commands
import math
from operator import itemgetter # for sorting lists by dict value
import HTMLParser # required for HTML to unicode translation
from lxml import etree as et

import config

# pcbmode modules
from point import Point
from svgpath import SvgPath
import messages as msg
import hashlib



def create_bom():
    """
    
    """

    pass

