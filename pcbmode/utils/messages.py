#!/usr/bin/python

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

    print('')
    print('-----------------------------')
    print('Yikes, ERROR!')
    print('')
    print('* %s' % info)
    print('')
    print('Solder on!')
    print('-----------------------------')
    print('')

    if error_type != None:
        raise error_type
    else:
        raise Exception




