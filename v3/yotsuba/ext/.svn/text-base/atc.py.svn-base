import math
import cherrypy
from time import time, strftime, localtime
from yotsuba.core import base
from yotsuba.lib import tori

class ActivityTrafficControl(tori.BaseInterface):
    TEMPLATE_DATA = """
        <style type="text/css">
        #menu {
            color: #ccc;
        }
        #menu span {
            color: #999;
        }
        .cfn, .enn {
            width: 230px;
        }
        .cbs {
            text-align: right;
        }
        .cbc, .cbe {
            border-right: 1px solid #ccc;
            padding-right: 10px;
            width: 160px;
        }
        .cbe, .cbn {
            padding-left: 10px;
        }
        </style>
        
        <h2>Activity Traffic Control</h2>
        
        <p id="menu">
            % if secure:
            <a href="./">Dashboard</a> |
            <a href="config">Configuration</a> |
            <a href="environ">WSGI Environment</a> |
            % endif
            <span>Uptime: ${uptime}</span>
        </p>
        
        % if mode == "config":
        
            <h3>Configuration</h3>
            <table cellpadding="5" cellspacing="0" width="100%">
            <tr><td class="cfn">Original Configuration</td><td class="cfv">${original_config}</td></tr>
            % for cfn, cfv in config:
            <tr><td class="cfn">${cfn}</td><td class="cfv">${cfv}</td></tr>
            % endfor
            </table>
        
        % elif mode == "environ":
        
            <h3>WSGI Environment</h3>
            <table cellpadding="5" cellspacing="0" width="100%">
            % for enn, env in environ:
            <tr><td class="enn">${enn}</td><td class="env">${env}</td></tr>
            % endfor
            </table>
        
        % else:
        
            <h3>Cache Data Blocks</h3>
            % if len(cache_blocks) > 0:
                <form action="/atc/webcache" method="post">
                    <input type="hidden" name="_method" value="delete"/>
                    <button type="submit">Clear all cache blocks</button>
                    <label>${total_cache_size}</label>
                </form>
                <table cellpadding="5" cellspacing="0" width="100%">
                    % for cbn, cbs, cbe, cbc in cache_blocks:
                    <tr><td class="cbc">${cbc}</td><td class="cbe">${cbe}</td><td class="cbn">${cbn}</td><td class="cbs">${cbs}</td></tr>
                    % endfor
                </table>
            % endif
        
        % endif
    """
    def __init__(self):
        if "startup_time" not in tori.memory:
            tori.memory["startup_time"] = time()
    
    def index(self):
        if tori.request.wsgi_environ['PATH_INFO'][-1] != "/":
            self.redirect("./")
        else:
            return self.default()
    index.exposed = True
    
    def default(self, *paths):
        mode = len(paths) > 0 and paths[0] or None
        
        # retrieve information (cherrypy configuration)
        config = []
        raw_config = tori.request.config
        key_config = raw_config.keys()
        key_config.sort()
        for key in key_config:
            config.append((key, raw_config[key]))
        original_config = str(tori.static_routing)
        
        # retrieve information (WSGI)
        environ = []
        raw_environ = tori.request.wsgi_environ
        key_environ = raw_environ.keys()
        key_environ.sort()
        for key in key_environ:
            environ.append((key, raw_environ[key]))
        
        # retrieve information (cache blocks)
        cache_blocks = []
        total_cache_size = 0
        raw_cache_blocks = None
        try:
            raw_cache_blocks = self.cache()
            if raw_cache_blocks is None:
                raise
        except:
            raw_cache_blocks = {}
        for cache_block_name, cache_block_data in raw_cache_blocks.iteritems():
            this_size = cache_block_data.data()
            this_expiration = cache_block_data.expiration_time()
            this_cache_time = cache_block_data.registered_time()
            
            total_cache_size += self.getDataSize(this_size)
            
            if this_expiration is not None and this_expiration > 0:
                this_expiration = strftime("%Y.%m.%d %H:%M:%S", localtime(this_expiration))
            elif this_expiration == None:
                this_expiration = "No expiration"
            
            this_cache_time = strftime("%Y.%m.%d %H:%M:%S", localtime(this_cache_time))
            
            cache_blocks.append((cache_block_name, self.getFriendlyDataSize(this_size), this_expiration, this_cache_time))
        
        return tori.UserInterface.response(self.render(
            self.TEMPLATE_DATA,
            secure = tori.debug,
            mode = mode,
            uptime = self.getUptime(),
            config = config,
            original_config = original_config,
            environ = environ,
            cache_blocks = cache_blocks,
            template_cache = template_cache,
            total_cache_size = self.getFriendlyDataSize(total_cache_size, True),
            direct_rendering = False
        ))
    default.exposed = True
    
    def webcache(self, **params):
        if '_method' in params and params['_method'] == "delete":
            self.purge_cache()
            self.redirect('./')
        elif self.isGET():
            self.redirect('./')
        else:
            self.respond_status(405, "Not allowed")
    webcache.exposed = True
    
    def getUptime(self):
        days = 0
        hours = 0
        minutes = 0
        seconds = float(time() - tori.memory["startup_time"])
        
        if seconds >= 60:
            minutes = math.floor(seconds / 60)
            seconds = math.floor(seconds) % 60
        
        if minutes >= 60:
            hours = math.floor(minutes / 60)
            minutes = math.floor(minutes) % 60
        
        if hours >= 24:
            days = math.floor(hours / 60)
            hours = math.floor(hours) % 60
        
        output = []
        
        if days > 0:
            output.append("%d day%s" % (days, days == 1 and '' or 's'))
        
        if hours > 0:
            output.append("%d hour%s" % (hours, hours == 1 and '' or 's'))
        
        if minutes > 0:
            output.append("%d minute%s" % (minutes, minutes == 1 and '' or 's'))
        
        output.append("%d second%s" % (seconds, seconds == 1 and '' or 's'))
        
        return ' '.join(output)
    
    def getDataSize(self, blockData):
        if not base.isString(blockData):
            return 0
        
        return len(blockData)
    
    def getFriendlyDataSize(self, blockData, bypassCheck = False):
        if not bypassCheck and not base.isString(blockData):
            return "unknown"
        
        dataSize = float(base.isString(blockData) and len(blockData) or blockData)
        
        return base.convertToHumanReadableDataUnit(dataSize)