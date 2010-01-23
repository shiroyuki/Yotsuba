"""
Multi-threading framework for Yotsuba 3

Author: Juti Noppornpitak <juti_n@yahoo.co.jp>
Copyright: Shiroyuki Studio

This framework is to make multi-threading programming in Python even easier. The
current core is compatible with Python 2.6.
"""

import Queue
import threading

class MTBaseQueueException(Exception):
    def __init__(self, message = None):
        if message is None:
            message = "Generic multi-threading framework error exception"
        else:
            message = unicode(message)
        super(Exception, self).__init__(message)

class MTBase(threading.Thread):
    def lineUp(self, queue):
        if 'queues' in dir(self):
            self.queues = []
        isAlreadyOnTheList = queue not in self.queues
        if isAlreadyOnTheList:
            self.queues.append(queue)
        else:
            raise MTBaseQueueException()
    def init(self, function, args = None):
        """Initialize the function to run"""
        pass