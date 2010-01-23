from __future__ import print_function
from yotsuba3.test import core_mt

import math

print("Demonstration on passing functions as arguments")

def x(m, n):
    print("%d" % sum([m, n]))

def y(a, *b):
    a(*b)

y(x, 1, 2)

print("Now, the fun is over. Let's do the real stuff.")

core_mt.run()