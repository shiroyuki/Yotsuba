#from __future__ import print_function
#from yotsuba3.test import core_mt

import math

print "Demonstration on passing functions as arguments"

def x(m, n):
    print "%d" % sum([m, n])

def y(a, *b):
    a(*b)

def z(*a):
    if len(a) > 2:
        a[0](*a[1:])
    else:
        a[0]()

def p(a = None):
    print a

a = 20
p(a = a)
y(x, 1, 2)
z(x, 1, 2)

import time
from Queue import Queue
from threading import Thread
import urllib2

st = time.time()

def workerThread():
    while True:
        item = q.get()
        f = urllib2.urlopen(item)
        print "Done"
        q.task_done()

q = Queue()
for i in range(4):
     t = Thread(target=workerThread)
     t.setDaemon(True)
     t.start()

for item in range(8):
    q.put("http://c.shiroyuki.com/feeds/featured-content.xml")

q.join()

print "%s sec" % (time.time() - st)

#print("Now, the fun is over. Let's do the real stuff.")

#core_mt.run()