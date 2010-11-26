Lesson 2: XML Parsing
=====================

Scenario
--------

Suppose you want to write a code that parse any arbitery RSS feeds. Generally,
the developers should have no problem with DOM iteration or XPath. However, it
may become frustration for someone who just comes straight from web front-end
development.

Solution
--------

You can use :py:mod:`yotsuba.lib.kotoba.Kotoba` to help you with that. Suppose
you have a variable called ``rss_data`` containing an XML data.

First, parse the data.::

    from yotsuba.lib.kotoba import Kotoba
    rss_xml = Kotoba(rss_data)

Then, find element *item*.::

    raw_items = rss_xml.get("item")

.. note::
    Now, ``raw_items`` is an instance of :py:mod:`yotsuba.lib.kotoba.DOMElements`
    as a result of calling the method ``get`` of :py:mod:`yotsuba.lib.kotoba.Kotoba`

Then, find elements *title*, *link*, *description*, *comments* and *pubDate*
under each block of element *item*.::

    for item in raw_items:
        title = item.get('title').data()
        link = item.get('link').data()
        description = item.get('description').data()
        comments = item.get('comments').data()
        publishedDate = item.get('pubDate').data()

.. note::
    If the specified elements are not found, the method ``data`` will return an empty string.

If you want the title of the first item, you can do::

    first_title = rss_xml.get("item title")
    if first_title: first_title = first_title[0]

Limitation
----------

While other libraries can parse arbitery document, even HTML 4, 
:py:mod:`yotsuba.lib.kotoba.Kotoba` is limited by ``xml.dom.minidom``. So, it
cannot read anything other than XML.

Additionally, :py:mod:`yotsuba.lib.kotoba.Kotoba` understands only two pseudo classes, ``:root`` and ``:empty``.

Next, :doc:`lesson3-web-development`

.. seealso::
    
    Module :py:mod:`yotsuba.lib.kotoba`
        XML Parser with CSS selectors
    
    Module :py:mod:`yotsuba.lib.aria`
        Feed reader