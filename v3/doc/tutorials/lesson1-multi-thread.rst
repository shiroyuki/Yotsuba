Lesson 1: Multi-threading programming
=====================================

Scenario
--------

Suppose you want to write a code to find files larger than 100MB in multiple location.

.. code-block:: python
    :linenos:

    '''
    Multi-thread disk scanner for large files
    
    .. codeauthor:: Juti Noppornpitak <juti_n@yahoo.co.jp>
    '''
    
    from math import pow
    from yotsuba.core import base, fs
    
    threshold = pow(1024,2) * 100 # 100 MB
    inputs = []
    entries = []
    locations = ["/Users/jnopporn/Downloads", "/Users/jnopporn/Documents", "/Applications"]
    
    def worker(i):
        size = fs.size(i)
        if size > threshold:
            entries.append((i, fs.size(i)))
    
    print "Threshold: %16s" % base.convert_to_readable_size(threshold)
    
    for location in locations:
        all_entries = fs.browse(location, True)
        inputs.extend(all_entries['directories'])
        inputs.extend(all_entries['files'])
    
    for i in inputs:
        worker(i)
    
    for e in entries:
        print "%16s\t%s" % (base.convert_to_readable_size(e[1]), e[0])

Although this is very easy, if you are looking in a large number of locations,
multiple threads might speed up the code.

Solution
--------

First of all, let's import :py:mod:`yotsuba.core.mt`.

Then, replace the ``for`` loop with the following::

    mtfw = mt.MultiThreadingFramework()
    mtfw.run(
        inputs,
        worker
    )

In the end, you will have something like below.

.. code-block:: python
    :linenos:

    '''
    Multi-thread disk scanner for large files
    
    .. codeauthor:: Juti Noppornpitak <juti_n@yahoo.co.jp>
    '''
    
    from math import pow
    from yotsuba.core import base, fs, mt
    
    threshold = pow(1024,2) * 100 # 100 MB
    inputs = []
    entries = []
    locations = ["/Users/jnopporn/Downloads", "/Users/jnopporn/Documents", "/Applications"]
    
    def worker(i):
        size = fs.size(i)
        if size > threshold:
            entries.append((i, fs.size(i)))
    
    print "Threshold: %16s" % base.convert_to_readable_size(threshold)
    
    for location in locations:
        all_entries = fs.browse(location, True)
        inputs.extend(all_entries['directories'])
        inputs.extend(all_entries['files'])
    
    mtfw = mt.MultiThreadingFramework()
    mtfw.run(inputs, worker, tuple())
    
    for e in entries:
        print "%16s\t%s" % (base.convert_to_readable_size(e[1]), e[0])

What is the difference?
-----------------------

When you use ``for`` loop, each call to ``worker`` will pause the caller
thread until ``worker`` finishes execution. In the meanwhile,
:py:mod:`yotsuba.core.mt.MultiThreadingFramework` scans multiple location
simutaneously in multiple threads.

.. note::
    After execution, :py:mod:`yotsuba.core.mt.MultiThreadingFramework` will kill
    all child threads created during the process.

Next, :doc:`lesson2-xml-parsing`

.. seealso::

    Module :py:mod:`yotsuba.core.base`
        Base Module
    
    Module :py:mod:`yotsuba.core.fs`
        File System API
    
    Module :py:mod:`yotsuba.core.mt`
        Fuoco Multi-threadinf Programming Framework