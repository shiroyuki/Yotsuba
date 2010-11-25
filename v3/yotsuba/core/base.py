# -*- coding: utf-8 -*-

import re
import hashlib as h
import logging

__VERSION__ = 3.0
REPO_TYPE = "svn"

class logger(object):
    '''
    Deplicated class for get_logger
    '''
    class level(object):
        debugging = logging.DEBUG
        info = logging.INFO
        warning = logging.WARN
        critical = logging.CRITICAL
        error = logging.ERROR
    
    @staticmethod
    def getBasic(name = "basic logger", level = logging.ERROR):
        logging.basicConfig(level=level)
        newLogger = logging.getLogger(name)
        return newLogger
    
    @staticmethod
    def disable(level=logging.CRITICAL):
        logging.disable(level)

def get_logger(name, level=logging.DEBUG): # default for name should be __name__ for each caller module
    log = logging.getLogger()
    log.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    log.addHandler(ch)
    return log

def getVersion():
    return u"Yotsuba %s" % __VERSION__

# Utilities
def isList(objRef):
    return type(objRef) is list

def isTuple(objRef):
    return type(objRef) is tuple

def isString(objRef):
    return type(objRef) in [unicode, str]

def convertToUnicode(objRef):
    return type(objRef) is not unicode and unicode(objRef) or objRef

def isNumber(objRef):
    return type(objRef) in [int, long, float]

def isFloatingNumber(objRef):
    return type(objRef) is float

def isIntegerNumber(objRef):
    return type(objRef) in [int, long]

def isNaturalNumber(objRef):
    return inIntegerNumber(objRef) and objRef >= 0

def convertToInteger(objRef):
    try:
        return int(objRef)
    except:
        return None

def convertToFloatingNumber(objRef):
    try:
        return float(objRef)
    except:
        return None

def convertToBoolean(objRef):
    convertible = isString(objRef) and re.match("^(true|false)$", objRef, re.I)
    result = None
    if convertible:
        result = re.search("^true$", objRef, re.I) is not None
    return result

def convert_to_readable_size(dataSize, bypassCheck = False):
    unit = ['B', 'KB', 'MB', 'TB']
    unitPointer = 0
    dataSize = float(dataSize)
    
    while dataSize >= 1024:
        dataSize /= 1024
        unitPointer += 1
    
    return "%.2f %s" % (dataSize, unit[unitPointer])

def hash(message, *hash_algos):
    output = ''
    for hash_algo in hash_algos:
        try:
            engine = h.new(hash_algo, message)
            output += engine.hexdigest()
        except:
            pass
    
    if not output:
        s512 = h.sha512(message)
        md5 = h.md5(message)
        output = '%s%s' % (s512.hexdigest(), md5.hexdigest())

    return output

def has_everything_in(iterable_object, *item_or_key):
    for x in item_or_key:
        if x not in iterable_object: return False
    return True