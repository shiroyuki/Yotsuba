import os
import re

from yotsuba3.lib.kotoba import Kotoba, DOMElement

defaultErrorTemplate = 'error.html'

# Error pages
def errorResponse(status, message, traceback, version):
    substitutions = {
        'code':    status,
        'msg':     re.sub(" (u|r)?'", " ", re.sub("' ", " ", message))
    }
    return yotsuba.fs.read(os.path.join(path['template'], errorTemplate)) % substitutions

additionalConfig = {
    'log.screen': False,                    # Disable trackback information
    'error_page.default': errorResponse     # Use the custom error response from Tori
}

# Setup
def setup(setupFilename):
    """
    Set up the environment
    """
    
    global baseURI
    global basePath
    global path
    global errorTemplate
    global staticRouting
    
    # Initialization
    baseURI = ''
    basePath = ''
    path = {}
    errorTemplate = defaultErrorTemplate
    staticRouting = {}
    
    # Base path
    basePath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
    
    # Load the configuration files
    targetDestination = "%s/%s" % (basePath, setupFilename)
    xmldoc = Kotoba(targetDestination)
    
    # Store the basic paths
    pathIndices = xmldoc.get('basepath *')
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
    __baseConfigKey = 'tools.static'
    
    for referenceSetting in xmldocOnStaticRouting:
        __type = referenceSetting.name()
        __ref = referenceSetting.attr['ref']
        __link = referenceSetting.attr['link']
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
