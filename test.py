#!/usr/bin/env python

import yotsuba

global numOfCases
global numOfFailedCases

forceShowLog = False
forceHideLog = True
numOfCases = 0
numOfFailedCases = 0

def tEqual(label, testingValue, expectedValue):
	global numOfCases
	global numOfFailedCases
	numOfCases += 1
	if testingValue == expectedValue:
		print "O\tEquality: %s" % label
	else:
		print "X\tEquality: %s\n\t\tTesting Value:\t%s\n\t\tExpected Value:\t%s" % (label,testingValue, expectedValue)
		numOfFailedCases += 1

def tMore(label, testingValue, expectedValue, reverse = False):
	global numOfCases
	global numOfFailedCases
	numOfCases += 1
	if testingValue > expectedValue and not reverse:
		print "O\tMore-than: %s" % label
	elif not testingValue <= expectedValue and reverse:
		print "O\tLess-than: %s" % label
	else:
		print "X\tEquality: %s\n\t\tTesting Value:\t%s\n\t\tExpected Value:\t%s" % (label,testingValue, expectedValue)
		numOfFailedCases += 1

def tExist(label, testingObject, expectedFailed = False):
	global numOfCases
	global numOfFailedCases
	numOfCases += 1
	if not testingObject == None and not expectedFailed:
		print "O\tExistence: %s" % (label)
		return True
	elif testingObject == None and expectedFailed:
		print "O\tNon-existence: %s" % (label)
		return True
	else:
		print "X\tExistence: %s" % (label)
		numOfFailedCases += 1
		return False

print "========================================================================"
print "Yotsuba Project 2 > Unit Test"
print "------------------------------------------------------------------------"
# sdk.xml > Initialization test
yotsuba.xml.read("test", "xml-test-1.xml")
# sdk.xml > Existance tests
passedQueries = ['c1', 'c c1', 'root c c1', 'root c1', 'root > c c1', 'root c > c1', 'root > c > c1', 'common', 'c c1, e e11']
failedQueries = ['c3', 'c c3', 'root > c1', 'root c e1']
for pq in passedQueries:
	tMore("XML Query Test / Existance (%s)" % pq, yotsuba.xml.query('test', pq).length(), 0)
for fq in failedQueries:
	tEqual("XML Query Test / Existance (%s)" % fq, yotsuba.xml.query('test', fq).length(), 0)
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
	'*': 21,
	'c common': 1,
	'c + d': 1,
	'c ~ e': 2,
	'e common': 3,
	'e > common': 1,
	'e > e1 common': 1,
	'd common': 0,
	'c c1, e e11': 2
}
for pqK, pqV in passedQueries.iteritems():
	tEqual("XML Query Test / Correctness (%s)" % pqK, yotsuba.xml.query('test', pqK).length(), pqV)
# sdk.xml > Data extraction tests
tEqual("XML Query Test (Data)", yotsuba.xml.query('test', 'c c1').data(), yotsuba.xml.trees['test'].children[2].children[0].data())
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
	print ":\tCreating SO from '%s'" % pqK
	tEqual("The selector object construction (Name)", yotsuba.xml.makeSelectorObject(pqK).name(), pqV[0])
	tEqual("The selector object construction (ID/Operator)", yotsuba.xml.makeSelectorObject(pqK).attr('id')[0], pqV[1])
	tEqual("The selector object construction (ID/Value)", yotsuba.xml.makeSelectorObject(pqK).attr('id')[1], pqV[2])
	tEqual("The selector object construction (Filters)", ''.join(yotsuba.xml.makeSelectorObject(pqK).filter()), pqV[3])
print "------------------------------------------------------------------------"
print "Score\t%d/%d\t%.2f%%" % (numOfCases - numOfFailedCases, numOfCases, (numOfCases - numOfFailedCases)*100/numOfCases)
print "========================================================================"
if (numOfFailedCases > 0 or forceShowLog) and not forceHideLog:
	print "Yotsuba Project 2 > Testing Logs"
	print "------------------------------------------------------------------------"
	try:
		yotsuba.fs.remove('test.log')
	except:
		pass
	if not yotsuba.fs.writable('./'):
		print 'Not writable'
	if yotsuba.fs.write('test.log', yotsuba.log.export()):
		print 'The report was just written'
	else:
		print 'The report was not written'
	if not yotsuba.fs.exists('test.log'):
		print 'Failed to write the report'
	else:
		print "See the 'test.log'"
	print "========================================================================"