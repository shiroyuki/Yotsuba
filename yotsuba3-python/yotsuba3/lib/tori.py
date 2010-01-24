import os
import sys
import re

import cherrypy

# Disable Yotsuba 3's XML module until it is usable
#from yotsuba3.lib.kotoba import Kotoba, DOMElement

# Use Yotsuba 2's XML module instead
import yotsuba
Kotoba = yotsuba.XML

defaultErrorTemplate = 'error.html'
baseURI = ''
basePath = ''
path = {}
errorTemplate = defaultErrorTemplate
staticRouting = {}

class WebFrameworkException(Exception):
    pass

# Error pages
def errorResponse(status, message, traceback, version):
    substitutions = {
        'code':    status,
        'msg':     re.sub(" (u|r)?'", " ", re.sub("' ", " ", message))
    }
    return yotsuba.fs.read(os.path.join(path['template'], errorTemplate)) % substitutions

defaultConfig = {
    'log.screen': False,                    # Disable trackback information
    'error_page.default': errorResponse     # Use the custom error response from Tori
}

# Setup
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
    errorTemplate = defaultErrorTemplate
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
        
        # Prepare for routing
        # Note: All keys in staticRouting have to be ASCII.
        
        if not yotsuba.fs.exists(path['session']):
            raise Exception("%s not found" % path['session'])
        
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
            
            staticRouting[baseURI + __link] = {
                str(__cKeyFlag): True,
                str(__cKeyPath): __ref
            }
        
        # Add custom error pages
        errorTemplate = xmldoc.get('errorTemplate').data()
    except:
        raise WebFrameworkException("Error while reading configuration from %s" % targetDestination)
    
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

def render(source, givenContext = None):
    if givenContext is None:
        givenContext = ContextContainer()
    mylookup = TemplateLookup(
        directories = [path['template']],
        output_encoding = 'utf-8',
        encoding_errors = 'replace'
    )
    mytemplate = mylookup.get_template(source)
    return mytemplate.render(c = givenContext)

##################
# Base Interface #
##################

class BaseInterface(object):
    def __init__(self):
        self.c = ContextContainer()
        pass
    
    def render(self, source):
        return render(source, self.c)