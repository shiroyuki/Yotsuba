Lesson 1: Multi-threading programming
=====================================

Scenario
--------

Suppose you want to write a code that fetch RSS feeds from multiple sources at
the given time.

::

    from yotsuba.lib.aria import Feeds
    
    # input
    urls = [
        ("my blog's rss", 'http://nikki.shiroyuki.com/rss'),
        ("service status", 'http://status.shiroyuki.com/rss')
    ]
    
    # output
    feeds = {}
    
    # worker
    def feed_receiver(input, output):
        description, url = input
        feeds = Feeds.make_from_rss_feed(url)
        output[description[0]] = feeds # description: processed response
    
    for url in urls:
        feed_receiver(url, feeds)

The good news is that retrieving something via HTTP is very simple. However,
the bad news is that retrieving too many feeds linearly is obviously slow. So,
let's use Fuoco (:py:mod:`yotsuba.core.mt`) to help you.

Solution
--------

First of all, let's import ``MultiThreadingFramework`` from :py:mod:`yotsuba.core.mt`.

Then, replace the *for* loop with the following::

    mtfw = MultiThreadingFramework()
    mtfw.run(
        urls,
        feed_receiver,
        tuple([feeds])
    )

In the end, you will have something like below.

::

    from yotsuba.core.mt import MultiThreadingFramework
    from yotsuba.lib.aria import Feeds
    
    # input
    urls = [
        ("my blog's rss", 'http://nikki.shiroyuki.com/rss'),
        ("service status", 'http://status.shiroyuki.com/rss')
    ]
    
    # output
    feeds = {}
    
    # thread worker
    def feed_receiver(input, output):
        description, url = input
        feeds = Feeds.make_from_rss_feed(url)
        output[description[0]] = feeds # description: processed response
    
    mtfw = MultiThreadingFramework()
    mtfw.run(
        urls,
        feed_receiver,
        tuple([feeds])
    )

What is the difference?
-----------------------

When you use ``for`` loop, each call to ``feed_receiver`` will pause the caller
thread until ``feed_receiver`` finishes execution. In the meanwhile,
:py:mod:`yotsuba.core.mt.MultiThreadingFramework` is retrieving data from
multiple sources simutaneously in multiple threads.

.. note::
    After execution, :py:mod:`yotsuba.core.mt.MultiThreadingFramework` will kill
    all child threads created during the process.

Next, :doc:`lesson2-xml-parsing`

.. seealso::
    Module :py:mod:`yotsuba.core.mt`
        XML Parser with CSS selectors