import os
import sys
import re

import cherrypy

from yotsuba3.core import base

# Disable Yotsuba 3's XML module until it is usable
#from yotsuba3.lib.kotoba import Kotoba, DOMElement

# Use Yotsuba 2's XML module instead
import yotsuba
Kotoba = yotsuba.XML

baseURI = ''
basePath = ''
path = {}
errorTemplate = None
staticRouting = {}

class WebFrameworkException(Exception):
    pass

class WebFrameworkErrorPage(object):
    DEFAULT_TEMPLATE = """<!doctype html>
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
        <head>
            <title>Tori</title>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            <style type="text/css">
                body {
                    font-family: 'Helvetica', 'Arial';
                    font-weight: normal;
                    font-size: 16px;
                    margin: 0;
                    padding: 0;
                    min-width: 720px;
                }
                
                h1 {
                    font-weight: normal;
                    font-size: 24px;
                    margin: 0;
                    padding: 10px 20px;
                    background-color: #000;
                    color: #99cc00;
                }
                
                h2 {
                    font-weight: normal;
                    font-size: 20px;
                    margin: 0;
                    padding: 10px 20px;
                    background-color: #669900;
                }
                
                h3 {
                    border-top: 3px solid #000;
                    font-weight: bold;
                    margin: 10px 20px;
                    padding: 5px 0;
                }
                
                pre {
                    white-space: pre-wrap;
                    font-size: 12px;
                    padding: 0;
                    margin: 0;
                }
                
                #ts {
                    border: 1px solid #ffcc00;
                    background-color: #ffffcc;
                    padding: 10px;
                    margin: 5px 20px;
                    border-radius: 10px;
                    -moz-border-radius: 10px;
                    -webkit-border-radius: 10px;
                }
                
                #footer {
                    padding: 30px 20px;
                    color: #999;
                }
                
                table {
                    margin: 5px 20px;
                    display: block;
                }
                
                th {
                    color: #999;
                    font-weight: normal;
                    vertical-align: top;
                    text-align: right;
                    width: 100px;
                    padding-top: 5px;
                    padding-left: 10px;
                    padding-right: 10px;
                    padding-bottom: 5px;
                    border-right: 1px solid #ccc;
                }
                
                td {
                    vertical-align: top;
                    padding-top: 5px;
                    padding-left: 10px;
                    padding-bottom: 5px;
                }
            </style>
        </head>
        <body>
            <h1>Yotsuba Project</h1>
            <h2>Tori Web Framework</h2>
            <h3>Response</h3>
            <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                    <th>Code</th>
                    <td>HTTP %(code)s.</td>
                </tr>
                <tr>
                    <th>Reason</th>
                    <td>%(msg)s</td>
                </tr>
            </table>
            <h3>Tracing Stack</h3>
            <div id="ts">
                <pre>%(tracingStack)s</pre>
            </div>
            <p id="footer">
                &copy; 2009 Juti Noppornpitak (Shiroyuki Studio). All Rights
                Reserved. %(version)s is licensed under LGPL and MIT.
            </p>
        </body>
        </html>"""
    
    @staticmethod
    def response(status, message, traceback, version):
        """ Error Handler """
        substitutions = {
            'version':      base.getVersion(),
            'code':         status,
            'msg':          re.sub(" (u|r)?'", " ", re.sub("' ", " ", message)),
            'tracingStack': cherrypy._cperror.format_exc()
        }
        template = errorTemplate is None and WebFrameworkErrorPage.DEFAULT_TEMPLATE or errorTemplate
        return template % substitutions

defaultConfig = {
    'log.screen':           False,                          # Disable trackback information
    'error_page.default':   WebFrameworkErrorPage.response  # Use the custom error response from Tori
}

##################
# Setup function #
##################

run = cherrypy.quickstart

def setup(setupFilename, enableDebuggingMode = False, additionalConfig = None):
    """
    Set up the environment
    """
    
    global baseURI
    global basePath
    global path
    global errorTemplate
    global staticRouting
    global defaultConfig
    
    # Initialization
    __baseConfigKey = 'tools.static'
    baseURI = ''
    basePath = ''
    path = {}
    errorTemplate = None
    staticRouting = {}
    
    # Get the reference to the calling function
    f = sys._getframe(1)
    c = f.f_code
    referenceToCaller = c.co_filename
    
    # Base path
    basePath = os.path.abspath(os.path.dirname(os.path.abspath(referenceToCaller)))
    
    # Get the location of the given the configuration files
    targetDestination = "%s/%s" % (basePath, setupFilename)
    
    try:
        # Load the configuration files
        xmldoc = Kotoba(targetDestination)
        
        # Store the basic paths
        pathIndices = xmldoc.get('basepath *')
        pathIndices = pathIndices.list() # [Legacy] the way to get the list of node in Yotsuba 2
        for pathIndex in pathIndices:
            path[pathIndex.name()] = os.path.join(basePath, pathIndex.data())
        
        # Get the base URI
        baseURI = xmldoc.get('baseURI').data()
        baseURI = baseURI.strip()
        baseURI = re.sub("^/", "", baseURI)
        baseURI = re.sub("/$", "", baseURI)
        
        # Prepare for routing
        # Note: All keys in staticRouting have to be ASCII.
        
        if not yotsuba.fs.exists(path['session']):
            try:
                yotsuba.fs.mkdir(path['session'])
            except:
                raise WebFrameworkException("%s not found" % path['session'])
        
        staticRouting[baseURI] = {
            'tools.sessions.on': True,
            'tools.sessions.timeout': 10,
            'tools.sessions.storage_type': 'file',
            'tools.sessions.storage_path': path['session']
        }
        
        xmldocOnStaticRouting = xmldoc.get('staticRouting file, staticRouting dir')
        xmldocOnStaticRouting = xmldocOnStaticRouting.list() # [Legacy] the way to get the list of node in Yotsuba 2
        
        for referenceSetting in xmldocOnStaticRouting:
            __type = referenceSetting.name()
            try:
                __ref = referenceSetting.attr['ref']
            except:
                __ref = referenceSetting.attr('ref')
            try:
                __link = referenceSetting.attr['link']
            except:
                __link = referenceSetting.attr('link')
            __cBaseKey = "%s%s" % (__baseConfigKey, __type)
            __cKeyFlag = "%s.on" % (__cBaseKey)
            __cKeyPath = "%s.%s" % (__cBaseKey, __type)
            
            __ref = os.path.join(path['static'], __ref)
            
            if __type == 'file' and __ref is not None:
                __cKeyPath += 'name'
            
            staticRouting[baseURI + '/' + __link] = {
                str(__cKeyFlag): True,
                str(__cKeyPath): __ref
            }
    except:
        raise WebFrameworkException("Error while reading configuration from %s" % targetDestination)
    
    try:
        # Add custom error pages
        if xmldoc.get('errorTemplate').length() > 0:
            errorTemplate = xmldoc.get('errorTemplate').data()
            errorTemplate = yotsuba.fs.read(os.path.join(path['template'], errorTemplate))
    except:
        raise WebFrameworkException("Error while setting up a custom error error page.")
    
    if not enableDebuggingMode:
        cherrypy.config.update(defaultConfig)
    
    if additionalConfig is not None:
        cherrypy.config.update(additionalConfig)

######################
# Rendering function #
######################

from mako.template import Template
from mako.lookup import TemplateLookup

class ContextContainer(object):
    def __str__(self):
        rt = 'ContextContainer:'
        for k, v in self.__dict__.iteritems():
            rt += u' %s = %s' % (unicode(k), unicode(v))
        return rt

def render(source, givenContext = None, **kwargs):
    givenContext = givenContext is None and ContextContainer() or givenContext
    mylookup = TemplateLookup(
        directories = [path['template']],
        output_encoding = 'utf-8',
        encoding_errors = 'replace'
    )
    mytemplate = mylookup.get_template(source)
    return mytemplate.render(baseURI = baseURI, c = givenContext, **kwargs)

##################
# Base Interface #
##################

class BaseInterface(object):
    def __init__(self):
        self.c = ContextContainer()
        pass
    
    def render(self, source, **kwargs):
        return render(source, self.c, **kwargs)