from time import time
from sys import exc_info
from traceback import print_tb
from yotsuba.core import base

global totalUsageTime
totalUsageTime = 0.0

def doTests(title, *testers):
    textBlock(title)
    thBlock()
    for tester in testers:
        doTest(tester)

def doTest(tester):
    global totalUsageTime
    
    maxRepeat = 2
    
    result = "o"
    startingTime = None
    elapsedTimes = [0, 0]
    
    reason = ''
    val = None
    tb = None
    
    repeat = 0
    
    while repeat < maxRepeat:
        try:
            startingTime = time()
            tester()
        except:
            result = "x"
            reason = " (E: %s)" % base.convertToUnicode(exc_info()[0])
            val, tb = exc_info()[1], exc_info()[2]
        finally:
            elapsedTime = time() - startingTime
            totalUsageTime += elapsedTime
            elapsedTimes[repeat] = elapsedTime
            repeat += 1
            if len(reason) > 0:
                break
    
    print "  %s\t%2.4f\t%2.4f\t%s%s" % (result, elapsedTimes[0], elapsedTimes[1], tester.__doc__, reason)
    if tb is not None:
        print "."*80
        print_tb(tb)
        print "  Given value: %s" % val
        print "."*80

def thBlock():
    print "  o/x\tCold\tHot\tTest"
    print "-"*80

def textBlock(text):
    if len(text) > 76 and len(text) > 73:
        text = text[:73] + "..."
    whiteSpaces     = " " * (76 - len(text))
    topBottomLine   = "+" + "-"*78 + "+"
    
    print
    print topBottomLine
    print "| " + text + whiteSpaces + " |"
    print topBottomLine
    print