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

mode = ''
baseURI = ''
basePath = ''
path = {}
errorTemplate = None
staticRouting = {}
defaultConfig = {}
settings = {}

##################
# Setup function #
##################

class serverInterface(object):
    @staticmethod
    def standalone(*largs, **kwargs):
        cherrypy.quickstart(*largs, **kwargs)
    
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
        if mode == "application":
            application = serverInterface.application(*largs, **kwargs)
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
    
    # Initialization
    __baseConfigKey = 'tools.static'
    mode = 'local'
    baseURI = ''
    basePath = ''
    path = {}
    errorTemplate = None
    staticRouting = {}
    defaultConfig = {
        'tools.decode.on':      True,
        'tools.encode.on':      True,
        'tools.gzip.on':        True,
        'log.screen':           False,                          # Disable trackback information
        'error_page.default':   DefaultErrorPage.response       # Use the custom error response from Tori
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
        
        # Get operational mode
        xmlOnMode = xmldoc.get("mode")
        if xmlOnMode.length > 0:
            mode = xmlOnMode.data()
        
        # Store the basic paths in the memory. Make the directory for the destination if necessary.
        pathIndices = xmldoc.get('basepath *')
        pathIndices = pathIndices.list() # [Legacy] the way to get the list of node in Yotsuba 2
        for pathIndex in pathIndices:
            pathName = pathIndex.name()
            path[pathName] = os.path.join(basePath, pathIndex.data())
            makeDirectoryIfNotExist(path[pathName])
        
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
            'tools.staticdir.root':        path['static']
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
            
            if __type == 'file' and __ref is not None:
                __cKeyPath += 'name'
            
            staticRouting[baseURI + '/' + __link] = {
                str(__cKeyFlag): True,
                str(__cKeyPath): __ref
            }
        
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
    except:
        raise WebFrameworkException("Error while reading configuration from %s" % targetDestination)
    
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
        return render(source, baseURI = baseURI, **kwargs)
    
    def customResponse(self, code, message = None):
        cherrypy.response.status = code
        if message is not None:
            cherrypy.response.body = [message]
    
    def response(self, code, message = None):
        if base.isString(message) and len(message) > 0:
            raise cherrypy.HTTPError(code, message)
        else:
            raise cherrypy.HTTPError(code)
    
    def redirect(self, url, code = None):
        if base.isIntegerNumber(code):
            raise cherrypy.HTTPRedirect(url, code)
        else:
            raise cherrypy.HTTPRedirect(url)

class UserInterface(object):
    TEMPLATE = """<!doctype html>
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
        <head>
            <title>Tori Web Framework - Project Yotsuba</title>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            <style type="text/css">
                body    { font-family: 'Helvetica', 'Arial'; font-weight: normal; font-size: 16px; margin: 0; padding: 0; min-width: 720px; }
                h1      { font-weight: normal; font-size: 24px; margin: 0; padding: 10px 20px; background-color: #000; color: #99cc00; }
                h2      { font-weight: normal; font-size: 20px; margin: 0; padding: 10px 20px; background-color: #669900; color: #ffffff; }
                h3      { border-top: 3px solid #000; font-weight: bold; margin: 10px 0px; padding: 5px 0; }
                pre     { white-space: pre-wrap; font-size: 12px; padding: 0; margin: 0; }
                table   { margin: 5px 20px; display: block; }
                table.vertical th { color: #999; font-weight: normal; vertical-align: top; text-align: right; width: 200px; padding-top: 5px; padding-left: 10px; padding-right: 10px; padding-bottom: 5px; border-right: 1px solid #ccc; }
                table.vertical td { vertical-align: top; padding-top: 5px; padding-left: 10px; padding-bottom: 5px; }
                #response {margin: 20px;}
                #footer { padding: 30px 20px; color: #999; }
            </style>
        </head>
        <body>
            <h1>Yotsuba Project</h1>
            <h2>Tori Web Framework</h2>
            <div id="response">
            <!-- Custom Content -->
            %(response)s
            <!-- Custom Content -->
            </div>
            <p id="footer">
                &copy; 2009 Juti Noppornpitak (Shiroyuki Studio). All Rights
                Reserved. %(version)s is licensed under LGPL and MIT.
            </p>
        </body>
        </html>"""
    
    @staticmethod
    def response(responseContent):
        substitutions = {
            'version':      base.getVersion(),
            'response':     responseContent
        }
        return UserInterface.TEMPLATE % substitutions

class DefaultErrorPage(object):
    DEFAULT_TEMPLATE = """
        <style type="text/css">
            #ts     { border: 1px solid #ffcc00; background-color: #ffffcc; padding: 10px; border-radius: 10px; -moz-border-radius: 10px; -webkit-border-radius: 10px; }
            
        </style>
        <h3>Response</h3>
        <table cellpadding="0" cellspacing="0" border="0" class="vertical">
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
    """
    
    @staticmethod
    def response(status, message, traceback, version):
        """ Error Handler """
        substitutions = {
            'code':         status,
            'msg':          re.sub(" (u|r)?'", " ", re.sub("' ", " ", message)),
            'tracingStack': cherrypy._cperror.format_exc()
        }
        
        responseContent = None
        
        # If the error template is not specified, use the default one.
        if errorTemplate is None:
            responseContent = DefaultErrorPage.DEFAULT_TEMPLATE % substitutions
            responseContent = UserInterface.response(responseContent)
        else:
            responseContent = render(errorTemplate, **substitutions)
        return responseContent

#############
# Utilities #
#############

def makeDirectoryIfNotExist(destination):
    if not yotsuba.fs.exists(destination):
        try:
            yotsuba.fs.mkdir(destination)
        except:
            raise WebFrameworkException("%s not found" % destination)