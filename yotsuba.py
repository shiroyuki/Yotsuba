#!/usr/bin/python
# Yotsuba SDK and Framework
# Version 2.0 (Developmental)
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# License: LGPL

# For testing features
import os, sys, re, dircache
import StringIO
import hashlib, base64
import xml.dom.minidom
import cPickle
import pickle
import cgi, Cookie
import mimetypes, MimeWriter
import email, poplib, imaplib, smtplib

# For experimental features
import thread, threading

PROJECT_TITLE = "Yotsuba"
PROJECT_CODENAME = "Kotoba"
PROJECT_MAJOR_VERSION = 2
PROJECT_MINOR_VERSION = 0
PROJECT_STATUS = "experimental"
PROJECT_VERSION = "%d.%d (%s)" % (PROJECT_MAJOR_VERSION, PROJECT_MINOR_VERSION, PROJECT_STATUS)
PROJECT_SIGNATURE = "%s/%s %s" % (PROJECT_TITLE, PROJECT_CODENAME, PROJECT_VERSION)


# SDK.EC > Default Configuration
DEFAULT_CONTENT_TYPE = 'text/html;charset=UTF-8'
DEFAULT_PATH_TO_SESSION_STORAGE = 'sessions/'

# SDK.FS > Common Definitions
FILE            = 0
DIRECTORY       = 1
LINK            = 2
READ_NORMAL     = 'r'
READ_BINARY     = 'rb'
READ_PICKLE     = 'pickle::read'
WRITE_NORMAL    = 'w'
WRITE_BINARY    = 'wb'
WRITE_PICKLE    = 'pickle::write'

global core
global sdk
global fw
global config
config = {}

def config(source, value = None, force_to_reload = False):
    """
    This function is to update and possibly append
    the configuration of the SDK specifically for
    one session of execution.

    The parameter `source` can be either types `str` (string)
    or `dict` (dictionary). If it is of type string and the
    parameter `value` is set, this function treats the string
    `source` as a key variable. Otherwise, it treats the
    parameter `source` as a filename.

    The parameter `force_to_reload` is optional, used when
    you want to force the function to wipe out the current
    configuration and load the currently submitted one.
    """
    if type(source) == dict:
        config.update(source)
    if type(source) == str:
        if not value:
            # Require XML module
            pass
            #YotsubaSDKPackage.fs.read(source)
        else:
            config[source] = value

class YotsubaCorePackage:
    """
    Yotsuba's Core package is designed to handle any low-level operations (I/O operations etc.) and initialization.
    """
    class fs:
        # Make directory
        def mkdir(self, destpath):
            try:
                os.mkdir(destpath)
                return True
            except:
                return False

        # Check the size of file or directory
        def size(self, destpath):
            size = int(os.stat(destpath)[6])
            return size

        # Friendly Path Identifier
        def abspath(self, destpath, request_relative_path_fixed = False):
            if request_relative_path_fixed:
                if not re.compile('^/').match(destpath):
                    destpath = '/' + destpath
                return os.path.abspath( os.getcwd() + destpath )
            else:
                return os.path.abspath( destpath )

        # Symbol-instance checker
        def checkType(self, destpath):
            if not os.path.exists(destpath):
                return -1
            if os.path.isfile( self.abspath( destpath) ) or (os.path.islink( self.abspath( destpath ) ) and os.path.isfile( self.abspath( destpath) ) ):
                return FILE
            return DIRECTORY

        def exists(self, destpath):
            return    os.access(os.path.abspath(destpath), os.F_OK)

        def readable(self, destpath):
            return    os.access(os.path.abspath(destpath), os.R_OK)

        def writable(self, destpath):
            return    os.access(os.path.abspath(destpath), os.W_OK)

        def executable(self, destpath):
            return    os.access(os.path.abspath(destpath), os.X_OK)

        def isfile(self, destpath):
            return     self.checkType(destpath) == FILE

        def isdir(self, destpath):
            return    self.checkType(destpath) == DIRECTORY

        # Browsing Function
        def browse(self, destpath, request_abspath_shown = False, filter = None, filterToSearch = False):
            # Check if this is a directory
            if not self.isdir( self.abspath( destpath ) ) or not self.readable( self.abspath(destpath) ):
                return None
            # Get the list of items
            dls = os.listdir(destpath)
            # Classify each item
            files = []
            directories = []
            ref = None
            if filter:
                ref = re.compile(filter)
            for item in dls:
                if ref:
                    # if matched not in search mode, filter out.
                    # then, `unmatched` items kept
                    if ref.match(item) and not filterToSearch: continue
                    # if unmatched in search mode, filter out.
                    # then, `matched` items kept
                    if not ref.match(item) and filterToSearch: continue
                if self.isfile( destpath + '/' + item ):
                    if request_abspath_shown:
                        files.append(self.abspath(destpath + '/' + item))
                    else:
                        files.append(item)
                    #end if
                elif self.isdir( destpath + '/' + item ):
                    if request_abspath_shown:
                        directories.append(self.abspath(destpath + '/' + item))
                    else:
                        directories.append(item)
                    #end if
                else:
                    pass
                #end if
            files.sort()
            directories.sort()
            return {'files':files, 'directories':directories}

        # Reading Function
        def read(self, filename = '', mode = READ_NORMAL):
            if filename == '':
                # read stdin by default
                return sys.stdin.read()
            if mode == READ_PICKLE:
                # use pickle for reading
                if not self.size(filename) > 0:
                    return None
                data = cPickle.load(open(filename, 'rb'))
                return data

            # This part does not use pickle.
            if not self.isfile(filename):
                return None
            data = open(filename, mode).read()
            return data

        # Web Data Fetching Function
        def readWeb(self, url):
            try:
                import pycurl
                rp = pycurl.Curl()
                rp.setopt(pycurl.URL, url)
                rp.perform()
                return rp.getinfo(pycurl.HTTP_CODE)
            except:
                return None

        # Writing Function
        def write(self, filename, data, mode = WRITE_NORMAL):
            if mode == WRITE_PICKLE:
                # use pickle for writing
                #if self.exists(filename):
                #    os.unlink(filename)
                try:
                    fp = open(filename, 'wb')
                    cPickle.dump(data, fp)
                    fp.close()
                    return True
                except:
                    return False

            # This part does not use pickle.
            if self.isfile(filename):
                os.unlink(filename)
            try:
                fp = open(filename, mode)
                fp.write(data)
                fp.close()
            except:
                return False
            return True

        # Removal Function
        def remove(self, destpath):
            if self.isdir(destpath):
                os.removedirs(destpath)
                return True
            elif self.isfile(destpath, True):
                os.unlink(destpath)
                return True
            return False

    class log:
        # Local configuration
        maxAllowedLevel = 2
        # Flags
        noticeLevel = 0
        warningLevel = 1
        errorLevel = 2
        codeWatchLevel = 3
        # Storage
        logs = []
        # Indicator
        hasError = False
        
        def report(self, content, level = 0):
            if level == self.errorLevel:
                self.hasError = True
            self.logs.append(self.logObject(content, level))
        def export(self, level = -1, onlyOneLevel = False, toArray = False):
            """
            Export logs as a hash table
            """
            table = []
            for log in self.logs:
                if log.level < level:
                    continue
                textMessage = ''
                if log.level == self.noticeLevel:
                    textMessage = 'Note'
                elif log.level == self.warningLevel:
                    textMessage = 'Warn'
                elif log.level == self.errorLevel:
                    textMessage = 'Error'
                elif log.level == self.codeWatchLevel:
                    textMessage = 'Watch'
                else:
                    textMessage = 'Alert'
                textMessage += ':\t' + log.content
                table.append(textMessage)
            return '\n'.join(table)
        class logObject:
            """
            The object class of log message
            """
            # 0: Notification (Default)
            # 1: Warning
            # 2: Error
            
            content = ''
            level = 0
            time = None
            def __init__(self, content, level = 0):
                self.content = content
                self.level = level

class YotsubaSDKPackage:
    class time:
        """
        This package is the simple version of the time object in Python.
        """
        def getTimeCodeInteger(self, timeObject = None):
            from time import gmtime, strftime
            if not timeObject:
                timeObject = gmtime()
            return int(strftime("%Y%m%d%H%M", timeObject))
        
        def readTimeCode(self, timeCode):
            result = [0, 0, 0, 0, 0]
            try:
                for i in range(5):
                    result[i] = int(timecode/pow(10, 8 - 2*i))
                    result.append(str(result[i]))
                    red_timecode = int(result[i]*pow(10, 8 - 2*i))
                    timecode -= red_timecode
            except:
                core.log.report('[sdk.time.readTimeCode] there was an error occurred during parsing the time code.', core.log.errorLevel)
            return result
    
    

    class crypt:
        cryptographicDepthLevel = 10
        
        def serialise(self, dataObject):
            return cPickle.dumps(dataObject, pickle.HIGHEST_PROTOCOL)
        
        def revertSerialise(self, serialisedData):
            return cPickle.loads(serialisedData)
        
        def hash(self, text, hashPackage = None):
            rstring = ''
            hashdict = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512', 'ripemd160']
            if hashPackage:
                hashdict = hashPackage
            for hashalg in hashdict:
                m = hashlib.new(hashalg)
                m.update(text)
                rstring += m.hexdigest()
            return rstring

        def encrypt(self, text):
            rstring = text
            for loopindex in range(0, self.cryptographicDepthLevel):
                rstring = base64.b64encode(rstring)
            return rstring

        def decrypt(self, text):
            rstring = text
            for loopindex in range(0, self.cryptographicDepthLevel):
                rstring = base64.b64decode(rstring)
            return rstring

    class log:
        """
        yotsuba.sdk.log

        Content intepretation and log-base processing package
        """

        # Add slashes to the given string
        def addslashes(self, string):
            return re.sub("'", "\\'", string)

        # Convert a given context to a wiki-like content.
        # This function uses the same rule that mediawiki uses.
        def convert_to_wiki(self, content):
            raw_lines = re.split('(\r\n|\n|\r)', content)
            lines = []
            result = []
            for line in raw_lines:
                lines.append(re.split('( |<.*>)', line))
                for i in range(0, len(lines[-1])):
                    if re.match('(http|https|ftp|sftp|irc)\://', lines[-1][i]):
                        temp = re.sub('^\.+', '', lines[-1][i])
                        temp = re.sub('\.+$', '', temp)
                        temp_link = '<a href="%s">%s</a>' % (temp, temp)
                        content = re.sub(temp, temp_link, content)
            return content

    class mail:
        defaultMessageSubject = 'Untitled Message'
        re_validEmailAddress = re.compile("[a-z0-9\-\+\_]+(\.[a-z0-9\-\+\_]+)*\@[a-z0-9\-\+\_]+(\.[a-z0-9\-\+\_]+)*(\.[a-z]+)+$")
        connectionNodes = {}
        messages = {}
        
        def validateEmailAddress(self, emailAddr):
            return not self.re_validEmailAddress.match(emailAddr) == None
        
        def addConnection(self, connectionName):
            if self.connectionNodes.has_key(connectionName):
                return False
            # Add a connection node
            self.connectionNodes[connectionName] = None
            return True
        
        def removeConnection(self, connectionName):
            try:
                del self.connectionNodes[connectionName]
                return True
            except:
                return False
        
        def connection(self, connectionName):
            return self.connectionNodes
        
        def addMessage(self, messageName):
            if self.messages.has_key(messageName):
                return False
            # Add a connection node
            self.messages[messageName] = None
            return True
        
        def removeMessage(self, messageName):
            try:
                del self.messages[messageName]
                return True
            except:
                return False
        
        def message(self, messageName):
            return self.messages[messageName]
        
        def send(self, connectionName, messageNames):
            if type(messageName) == dict:
                for messageName in messageNames:
                    # send a message
                    pass
            else:
                # send a message
                pass
            pass
        
        def receive(self, connectionName):
            pass

class YotsubaFWPackage:
    class ec:
        """
        Environment Controller
        """
        
        headers = {
            'Content-Type': DEFAULT_CONTENT_TYPE
        }
        cookies = Cookie.SimpleCookie()
        session = None
        sessionPath = ''
        
        def env(self, keyIndex):
            if os.environ.has_key(keyIndex):
                return os.environ[keyIndex]
            else:
                return None
        
        def header(self, key = None, value = None, selfPrint = False):
            if key:
                try:
                    if value and type(x) == str:
                        self.headers[key] = value
                    return self.headers[key]
                except:
                    core.log.report(
                        "[fw.ec.header] failed to retrieve a value of header %s"\
                        % key,
                        core.log.warningLevel
                    )
            else:
                lines = []
                for k, v in headers.iteritems():
                    lines.append('%s: %s' % (k, v))
                result = '%s\n%s\n\n' % ('\n'.join(lines), self.printCookie())
                if selfPrint:
                    print result
                return result
        # Cookies
        def cookie(self, key, newValue = ''):
            if newValue == '':
                cookies[key] = newValue
            return cookies[key].value
        
        def printCookie(self):
            return cookies.output()
        
        # Sessions
        def session(self, key, newValue = None):
            # Initialization
            localRenewSession = False
            # If the session data is not initialized, then the initialization will
            # be preceeded first by default.
            if not self.session:
                self.session = self.sessionObject()
                core.log.report("[fw.ec.session] Initialized the session information")
                sid = self.cookie('sid')
                locationToLoad = fs.abspath(self.sessionPath + '/' + sid, True)
                if sid and fs.exists(locationToLoad):
                    try:
                        self.session = fs.read(locationToLoad, READ_PICKLE)
                        if self.session:
                            core.log.report("[fw.ex.session] Session '%s' restored" % sid)
                        else:
                            localRenewSession = True
                            core.log.report("[fw.ex.session] Session '%s' failed to be restored" % sid, core.log.warningLevel)
                    except:
                        localRenewSession = True
                        core.log.report("[fw.ex.session] Session '%s' failed to be restored as fs threw exception." % sid, core.log.errorLevel)
                else:
                    sid = hashlib.new(str(time.time())).hexdigest()
                    self.session.id = sid
                self.cookie('sid', sid)
            # Then, load or change the data.
            if not self.session.data.has_key(key) and not newValue:
                core.log.report("[fw.ec.session] No session variable '%s' found" % key, core.log.warningLevel)
            if not newValue == None:
                session.data[key] = newValue
                core.log.report("[fw.ec.session] Session variable '%s' updated" % key)
            # Save only if there is update
            if not newValue == None:
                if self.sessionSave():
                    core.log.report("[fw.ec.session] Session variable '%s' stored" % key)
                    return self.session.data[key]
                else:
                    core.log.report("[fw.ec.session] Session variable '%s' not stored" % key, core.log.warningLevel)
                    return None
            if self.session.data.has_key(key):
                core.log.report("[fw.ec.session] Session variable '%s' accessed" % key)
                return self.session.data[key]
            core.log.report("[fw.ec.session] Session variable '%s' not found" % key)
            return None

        def sessionSave(self):
            # Look for session ID
            if not self.session:
                core.log.report("[fw.ec.sessionSave] The session identifier is invalid.", core.log.errorLevel)
                return False
            # Look for the configuration for the session storage
            if not self.sessionPath == '':
                self.sessionPath = DEFAULT_PATH_TO_SESSION_STORAGE
            # Look for the session storage
            # CASE: Cannot find the session storage.
            if not fs.exists(self.sessionsPath):
                core.log.report("[fw.ec.sessionSave] The session storage does not exist.", core.log.warningLevel)
                if fs.mkdir(self.sessionPath):
                    core.log.report("[fw.ec.sessionSave] The session storage is initialized.")
                    if fs.writable(self.sessionPath):
                        core.log.report("[fw.ec.sessionSave] The session storage is confirmed to be accessible.")
                else:
                    core.log.report("[fw.ec.sessionSave] The creation of the session storage is not permitted.", core.log.errorLevel)
            # CASE: The session storage is found.
            else:
                core.log.report("[fw.ec.sessionSave] Found the session storage")
            # Prepare the path of the session storage for this session
            locationToSave = fs.abspath(self.sessionPath + '/' + self.session.id, True)
            # Locate the existed information of this session
            if not fs.exists(locationToSave):
                core.log.report("[fw.ec.sessionSave] Session ID '%s' does not exists but it will be automatically generated." % self.session.id, core.log.warningLevel)
            # Test writing
            if not fs.writable(locationToSave):
                core.log.report("[fw.ec.sessionSave] Session ID '%s' is not saved as backing up this session is not permitted." % self.session.id, core.log.warningLevel)
                return False
            # Backup
            if not fs.write(locationToSave, self.session.data, WRITE_PICKLE):
                core.log.report("[fw.ec.sessionSave] Session '%s' is not saved as the result of failed backup." % self.session.id, core.log.errorLevel)
                return False
            return True

        class sessionObject:
            id = None
            data = {}
            
            def __init__(self, id):
                self.id = id
                
    class ui:
        """
        User Interface Package
        """
        encoding = 'utf-8'
        tagPrefix = ''
        tags = {}
        
        def __init__(self, tagPrefix = ''):
            self.tagPrefix = tagPrefix
        
        def loadTagLibrary(self, XMLFilename, forceReload = False):
            sdk.xml.read('UITags', XMLFilename, forceReload)
            self.tags = sdk.xml.query('tagLibrary tag', 'UITags')
        
        def tag(self, key, newValue = None):
            if not self.tags.has_key(key) and not newValue == None:
                return ''
            if not newValue == None:
                self.tags[key] = '%s' % newValue
            return self.tags[key]
        
        def translate(self, template):
            if not type(template) == str:
                return ''
            if fs.exists(template):
                template = fs.read(template)
            for tagKey, tagValue in tags:
                re.sub("<%s%s/>" % (self.tagPrefix, tagKey), self.tagValue, template)
            return template
    
    class url:
        """
        URL Creation Package
        """
        minimumLengthOfQueryString = 3
        
        def buildQueryString(self, queryHash = None):
            if not queryHash:
                return ''
            if len(queryHash.keys()) <= 0:
                return ''
            resultString = []
            for queryKey, queryValue in queryHash:
                if queryKey == '' or queryValue == '':
                    core.log.report('Empty query key or value is used in fw.url.buildQieryString', core.log.warningLevel)
                    continue
                resultString.append('%s=%s' % (queryKey, queryValue))
            return '&'.join(resultString)
        
        def buildURL(self, destination, queryHash = None, port = None):
            queryString = self.buildQueryString(queryHash)
            resultURL = destination
            if not re.match(".+\://.+", destination):
                resultURL += 'http://' + destination
            if port and type(port) == int:
                if re.match("\?", resultURL):
                    resultURLCom = re.split('\?', resultURL, 1)
                    resultURL += '%s:%d?%s' % (resultURLCom[0], port, resultURLCom[1])
                else:
                    resultURL += ':%d' % port
            if queryString and len(queryString) >= self.minimumLengthOfQueryString:
                resultURL += '?%s' % queryString
            return resultURL

class YotsubaCore:
    log = YotsubaCorePackage.log()
    
    testBiggerLock = thread.allocate_lock()
    testLock = thread.allocate_lock()
    enter = []
    exit = []
    x = 0
    
    def multiThreadTest(self):
        self.testBiggerLock.acquire()
        print "Checkpoint 1"
        for i in range(200):
            thread.start_new(self.counter, (i,))
        print "Checkpoint 2"
        self.testBiggerLock.release()
        self.testBiggerLock.acquire()
        print "Checkpoint 3"
        print self.x
        print self.enter
        print self.exit
        print "Checkpoint 4"
        self.testBiggerLock.release()
        
    def counter(self, i):
        print "Run ", i
        self.enter.append(i)
        for j in range(200):
            self.x = i * j
        self.exit.append(i)

class YotsubaSDK:
    crypt = YotsubaSDKPackage.crypt()
    log = YotsubaSDKPackage.log()
    mail = YotsubaSDKPackage.mail()
    time = YotsubaSDKPackage.time()

class YotsubaFW:
    ec = YotsubaFWPackage.ec()

class YotsubaPackageFileSystemInterface:
    # Make directory
    def mkdir(self, destpath):
        try:
            os.mkdir(destpath)
            return True
        except:
            return False

    # Check the size of file or directory
    def size(self, destpath):
        size = int(os.stat(destpath)[6])
        return size

    # Friendly Path Identifier
    def abspath(self, destpath, request_relative_path_fixed = False):
        if request_relative_path_fixed:
            if not re.compile('^/').match(destpath):
                destpath = '/' + destpath
            return os.path.abspath( os.getcwd() + destpath )
        else:
            return os.path.abspath( destpath )

    # Symbol-instance checker
    def checkType(self, destpath):
        if not os.path.exists(destpath):
            return -1
        if os.path.isfile( self.abspath( destpath) ) or (os.path.islink( self.abspath( destpath ) ) and os.path.isfile( self.abspath( destpath) ) ):
            return FILE
        return DIRECTORY

    def exists(self, destpath):
        return    os.access(os.path.abspath(destpath), os.F_OK)

    def readable(self, destpath):
        return    os.access(os.path.abspath(destpath), os.R_OK)

    def writable(self, destpath):
        return    os.access(os.path.abspath(destpath), os.W_OK)

    def executable(self, destpath):
        return    os.access(os.path.abspath(destpath), os.X_OK)

    def isfile(self, destpath):
        return    self.checkType(destpath) == FILE

    def isdir(self, destpath):
        return    self.checkType(destpath) == DIRECTORY

    # Browsing Function
    def browse(self, destpath, request_abspath_shown = False, filter = None, filterToSearch = False):
        # Check if this is a directory
        if not self.isdir( self.abspath( destpath ) ) or not self.readable( self.abspath(destpath) ):
            return None
        # Get the list of items
        dls = os.listdir(destpath)
        # Classify each item
        files = []
        directories = []
        ref = None
        if filter:
            ref = re.compile(filter)
        for item in dls:
            if ref:
                # if matched not in search mode, filter out.
                # then, `unmatched` items kept
                if ref.match(item) and not filterToSearch: continue
                # if unmatched in search mode, filter out.
                # then, `matched` items kept
                if not ref.match(item) and filterToSearch: continue
            if self.isfile( destpath + '/' + item ):
                if request_abspath_shown:
                    files.append(self.abspath(destpath + '/' + item))
                else:
                    files.append(item)
                #end if
            elif self.isdir( destpath + '/' + item ):
                if request_abspath_shown:
                    directories.append(self.abspath(destpath + '/' + item))
                else:
                    directories.append(item)
                #end if
            else:
                pass
            #end if
        files.sort()
        directories.sort()
        return {'files':files, 'directories':directories}

    # Reading Function
    def read(self, filename = '', mode = READ_NORMAL):
        if filename == '':
            # read stdin by default
            return sys.stdin.read()
        if mode == READ_PICKLE:
            # use pickle for reading
            if not self.size(filename) > 0:
                return None
            data = cPickle.load(open(filename, 'rb'))
            return data

        # This part does not use pickle.
        if not self.isfile(filename):
            return None
        data = open(filename, mode).read()
        return data

    # Web Data Fetching Function
    def readWeb(self, url):
        try:
            import pycurl
            rp = pycurl.Curl()
            rp.setopt(pycurl.URL, url)
            rp.perform()
            return rp.getinfo(pycurl.HTTP_CODE)
        except:
            return None

    # Writing Function
    def write(self, filename, data, mode = WRITE_NORMAL):
        if mode == WRITE_PICKLE:
            # use pickle for writing
            #if self.exists(filename):
            #    os.unlink(filename)
            try:
                fp = open(filename, 'wb')
                cPickle.dump(data, fp)
                fp.close()
                return True
            except:
                return False

        # This part does not use pickle.
        if self.isfile(filename):
            os.unlink(filename)
        try:
            fp = open(filename, mode)
            fp.write(data)
            fp.close()
        except:
            return False
        return True

    # Removal Function
    def remove(self, destpath):
        if self.isdir(destpath):
            os.removedirs(destpath)
            return True
        elif self.isfile(destpath):
            os.unlink(destpath)
            return True
        return False

class YotsubaPackageXML:
    rule_descendantCombinator = ' '
    rule_childCombinator = '>'
    rule_adjacentSiblingCombinator = '+'
    rule_generalSiblingCombinator = '~'
    specialRules = [
        rule_childCombinator,
        rule_adjacentSiblingCombinator,
        rule_generalSiblingCombinator
    ]
    trees = {}
    locks = {}
    runningThreads = {}
    exitedThreads = {}
    sharedMemory = {}
    
    def __init__(self):
        """
        This package is a breakthrough of XML parsers in Python using
        basic CSS3-selector method, instead of XPath.
        
        This is a prototype.
        """
        self.locks['referencing'] = thread.allocate_lock()
    
    def read(self, treeName, source):
        """
        Read and parse either a XML-formatted string or a XML document file and
        store for querying.
        """
        tree = None
        treeOrg = None
        core.log.report('sdk.xml.read')
        try:
            if fs.exists(source):
                treeOrg = xml.dom.minidom.parse(source)
            else:
                treeOrg = xml.dom.minidom.parseString(source)
        except:
            core.log.report(
                '[sdk.xml.read] the parameter `source` is neither an existed filename nor a valid XML-formatted string. This original message is:\n\t%s' %
                sys.exc_info()[0],
                core.log.errorLevel
            )
            return False
        try:
            for node in treeOrg.childNodes:
                if not node.nodeType == node.ELEMENT_NODE:
                    continue
                tree = self.buildTreeOnTheFly(node)
                break
            self.trees[treeName] = tree
        except:
            core.log.report(
                '[sdk.xml.read] Tree creation raised errors.\n\t%s' % sys.exc_info()[0],
                core.log.errorLevel
            )
            return False
        del treeOrg
        return True
    
    def query(self, treeName, selector, useMultiThread = False):
        """
        Query for elements according to the supplied combination of CSS-3 selectors.
        """
        # If `treeName` and `selector` are not of type string, returns an empty list.
        if not type(selector) == str or  not type(treeName) == str:
            core.log.report(
                '[sdk.xml.query] unexpected types of treeName and selector',
                core.log.warningLevel
            )
            # return nothing if either no treeName or no selector is not a string
            return self.queriedNodes([])
        else:
            pass
        # If there is no reference to the tree named by `treeName`, return an empty list.
        if type(treeName) == str and not self.trees.has_key(treeName):
            core.log.report(
                '[sdk.xml.query] the required tree "%s" does not exist.' % treeName,
                core.log.warningLevel
            )
            # return nothing if there is not a tree called by treeName
            return self.queriedNodes([])
        else:
            pass
        # Creates a selector reference
        selectorReference = sdk.crypt.hash(selector, ['sha'])
        # Initializes the list of queried nodes
        resultList = []
        self.sharedMemory[selectorReference] = []
        # Gets the reference to the root node
        startupNode = None
        try:
            startupNode = self.trees[treeName]
        except:
            startupNode = treeName
        # Queries cleanup (Clear out the tab character)
        selector = re.sub("\t", " ", selector)
        # Engroups
        queries = re.split("\,", selector)
        # Allocates for a locks
        self.locks[selectorReference] = thread.allocate_lock()
        if useMultiThread:
            self.locks[selectorReference].acquire()
            self.runningThreads[selectorReference] = []
            self.exitedThreads[selectorReference] = []
        
        for query in queries:
            # Multi-threading feature
            if useMultiThread:
                if query in self.runningThreads[selectorReference]:
                    continue
                self.runningThreads[selectorReference].append(query)
                thread.start_new(self.queryWithOneSelector, (selectorReference, startupNode, query, True))
            else:
                self.queryWithOneSelector(selectorReference, startupNode, query, False)
        
        self.locks[selectorReference].acquire()
        resultList = self.sharedMemory[selectorReference]
        self.locks[selectorReference].release()
        
        if useMultiThread:
            self.locks['referencing'].acquire()
            while self.locks[selectorReference].locked():
                pass
            del self.sharedMemory[selectorReference]
            del self.runningThreads[selectorReference]
            del self.exitedThreads[selectorReference]
            del self.locks[selectorReference]
            try:
                self.locks['referencing'].release()
            except:
                print "Removing referencing denied"
        return self.queriedNodes(resultList)
    
    def queryWithOneSelector(self, selectorReference, startupNode, query, useMultiThread = False):
        """
        Query for elements by a single combination of CSS-3 selectors. This is
        not meant to be used directly. Please use query(...) instead.
        """
        # Gets the path
        combination = re.split("\ +", query.strip())
        if len(combination) > 0:
            try:
                self.sharedMemory[selectorReference].extend(
                    self.traverse(startupNode, combination)
                )
                if useMultiThread:
                    self.exitedThreads[selectorReference].append(query)
            except:
                core.log.report(
                    "Shared Memory [%s] not available" % selectorReference,
                    core.log.errorLevel
                )
            if not selectorReference in self.runningThreads and useMultiThread:
                thread.exit()
            if useMultiThread and len(self.runningThreads[selectorReference]) == len(self.exitedThreads[selectorReference]):
                try:
                    self.locks[selectorReference].release()
                except:
                    core.log.report(
                        "Lock [%s] already released" % selectorReference,
                        core.log.errorLevel
                    )
        else:
            core.log.report(
                "No operation [%s]" % selectorReference,
                core.log.errorLevel
            )
    
    def traverse(self, node, selector, selectorLevel = 0, poleNode = None, singleSiblingSearch = False):
        """
        Performs querying at the low level on the tree. This function is
        different from query() that it's querying based on each position.
        The speed complexity is O(n) where n is the number of nodes.
        
        Please notes that this function treats the parameter node as the
        root of a subtree of its origin.
        
        See http://doc.shiroyuki.com/lib/Yotsuba_SDK_XML_Package#def_traverse.28node.2C_selector.2C_selectorLevel.2C_poleNode.2C_singleSiblingSearch.29
        for the description of parameters
        """
        try:
            rule = self.rule_descendantCombinator
            # If there is no selector, return an empty list
            if selectorLevel >= len(selector):
                return []
            if selector[selectorLevel] in self.specialRules:
                selectorLevel += 1
                try:
                    rule = selector[selectorLevel - 1]
                except:
                    core.log.report(
                        '%d:%s\n\t|_ Failed to determine the special rule' % (node.level, node.name()),
                        core.log.warningLevel
                    )
            # If two or more rules are specified consecutively, regards this selector as ill-formatted
            if selector[selectorLevel] in self.specialRules:
                return []
            # Makes the selector object
            s = self.makeSelectorObject(selector[selectorLevel])
            # First, check if the current element is on the path regardless to the attributes and some filtering options
            isTheNodeOnThePath = \
                ( \
                    s.name() == '*' \
                ) or ( \
                    s.name() == '' \
                    and ( \
                        len(s.attr().keys()) > 0 \
                        or len(s.filter()) > 0 \
                    ) \
                ) or ( \
                    s.name() == node.name() \
                )
            # Second, uses attributes to filter out the element that is not qualified.
            # (attrIndex = [EQUALITY_SIGN, [SPECIFIC_VALUE]]
            if isTheNodeOnThePath:
                for attrIndex in s.attr().keys():
                    # Check if the selector requires the element to have this specific attribute `attrIndex`
                    if s.attr(attrIndex)[1] == None:
                        if not node.hasAttr(attrIndex):
                            isTheNodeOnThePath = False
                            break
                    # Check if the selector requires the element to have this attribute `attrIndex` with
                    # the specific value.
                    else:
                        # Annoying check for slipped errors
                        if len(node.attr(attrIndex)) == 0:
                            isTheNodeOnThePath = False
                            break
                        # Then, real check
                        else:
                            # Get the list of the values, separated by tab character or white spaces.
                            s_attrValueList = re.split("(\t| )+", node.attr(attrIndex))
                            # Check the rules are BROKEN
                            if not (s.attr(attrIndex)[0] == '=' and node.attr(attrIndex) == s.attr(attrIndex)[1])\
                               and not (s.attr(attrIndex)[0] == '|=' and re.match("^(%s)-.*" % s.attr(attrIndex)[1], node.attr(attrIndex)))\
                               and not (s.attr(attrIndex)[0] == '*=' and re.match(".*(%s).*" % s.attr(attrIndex)[1], node.attr(attrIndex)))\
                               and not (s.attr(attrIndex)[0] == '~=' and s.attr(attrIndex)[1] in s_attrValueList)\
                               and not (s.attr(attrIndex)[0] == '$=' and s.attr(attrIndex)[1] == s_attrValueList[-1])\
                               and not (s.attr(attrIndex)[0] == '^=' and s.attr(attrIndex)[1] == s_attrValueList[0]):
                                isTheNodeOnThePath = False
                                break
                            # Otherwise this is on the path
                            else:
                                pass
            # Third, check the filters
            if isTheNodeOnThePath:
                for filterOption in s.filter():
                    if filterOption == 'root' and not node.level == 0:
                        isTheNodeOnThePath = False
                        break
                    elif filterOption == 'empty' and (len(node.children) > 0 or node.data()):
                        isTheNodeOnThePath = False
                        break
            # Check if this node is on the selector path but not the destination
            if isTheNodeOnThePath:
                selectorLevel += 1
            # Allocate the memory of the result list
            resultList = []
            # Check the rule
            # Handle a child combinator
            if rule == self.rule_childCombinator:
                if isTheNodeOnThePath and self.isTheEndOfPathReached(selector, selectorLevel):
                    return [node]
                #elif isTheNodeOnThePath and not self.isTheEndOfPathReached(selector, selectorLevel):
                #    for cnode in node.children:
                #        # Adds the child node to the result list
                #        resultList.extend(self.traverse(cnode, selector, selectorLevel))
                #    return resultList
                else:
                    core.log.report(
                        '%d:%s (Limit break, Force-stop)' % (node.level, node.name()),
                        core.log.codeWatchLevel
                    )
                    return []
            # Handle a heirarchy combinator
            elif rule == self.rule_descendantCombinator:
                # If the node is on the path and it is the end of the path
                if isTheNodeOnThePath and self.isTheEndOfPathReached(selector, selectorLevel):
                    # If the last element required on the path is a wild card,
                    # keeps the iterator going to the bottom of the tree.
                    if self.makeSelectorObject(selector[-1]).name() == '*':
                        selectorLevel -= 1
                    else: pass
                    resultList.append(node)
                cnodeIndex = -1
                doSkip = True
                for cnode in node.children:
                    cnodeIndex += 1
                    # This is the last node to be skipped based on the poleNode.
                    if poleNode and poleNode.name() == cnode.name() and poleNode.level == cnode.level:
                        doSkip = False
                        continue
                    # Skips if this node comes before the poleNode.
                    if poleNode and doSkip:
                        continue
                    # If this is the single sibling search, skips the next
                    # sibling until it meets the criteria.
                    if singleSiblingSearch:
                        doSkip = True
                    # Adds the child node to the result list
                    resultList.extend(self.traverse(cnode, selector, selectorLevel))
                return resultList
            # Handles an adjacent sibling combinator (get one next sibling)
            elif rule == self.rule_adjacentSiblingCombinator:
                resultList.extend(
                    self.traverse(node.parent().parent(), selector, selectorLevel, node.parent(), True)
                )
                return resultList
            # Handles a general sibling combinator (get all next siblings)
            elif rule == self.rule_generalSiblingCombinator:
                resultList.extend(
                    self.traverse(node.parent().parent(), selector, selectorLevel, node.parent())
                )
                return resultList
            # No rule applied
            else:
                return []
        except:
            core.log.report(
                '[sdk.xml.traverse] Unknown errors at %d:%s\n\t%s' % (node.level, node.name(), sys.exc_info()[0]),
                core.log.errorLevel
            )
            raise '[sdk.xml.traverse] Unknown errors at %d:%s\n\t%s' % (node.level, node.name(), sys.exc_info()[0])
            return []
    
    def makeSelectorObject(self, selectorObjectString):
        """
        Makes a selector object with a selector-object string (a tag name with or without attributes).
        Returns a null object if the selectorObjectString is not well-formatted.
        
        A well-formatted selector objects should be in the following patterns.
        - element
        - element[attrName]
        - element[attrName=attrValue]
        - element[attrName^=attrValue]
        - element[attrName$=attrValue]
        - element[attrName~=attrValue]
        - element[attrName*=attrValue]
        - element[attrName|=attrValue]
        - element[attrName1=attrValue1][attrName2=attrValue2]...[attrNameN=attrValueN]
        - element[...]:filter1:filter2:...:filterN
        
        (Source: http://docs.jquery.com/Selectors)
        (Source: http://www.w3.org/TR/css3-selectors/#selectors)
        """
        
        SOName = ''
        SOOptions = ''
        SOAttrs = ''
        SOFilters = ''
        RE_Attr = re.compile(".*\[.*")
        RE_Filter = re.compile(".*:.*")
        if RE_Attr.match(selectorObjectString) and RE_Filter.match(selectorObjectString):
            # Extract the tag name and its options/filters
            SOName, SOOptions = re.split("\[", selectorObjectString, 1)
            # Extract the attribute filters and the selecting filters
            SOAttrs, SOFilters = re.split(":", SOOptions, 1)
        elif RE_Attr.match(selectorObjectString) and not RE_Filter.match(selectorObjectString):
            # Extract the tag name and its options/filters
            SOName, SOOptions = re.split("\[", selectorObjectString, 1)
            # Extract the attribute filters and the selecting filters
            SOAttrs = SOOptions
        elif not RE_Attr.match(selectorObjectString) and RE_Filter.match(selectorObjectString):
            # Extract the tag name and its options/filters
            SOName, SOOptions = re.split(":", selectorObjectString, 1)
            # Extract the attribute filters and the selecting filters
            SOFilters = SOOptions
        else:
            SOName = selectorObjectString
        # Free memory
        del SOOptions
        # Check the requirement
        if (len(SOAttrs) > 0 and not re.match(".+\]$", SOAttrs)) or re.match(".*:$", SOFilters):
            return None
        # Engroup attributes
        SOAttrs = re.split("\]\[", SOAttrs[:-1])
        # Engroup filters
        SOFilters = re.split(":", SOFilters)
        # Prepare to make an object
        SOAttrsRaw = SOAttrs
        SOAttrs = {}
        for SOAttr in SOAttrsRaw:
            if re.match("[a-zA-Z0-9_\-]+=.+", SOAttr):
                k, v = re.split("=", SOAttr, 1)
                SOAttrs[k] = ['=', v]
            elif re.match("[a-zA-Z0-9_\-]+\|=.+", SOAttr):
                k, v = re.split("\|=", SOAttr, 1)
                SOAttrs[k] = ['|=', v]
            elif re.match("[a-zA-Z0-9_\-]+\^=.+", SOAttr):
                k, v = re.split("\^=", SOAttr, 1)
                SOAttrs[k] = ['^=', v]
            elif re.match("[a-zA-Z0-9_\-]+\$=.+", SOAttr):
                k, v = re.split("\$=", SOAttr, 1)
                SOAttrs[k] = ['$=', v]
            elif re.match("[a-zA-Z0-9_\-]+\*=.+", SOAttr):
                k, v = re.split("\*=", SOAttr, 1)
                SOAttrs[k] = ['*=', v]
            elif re.match("[a-zA-Z0-9_\-]+\~=.+", SOAttr):
                k, v = re.split("\~=", SOAttr, 1)
                SOAttrs[k] = ['~=', v]
            elif re.match("[a-zA-Z0-9_\-]+", SOAttr):
                k = SOAttr
                SOAttrs[k] = [None, None]
        if SOName == '' and (len(SOAttrs) == 0 or len(SOFilters) == 0):
            return None
        return self.selectorObject(SOName, SOAttrs, SOFilters)
        
    
    def isTheEndOfPathReached(self, selector, selectorLevel):
        """
        Check if the code walk to the end of the selector.
        This is not meant to be used directly.
        """
        try:
            return selectorLevel >= len(selector) - selector.count('>') - selector.count('+') - selector.count('~')
        except:
            return False
    
    def buildTreeOnTheFly(self, node, parentNode = None, level = 0, levelIndex = 0):
        """
        Construct an XML tree for query.
        This is not meant to be used directly.
        """
        if not node.nodeType == node.ELEMENT_NODE:
            # Ignore non-element node
            return None
        try:
            # Class-node instance of the parameter `node`
            treeNode = self.node(node, parentNode, level, levelIndex)
            if len(node.childNodes) > 0:
                core.log.report('%d:%s > Constructing children' % (level, treeNode.name()), core.log.codeWatchLevel)
                cnodeIndex = -1
                for cnode in node.childNodes:
                    try:
                        cnodeIndex += 1
                        childNode = self.buildTreeOnTheFly(cnode, treeNode, level + 1, cnodeIndex)
                        if childNode == None:
                            continue
                        core.log.report('%d:%s/%s' % (level, treeNode.name(), childNode.name()), core.log.codeWatchLevel)
                        treeNode.children.append(childNode)
                    except:
                        core.log.report(
                            '[sdk.xml.buildTreeOnTheFly] Childen creation failed\n\t%s' % sys.exc_info()[0],
                            core.log.errorLevel
                        )
                        return None
                core.log.report('%d:%s > %d children constructed' % (level, treeNode.name(), len(treeNode.children)), core.log.codeWatchLevel)
            return treeNode
        except:
            core.log.report(
                '[sdk.xml.buildTreeOnTheFly] Node creation failed\n\t%s' % sys.exc_info()[0],
                core.log.errorLevel
            )
            return None
    
    class node:
        level = 0
        element = None
        children = None
        parentElement = None
        hash = None
        
        def __init__(self, element, parent = None, level = 0, levelIndex = 0):
            self.level = level
            self.element = element
            self.children = []
            self.parentElement = parent
            self.hash = hashlib.md5("%s:%s:%s" % (level, levelIndex, element.tagName)).hexdigest()
        
        def parent(self):
            return self.parentElement
        
        def name(self):
            return self.element.tagName
        
        def attr(self, attrName):
            return self.element.getAttribute(attrName)
        
        def hasAttr(self, attrName):
            return self.element.hasAttribute(attrName)
        
        def data(self):
            try:
                if not self.element.hasChildNodes():
                    # Empty node
                    return ''
                resultData = []
                for dataNode in self.element.childNodes:
                    try:
                        if not dataNode.nodeType in (dataNode.TEXT_NODE, dataNode.CDATA_SECTION_NODE):
                            # Ignore non-data node
                            del resultData
                            return ''
                        resultData.append(dataNode.data)
                    except:
                        # Malform XML document
                        del resultData
                        return ''
                return '\n'.join(resultData)
            except:
                return ''
        
        def child(self, indexNumber = 0):
            try:
                return self.children[indexNumber]
            except:
                return []
    
    class queriedNodes:
        elements = None
        
        def __init__(self, elements):
            self.elements = []
            for element in elements:
                if element in self.elements:
                    continue
                self.elements.append(element)
        
        def eq(self, indexNumber = 0):
            try:
                return self.elements[indexNumber]
            except:
                return None
        
        def data(self):
            output = []
            for element in self.elements:
                output.append(element.data())
            return ''.join(output)
        
        def length(self):
            return len(self.elements)
    class selectorObject:
        SOName = None
        SOAttrs = None
        SOFilters = None
        
        def __init__(self, name, attrs = {}, filters = []):
            self.SOName = name
            if type(attrs) == dict:
                self.SOAttrs = attrs
            else:
                self.SOAttrs = {}
            if type(filters) == list:
                self.SOFilters = filters
            else:
                self.SOFilters = []
        
        def name(self):
            return self.SOName
        
        def attr(self, attrName = None):
            if not attrName:
                return self.SOAttrs
            try:
                return self.SOAttrs[attrName]
            except:
                return [None, '']
        
        def filter(self):
            return self.SOFilters

class MailerObject:
    _server = None
    _port = None
    _SSLEnabled = False
    _username = None
    _password = None
    
    def __init__(self, server, port = None, SSLEnabled = False):
        self.server(server)
        self.port(port)
        self.enableSSL(SSLEnabled)
    
    def server(self, server = None):
        if server is not None:
            self._server = server
        return self._server
    
    def port(self, port = None):
        if port is not None:
            self._port = port
        return self._port
    
    def SSLEnabled(self, enable = None):
        if enable is not None:
            self._SSLEnabled = enable
        return self._SSLEnabled
    
    def username(self, username = None):
        if username is not None:
            self._username = username
        return self._username
    
    def password(self, password = None):
        if password is not None:
            self._password = password
        return self._password
    
    def connect(self, username = None, password = None):
        if username is not None:
            self.username(username)
        if password is not None:
            self.password(password)

class MailSender(MailerObject):
    sender = None
    _from = None
    _to = None
    _cc = None
    _bcc = None
    
    def __init__(self, server, port = None, SSLEnabled = False):
        MailerObject.__init__(self, server, port, SSLEnabled)
        self.useSMTP()
    
    def useSMTP(self):
        if self.port() is None and not self.SSLEnabled():
            self.port(poplib.POP3_PORT)
        elif self.port() is None and self.SSLEnabled():
            self.port(poplib.POP3_SSL_PORT)
        if self.SSLEnabled():
            self.sender = smtplib.SMTP_SSL(self.server(), self.port())
        else:
            self.sender = smtplib.SMTP(self.server(), self.port())
    
    def connect(self, username = None, password = None):
        MailerObject.connect(username, password)
        try:
            self.sender.login(self.username(), self.password())
            return True
        except:
            return False
    
    def send(self):
        pass
    
    def disconnect(self):
        try:
            self.sender.quit()
            return True
        except:
            return False

class MailReceiver(MailerObject):
    receiver = None
    isIMAP = False
    
    def usePOP(self):
        if self.port() is None and not self.SSLEnabled():
            self.port(poplib.POP3_PORT)
        elif self.port() is None and self.SSLEnabled():
            self.port(poplib.POP3_SSL_PORT)
        
        if self.SSLEnabled():
            self.receiver = poplib.POP3_SSL(self.server(), self.port())
        else:
            self.receiver = poplib.POP3(self.server(), self.port())
        self.isIMAP = False
    
    def useIMAP(self):
        if self.port() is None and not self.SSLEnabled():
            self.port(imaplib.IMAP4_PORT)
        elif self.port() is None and self.SSLEnabled():
            self.port(imaplib.IMAP4_SSL_PORT)
        
        if self.SSLEnabled():
            self.receiver = imaplib.IMAP4_SSL(self.server(), self.port())
        else:
            self.receiver = imaplib.IMAP4(self.server(), self.port())
        self.isIMAP = True
    
    def connect(self, username = None, password = None):
        MailerObject.connect(username, password)
        try:
            if self.isIMAP:
                self.receiver.login(self.username(), self.password())
            else:
                self.receiver.user(self.username())
                self.receiver.pass_(self.password())
        except Exception, e:
            core.log.report(e, core.log.errorLevel)
    
    def disconnect(self):
        try:
            if self.isIMAP:
                self.receiver.logout()
            else:
                self.receiver.quit()
            del self._messages
            self._messages = []
            return True
        except:
            return False
    
    def getNumberOfMessages(self):
        try:
            if self.isIMAP:
                return 0
            else:
                return self.receiver.stat()[0]
        except:
            return -1
    
    def getSizeOfMailbox(self):
        try:
            if self.isIMAP:
                return 0
            else:
                return self.receiver.stat()[1]
        except:
            return -1
    
    def read(self, messageID, numberOfLines = 0):
        message = None
        rmessage = None
        if self.isIMAP:
            # Not currently supported
            return None
        else:
            if numberOfLines < 1:
                rmessage = self.receiver.top(messageID, numberOfLines)
            else:
                rmessage = self.receiver.retr(messageID)
        
        message = MailMessage()
        message.decrypt(message, self.isIMAP)
        
        return message

class MailMessage:
    headers = {}
    
    defaultMessageContentType = 'text/html'
    subject = 'Untitled Message'
    charset = None
    
    locked = False
    
    data = {
        'reponse':  '',
        'subject':  '',
        'OContent': [], # Original Content
        'PContent': [], # Processed Content
        'size':     0
    }
    
    dataBlocks = []
    
    textMessageComponents = []
    
    HTMLMessageComponents = []
    
    files = [] # attachment
    
    def __init__(self):
        pass
    
    def encrypt(self):
        
        ########################################################################
        # Prototype code from http://code.activestate.com/recipes/52243/
        # by Richard Jones
        ########################################################################
        #
        # import sys, smtplib, MimeWriter, base64, StringIO
        # 
        # message = StringIO.StringIO()
        # writer = MimeWriter.MimeWriter(message)
        # writer.addheader('Subject', 'The kitten picture')
        # writer.startmultipartbody('mixed')
        # 
        # # start off with a text/plain part
        # part = writer.nextpart()
        # body = part.startbody('text/plain')
        # body.write('This is a picture of a kitten, enjoy :)')
        # 
        # # now add an image part
        # part = writer.nextpart()
        # part.addheader('Content-Transfer-Encoding', 'base64')
        # body = part.startbody('image/jpeg')
        # base64.encode(open('kitten.jpg', 'rb'), body)
        # 
        # # finish off
        # writer.lastpart()
        # 
        # # send the mail
        # smtp = smtplib.SMTP('smtp.server.address')
        # smtp.sendmail('from@from.address', 'to@to.address', message.getvalue())
        # smtp.quit()
        #
        ########################################################################
        
        # Assumes the message is ready for encryption
        messageBuffer = StringIO.StringIO()
        writer = MimeWriter.MimeWriter(messageBuffer)
        writer.addheader('Subject', self.subject)
        writer.startmultipartbody('mixed');
        
        # Starts with a default-content-type part
        part = writer.nextpart()
        if (len(self.HTMLMessageComponents) > 0):
            body = part.startbody('text/html')
            body.write('\n'.join(self.HTMLMessageComponents))
        else:
            body = part.startbody('text/html')
            body.write('\n'.join(self.HTMLMessageComponents))
        pass
    
    def decrypt(self, messageContent, receivedViaIMAP = False, overridingSubject = True):
        self.locked = True
        if receivedViaIMAP:
            pass
        else: # POP3 Message
            self.data['response'] = messageContent[0]
            self.data['OContent'] = messageContent[1] # Original Message
            self.data['PContent'] = email.message_from_string('\n'.join(messageContent[1])) # Processed Message
            self.data['size'] = int(messageContent[2])
            
            for PContentKey in self.data['PContent'].keys():
                if self.headers.has_key(PContentKey.lower()):
                    self.headers[PContentKey.lower()] += " %s" % value
                else:
                    self.headers[PContentKey.lower()] = "%s" % value
            
            if "subject" in self.headers.keys() and overridingSubject:
                self.subject = self.headers['subject']
            else:
                self.subject = "Untitled Message"
                
            self.charset = "UTF-8"
            
            if self.data['PContent'].is_multipart():
                # Assumes that this is a multipart message.
                for mpart in self.data['PContent'].walk():
                    mpartFilename = mpart.get_filename()
                    mpartMainContentType = mpart.get_content_maintype()
                    mpartSubContentType = mpart.get_content_subtype()
                    # If the content type of this part is in the pattern multipart/*
                    # or message/*, ignores this part.
                    if mpartMainContentType in ['multipart', 'message']:
                        continue
                    
                    self.dataBlocks.append(str(mpart.get_content_type()) + '; filename=' + str(mpart.get_filename()) + '; charset=' + str(mpart.get_content_charset()))
                    
                    if mpartMainContentType in ['text'] and not mpartFilename:
                        localDecodedData = []
                        # Extracts the data of this part
                        if mpartSubContentType in ['plain', 'html']:
                            localDecodedData.append(mpart.get_payload(decode = True))
                            if not self.charset:
                                self.charset = part.get_content_charset()
                        if mpartSubContentType == 'plain':
                            self.textMessageComponents.append(localDecodedData)
                        elif mpartSubContentType == 'html':
                            self.HTMLMessageComponents.append(localDecodedData)
                    
                    elif mpart.get_filename():
                        self.files.append(mpart)
            else:
                localDecodedData = self.data['PContent'].get_payload()
                self.textMessageComponents.append(localDecodedData)
                self.HTMLMessageComponents.append(localDecodedData)
        self.locked = False
    
    def attr(self, key = '', value = ''):
        ableToSave = False
        if key.strip() == 'from':
            ableToSave = not value.strip() == '' and YotsubaSDKPackage.mail.validateEmailAddress(value.strip())
        elif key.strip() == 'to' or key.strip() == 'cc' or key.strip() == 'bcc':
            receivers = value.split(',')
            for receiver in receivers:
                if receiver.strip() == '':
                    continue
                if not YotsubaSDKPackage.mail.validateEmailAddress(receiver.strip()):
                    ableToSave = False
                    break
        elif key.strip() == 'subject':
            ableToSave = not value.strip() == defaultMessageSubject
        else: # body
            ableToSave = not value.strip() == ''
        if ableToSave:
            self.data[key] = value.strip()
        return self.data[key]
    def load(self, filename):
        try:
            return YotsubaSDKPackage.fs.read(filename, self, READ_PICKLE)
        except:
            return None
        
    def save(self, filename):
        try:
            return YotsubaSDKPackage.fs.write(filename, self, WRITE_PICKLE)
        except:
            return False

# [Legacy module structure for Yotsuba 2.0a2]
core = YotsubaCore()
sdk = YotsubaSDK()
fw = YotsubaFW()

# [New Code for Yotsuba 2.0a3]
# File System Interface
fs = YotsubaPackageFileSystemInterface()

# Kotoba: An XML Query Representative
kotoba = YotsubaPackageXML()

if __name__ == '__main__':
    #core.multiThreadTest();
    print PROJECT_SIGNATURE
    