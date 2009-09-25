#!/usr/bin/python
# Yotsuba 2.0 (Stable)
# Project Yotsuba
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# License: GNU Lesser General Public License and MIT License

# For testing features
import os
import sys
import re
import hashlib
import base64
import xml.dom.minidom
import cPickle
import smtplib

# For experimental features
import thread, threading

PROJECT_TITLE = "Yotsuba"
PROJECT_CODENAME = "Kotoba"
PROJECT_MAJOR_VERSION = 2
PROJECT_MINOR_VERSION = 0
PROJECT_STATUS = "stable"
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

class SystemLog:
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
        self.logs.append(self.LogObject(content, level))
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
    class LogObject:
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

class Cryptographer:
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

class FileSystemInterface:
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
        return    os.path.exists(destpath)

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

class XML(object):
    """
    XML parser using CSS3 selector.
    
    Normally, this package is already instantiated upon importing this library.
    However, when the user instantiates an instance of this class, the internal
    term here is "Standalone Mode"
    """
    rule_descendantCombinator = ' '
    rule_childCombinator = '>'
    rule_adjacentSiblingCombinator = '+'
    rule_generalSiblingCombinator = '~'
    specialRules = [
        rule_childCombinator,
        rule_adjacentSiblingCombinator,
        rule_generalSiblingCombinator
    ]
    defaultTreeName = 'defaultTree' # for the standalone mode
    
    def __init__(self):
        """
        This package is a breakthrough of XML parsers in Python using
        basic CSS3-selector method, instead of XPath.
        
        This is a prototype.
        """
        self.locks = {}
        self.locks['referencing'] = thread.allocate_lock()
        self.trees = {}
        self.runningThreads = {}
        self.exitedThreads = {}
        self.sharedMemory = {}
        #self.__type__ = "yotsuba"
    
    def read(self, *params):
        """
        Read and parse either a XML-formatted string or a XML document file and
        store for querying.
        """
        if len(params) == 0:
            raise Exception("Expect at least one parameter, which indicates the source of the document or the XML-formatted string.");
        treeName = self.defaultTreeName
        source = params[-1]
        if len(params) > 1:
            treeName = params[0]
        tree = None
        treeOrg = None
        syslog.report('sdk.xml.read')
        try:
            if type(source) == str:
                if fs.exists(source):
                    treeOrg = xml.dom.minidom.parse(source)
                else:
                    treeOrg = xml.dom.minidom.parseString(source)
            elif type(source) == DOMElement:
                tree = source
            else:
                raise Exception("yotsuba.xml.read: Invalid input")
        except:
            syslog.report(
                '[sdk.xml.read] the parameter `source` is neither an existed filename nor a valid XML-formatted string. This original message is:\n\t%s' %
                sys.exc_info()[0],
                syslog.errorLevel
            )
            return False
        #if True:
        try:
            if tree is None:
                for node in treeOrg.childNodes:
                    if not node.nodeType == node.ELEMENT_NODE:
                        continue
                    tree = self.buildTreeOnTheFly(node)
                    break
            self.trees[treeName] = tree
        except:
            syslog.report(
                '[sdk.xml.read] Tree creation raised errors.\n\t%s' % sys.exc_info()[0],
                syslog.errorLevel
            )
            return False
        del treeOrg
        return tree is not None
    
    def get(self, selector, useMultiThread = False):
        """
        Get elements according to the supplied combination of CSS-3 selectors.
        This method is suitable for the standalone/default mode.
        """
        syslog.report("(Interface) Looking for [%s]" % selector)
        return self.query(self.defaultTreeName, selector, useMultiThread)
    
    def query(self, treeName, selector, useMultiThread = False):
        """
        Query for elements according to the supplied combination of CSS-3
        selectors. This method is suitable if there are multiple trees within
        one instance of XML.
        
        (Note: The goal is to support a value of treeName as an instance of self.node
        and self.queryNodes. The support on self.node is not quite working.)
        """
        # If `treeName` and `selector` are not of type string, returns an empty list.
        if not type(selector) == str:
            syslog.report(
                '[sdk.xml.query] unexpected types of the selector',
                syslog.warningLevel
            )
            # return nothing if either no treeName or no selector is not a string
            return XMLQueriedNodes()
        
        syslog.report("Looking for [%s]" % selector)
        
        if not type(treeName) == str and not type(treeName) == DOMElement and not type(treeName) == XMLQueriedNodes:
            syslog.report(
                '[sdk.xml.query] unexpected types of treeName',
                syslog.warningLevel
            )
            # return nothing if either no treeName or no selector is not a string
            # print "Type of Tree Name:", type(treeName), "::" , str(treeName)
            return XMLQueriedNodes()
        
        # If there is no reference to the tree named by `treeName`, return an empty list.
        if type(treeName) == str and not self.trees.has_key(treeName):
            syslog.report(
                '[sdk.xml.query] the required tree "%s" does not exist.' % treeName,
                syslog.warningLevel
            )
            # return nothing if there is not a tree called by treeName
            return XMLQueriedNodes()
        
        # Creates a selector reference
        selectorReference = crypt.hash(selector, ['sha'])
        # Initializes the list of queried nodes
        resultList = []
        self.sharedMemory[selectorReference] = []
        
        # Gets the reference to the root node
        startupNodes = []
        if type(treeName) == str:
            startupNodes.append(self.trees[treeName])
        elif type(treeName) == DOMElement:
            startupNodes.append(treeName)
        elif type(treeName) == XMLQueriedNodes:
            startupNodes.extend(treeName.list())
        else:
            raise Exception("Failed to determine the list of startup nodes for querying\ntreeName is of type %s" % str(type(treeName)))
        
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
            for startupNode in startupNodes:
                syslog.report("Query for [%s]" % query)
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
        return XMLQueriedNodes(resultList)
    
    def queryWithOneSelector(self, selectorReference, startupNode, query, useMultiThread = False):
        """
        Query for elements by a single combination of CSS-3 selectors. This is
        not meant to be used directly. Please use query(...) instead.
        """
        # Gets the path
        syslog.report("Started querying with one selector [%s]" % query)
        combination = re.split("\ +", query.strip())
        if len(combination) > 0:
            try:
                syslog.report("Extending the shared memory")
                self.sharedMemory[selectorReference].extend(
                    self.traverse(startupNode, combination)
                )
                syslog.report("Extended the shared memory")
                if useMultiThread:
                    self.exitedThreads[selectorReference].append(query)
            except:
                syslog.report(
                    "Shared Memory [%s] not available" % selectorReference,
                    syslog.errorLevel
                )
            if not selectorReference in self.runningThreads and useMultiThread:
                thread.exit()
            if useMultiThread and len(self.runningThreads[selectorReference]) == len(self.exitedThreads[selectorReference]):
                try:
                    self.locks[selectorReference].release()
                except:
                    syslog.report(
                        "Lock [%s] already released" % selectorReference,
                        syslog.errorLevel
                    )
        else:
            syslog.report(
                "No operation [%s]" % selectorReference,
                syslog.errorLevel
            )
        syslog.report("Stopped querying with one selector")
    
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
            syslog.report("Traverse [%d/%s:%d:%s]" % (node.level, node.name(), selectorLevel, ' '.join(selector)))
            rule = self.rule_descendantCombinator
            # If there is no selector, return an empty list
            if selectorLevel >= len(selector):
                syslog.report(
                    '%d:%s\n\t|_ Could not find one (SLV:%d != SLN:"%s")' % (node.level, node.name(), selectorLevel, ' '.join(selector)),
                    syslog.warningLevel
                )
                return []
            if selector[selectorLevel] in self.specialRules:
                selectorLevel += 1
                try:
                    rule = selector[selectorLevel - 1]
                except:
                    syslog.report(
                        '%d:%s\n\t|_ Failed to determine the special rule' % (node.level, node.name()),
                        syslog.warningLevel
                    )
            # If two or more rules are specified consecutively, regards this selector as ill-formatted
            if selector[selectorLevel] in self.specialRules:
                syslog.report("Consecutive hierarchical directive found", syslog.warningLevel)
                return []
            # Makes the selector object
            s = self.makeSelectorObject(selector[selectorLevel])
            # First, check if the current element is on the path regardless to the attributes and some filtering options
            isTheNodeOnThePath = (
                    s.name() == '*'
                ) or (
                    s.name() == ''
                    and (
                        len(s.attr().keys()) > 0
                        or len(s.filter()) > 0
                    )
                ) or (
                    s.name() == node.name()
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
                    syslog.report(
                        '%d:%s (Limit break, Force-stop)' % (node.level, node.name()),
                        syslog.codeWatchLevel
                    )
                    return []
            # Handle a heirarchy combinator
            elif rule == self.rule_descendantCombinator:
                isTheEndOfPathReached = self.isTheEndOfPathReached(selector, selectorLevel)
                # If the node is on the path and it is the end of the path
                if isTheNodeOnThePath and self.isTheEndOfPathReached(selector, selectorLevel):
                    # If the last element required on the path is a wild card,
                    # keeps the iterator going to the bottom of the tree.
                    if self.makeSelectorObject(selector[-1]).name() == '*':
                        selectorLevel -= 1
                    else: pass
                    resultList.append(node)
                else:
                    syslog.report( "ON_PATH_FINALE %s" % str(isTheNodeOnThePath) )
                    syslog.report( "BOTTOM_OF_TREE %s" % str(isTheEndOfPathReached) )
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
                syslog.report("What is this combination?")
                return []
        except:
            syslog.report(
                '[sdk.xml.traverse] Unknown errors at %d:%s\n\t%s' % (node.level, node.name(), sys.exc_info()[0]),
                syslog.errorLevel
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
            treeNode = DOMElement(node, parentNode, level, levelIndex)
            if len(node.childNodes) > 0:
                syslog.report('%d:%s > Constructing children' % (level, treeNode.name()), syslog.codeWatchLevel)
                cnodeIndex = -1
                for cnode in node.childNodes:
                    try:
                        cnodeIndex += 1
                        childNode = self.buildTreeOnTheFly(cnode, treeNode, level + 1, cnodeIndex)
                        if childNode == None:
                            continue
                        syslog.report('%d:%s/%s' % (level, treeNode.name(), childNode.name()), syslog.codeWatchLevel)
                        treeNode.children.append(childNode)
                    except:
                        syslog.report(
                            '[sdk.xml.buildTreeOnTheFly] Childen creation failed\n\t%s' % sys.exc_info()[0],
                            syslog.errorLevel
                        )
                        return None
                syslog.report('%d:%s > %d children constructed' % (level, treeNode.name(), len(treeNode.children)), syslog.codeWatchLevel)
            return treeNode
        except:
            syslog.report(
                '[sdk.xml.buildTreeOnTheFly] Node creation failed\n\t%s' % sys.exc_info()[0],
                syslog.errorLevel
            )
            return None
    
    class selectorObject(object):
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
class DOMElement(object):
    level = 0
    element = None
    parentElement = None
    hash = None
    children = None
    
    def __init__(self, element, parent = None, level = 0, levelIndex = 0):
        self.level = level
        self.element = element
        self.parentElement = parent
        self.hash = hashlib.md5("%s:%s:%s" % (level, levelIndex, element.tagName)).hexdigest()
        self.children = []
    
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
    
    def child(self, indexNumber = None):
        try:
            if indexNumber is None:
                return self.children
            else:
                return self.children[indexNumber]
        except:
            return []
    
    def get(self, selector):
        q = XML()
        q.read(self)
        return q.get(selector)

class XMLQueriedNodes(object):
    elements = None
    
    def __init__(self, elements = []):
        self.elements = []
        for element in elements:
            if element in self.elements:
                continue
            self.elements.append(element)
    
    def eq(self, indexNumber = None):
        try:
            if indexNumber is None:
                return self.elements
            else:
                return self.elements[indexNumber]
        except:
            return None
    
    def list(self):
        return self.elements
    
    def data(self):
        output = []
        for element in self.elements:
            output.append(element.data())
        return ''.join(output)
    
    def get(self, selector):
        q = XML()
        ret = []
        for element in self.elements:
            q.read(element)
            ret.extend(q.get(selector).list())
        return XMLQueriedNodes(ret)
    
    def length(self):
        return len(self.elements)

class Postman(object):
    """
    Mail sender
    """
    __username = None
    __password = None
    __server = None
    __port = None
    __ssl = None
    __packages = None
    __from = None
    
    def __init__(self, yourself, server = 'localhost', port = None, secure = False):
        if yourself is not None:
            self.initialize(yourself, server, port, secure)
    
    def initialize(self, yourself, server = 'localhost', port = None, secure = False):
        self.__from = yourself
        self.__server = server
        if port is None:
            if secure:
                self.__port = 465
            else:
                self.__port = 25
        else:
            self.__port = port
        self.__ssl = secure
        self.__packages = []
    
    def login(self, username, password):
        self.__username = username
        self.__password = password
    
    def addPackage(self, package):
        self.__packages.append(package)
    
    def send(self):
        if self.__from is None:
            return
        postman = smtplib.SMTP(self.__server, self.__port)
        if self.__ssl:
            postman = smtplib.SMTP_SSL(self.__server, self.__port)
        for package in self.__packages:
            postman.sendmail(self.__from, package.destination, package.compile())
        postman.quit()

class MailPackage(object):
    """
    Message Holder
    """
    destination = None
    __headers = None
    __title = None
    __content = None
    __type = None
    
    def __init__(self, to, title, content, type = 'text/plain'):
        self.__headers = {
            'To': to,
            'Content-Type': type
        }
        self.destination = to
        self.__title = title
        self.__content = content
    
    def header(self, key, value = None):
        if value is not None:
            self.__headers[key] = value
        if key in self.__headers:
            return self.__headers[key]
        return ''
    
    def compile(self):
        compiledHeader = []
        for k, v in self.__headers:
            compiledHeader.append("%s: %s" % (k, v))
        return '\r\n'.join(['\r\n'.join(compiledHeader), self.__content])

# [Enabled packages (not thread-safe)]
# File System Interface
fs      = FileSystemInterface()
# System Log
syslog  = SystemLog()
# Kotoba, An XML Query Representative
kotoba  = XML()
# Cryptographer
crypt   = Cryptographer()

if __name__ == '__main__':
    #core.multiThreadTest();
    print PROJECT_SIGNATURE
    
