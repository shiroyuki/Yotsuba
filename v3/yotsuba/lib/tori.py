# -*- coding: utf-8 -*-
'''
**Tori web framework**  is a simple web framework working on the top of CherryPy
3.1+. It is designed to get started with CherryPy without repeating the commonly
used configuration or procedure to run the application.

It is also designed to with deployment in mind where the app starter can be used
as standalone WSGI server, WSGI application (wrapper) or Google App Engine application.
'''

__version__ = 1.0
__scan_only__ = [
    ('response', 'multiple-key dictionary', 'See cherrypy.response for more detail.'),
    ('request', 'multiple-key dictionary', 'See cherrypy.request for more detail.'),
    ('session', 'dict', 'See cherrypy.session for more detail.'),
    'ServiceMode',
    'ServerInterface',
    'setup',
    'start_session',
    'render',
    'minify_content',
    'WebFrameworkException',
    'BaseInterface',
    'RESTInterface'
]

import os
import re
import sys
from mimetypes import guess_type
from time import time
from wsgiref import handlers

import cherrypy

from yotsuba.core import base, fs
from yotsuba.lib.kotoba import Kotoba

try:
    from mako.template import Template
    from mako.lookup import TemplateLookup
    from mako.exceptions import html_error_template
except:
    pass

try:
    from tenjin import Engine, MemoryCacheStorage
    from tenjin.helpers import *
except:
    pass

try:
    from google.appengine.api.memcache import Client as google_cache
except:
    pass

# Global variables
debug = False
settings = {}
memory = {}
template = {
    'use': 'mako', # default is mako
    'mako': {
        'options': {
            'input_encoding':  'utf-8',
            'output_encoding': 'utf-8',
            'encoding_errors': 'replace'
        },
        'engine': None,
        'get': None,
        'cache': {}
    },
    'tenjin': {
        'engine': None
    }
}

response = cherrypy.response
request = cherrypy.request
session = None

log = base.logger.getBasic("Yotsuba/Tori")

##################
# Setup function #
##################

class ServiceMode(object):
    '''
    ServiceMode is just a group of keywords to tell ServerInterface which mode to run.
    
    This class provides only static attributes. You may instantiate but nothing works.
    '''
    __scan_only__ = [
        ('server', 'str', 'Tell the service script to run the application in WSGI server mode (standalone).'),
        ('application', 'str', 'Tell the service script to run the application in WSGI application/wrapper mode with a web server like *Apache* 2.x with *mod_wsgi*).'),
        ('GAE', 'str', 'Tell the service script to run the application in WSGI application/wrapper mode on Google App Engine.')
    ]
    server = "local"
    application = "application"
    GAE = "gae"

class ServerInterface(object):
    '''
    ServerInterface is like a switch to control how you deploy your application.
    
    It supports three modes described in *tori.ServiceMode*.
    '''
    @staticmethod
    def standalone(*largs, **kwargs):
        '''
        Run the application in WSGI server mode (standalone).
        '''
        global base_uri
        global static_routing
        
        print "Yotsuba 3 / Tori Web Framework"
        print "Mode:\tWSGI server"
        
        largs = list(largs)
        
        if len(largs) < 2:
            largs.append(base_uri)
        if 'config' not in kwargs:
            if len(largs) < 3:
                print "Init:\tStatic Routing from the configuration file"
                largs.append(static_routing)
            else:
                largs[2] = static_routing
        else:
            print "Init:\tStatic Routing from the manual configuration"
        print "Server:\tRunning (press [CTRL]+[C] to stop)"
        cherrypy.quickstart(*largs, **kwargs)
        print
        print "Server:\tStop"
    
    @staticmethod
    def application(*largs, **kwargs):
        '''
        Run the application in WSGI application/wrapper mode with a web server
        or on Google App Engine.
        
        To run the application on Google App Engine, it is not recommended to
        use this function directly. Please use *ServerInterface.auto* instead.
        '''
        global base_uri
        global static_routing
        
        largs = list(largs)
        
        if len(largs) < 2:
            largs.append(base_uri)
        if not static_routing:
            raise WebFrameworkException("Configuration is not available.")
        cherrypy.config.update({
            'environment': 'embedded'
        })
        if 'config' in kwargs:
            static_routing = kwargs['config']
            del kwargs['config']
        
        application = cherrypy.Application(*largs, **kwargs)
        application.merge(static_routing)
        return application
    
    @staticmethod
    def auto(*largs, **kwargs):
        '''
        Run in auto mode. This is vary, depending on the configuration.
        '''
        application = None
        if mode in [ServiceMode.application, ServiceMode.GAE]:
            application = ServerInterface.application(*largs, **kwargs)
            if mode == ServiceMode.GAE:
                handlers.CGIHandler().run(application)
        else:
            ServerInterface.standalone(*largs, **kwargs)
        return application

def setup(configuration_filename=None, use_tori_custom_error_page=False, support_unicode=True, enable_compression=False, auto_config=False, additional_config=None):
    """
    Set up the environment
    
    `configuration_filename` is the name of the configuration file in XML. By
    default, it is null and instruct the system to use the default settings.
    
    `use_tori_custome_error_page` is a flag to tell whether the application
    process should use the nicer custom error page. Please note that enabling
    this feature will slightly decrease performance. This is a known issue
    for CherryPy 3.1+.
    
    `support_unicode` is a flag to tell whether the application process should
    support unicode. Please note that enabling this feature will slightly decrease performance.
    
    `enable_compression` is a flag to tell whether the application process
    should compress the output. Please note that enabling this feature will
    decrease performance and possibly mess up JavaScript. This feature is
    disabled by default when the X/HTML document contains **pre** elements.
    Use with caution.
    
    `auto_config` is a flag to tell whether the application process
    should create a configuration file (named by `configuration_filename`)
    automatically if not existed. When the function detect that the configuration
    file doesn't exist, with this flag enabled, it will create the configuration
    file with the default configuration. Then, it will terminated the process.
    This gives the developers an opportunity to config the settings before proceeding.
    
    `additional_config` is a configuration dictionary for CherryPy 3.1+. It is
    for adding some additional configuration directly to CherryPy which is the
    underlying framework. Please note that this will override any configuration
    from the configuration file.
    """
    
    global mode
    global base_uri
    global base_path
    global path
    global error_template
    global static_routing
    global settings
    global template
    global debug
    
    # Initialization
    __base_config_key = 'tools.static'
    mode = 'local'
    port = 8080
    base_uri = ''
    base_path = ''
    path = {}
    error_template = None
    static_routing = {}
    default_config = {
        'global': {
            'server.thread_pool':       10,
            'server.socket_queue_size': 10,
            'server.socket_host':       '0.0.0.0',
            'server.socket_port':       port,
            'tools.decode.encoding':    'utf-8',
            'tools.encode.encoding':    'utf-8',
            'tools.decode.on':          support_unicode,
            'tools.encode.on':          support_unicode,
            'tools.gzip.on':            enable_compression,
            'log.screen':               False                          # Disable trackback information
        }
    }
    
    if use_tori_custom_error_page:
        # Use the custom error response from Tori
        default_config['global']['error_page.default'] = DefaultErrorPage.response
    
    settings = {}
    standard_config = """<?xml version="1.0" encoding="UTF-8"?>
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
    """
    
    # Get the reference to the calling function
    f = sys._getframe(1)
    c = f.f_code
    reference_to_caller = c.co_filename
    
    # Base path
    base_path = os.path.abspath(os.path.dirname(os.path.abspath(reference_to_caller)))
    
    # Get the location of the given the configuration files
    target_destination = configuration_filename
    if not re.search('^/', configuration_filename):
        target_destination = "%s/%s" % (base_path, configuration_filename)
    
    try:
        # Load the configuration files
        xmldoc = Kotoba()
        xmldoc.read(target_destination)
    except:
        if auto_config:
            fs.write(target_destination, standard_config, "w")
            xmldoc = Kotoba(target_destination)
        else:
            raise WebFrameworkException("Error while reading configuration from %s" % target_destination)
    
    try:
        # Get operational mode
        xml_on_mode = xmldoc.get("mode")
        if len(xml_on_mode) > 0:
            mode = xml_on_mode.data()
    except:
        raise WebFrameworkException("Error while determining the running mode")
    
    try:
        # Get operational port. This will be ignored in GAE mode
        xml_on_port = xmldoc.get("port")
        if len(xml_on_port) > 0:
            port = base.convertToInteger(xml_on_port.data())
            default_config['global']['server.socket_port'] = port
    except:
        raise WebFrameworkException("Error while determining the running port")
    
    try:
        # Store the basic paths in the memory. Make the directory for the destination if necessary.
        path_indices = xmldoc.get('base_path *')
        for path_index in path_indices:
            pathName = path_index.name
            path[pathName] = os.path.join(base_path, path_index.data())
            make_directory_if_not_existed(path[pathName])
    except:
        raise WebFrameworkException("Error while setting up the directories")
    
    try:
        # Get application settings
        xml_on_settings = xmldoc.get("settings option")
        if xml_on_settings:
            for option in xml_on_settings:
                option_data = option.data()
                
                option_data_as_floating_number = base.convertToFloatingNumber(option_data)
                option_data_as_integer = base.convertToInteger(option_data)
                option_data_as_boolean = base.convertToBoolean(option_data)
                
                if re.match("^\d+(\.\d+)?$", option_data):
                    if option_data_as_floating_number is not None:
                        # the option data is integer-convertible.
                        option_data = option_data_as_floating_number
                    elif option_data_as_integer is not None:
                        # the option data is integer-convertible.
                        option_data = option_data_as_integer
                elif option_data_as_boolean is not None:
                    # the option data is boolean-convertible.
                    option_data = option_data_as_boolean
                
                settings[option.attrs['name']] = option_data
        
        # Recognized options by framework (with the default value)
        recognized_options = {
            'debug': True,
            'no_cache': True,
            'direct_rendering': True,
            'text_minification': False
        }
        
        for recognized_option, default_option in recognized_options.iteritems():
            if recognized_option not in settings:
                settings[recognized_option] = default_option
        
        if 'debug' in settings:
            debug = settings['debug']
    except:
        raise WebFrameworkException("Error while reading anonymous settings for this application")
    
    try:
        # Get the base URI
        base_uri = xmldoc.get('base_uri').data()
        base_uri = base_uri.strip()
        base_uri = re.sub("^/", "", base_uri)
        base_uri = re.sub("/$", "", base_uri)
        
        static_routing[base_uri + '/'] = {
            'tools.caching.on':             True,
            'tools.caching.cache_class':    cherrypy.lib.caching.MemoryCache,
            'tools.caching.delay':          259200, # 3 days
            'tools.caching.maxobjsize':     26214400, # 25 MB
            'tools.caching.maxsize':        104857600, # 100 MB
            'tools.sessions.on':            True,
            'tools.sessions.timeout':       10,
            'tools.sessions.storage_type':  'file',
            'tools.sessions.storage_path':  path['session']
        }
        
        default_config['global']['tools.staticdir.root'] = path['static']
        default_config['global']['tools.staticfile.root'] = path['static']
        
        if settings['no_cache']:
            doc_root_settings = static_routing[base_uri + '/']
            doc_root_settings['tools.caching.on'] = False
        
        if mode == ServiceMode.GAE:
            doc_root_settings = static_routing[base_uri + '/']
            doc_root_settings['tools.caching.on'] = False
            del doc_root_settings['tools.sessions.storage_type']
            del doc_root_settings['tools.sessions.storage_path']
        
        xmldocOnstatic_routing = xmldoc.get('static_routing file, static_routing dir')
        
        for referenceSetting in xmldocOnstatic_routing:
            __type = referenceSetting.name
            __ref = referenceSetting.attrs['ref']
            __link = referenceSetting.attrs['link']
            __cBaseKey = "%s%s" % (__base_config_key, __type)
            __cKeyFlag = "%s.on" % (__cBaseKey)
            __cKeyPath = "%s.%s" % (__cBaseKey, __type)
            
            if __type == 'file' and __ref is not None:
                __cKeyPath += 'name'
                #__ref = os.path.join(path['static'], __ref)
            
            if __type == 'dir':
                make_directory_if_not_existed(os.path.join(path['static'], __ref))
            
            static_routing[base_uri + '/' + __link] = {
                str(__cKeyFlag): True,
                str(__cKeyPath): __ref
            }
        
        items_in_static = fs.browse(path['static'])
        for item_type in items_in_static:
            for item in items_in_static[item_type]:
                if item[0] == ".": continue
                __type = item_type == "files" and "file" or "dir"
                __ref = item
                __link = item
                
                __route_address = '%s/%s' % (base_uri, __link)
                if __route_address in static_routing:
                    continue
                
                __cBaseKey = "%s%s" % (__base_config_key, __type)
                __cKeyFlag = "%s.on" % (__cBaseKey)
                __cKeyPath = "%s.%s" % (__cBaseKey, __type)
                
                if __type == 'file' and __ref is not None:
                    __cKeyPath += 'name'
                
                if __type == 'dir':
                    make_directory_if_not_existed(os.path.join(path['static'], __ref))
                
                static_routing[__route_address] = {
                    str(__cKeyFlag): True,
                    str(__cKeyPath): __ref
                }
    
    except:
        raise WebFrameworkException("Error while setting up routing")
    
    try:
        # Determine the template system
        xml_on_rendering = xmldoc.get("rendering")
        if xml_on_rendering:
            template['use'] = xml_on_rendering.data()
        else:
            template['use'] = 'mako'
        
        if template['use'] == 'tenjin':
            enable_caching = not settings['no_cache']
            if enable_caching:
                enable_caching = MemoryCacheStorage()
            template['tenjin']['engine'] = Engine(
                path=[path['template']],
                cache = enable_caching
            )
        else:
            template_filesystem_checks = settings['no_cache']
            if mode == ServiceMode.GAE:
                template['mako']['engine'] = TemplateLookup(
                    directories = [path['template']],
                    filesystem_checks=template_filesystem_checks,
                    **template['mako']['options']
                )
            else:
                template['mako']['engine'] = TemplateLookup(
                    directories = [path['template']],
                    module_directory=os.path.join(path['session'], 'cache', 'template'), # disable for GAE apps
                    filesystem_checks=template_filesystem_checks,
                    **template['mako']['options']
                )
            template['mako']['get'] = template['mako']['engine'].get_template
    except:
        raise WebFrameworkException("Error while setting up the template system")
    
    try:
        # Add custom error pages
        xml_on_error_template = xmldoc.get('error_template')
        if xml_on_error_template:
            error_template = xml_on_error_template.data()
            error_template = fs.read(os.path.join(path['template'], error_template))
    except:
        raise WebFrameworkException("Error while setting up a custom error error page.")
    
    
    cherrypy.config.update(default_config)
    
    if additional_config is not None:
        cherrypy.config.update(additional_config)

def start_session():
    '''
    Start session (CherryPy)
    '''
    try:
        global session
        if not session:
            session = cherrypy.session
        return True
    except:
        return False

######################
# Rendering function #
######################

def render(source, **kwargs):
    '''
    This function is to render templates. It is currently support Mako template
    only. It is to support other libraries in the future.
    
    This function *can* have more than *one* parameter. There are *three* optional
    parameters only used by this function which are described below. The *rest* are
    context variables for rendering.
    
    The required parameter *source* is a string indicating the location of the
    template. If the optional parameter *direct_rendering* is false, it will
    attempt to render the *source* directly as if it is a template data.
    
    The optional parameter *direct_rendering* is a boolean acting as a switch to
    enable or disable the behaviour described above. This option may be set
    globally in the configuration file. It is set to 'False' by default.
    
    The optional parameter *text_minification* is a boolean acting as a switch to
    enable or disable auto HTML minification. This option may be set globally in
    the configuration file. Currently, it doesn't fully support JavaScript
    minification. It is set to 'False' by default.
    '''
    global base_uri
    global settings
    global template
    
    # Local flags (optional parameters)
    flag_memory_cache_template = "cache_template"
    flag_text_minification = "text_minification"
    flag_direct_rendering = "direct_rendering"
    
    # Switches
    enable_text_minification = kwargs[flag_text_minification] if flag_text_minification in kwargs else (flag_text_minification in settings and settings[flag_text_minification])
    enable_direct_rendering = kwargs[flag_direct_rendering] if flag_direct_rendering in kwargs else (flag_direct_rendering in settings and settings[flag_direct_rendering])
    
    # Default output
    output = ''
    
    if template['use'] == 'tenjin':
        # Render with Tenjin
        tenjin_engine = None

        if os.path.exists(source):
            path_to_source = os.path.dirname(source)
            source = source[len(path_to_source) + 1:]
            tenjin_engine = Engine(path=[path_to_source])
        elif os.path.exists(os.path.join(path['template'], source)):
            tenjin_engine = template['tenjin']['engine']
        elif not enable_direct_rendering:
            raise cherrypy.HTTPError(500, "Text rendering with Tenjin is not supported at this time.")
        else:
            raise cherrypy.HTTPError(500, "Cannot render the template with Tenjin")
        
        output = tenjin_engine.render(source, kwargs)
    else:
        # Render with Mako
        mako_template = None
        
        if os.path.exists(source):
            mako_template = Template(filename = source, **template['mako']['options'])
        elif os.path.exists(os.path.join(path['template'], source)):
            mako_template = template['mako']['get'](source)
        elif not enable_direct_rendering:
            mako_template = Template(source, **template['mako']['options'])
        else:
            raise cherrypy.HTTPError(500, "Cannot render the template with Mako")
        
        try:
            output = mako_template.render(**kwargs)
        except:
            raise Exception(html_error_template().render())
    
    # HTML Minification
    if enable_text_minification:
        output = minify_content(output, True)
    
    return output

def minify_content(original_code, full_compression=False, force_op=False, file_type=None):
    '''
    Minify content (text data). Work best with HTML and CSS. This function is
    automatically temporarily disabled if HTML tag *pre* or *code* is detected
    unless it is forced to do.
    
    *original_code* is required as a string.
    
    *full_compression* (optional, boolean, default: False). It tells the function
    whether it should forcefully minify everything in details. This is not recommended
    for mixed content.
    
    *force_op* (optional, boolean, default: False) forces the function to minify
    content unless it is false.
    
    *file_type* (optional, string, default: None) indicates the type of target
    content for the better minification.
    
    Returns a string of minified *original_code*.
    '''
    
    global settings
    flag_file_type = "file_type"
    flag_force_op = "force_op"
    
    if not force_op and re.search('<(pre|code)', original_code):
        return original_code
    
    output = original_code
    
    output = re.sub("\n( |\t)+", "\n ", output)
    output = re.sub("\n ?//[^\n]+", "\n ", output)
    
    output = re.sub("( |\t)+$", " ", output)
    output = re.sub("\n( |\t)+", ' ', output)
    output = re.sub("\n+", "\n", output)
    output = re.sub("\n", "==========", output)
    
    output = re.sub("\s+", " ", output)
    
    output = re.sub("==========", "\n", output)
    output = re.sub("\n/", "/", output)
    output = re.sub(";\n", ";", output)
    output = re.sub(",\n", ",", output)
    output = re.sub("\)\s+\{\n*", "){", output)
    output = re.sub(" />", "/>", output)
    output = re.sub("\} \{", "}{", output)
    
    output = re.sub("<!--", "∂", output)
    output = re.sub("-->", "∂", output)
    output = re.sub("∂[^∂]+∂", "", output)
    
    if file_type and file_type == 'text/css':
        output = re.sub("/\*", "∂", output)
        output = re.sub("\*/", "∂", output)
        output = re.sub("∂[^∂]+∂", "", output)
        output = re.sub("\s?\{\s?", "{", output)
        output = re.sub("\s?\}\s?", "}", output)
        output = re.sub("\s?:\s?", ":", output)
        output = re.sub("\s?;\s?", ";", output)
    
    if full_compression:
        output = re.sub("\n+", " ", output)
        
        target_tags = ['html', 'head', 'title', 'style', 'body', 'link', 'meta', 'script', 'div', 'p', 'ul', 'ol', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4']
        for target_tag in target_tags:
            output = re.sub(" <%s" % target_tag, "<%s" % target_tag, output)
            output = re.sub(" ?<%s> ?" % target_tag, "<%s>" % target_tag, output)
            output = re.sub(" ?</%s> ?" % target_tag, "</%s>" % target_tag, output)
    
    if debug:
        log = base.logger.getBasic(name = "tori.minify_content", level=base.logger.level.debugging)
        original_size = len(original_code)
        compressed_size = len(output)
        compressed_level = 100.0 - compressed_size*100.0/original_size
        log.debug("Compression Level: %.2f%%" % compressed_level)
    
    output = re.sub(" +", " ", output)
    
    output = output.strip()
    
    return output

#############
# Exception #
#############

class WebFrameworkException(Exception):
    '''Exception specifically used by Tori during initilization'''
    __scan_only__ = []

####################
# Basic Interfaces #
####################

class MemoryBlock(object):
    '''
    A memory block used by caching mechanism via *BaseInterface*-base interfaces
    '''
    def __init__(self, data, duration):
        if base.isNumber(duration) and duration < 1:
            raise Exception("A memory block needs to stay longer than 1 second.")
        self.__data = data
        self.__registered_time = time()
        self.__duration = duration
    
    def data(self):
        return self.__data
    
    def is_expired(self):
        if self.__duration:
            return time() > self.__registered_time + self.__duration
        else:
            return False
    
    def duration(self):
        return self.__duration
    
    def expiration_time(self):
        if self.__duration:
            return self.__registered_time + self.__duration
        else:
            return None
    
    def registered_time(self):
        return self.__registered_time

class BaseInterface(object):
    '''
    Base interface provides all basic functionalities for developing a web interface
    responsible for processing and responding incoming HTTP requests. Only compatible with CherryPy 3.1+.
    '''
    __class__ = "BaseInterface"
    flag_memory_cache = 'cache'
    
    def __init__(self):
        try:
            mc = google_cache()
            mc.flush_all()
        except: pass
    
    def purge_cache(self, *block_names):
        '''
        Purge cache blocks referenced by *block_names*
        
        Example: self.purge_cache('block_a', 'block_b', ...)
        
        Note that if block names aren't given, it will purge all cache blocks.
        '''
        global memory
        
        if len(block_names) == 0:
            try:
                del memory[self.flag_memory_cache]
            except:
                return False
            return True
        else:
            mref = memory[self.flag_memory_cache] # reference to shared memory
            for block_name in block_names:
                try:
                    if block_name in mref:
                        del mref[block_name]
                except:
                    return False
            
            # remove the memory cache if there is no cache stored
            if len(memory.keys()) == 0:
                del memory[self.flag_memory_cache]
            
            return True
    
    def clean_up_cache(self):
        ''' Purge all expired cache. '''
        global memory
        
        for mb_name, mb_data in memory[self.flag_memory_cache].iteritems():
            try:
                if mb_data.is_expired():
                    del memory[self.flag_memory_cache][mb_name]
            except:
                return False
        
        return True
    
    def cache(self, block_name = None, block_data = None, duration = None):
        '''
        Cache the data.
        
        If *block_name* is not given, it will return the clone of the memory blocks.
        
        If *block_data* is given, the cache data block will be updated.
        
        If *block_name* is given but the data is not available, it will return null pointer.
        
        If *duration* is below 0, the cache memory is kept as long as the server is
        running. If it is more than 0, the cache memory will be purged after the
        cache duration in seconds. If it is 0, it won't cache a thing.
        '''
        global settings
        
        if 'no_cache' in settings and settings['no_cache']:
            return block_data
        
        if base.isNumber(duration):
            if duration < 0:
                duration = None
            elif duration == 0:
                return block_data
        else:
            duration = None
        
        mref = None # reference to shared memory
        mc = None # Memcached client for a GAE app
        try:
            mc = google_cache()
            mref = mc.get(self.flag_memory_cache)
        except:
            pass
        
        global memory
        
        if self.flag_memory_cache not in memory:
            memory[self.flag_memory_cache] = mref and mref or {}
        
        mref = memory[self.flag_memory_cache]
        
        current_time = time()
        
        # If block_name is defined...
        if block_name:
            # If block_name is valid but the memory block is expired, then delete
            # the memory block.
            if block_name in mref and mref[block_name].is_expired():
                log.warn("CB %s is just expired." % block_name)
                del mref[block_name]
            
            # If block_data is defined, set or reset the memory block with
            # the new data (block_data) and return it.
            if block_data:
                mref[block_name] = MemoryBlock(block_data, duration)
                
                # Use Google's Memcached server for a GAE app to store the data
                # in the memory.
                try:
                    mc.set(self.flag_memory_cache, mref)
                except:
                    pass
                
                log.warn("CB %s is updated." % block_name)
                return block_data
        else:
            self.clean_up_cache()
            return dict(memory[self.flag_memory_cache])
        
        # If block_name is defined, block_name is not registered and block_data
        # is not defined, return None.
        return None
    
    def default(self, *path_info):
        '''
        Default routing to the static folder when the URL is not handled by Python.
        '''
        path_info = [path['static']] + list(path_info)
        file_path = os.path.join(*path_info)
        file_src = os.path.join(*path_info[:-1])

        cache_name = u"static:%s" % '/'.join(path_info)

        try:
            if not os.path.exists(file_path):
                file_path = None
                for file_candidate in fs.browse(file_src)['files']:
                    if re.match("%s\.[^\.]+" % path_info[-1], file_candidate):
                        file_path = os.path.join(file_src, file_candidate)
        except:
            self.respond_status(404)
        
        if file_path:
            mtime = os.stat(file_path)[-2]
            
            cache_name += u"/%s" % mtime
            
            if self.cache(cache_name):
                return self.cache(cache_name)
            
            try:
                fp = open(file_path, 'r')
                output = fp.read()
                fp.close()
            except IOError:
                return self.respond_status(403)
            except:
                raise WebFrameworkException("Unknown error")
            
            file_type = guess_type(file_path)
            if file_type:
                file_type = file_type[0]
                response.headers['Content-type'] = file_type
            else:
                file_type = 'text/html'
            
            if file_type in ['text/html', 'text/css', 'text/xml', 'application/javascript']:
                output = minify_content(output, True, file_type=file_type)
            
            self.cache(cache_name, output)
            
            response.headers['Cache-on-server'] = 'enabled'
            
            return output
        
        return self.respond_status(404)
    default.exposed = True
    
    def method(self):
        ''' Return the request method (GET, POST, DELETE, PUT) '''
        return cherrypy.request.method
    
    def isGET(self):
        ''' Check if this request is a GET request. '''
        return self.method() == "GET"
    
    def isPOST(self):
        ''' Check if this request is a POST request. '''
        return self.method() == "POST"
    
    def isDELETE(self):
        ''' Check if this request is a DELETE request. '''
        return self.method() == "DELETE"
    
    def isPUT(self):
        ''' Check if this request is a PUT request. '''
        return self.method() == "PUT"
    
    def isAuth(self):
        ''' Abstract: Check if the user is authenticated. '''
        return True
    
    def isAdmin(self):
        ''' Abstract: Check if the user is an administrator. '''
        return True
    
    def render(self, source, **kwargs):
        '''
        Wrapper method for *tori.BaseInterface.default_render*
        
        Example: self.render('shiroyuki.html', author='juti noppornpitak', direct_rendering=False)
        '''
        return self.default_render(source, **kwargs)
    
    def default_render(self, source, **kwargs):
        '''
        Render template from *source* with kwargs as context variables/options.
        
        For rendering options, please see *tori.render*.
        
        Example: self.default_render('shiroyuki.html', author='juti noppornpitak', direct_rendering=False)
        '''
        response.headers['Platform'] = base.getVersion() + " (Tori %s)" % __version__
        kwargs['base_uri'] = base_uri
        return render(source, **kwargs)
    
    def respond_status(self, code, message = None, break_now = True):
        '''
        Set the response status.
        
        *code* is a HTTP status code in interger.
        
        *message* is a response reason.
        
        *break_now* is a boolean. If *True*, this method will raise CherryPy's
        HTTPError exception. Otherwise, return status.
        '''
        if not base.isString(message) or len(message) == 0:
            message = None
        
        if 300 <= code < 400:
            del cherrypy.response.headers['Content-Type']
        
        if code >= 400 and break_now:
            if message:
                raise cherrypy.HTTPError(code, message)
            else:
                raise cherrypy.HTTPError(code)
        else:
            if message:
                cherrypy.response.status = u"%d %s" % (code, message)
            else:
                cherrypy.response.status = code
        
        return base.convertToUnicode(cherrypy.response.status)
    
    def redirect(self, url, code = None, use_internal_redirection = False):
        '''
        Redirect a URL with CherryPy's HTTPRedirect (exception).
        
        *url* is a string representing URL.
        
        *code* is a HTTP status code in interger.
        
        *use_internal_redirection* is to use CherryPy internal redirection. It
        will use the internal routing settings and won't respond like other kind
        of redirections. (The browser won't be prompted to move to the other address.)
        '''
        if base.isString(url) and url and not re.search("^https?://", url):
            if use_internal_redirection:
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

class RESTInterface(BaseInterface):
    '''
    Abstract class for a RESTful Interface based on *BaseInterface*. Only compatible with CherryPy 3.1+.
    '''
    __class__ = "RESTInterface"
    
    def __init__(self):
        self.throw_all_error = False

    # Medium-level functions that directly handle data by methods.
    def index(self):
        '''
        List resources

        GET ./
        '''
        self.respond_status(405)

    def new(self):
        '''
        Prompt to create a new resource

        GET ./new
        '''
        self.respond_status(405)

    def create(self):
        '''
        Create a new resource

        POST ./
        '''
        self.respond_status(405)

    def edit(self, key):
        '''
        Prompt to update a new resource

        GET ./{key}/edit
        '''
        self.respond_status(405)

    def update(self, key):
        '''
        Update the target resource

        POST ./{key}
        PUT  ./{key}
        '''
        self.respond_status(405)

    def show(self, key):
        '''
        Show the target resource

        GET ./{KEY}
        '''
        self.respond_status(405)

    def destroy(self, key):
        '''
        Delete the target resource

        POST ./{KEY}/delete
        DEL  ./{KEY}
        '''
        self.respond_status(405)

    # Medium-level functions that directly handle data by methods.
    def get(self, *args, **kwargs):
        '''
        Handle GET request
        
        GET ./*
        '''
        output = None
        if args and args[-1] == 'new':
            output = self.new(*args[:-1], **kwargs)
        elif args and args[-1] == 'edit':
            output = self.edit(*args[:-1], **kwargs)
        elif args:
            output = self.show(*args, **kwargs)
        else:
            output = self.index(*args, **kwargs)
        return output
    
    def post(self, *args, **kwargs):
        '''
        Handle POST request
        
        POST ./
        '''
        output = None
        if args and args[-1] == 'update':
            output = self.update(*args, **kwargs)
        elif args and args[-1] == 'delete':
            output = self.destroy(*args, **kwargs)
        else:
            output = self.create(*args, **kwargs)
        return output
    
    def put(self, *args, **kwargs):
        '''
        Handle PUT request
        
        PUT ./*
        '''
        return self.update(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        '''
        Handle DELETE request
        
        DELETE ./*
        '''
        return self.destroy(*args, **kwargs)

    def default(self, *args, **kwargs):
        '''
        Low-level function handling requests based on the method.
        '''
        result = None
        if self.throw_all_error:
            result = self.__default(*args, **kwargs)
        else:
            try:
                result = self.__default(*args, **kwargs)
            except TypeError:
                self.respond_status(400)
        return result
    default.exposed = True
    
    def __default(self, *args, **kwargs):
        '''
        Low-level function handling requests based on the method.
        '''
        result = None
        if self.isPOST():
            result = self.post(*args, **kwargs)
        elif self.isPUT():
            result = self.put(*args, **kwargs)
        elif self.isDELETE():
            result = self.delete(*args, **kwargs)
        else:
            result = self.get(*args, **kwargs)
        return result

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
            
            h1 {
                font-size: 16px;
                font-weight: normal;
                color: #666;
            }
            
            h2 {
                padding: 0 0 40px 0;
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
            
            button {
                border-radius: 5px;
                -moz-border-radius: 5px;
                -webkit-border-radius: 5px;
                -o-transition: all linear 100ms;
                -moz-transition: all linear 100ms;
                -webkit-transition: all linear 100ms;
                background-color: #eee;
                border: 1px solid #ccc;
                padding: 4px 8px;
                color: #000;
            }
            
            button:hover {
                background-color: #215498;
                border: 1px solid #000;
                color: #fff;
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
            
            /** IDs */
            #container {
                padding: 30px;
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
        return minify_content(render(UserInterface.TEMPLATE, direct_rendering=False, **substitutions), True)

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
            'tracingStack': debug and cherrypy._cperror.format_exc() or None
        }
        
        responseContent = None
        
        # If the error template is not specified, use the default one.
        if error_template is None:
            responseContent = render(DefaultErrorPage.DEFAULT_TEMPLATE, direct_rendering=False, **substitutions)
            responseContent = UserInterface.response(responseContent)
        else:
            responseContent = render(error_template, direct_rendering=False, **substitutions)
        return minify_content(responseContent, True)

#############
# Utilities #
#############

def make_directory_if_not_existed(destination):
    if not fs.exists(destination) and mode != ServiceMode.GAE:
        try:
            fs.mkdir(destination)
        except:
            raise WebFrameworkException("%s not found" % destination)
