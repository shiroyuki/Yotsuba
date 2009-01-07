#!/usr/bin/python
# Yotsuba SDK and Framework
# Version 2.0 (Developmental)
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# License: LGPL

# For testing features
import os, sys, re, dircache, pickle, cgi, hashlib, base64, Cookie, xml.dom.minidom

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
                data = pickle.load(open(filename, 'rb'))
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
                    pickle.dump(data, fp)
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
    
    class xml:
        """
        This package is a breakthrough of XML parsers in Python using
        basic CSS3-selector method, instead of XPath.
        
        This is a prototype.
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
        trees = {}
        locks = {}
        runningThreads = {}
        exitedThreads = {}
        sharedMemory = {}
        
        def __init__(self):
            self.locks['referencing'] = thread.allocate_lock()
        
        def read(self, treeName, source):
            """
            Read either a string or a file in the XML format and save.
            """
            tree = None
            treeOrg = None
            core.log.report('sdk.xml.read')
            try:
                if core.fs.exists(source):
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
        
        def query(self, treeName, selector):
            # If `treeName` and `selector` are not of type string, returns an empty list.
            if not type(selector) == str or  not type(treeName) == str:
                core.log.report(
                    '[sdk.xml.query] unexpected types of treeName and selector',
                    core.log.warningLevel
                )
                # return nothing if either no treeName or no selector is not a string
                return []
            else:
                pass
            # If there is no reference to the tree named by `treeName`, return an empty list.
            if type(treeName) == str and not self.trees.has_key(treeName):
                core.log.report(
                    '[sdk.xml.query] the required tree "%s" does not exist.' % treeName,
                    core.log.warningLevel
                )
                # return nothing if there is not a tree called by treeName
                return []
            else:
                pass
            # Creates a selector reference
            selectorReference = sdk.crypt.hash(selector, ['md5'])
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
            self.locks[selectorReference].acquire()
            self.runningThreads[selectorReference] = []
            self.exitedThreads[selectorReference] = []
            for query in queries:
                # [Locked]
                if query in self.runningThreads[selectorReference]:
                    continue
                self.runningThreads[selectorReference].append(query)
                thread.start_new(self.queryWithOneSelector, (selectorReference, startupNode, query))
            self.locks[selectorReference].acquire()
            resultList = self.sharedMemory[selectorReference]
            self.locks[selectorReference].release()
            self.locks['referencing'].acquire()
            while self.locks[selectorReference].locked():
                pass
            core.log.report(
                "Removed reference [%s]" % selectorReference,
                core.log.warningLevel
            )
            del self.sharedMemory[selectorReference]
            del self.runningThreads[selectorReference]
            del self.exitedThreads[selectorReference]
            del self.locks[selectorReference]
            try:
                self.locks['referencing'].release()
            except:
                print "Removing referencing denied"
            return self.queriedNodes(resultList)
        
        def queryWithOneSelector(self, selectorReference, startupNode, query):
            # Get the path
            combination = re.split("\ +", query.strip())
            if len(combination) > 0:
                try:
                    self.sharedMemory[selectorReference].extend(
                        self.traverse(startupNode, combination)
                    )
                    self.exitedThreads[selectorReference].append(query)
                except:
                    core.log.report(
                        "Shared Memory [%s] not available" % selectorReference,
                        core.log.errorLevel
                    )
                if not selectorReference in self.runningThreads:
                    thread.exit()
                if len(self.runningThreads[selectorReference]) == len(self.exitedThreads[selectorReference]):
                    core.log.report(
                        "Unlocked [%s]" % selectorReference,
                        core.log.warningLevel
                    )
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
            try:
                return selectorLevel >= len(selector) - selector.count('>') - selector.count('+') - selector.count('~')
            except:
                return False
        
        def buildTreeOnTheFly(self, node, parentNode = None, level = 0, levelIndex = 0):
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

    class crypt:
        cryptographicDepthLevel = 10
        
        def serialise(self, dataObject):
            return pickle.dumps(dataObject, pickle.HIGHEST_PROTOCOL)
        
        def revertSerialise(self, serialisedData):
            return pickle.loads(serialisedData)
        
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
        
        def validateEmailAddress(self, emailAddr):
            return not self.re_validEmailAddress.match(emailAddr) == None
        
        def createConnection(self, linkName):
            if self.connectionNodes.has_key(linkName):
                return False
            else:
                self.connectionNodes[linkName] = self.Connection()
                return True
        
        def removeConnection(self, linkName):
            if self.connectionNodes.has_key(linkName):
                del self.connectionNodes[linkName]
                return True
            else:
                return False
        
        def connection(self, linkName):
            self.createConnection(linkName)
            return self.connectionNodes[linkName]
        
        class Conenction:
            defaultOption = {
                "used":     False,
                "server":   None,
                "type":     None,
                "port":     None,
                "secure":   None
            }
            
            options = {
                "in": None,
                "out": None
            }
            
            def __init__(self, enableReceiving = False, enableSending = False):
                if enableReceiving:
                    self.options["in"] = self.defaultOption.copy()
                if enableSending:
                    self.options["out"] = self.defaultOption.copy()
            
            def configure(self, key, newValue = None):
                if self.options.has_key(key):
                    if not newValue == None:
                        options[key] = newValue
                    return options[key]
                return None
            
            def transmit(self, message = None):
                if not message == None:
                    # Sends the message
                    pass
                else:
                    # Receives the messages
                    pass
            
            def connect(self):
                pass
            
            def disconnect(self):
                pass
        
        class Message:
            data = {
                'from':        '',
                'to':        '',
                'cc':        '',
                'bcc':        '',
                'subject':    '',
                'body':        ''
            }

            files = [] # attachment

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

            def save(self, filename):
                try:
                    return YotsubaSDKPackage.fs.write(filename, data, WRITE_PICKLE)
                except:
                    return False

            def send(self):
                if data['from'] == '' or data['to'] == '':
                    return False

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
                locationToLoad = core.fs.abspath(self.sessionPath + '/' + sid, True)
                if sid and core.fs.exists(locationToLoad):
                    try:
                        self.session = core.fs.read(locationToLoad, READ_PICKLE)
                        if self.session:
                            core.log.report("[fw.ex.session] Session '%s' restored" % sid)
                        else:
                            localRenewSession = True
                            core.log.report("[fw.ex.session] Session '%s' failed to be restored" % sid, core.log.warningLevel)
                    except:
                        localRenewSession = True
                        core.log.report("[fw.ex.session] Session '%s' failed to be restored as core.fs threw exception." % sid, core.log.errorLevel)
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
            if not core.fs.exists(self.sessionsPath):
                core.log.report("[fw.ec.sessionSave] The session storage does not exist.", core.log.warningLevel)
                if core.fs.mkdir(self.sessionPath):
                    core.log.report("[fw.ec.sessionSave] The session storage is initialized.")
                    if core.fs.writable(self.sessionPath):
                        core.log.report("[fw.ec.sessionSave] The session storage is confirmed to be accessible.")
                else:
                    core.log.report("[fw.ec.sessionSave] The creation of the session storage is not permitted.", core.log.errorLevel)
            # CASE: The session storage is found.
            else:
                core.log.report("[fw.ec.sessionSave] Found the session storage")
            # Prepare the path of the session storage for this session
            locationToSave = core.fs.abspath(self.sessionPath + '/' + self.session.id, True)
            # Locate the existed information of this session
            if not core.fs.exists(locationToSave):
                core.log.report("[fw.ec.sessionSave] Session ID '%s' does not exists but it will be automatically generated." % self.session.id, core.log.warningLevel)
            # Test writing
            if not core.fs.writable(locationToSave):
                core.log.report("[fw.ec.sessionSave] Session ID '%s' is not saved as backing up this session is not permitted." % self.session.id, core.log.warningLevel)
                return False
            # Backup
            if not core.fs.write(locationToSave, self.session.data, WRITE_PICKLE):
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
            if core.fs.exists(template):
                template = core.fs.read(template)
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
    fs = YotsubaCorePackage.fs()
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
    xml = YotsubaSDKPackage.xml()

class YotsubaFW:
    ec = YotsubaFWPackage.ec()

core = YotsubaCore()
sdk = YotsubaSDK()
fw = YotsubaFW()

if __name__ == '__main__':
    #core.multiThreadTest();
    print PROJECT_SIGNATURE
    