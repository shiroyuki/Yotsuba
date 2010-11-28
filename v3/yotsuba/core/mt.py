"""
Fuoco is a simple **multi-threading programming framework** for Yotsuba 3. This
framework is to make multi-threading programming in Python even easier. The
framework will block the caller thread until all data is processed.

At the current state of the development, there are known limitations:

#. ``MultiThreadingFramework`` can only use one kind of the worker at a time.
#. ``MultiThreadingFramework.run`` can not return anything. Global variables
   can be used to resolve this problem.
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

class UnsupportedInputList(Exception):
    ''' Exception for unsupported input list '''

class UnsupportedCommonArguments(Exception):
    ''' Exception for unsupported common arguments '''

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
    list_types = [tuple, list]
    default_max_thread = 4
    data_queue = None
    number_of_false_term_signals = None
    
    def run(self, input, worker, common_args = None, max_thread = None):
        '''
        Run multiple workers simulteneously (in multiple threads).
        
        The parameter `worker` is a reference to a function that will be called by
        each thread.
        
        The parameter `input` is the input list that will be feeded to the queue.
        
        The parameter `common_args` is the common arguements for the worker.
        
        The parameter `max_thread` is the maximum number of threads used in one run. (Optional, default: 4)
        '''
        
        max_thread = (max_thread is None and type(max_thread) is not int) and self.default_max_thread or max_thread
        
        self.data_queue = Queue()
        self.number_of_false_term_signals = 0
        threads = []
        
        if type(input) not in self.list_types:
            raise UnsupportedInputList
        
        if common_args is not None:
            if type(common_args) not in self.list_types:
                raise UnsupportedCommonArguments
            
            if len(common_args) > 0:
                args = list(common_args)
                args = [worker] + common_args
                args = tuple(common_args)
            else:
                args = tuple([worker])
        
        # start threads
        for i in range(max_thread):
            t = Thread(target = self.__thread, args = args)
            t.daemon = True
            t.start()
            threads.append(t)
        
        # push data in list
        input_data = list(input)
        
        # add ThreadTermSignal
        input_data.extend([ThreadTermSignal] * max_thread)
        
        # put everything in the data queue
        for data in input_data:
            self.add_data(data, False)
    
        # block until all contents are downloaded
        self.data_queue.join()
        
        self.data_queue = None
        for thread in threads:
            del thread
        del threads
    
    def add_data(self, data, add_term_signal):
        self.data_queue.put(data)
        
    def __thread(self, worker, *args):
        try:
            while True:
                returned_data = None
                data = self.data_queue.get()
                
                # Check for the term signal
                if data is ThreadTermSignal:
                    # If this is false alarm
                    if self.number_of_false_term_signals > 0:
                        self.number_of_false_term_signals -= 1
                        continue
                    else:
                        sys.exit()
                
                # Call the processor
                if len(args) > 0:
                    returned_data = worker(data, *args)
                else:
                    returned_data = worker(data)
                
                # If the worker return something, add the data to the queue.
                if returned_data: self.add_data(returned_data, True)
                self.data_queue.task_done()
        except SystemExit:  pass
        finally:            self.data_queue.task_done()
