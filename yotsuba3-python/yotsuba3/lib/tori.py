PACKAGE_VERSION = "0.9"

import os
import sys
import re
import pprint

import cherrypy

from time import time

from wsgiref import handlers
from yotsuba3.core import base

# Disable Yotsuba 3's XML module until it is usable
#from yotsuba3.lib.kotoba import Kotoba, DOMElement

# Use Yotsuba 2's XML module instead
import yotsuba
Kotoba = yotsuba.XML

debug = False
mode = ''
baseURI = ''
basePath = ''
path = {}
errorTemplate = None
staticRouting = {}
defaultConfig = {}
settings = {}
memory = {}

global response
global request

response = cherrypy.response
request = cherrypy.request

##################
# Setup function #
##################
class serviceMode(object):
    server = "local"
    application = "application"
    GAE = "gae"

class serverInterface(object):
    @staticmethod
    def standalone(*largs, **kwargs):
        print "Yotsuba 3 / Tori Web Framework"
        print "Mode:\tWSGI server"
        if 'config' not in kwargs:
            print "Init:\tStatic Routing from the configuration file"
            kwargs['config'] = staticRouting
        print "Server:\tRunning"
        cherrypy.quickstart(*largs, **kwargs)
        print
        print "Server:\tStop"
    
    @staticmethod
    def application(*largs, **kwargs):
        '''
        Run as a WSGI application
        '''
        cherrypy.config.update({
            'environment': 'embedded'
        })
        application = cherrypy.Application(*largs, **kwargs)
        application.merge(staticRouting)
        return application
    
    @staticmethod
    def auto(*largs, **kwargs):
        '''
        Run in auto mode. This is vary, depending on the configuration.
        '''
        application = None
        if mode in [serviceMode.application, serviceMode.GAE]:
            application = serverInterface.application(*largs, **kwargs)
            if mode == serviceMode.GAE:
                handlers.CGIHandler().run(application)
        else:
            serverInterface.standalone(*largs, **kwargs)
        return application

def setup(setupFilename, enableDebuggingMode = False, additionalConfig = None):
    """
    Set up the environment
    """
    
    global mode
    global baseURI
    global basePath
    global path
    global errorTemplate
    global staticRouting
    global defaultConfig
    global settings
    global memory
    global debug
    
    # Initialization
    __baseConfigKey = 'tools.static'
    mode = 'local'
    baseURI = ''
    basePath = ''
    path = {}
    errorTemplate = None
    staticRouting = {}
    defaultConfig = {
        'tools.decode.encoding':    'utf-8',
        'tools.encode.encoding':    'utf-8',
        'tools.decode.on':          True,
        'tools.encode.on':          True,
        'tools.gzip.on':            True,
        'log.screen':               False,                          # Disable trackback information
        'error_page.default':       DefaultErrorPage.response       # Use the custom error response from Tori
    }
    settings = {}
    
    # Get the reference to the calling function
    f = sys._getframe(1)
    c = f.f_code
    referenceToCaller = c.co_filename
    
    # Base path
    basePath = os.path.abspath(os.path.dirname(os.path.abspath(referenceToCaller)))
    
    # Get the location of the given the configuration files
    targetDestination = setupFilename
    if not re.search('^/', setupFilename):
        targetDestination = "%s/%s" % (basePath, setupFilename)
    
    try:
        # Load the configuration files
        xmldoc = Kotoba(targetDestination)
    except:
        raise WebFrameworkException("Error while reading configuration from %s" % targetDestination)
    
    try:
        # Get operational mode
        xmlOnMode = xmldoc.get("mode")
        if xmlOnMode.length > 0:
            mode = xmlOnMode.data()
    except:
        raise WebFrameworkException("Error while determining the running mode")
    
    try:
        # Store the basic paths in the memory. Make the directory for the destination if necessary.
        pathIndices = xmldoc.get('basepath *')
        pathIndices = pathIndices.list() # [Legacy] the way to get the list of node in Yotsuba 2
        for pathIndex in pathIndices:
            pathName = pathIndex.name()
            path[pathName] = os.path.join(basePath, pathIndex.data())
            makeDirectoryIfNotExist(path[pathName])
    except:
        raise WebFrameworkException("Error while setting the directories")
    
    try:
        # Get the base URI
        baseURI = xmldoc.get('baseURI').data()
        baseURI = baseURI.strip()
        baseURI = re.sub("^/", "", baseURI)
        baseURI = re.sub("/$", "", baseURI)
        
        staticRouting[baseURI + "/"] = {
            'tools.sessions.on': True,
            'tools.sessions.timeout': 10,
            'tools.sessions.storage_type': 'file',
            'tools.sessions.storage_path': path['session'],
            'tools.staticdir.root':        path['static'],
            'tools.staticfile.root':       path['static']
        }
        
        if mode == serviceMode.GAE:
            del staticRouting[baseURI + "/"]['tools.sessions.storage_type']
            del staticRouting[baseURI + "/"]['tools.sessions.storage_path']
        
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
            
            if __type == 'file' and __ref is not None:
                __cKeyPath += 'name'
                #__ref = os.path.join(path['static'], __ref)
            
            if __type == 'dir':
                makeDirectoryIfNotExist(os.path.join(path['static'], __ref))
            
            staticRouting[baseURI + '/' + __link] = {
                str(__cKeyFlag): True,
                str(__cKeyPath): __ref
            }
    except:
        raise WebFrameworkException("Error while setting up routing")
    
    try:
        # Get application settings
        xmlOnSettings = xmldoc.get("settings option")
        if xmlOnSettings.length > 0:
            for option in xmlOnSettings.list():
                optionData = option.data()
                
                optionDataAsFloatingNumber = base.convertToFloatingNumber(optionData)
                optionDataAsInteger = base.convertToInteger(optionData)
                optionDataAsBoolean = base.convertToBoolean(optionData)
                
                if re.match("^\d+(\.\d+)?$", optionData):
                    if optionDataAsFloatingNumber is not None:
                        # the option data is integer-convertible.
                        optionData = optionDataAsFloatingNumber
                    elif optionDataAsInteger is not None:
                        # the option data is integer-convertible.
                        optionData = optionDataAsInteger
                elif optionDataAsBoolean is not None:
                    # the option data is boolean-convertible.
                    optionData = optionDataAsBoolean
                
                settings[option.attr('name')] = optionData
        if 'debug' in settings:
            debug = settings['debug']
        else:
            debug = True
    except:
        raise WebFrameworkException("Error while reading anonymous settings for this application")
    
    try:
        # Add custom error pages
        if xmldoc.get('errorTemplate').length() > 0:
            errorTemplate = xmldoc.get('errorTemplate').data()
            if xmldoc.get('errorTemplate').eq(0).attr('use') == 'mako':
                pass
            else:
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
from mako.exceptions import html_error_template

def render(source, **kwargs):
    # Local flags
    flag_HTMLMinification = "HTMLMinification"
    
    # Switches
    enable_HTMLMinification = kwargs[flag_HTMLMinification] if flag_HTMLMinification in kwargs else (flag_HTMLMinification in settings and settings[flag_HTMLMinification])
    
    # Local variables
    makoTemplate = None
    makoOptions = {
        'input_encoding':  'utf-8',
        'output_encoding': 'utf-8',
        'encoding_errors': 'replace'
    }
    
    # Default output
    output = ''
    
    # Render with Mako
    if os.path.exists(source):
        makoTemplate = Template(filename = source, **makoOptions)
    elif os.path.exists(os.path.join(path['template'], source)):
        makoLookup = TemplateLookup(directories = [path['template']], **makoOptions)
        makoTemplate = makoLookup.get_template(source)
    else:
        makoTemplate = Template(source, **makoOptions)
    
    try:
        if 'baseURI' in kwargs:
            output = makoTemplate.render(**kwargs)
        else:
            output = makoTemplate.render(baseURI = baseURI, **kwargs)
    except:
        raise Exception(html_error_template().render())
    
    # HTML Minification
    if enable_HTMLMinification and not re.search('<(pre|code)', output):
        output = re.sub("^( |\t)+", " ", output)
        output = re.sub("( |\t)+$", " ", output)
        output = re.sub("\n( |\t)+", ' ', output)
        output = re.sub("\n+", "\n", output)
        output = re.sub("\n", "==========", output)
        output = re.sub("\s+", " ", output)
        output = re.sub("==========", "\n", output)
        output = re.sub("\n/", "/", output)
        output = re.sub(" ?\*/\s+", "*/", output)
        output = re.sub(";\n", ";", output)
        output = re.sub(",\n", ",", output)
        output = re.sub(">\n", ">", output)
        output = re.sub("\)\s+\{\n*", "){", output)
        output = re.sub("\}\n", "}", output)
        output = output.strip()
    
    return output

#############
# Exception #
#############

class WebFrameworkException(Exception):
    pass

####################
# Basic Interfaces #
####################

class BaseInterface(object):
    '''
    Base (Web) interface providing basic functionality for rendering template.
    '''
    memoryBlockName_Cache = 'cache'
    memoryBlockName_CacheExpiration = 'cacheExpiration'
    
    def __init__(self):
        pass
    
    def purgeCache(self, *blockNames):
        if len(blockNames) == 0:
            try:
                del memory[self.memoryBlockName_Cache]
                del memory[self.memoryBlockName_CacheExpiration]
            except:
                return False
            return True
        else:
            for blockName in blockNames:
                try:
                    if blockName in memory[self.memoryBlockName_Cache]:
                        del memory[self.memoryBlockName_Cache][blockName]
                except:
                    return False
            if len(memory.keys()) == 0:
                del memory[self.memoryBlockName_Cache]
                del memory[self.memoryBlockName_CacheExpiration]
            return True
    
    def cache(self, blockName = None, blockData = None, duration = -1):
        '''
        Cache the data.
        
        If *blockName* is not given, it will return the clone of the memory blocks.
        
        If *blockData* is given, the cache data block will be updated.
        
        If *blockName* is given but the data is not available, it will return null pointer.
        
        If *duration* is below 0, the cache memory is kept as long as the server is
        running. If it is more than 0, the cache memory will be purged after the
        cache duration in seconds. If it is 0, it won't cache a thing.
        '''
        autoRefresh = False
        if blockData is not None and self.memoryBlockName_CacheExpiration not in memory:
            #print "Just started"
            autoRefresh = True
        elif self.memoryBlockName_CacheExpiration in memory:
            if 0 < memory[self.memoryBlockName_CacheExpiration] < time():
                #print "Expired"
                autoRefresh = True
            elif memory[self.memoryBlockName_CacheExpiration] == 0:
                #print "No caching"
                return None # No cache
            elif memory[self.memoryBlockName_CacheExpiration] == -1:
                #print "Forever caching"
                pass # forever caching
            else:
                #print "Not expired"
                pass # not expired
        
        if autoRefresh:
            #print "Purge cache"
            self.purgeCache()
        
        if self.memoryBlockName_Cache not in memory:
            #print "Resurrect the cache blocks"
            memory[self.memoryBlockName_Cache] = {}
        
        if blockData is not None:
            #print "Write the data [%s]" % blockName
            memory[self.memoryBlockName_Cache][blockName] = blockData
            memory[self.memoryBlockName_CacheExpiration] = duration > 0 and time() + duration or duration
        
        if blockName is None:
            #print "Clone: %s" % ', '.join(memory[self.memoryBlockName_Cache].keys())
            return dict(memory[self.memoryBlockName_Cache])
        
        if blockName in memory[self.memoryBlockName_Cache]:
            #print "Return: %s" % blockName
            return memory[self.memoryBlockName_Cache][blockName]
        
        return None
    
    def method(self):
        return cherrypy.request.method
    
    def isGET(self):
        return self.method() == "GET"
    
    def isPOST(self):
        return self.method() == "POST"
    
    def isDELETE(self):
        return self.method() == "DELETE"
    
    def isPUT(self):
        return self.method() == "PUT"
    
    def isAuth(self):
        '''
        Check if the user is authenticated.
        '''
        return True
    
    def isAdmin(self):
        '''
        Check if the user is an administrator.
        '''
        return True
    
    def render(self, source, **kwargs):
        response.headers['Platform'] = base.getVersion() + " (Tori %s)" % PACKAGE_VERSION
        return render(source, baseURI = baseURI, **kwargs)
    
    def respondStatus(self, code, message = None, breakNow = True):
        if base.isString(message) and len(message) > 0:
            message = None
        if breakNow:
            if message is not None:
                raise cherrypy.HTTPError(code, message)
            else:
                raise cherrypy.HTTPError(code)
        else:
            cherrypy.response.status = code
            if message is not None:
                cherrypy.response.body = [message]
    
    def redirect(self, url, code = None, enableInternalRedirection = False):
        if base.isString(url) and len(url) > 0 and not re.search("^https?://", url):
            if enableInternalRedirection:
                # internal redirect
                raise cherrypy.InternalRedirect(url)
            else:
                # redirect with headers
                code = base.isIntegerNumber(code) and code or 301
                cherrypy.response.status = code
                response.headers['Location'] = url
        elif base.isIntegerNumber(code):
            # external redirect with code
            raise cherrypy.HTTPRedirect(url, code)
        else:
            # external redirect without code
            raise cherrypy.HTTPRedirect(url)

class UserInterface(object):
    TEMPLATE = """<!DOCTYPE html>
        <html>
        <head>
            <title>Yotsuba 3 / Tori</title>
            <meta charset="utf-8"/>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
            <style type="text/css">
            /** Reset default */
            * {
                outline: none;
                margin: 0;
                padding: 0;
                border: none;
            }
            
            body {
                font-family: "Helvetica Neue", "Helvetica", "Arial", sans-serif;
                font-size: 13px;
                color: #444;
            }
            
            h1, h2, h3, h4, h5, h6 {
                font-family: "m-1c-1","m-1c-2", "Helvetica Neue", "Helvetica", "Arial", sans-serif;
            }
            
            li {
                list-style: none;
            }
            
            a {
                color: #215498;
            }
            
            a:hover {
                color: #cc0000;
            }
            
            img {
                vertical-align: middle;
            }
            
            /** Common class */
            .thinText {
                font-weight: 200;
            }
            
            .largeText {
                font-size: 16px;
            }
            
            .hidden {
                display: none;
            }
            
            #container {
                padding: 30px;
            }
            h1 {
                font-size: 16px;
                font-weight: normal;
                color: #666;
            }
            h2 {
                padding: 0 0 40px 0;
            }
            p {
                padding: 0 0 15px 0;
            }
            table {
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ccc;
                -webkit-border-radius: 5px;
            }
            table td {
                vertical-align: top;
            }
            table td.cfn,
            table td.enn {
                width: 230px;
            }
            table td.cbs {
                text-align: right;
            }
            button {
                margin-right: 2px;
                padding: 4px 8px;
                background-color: #ddd;
                color: #000;
            }
            
            #powerby {
                padding-top: 40px !important;
            }
            </style>
        </head>
        <body id="atc">
            <div id="container">
                <h1>Yotsuba 3 / Tori Web Framework</h1>
                <!-- Custom Content -->
                ${response}
                <!-- Custom Content -->
                <p id="powerby">Powered by <a href="http://yotsuba.shiroyuki.com">${version}</a></p>
                <p id="copyright">&copy; <a href="http://shiroyuki.com">Juti Noppornpitak</a></p>
            </div>
        </body>
        </html>"""
    
    @staticmethod
    def response(responseContent):
        substitutions = {
            'version':      base.getVersion(),
            'response':     responseContent
        }
        return render(UserInterface.TEMPLATE, **substitutions)

class DefaultErrorPage(object):
    DEFAULT_TEMPLATE = """
        <style type="text/css">
            #ts { border: 1px solid #ffcc00; background-color: #ffffcc; margin-top: 5px; padding: 10px; border-radius: 10px; border-radius: 10px; -moz-border-radius: 10px; -webkit-border-radius: 10px; }
        </style>
        <h2>HTTP ${code}</h2>
        <p>${msg}</p>
        % if tracingStack is not None:
            <h3>Tracing Stack</h3>
            <div id="ts">
                <pre>${tracingStack}</pre>
            </div>
        % endif
    """
    
    @staticmethod
    def response(status, message, traceback, version):
        """ Error Handler """
        substitutions = {
            'code':         status,
            'msg':          re.sub(" (u|r)?'", " ", re.sub("' ", " ", message)),
            'tracingStack': (debug or mode == serviceMode.server) and cherrypy._cperror.format_exc() or None
        }
        
        responseContent = None
        
        # If the error template is not specified, use the default one.
        if errorTemplate is None:
            responseContent = render(DefaultErrorPage.DEFAULT_TEMPLATE, **substitutions)
            responseContent = UserInterface.response(responseContent)
        else:
            responseContent = render(errorTemplate, **substitutions)
        return responseContent

#############
# Utilities #
#############

def makeDirectoryIfNotExist(destination):
    if not yotsuba.fs.exists(destination) and mode != serviceMode.GAE:
        try:
            yotsuba.fs.mkdir(destination)
        except:
            raise WebFrameworkException("%s not found" % destination)