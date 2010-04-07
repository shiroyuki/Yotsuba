import math
from time import time, strftime, localtime
from yotsuba3.core import base
from yotsuba3.lib import tori

class ActivityTrafficControl(tori.BaseInterface):
    TEMPLATE_DATA = """
        <style type="text/css">
        #menu {
            color: #ccc;
        }
        #menu span {
            color: #999;
        }
        </style>
        
        <h2>Activity Traffic Control</h2>
        
        % if secure:
        
        <p id="menu"><a href="./">Dashboard</a> | <a href="config">Configuration</a> | <a href="environ">WSGI Environment</a> | <span>Uptime: ${uptime}</span></p>
        
        % endif
        
        % if mode == "config":
        
            <h3>Configuration</h3>
            <table cellpadding="5" cellspacing="0" width="100%">
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
            <p>Expiration: ${cacheExpiration}</p>
            % if len(cacheBlocks) > 0:
                <form action="/atc/webcache" method="post">
                    <input type="hidden" name="_method" value="delete"/>
                    <button type="submit">Delete</button>
                    <label>${totalSize}</label>
                </form>
                <table cellpadding="5" cellspacing="0" width="100%">
                    % for cbn, cbs in cacheBlocks:
                    <tr><td class="cbn">${cbn}</td><td class="cbs">${cbs}</td></tr>
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
        
        config = []
        raw_config = tori.request.config
        key_config = raw_config.keys()
        key_config.sort()
        for key in key_config:
            config.append((key, raw_config[key]))
        
        environ = []
        raw_environ = tori.request.wsgi_environ
        key_environ = raw_environ.keys()
        key_environ.sort()
        for key in key_environ:
            environ.append((key, raw_environ[key]))
        
        cacheBlocks = []
        totalSize = 0
        raw_cacheBlocks = None
        try:
            raw_cacheBlocks = self.cache()
            if raw_cacheBlocks is None:
                raise
        except:
            raw_cacheBlocks = {}
        for sharedMemoryBlockName, sharedMemoryBlockData in raw_cacheBlocks.iteritems():
            totalSize += self.getDataSize(sharedMemoryBlockData)
            cacheBlocks.append((sharedMemoryBlockName, self.getFriendlyDataSize(sharedMemoryBlockData)))
        
        cacheExpiration = self.memoryBlockName_CacheExpiration in tori.memory and tori.memory[self.memoryBlockName_CacheExpiration] or None
        if cacheExpiration is not None and cacheExpiration > 0:
            cacheExpiration = strftime("%Y.%m.%d %H:%M:%S", localtime(tori.memory[self.memoryBlockName_CacheExpiration]))
        elif cacheExpiration is None:
            cacheExpiration = "Caching not initiated"
        elif cacheExpiration == 0:
            cacheExpiration = "Always"
        else:
            cacheExpiration = "No expiration"
        
        return tori.UserInterface.response(self.render(
            self.TEMPLATE_DATA,
            secure = tori.debug,
            mode = mode,
            uptime = self.getUptime(),
            config = config,
            environ = environ,
            cacheBlocks = cacheBlocks,
            cacheExpiration = cacheExpiration,
            totalSize = self.getFriendlyDataSize(totalSize, True)
        ))
    default.exposed = True
    
    def webcache(self, **params):
        if '_method' in params and params['_method'] == "delete":
            self.purgeCache()
            self.redirect('./')
        elif self.isGET():
            self.redirect('./')
        else:
            self.respondStatus(405, "Not allowed")
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
        
        unit = ['B', 'KB', 'MB', 'TB']
        unitPointer = 0
        dataSize = float(base.isString(blockData) and len(blockData) or blockData)
        
        while dataSize >= 1024:
            dataSize /= 1024
            unitPointer += 1
        
        return "%.2f %s" % (dataSize, unit[unitPointer])