import re

CORE_VERSION = 2.9
REPO_TYPE = "git"

def getVersion():
    return u"Yotsuba %s" % CORE_VERSION

# Utilities

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