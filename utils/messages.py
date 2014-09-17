#!/usr/bin/python

def info(info, newline=True):
    """
    """
    if newline == True:
        print "-- %s" % info
    else:
        print "-- %s" % info


def subInfo(info, newline=True):
    """
    """
    if newline == True:
        print " * %s" % info
    else:
        print " * %s" % info,


def error(info, error_type=None):
    """
    """
    print '-----------------------------'
    print 'Yikes, ERROR!'
    print '* %s' % info
    print 'Solder on!'
    print '-----------------------------'
    if error_type != None:
        raise error_type
    raise Exception




