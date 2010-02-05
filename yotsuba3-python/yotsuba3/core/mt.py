"""
Multi-threading framework for Yotsuba 3

Author: Juti Noppornpitak <juti_n@yahoo.co.jp>
Copyright: Shiroyuki Studio

This framework is to make multi-threading programming in Python even easier. The
current core is compatible with Python 2.6.
"""

import Queue
import threading

version = 0.1

class AgentThread(threading.Thread):
    # Queue Reference
    __dataQueue = None
    
    def __init__(self, threadObject, dataQueue = None):
        if dataQueue is not None:
            self.__dataQueue = dataQueue
        else:
            self.__dataQueue = Queue.Queue()
    
    def preprocess(self):
        pass
    
    def run(self):
        pass
    
    def postprocess(self):
        pass
    
    pass

class Manager(object):
    __simulteneousThreadLimit = None
    __agents = None
    def __init__(self, simulteneousThreadLimit = None):
        if simulteneousThreadLimit is not None:
            self.__simulteneousThreadLimit = threading.BoundedSemaphore(simulteneousThreadLimit)
        self.__agents = []
    
    def addThread(self, instanceOfAgentThread):
        agent = instanceOfAgentThread
        self.__agents.append(agent)
    
    def addFunction(self, referenceToFunction, *args, **kwargs):
        worker = threading.Thread(target = referenceToFunction, args = args, kwargs = kwargs)
        worker.setDaemon(True)
        pass

class BaseQueueException(Exception):
    def __init__(self, message = None):
        if message is None:
            message = "Generic multi-threading framework error exception"
        else:
            message = unicode(message)
        super(Exception, self).__init__(message)
