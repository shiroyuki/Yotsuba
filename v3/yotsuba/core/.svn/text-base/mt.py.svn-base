"""
High-level multi-threading framework for Yotsuba 3

This framework is to make multi-threading programming in Python even easier. The
current core is compatible with Python 2.6+.

At the current state of the development, there is a known limitation that it can
only run one kind of the worker. Also, the framework will block the caller thread
until all data is processed.
"""

import sys
from Queue import Queue
from threading import Thread, activeCount

__scan_only__ = ['MultiThreadingFramework', 'sample_worker_function']
__version__ = 1.1

def sample_worker_function(data):
    '''
    This is the sample worker function/method.
    
    Requirements for the worker function/method:
        1.  The first parameter must be something that stores the data from the queue.
        2.  The worker never returns anything unless it is a new data that you want it
            to be processed in the current pool.
    '''
    url = data
    # do something with the data

class ThreadTermSignal(object):
    '''
    Terminating Signal only used by MultiThreadingFramework
    '''
    __scan_only__ = []
    pass

class MultiThreadingFramework(object):
    '''
    Simple multi-threading framework for small tasks.
    '''
    __scan_only__ = ['run']
    dataQueue = None
    numberOfFalseTermSignal = None
    
    def run(self, input, worker, args = None, simulteneousWorkerLimit = None):
        '''
        Run multiple workers simulteneously (in multiple threads).
        
        The parameter *worker* is a reference to a function that will be called by
        the thread.
        
        The parameter *input* is the input list that will be feeded to the queue.
        
        The parameter *worker* is the data processing function. there is no need for it to handle the synchronization.
        
        @param args: the arguement for the worker
        @param simulteneousWorkerLimit: the limit of how many threads can be running simulteneously. (Optional, default: 4 or less depends on the length of urls)
        '''
        simulteneousWorkerLimit = (simulteneousWorkerLimit is None and type(simulteneousWorkerLimit) is not int) and 4 or simulteneousWorkerLimit
        
        self.dataQueue = Queue()
        self.numberOfFalseTermSignal = 0
        threads = []
        
        if type(input) is not list:
                raise Exception("The list of inputs for this method must be a list.")
        
        if args is not None:
            if type(args) not in [tuple, list]:
                raise Exception("The arguements for this method must be either a tuple or a list.")
            if len(args) > 0:
                args = list(args)
                args = [worker] + args
                args = tuple(args)
            else:
                args = tuple([worker])
        
        # start threads
        for i in xrange(simulteneousWorkerLimit):
            t = Thread(target = self.__thread, args = args)
            t.daemon = True
            t.start()
            threads.append(t)
        
        # add ThreadTermSignal
        inputData = list(input)
        inputData.extend([ThreadTermSignal] * simulteneousWorkerLimit)
        
        # put in the queue
        for data in inputData:
            self.__addData(data, False)
    
        # block until all contents are downloaded
        self.dataQueue.join()
        
        self.dataQueue = None
        for thread in threads:
            del thread
        del threads
    
    def __addData(self, data, addTermSignal):
        self.dataQueue.put(data)
        
    def __thread(self, worker, *args):
        try:
            while True:
                returnedData = None
                data = self.dataQueue.get()
                
                # Check for the term signal
                if data is ThreadTermSignal:
                    # If this is false alarm
                    if self.numberOfFalseTermSignal > 0:
                        self.numberOfFalseTermSignal -= 1
                        continue
                    else:
                        sys.exit()
                
                # Call the processor
                if len(args) > 0:
                    returnedData = worker(data, *args)
                else:
                    returnedData = worker(data)
                
                # If the worker return something, add the data to the queue.
                if returnedData is not None:
                    self.__addData(returnedData, True)
                
                self.dataQueue.task_done()
        except SystemExit:
            self.dataQueue.task_done()
            pass
        except:
            self.dataQueue.task_done()
            pass

