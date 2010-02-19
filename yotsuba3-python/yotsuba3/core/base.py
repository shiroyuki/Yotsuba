CORE_VERSION = 3.0

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