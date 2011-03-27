Lesson 3: Web Development
=========================

Scenario
--------

Quickly develop a web application or a web service.

Get started
-----------

Yotsuba 3 comes with a built-in web framework called :doc:`../references/tori`.

As Yotsuba 3 is a pure-Python library, it does not supply with executable commands
like a framework such as **Pylons** or **Django**. Nevertheless, it is not hard
to get started.

First of all, you need to a script that calls :py:mod:`yotsuba.lib.tori.setup`
with ``auto_config`` enabled. For example, you have a script called ``service.py``
at ``/home/dev/tori_app`` containing:

.. code-block:: python
    :linenos:
    
    # service.py
    from yotsuba.lib import tori
    tori.setup('config.xml', auto_config=True)

.. note::
    In order to save some unnecessary computation, the option ``auto_config`` is
    ``false`` by default.

Then from execute ``python service.py`` or ``python /home/dev/tori_app/service.py``.

At this point, do not freak out as the service does not start. The script just
created the configuration file ``config.xml`` which contains something similar to this

.. code-block:: xml
    :linenos:
    
    <?xml version="1.0" encoding="UTF-8"?>
    <webconfig>
        <mode>local</mode>
        <rendering>mako</rendering>
        <base_path>
            <static>static</static>
            <template>template</template>
            <session>memory</session>
        </base_path>
        <!--
        <port>8080</port>
        -->
        <base_uri>/</base_uri>
        <static_routing>
        <!--
            <file link="favicon.ico" ref="favicon.ico" />
            <dir link="image" ref="image" />
            <dir link="css" ref="css" />
            <dir link="js" ref="js" />
        -->
        </static_routing>
        <settings>
            <option name="debug">false</option>
            <option name="text_minification">false</option>
            <option name="no_cache">true</option>
        </settings>
    </webconfig>

As it is, what does this file tell you?
#. ``mode`` tells you what mode it is. There are three modes supported.

 * ``local`` (standalone, WSGI server)
 * ``app`` (WSGI application)
 * ``gae`` (WSGI application for Google App Engine)

#. ``rendering`` tells you what rendering engine it uses. There are two engines automatically supported.

 * ``mako`` (Mako template)
 * ``tenjin`` (Tenjin template known as *PyTenjin*)

#. ``base_path`` is telling you the base paths of ``static`` (static file), ``template`` (templates) and ``session`` (file-based session storage). These will be created on demand if not existed. Please note that these are based on the current working directory.
#. ``port`` (optional) is telling you what port it is listening to. This only works in mode ``local``.
#. ``base_uri`` is telling you the base URI of the application.
#. ``static_routing`` tells you where the static content is and how to get it. Please note that anything in ``static`` will be automatically mapped with the same path. See the next example on advanced routing.
#. ``settings`` tells you the settings the app is using. There are three main settings.

 * ``debug`` is to enable debugging messages.
 * ``text_minification`` is to enable text minification (e.g. XML, HTML, CSS, JavaScript etc.)
 * ``no_cache`` is to disable in-memory caching mechanism. Primarily used to disable :py:mod:`yotsuba.lib.tori.BaseInterface.cache`.

Play around with configuration
------------------------------

Suppose you want to go fancy with the configuration by:

#. run the app on port 80.
#. change the location of the session storage to ``/tmp/tori_app/``
#. use other ICO file as ``favicon.ico``
#. rename the directory name in the static folder from ``very_ugly_name`` to ``something_better`` without physically renaming it.

Then, you will have something like this.

.. code-block:: xml
    :linenos:
    
    <?xml version="1.0" encoding="UTF-8"?>
    <webconfig>
        <mode>local</mode>
        <rendering>mako</rendering>
        <base_path>
            <static>static</static>
            <template>template</template>
            <session>/tmp/tori_app/</session>
        </base_path>
        <port>80</port>
        <base_uri>/</base_uri>
        <static_routing>
            <file link="favicon.ico" ref="favicon-beta.ico" />
            <dir link="something_better" ref="very_ugly_name" />
        </static_routing>
        <settings>
            <option name="debug">false</option>
            <option name="text_minification">false</option>
            <option name="no_cache">true</option>
        </settings>
    </webconfig>

At this point, the application is still not runable. You need the next step to run.

Wait! "Hello, world!" again!?
-----------------------------

Well, yes. Now, assume that you want to "Hello, world!" again with Tori.

Create an interface
+++++++++++++++++++

Well, Tori **interface** is the same sense as **controller** in many web
frameworks, **view** in Django or **Servlet** in Java.

In Yotsuba's Tori, you can use a class inherited from

* :py:mod:`yotsuba.lib.tori.BaseInterface`
* :py:mod:`yotsuba.lib.tori.RESTInterface`
* any ``object``-based class

For starter, we will put everything in ``service.py``.

.. code-block:: python
    :linenos:
    
    # service.py
    from yotsuba.lib import tori
    tori.setup('config.xml') # disable auto_config
    
    class HelloWorld(tori.BaseInterface):
        def index(self):
            return "Hello, world!"
        index.exposed = True

Please note that this is the same way you do in CherryPy 3.1+. Please visit
http://cherrypy.org/wiki/CherryPyTutorial for more information.

Run the application
+++++++++++++++++++

Finally, add ``application = tori.ServerInterface.auto(HelloWorld())`` to start
the application.

.. code-block:: python
    :linenos:
    
    # service.py
    from yotsuba.lib import tori
    tori.setup('config.xml') # disable auto_config
    
    class HelloWorld(tori.BaseInterface):
        def index(self):
            return "Hello, world!"
        index.exposed = True
    
    def main():
        application = tori.ServerInterface.auto(HelloWorld())
    
    if __name__ == "__main__":
        main()

Run ``python service.py`` (or with the absolute path) again. Now, you should be
able to access to your app at http://127.0.0.1/.

.. note::

    The application is listening at ``0.0.0.0:80``.

What is so fascinating about Tori comparing to plain CherryPy?
--------------------------------------------------------------

`CherryPy <http://cherrypy.org>`_ is a very good framework but it is like
writing "Hello, world!" in Java comparing to Python. Yotsuba's **Tori** is
developed to reduce the complexity of getting started with CherryPy and make the
development with the framework more enjoyable.

As Tori is developed as the wrapper of CherryPy, hence Tori is fully compatible
with all tools available in CherryPy.

Tori is made for deployment into any platform with a single script.

Conclusion
==========

To be frank with you, beside doing something very fancy, I (Juti, the author)
can develop pretty much every thing with Yotsuba 3. These tutorials are only
giving you some highlighted features of Yotsuba 3. You can explore more about
other built-in on this site.

.. seealso::
    
    Module :py:mod:`yotsuba.lib.tori`
        Web framework