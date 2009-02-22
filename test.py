#!/usr/bin/env python

# Test Suite 1.1 for Yotsuba 2.0
# Juti Noppornpitak <juti_n@yahoo.co.jp>
import sys
import time

import yotsuba

global showOutput
global output
global forceShowLog
global forceHideLog
global numOfStressTests
global numOfCases
global numOfFailedCases

showOutput = True
output = []
forceShowLog = False
forceHideLog = False
numOfStressTests = 200
numOfCases = 0
numOfFailedCases = 0

def tPrint(message):
    global output
    output.append(str(message))

def tPrintMessage():
    global showOutput
    global output
    if showOutput:
        print "\n".join(output)

def tEqual(label, testingValue, expectedValue):
    global numOfCases
    global numOfFailedCases
    numOfCases += 1
    if testingValue == expectedValue:
        tPrint("O\tEquality: %s" % label)
    else:
        tPrint("X\tEquality: %s\n\t\tTesting Value:\t%s\n\t\tExpected Value:\t%s" % (label,testingValue, expectedValue))
        numOfFailedCases += 1

def tMore(label, testingValue, expectedValue, reverse = False):
    global numOfCases
    global numOfFailedCases
    numOfCases += 1
    if testingValue > expectedValue and not reverse:
        tPrint("O\tMore-than: %s" % label)
    elif not testingValue <= expectedValue and reverse:
        tPrint("O\tLess-than: %s" % label)
    else:
        tPrint("X\tEquality: %s\n\t\tTesting Value:\t%s\n\t\tExpected Value:\t%s" % (label,testingValue, expectedValue))
        numOfFailedCases += 1

def tExist(label, testingObject, expectedFailed = False):
    global numOfCases
    global numOfFailedCases
    numOfCases += 1
    if not testingObject == None and not expectedFailed:
        tPrint("O\tExistence: %s" % (label))
        return True
    elif testingObject == None and expectedFailed:
        tPrint("O\tNon-existence: %s" % (label))
        return True
    else:
        tPrint("X\tExistence: %s" % (label))
        numOfFailedCases += 1
        return False

def testingProcedure():
    global forceShowLog
    global forceHideLog
    global numOfCases
    global numOfFailedCases
    
    # sdk.xml > Initialization test
    if not yotsuba.fs.exists("test.xml"):
        raise "Cannot find test.xml"
    if not yotsuba.fs.readable("test.xml"):
        raise "Cannot read test.xml"
    if not yotsuba.kotoba.read("test", "test.xml"):
        raise "Cannot parse test.xml"
    tEqual("XML Tree Construction", len(yotsuba.kotoba.trees['test'].children), 6)
    tEqual("XML Tree Construction", yotsuba.kotoba.trees['test'].child().name(), 'a')
    tEqual("XML Tree Construction", yotsuba.kotoba.trees['test'].child().parent().name(), 'root')
    # sdk.xml > Existance tests
    passedQueries = ['c1', 'c c1', 'root c c1', 'root c1', 'root > c c1', 'root c > c1', 'root > c > c1', 'common', 'c c1, e e11']
    failedQueries = ['c3', 'c c3', 'root > c1', 'root c e1']
    for pq in passedQueries:
        tMore("XML Query Test / Existance (%s)" % pq, yotsuba.kotoba.query('test', pq).length(), 0)
    for fq in failedQueries:
        tEqual("XML Query Test / Existance (%s)" % fq, yotsuba.kotoba.query('test', fq).length(), 0)
    # sdk.xml > Correctness tests
    passedQueries = {
        'common': 4,
        'common[id]': 0,
        'common[name]': 2,
        'common[id=c]': 0,
        'common[name=c]': 1,
        'common[name|=utf]': 1,
        'common[name~=of]': 1,
        'common[name~=f]': 0,
        'common[name^=utf-8\']': 1,
        'common[name^=utf]': 0,
        'common[name$=buddha]': 1,
        'common[name$=dha]': 0,
        'common[name*=am]': 1,
        '[name=c]': 1,
        'root common': 4,
        'root * common': 4,
        'root *': 20,
        'root:root': 1,
        'root:root:empty': 0,
        'c:root': 0,
        'b:empty': 1,
        'c:empty': 0,
        '*': 21,
        'c common': 1,
        'c + d': 1,
        'c ~ e': 2,
        'e common': 3,
        'e > common': 1,
        'e > e1 common': 1,
        'd common': 0,
        'c c1, e e11': 2,
    }
    for pqK, pqV in passedQueries.iteritems():
        tEqual("XML Query Test / Correctness (%s)" % pqK, yotsuba.kotoba.query('test', pqK).length(), pqV)
    # sdk.xml > Data extraction tests
    tEqual("XML Query Test (Data)", yotsuba.kotoba.query('test', 'c c1').data(), yotsuba.kotoba.trees['test'].children[2].children[0].data())
    # sdk.xml > Selector-object tests
    passedQueries = {
        'element': ['element', None, '', ''],
        'element[id]': ['element', None, None, ''],
        'element[id=0]': ['element', '=', '0', ''],
        'element:first-child': ['element', None, '', 'first-child'],
        'element[id=0]:first-child': ['element', '=', '0', 'first-child'],
        'element[class=what][id=0][name=google]:first-child:empty': ['element', '=', '0', 'first-childempty']
    }
    for pqK, pqV in passedQueries.iteritems():
        tPrint(":\tCreating SO from '%s'" % pqK)
        tEqual("The selector object construction (Name)", yotsuba.kotoba.makeSelectorObject(pqK).name(), pqV[0])
        tEqual("The selector object construction (ID/Operator)", yotsuba.kotoba.makeSelectorObject(pqK).attr('id')[0], pqV[1])
        tEqual("The selector object construction (ID/Value)", yotsuba.kotoba.makeSelectorObject(pqK).attr('id')[1], pqV[2])
        tEqual("The selector object construction (Filters)", ''.join(yotsuba.kotoba.makeSelectorObject(pqK).filter()), pqV[3])
    tPrint("------------------------------------------------------------------------")

def runTests():
    t_localStat = []
    for round in range(numOfStressTests):
        t_start = time.time()
        testingProcedure()
        t_localStat.append(time.time() - t_start)
    return t_localStat

def getAverage(list):
    total = 0
    for item in list:
        total += item
    return total / len(list)

def getMin(list):
    if len(list) == 0:
        return 0
    minNumber = list[0]
    for item in list:
        if minNumber > item:
            minNumber = item
    return minNumber

def getMax(list):
    maxNumber = 0
    for item in list:
        if maxNumber < item:
            maxNumber = item
    return maxNumber

if __name__ == '__main__':
    yotsuba.core.log.report("Begin testing")
    print "========================================================================"
    print "Yotsuba Project 2 > Test Suite (%d loops)" % numOfStressTests
    print "------------------------------------------------------------------------"
    
    # Calls the test suite
    t_stat = None
    if yotsuba.fs.exists('test.stat'):
        t_stat = yotsuba.fs.read('test.stat', yotsuba.READ_PICKLE)
    else:
        t_stat = []
    
    t_currentStat = runTests()
    t_stat.extend(t_currentStat)
    
    yotsuba.fs.write('test.stat', t_stat, yotsuba.WRITE_PICKLE)
    
    print "Running Time"
    print "    Current\t\t%.5f\tsecond(s)" % getAverage(t_currentStat)
    print "    Average\t\t%.5f\tsecond(s)" % getAverage(t_stat)
    print "    Minimum\t\t%.5f\tsecond(s)" % getMin(t_stat)
    print "    Maximum\t\t%.5f\tsecond(s)" % getMax(t_stat)
    print "    Improvement\t\t%.2f\t%%" % (( getAverage(t_stat) - getAverage(t_currentStat) ) / getAverage(t_stat) * 100)
    print "    Potential\t\t%.2f\t%%\t%.2f\t%%" % (
        (( 1 - (getAverage(t_currentStat) - getMin(t_stat) ) / ( getMax(t_stat) - getMin(t_stat) ) ) * 100),
        (( 1 - (getAverage(t_stat) - getMin(t_stat) ) / ( getMax(t_stat) - getMin(t_stat) ) ) * 100),
    )
    print "    Total tests\t\t%d\ttests" % (len(t_stat))
    # End of calls
    
    print "Test Score\t\t%d/%d\t%.2f\t%%" % (numOfCases - numOfFailedCases, numOfCases, (numOfCases - numOfFailedCases)*100/numOfCases)
    if (numOfFailedCases > 0 or forceShowLog) and not forceHideLog:
        print "------------------------------------------------------------------------"
        tPrintMessage()
    if yotsuba.core.log.hasError and not forceHideLog:
        print "------------------------------------------------------------------------"
        try:
                yotsuba.fs.remove('test.log')
        except:
                pass
        if not yotsuba.fs.writable('./'):
                print 'Not writable'
        if yotsuba.fs.write('test.log', yotsuba.core.log.export()):
                print 'The report was just written'
        else:
                print 'The report was not written'
        if not yotsuba.fs.exists('test.log'):
                print 'Failed to write the report'
        else:
                print "See the 'test.log'"
    else:
        yotsuba.fs.remove('test.log')
    print "========================================================================"
