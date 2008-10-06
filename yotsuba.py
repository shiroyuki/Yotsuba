#!/usr/bin/python
# Yotsuba SDK and Framework
# Version 2.0 (Developmental)
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License

import os, sys, re, dircache, pickle, cgi, hashlib, base64, xml.parsers.expat, Cookie, xml.dom.minidom
import xml.etree.ElementTree as ETAPI

# SDK.EC > Default Configuration
DEFAULT_CONTENT_TYPE = 'text/html;charset=UTF-8'
DEFAULT_PATH_TO_SESSION_STORAGE = 'sessions/'

# SDK.FS > Common Definitions
FILE		= 0
DIRECTORY	= 1
LINK		= 2
READ_NORMAL	= 'r'
READ_BINARY	= 'rb'
READ_PICKLE	= 'pickle::read'
WRITE_NORMAL	= 'w'
WRITE_BINARY	= 'wb'
WRITE_PICKLE	= 'pickle::write'

global core
global sdk
global fw
global config
config = {}

class YotsubaUnitTestPackage:
	def __init__(self):
		core.log.report("Begin testing")

class YotsubaCorePackage:
	class base:
		name = 'Yotsuba SDK'
		version = 2.0

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
	class log:
		# Local configuration
		maxAllowedLevel = 2
		# Definitions
		noticeLevel = 0
		warningLevel = 1
		errorLevel = 2
		# Storage
		logs = []
		
		def report(self, content, level = 0):
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
		basic CSS3-selector method, instead of XPath. The rules is based on jQuery API
		
		This function is still based on ElementTree API in order to reduce
		the additional footprint.
		"""
		rule_heirarchy = ' '
		rule_matchNextLevel = '>'
		rule_matchOneNextSibling = '+'
		rule_matchAllNextSiblings = '~'
		files = {}
		
		def test(self, filename):
			print sdk.fs.read('xml-test-1.xml');
		
		def query(self, selector, source):
			# Checks type of both `selector` and `source` (expected: str)
			if not (type(selector) == str and type(source) == str):
				return []
			# Initializes local variables
			resultElements = []
			resultElement = None
			data = ''
			groups = selector.split(",")
			# Prepares data
			if sdk.fs.exists(source) and not self.files.has_key(source):
				data = sdk.fs.read(source)
				self.files[source] = sdk.fs.read(source)
			else:
				data = source
			# Iterates the dom tree
			for group in groups:
				resultElement = self.queryPerGroup(group, data)
				if resultElement and type(resultElement) == list and len(resultElement) > 0:
					resultElement.append(resultElement)
			# Frees memory
			del self.files[source]
			# Returns result
			return resultElement
		
		def queryPerGroup(self, selector, data):
			selector = selector.strip()
			if re.match("^(>|\+|~)", selector) or  re.match("(>|\+|~)$", selector):
				return None
			order = re.split("( |\t)+", selector)
			return self.traverse(order, 0, data)
		
		# Unfinished
		def traverse(self, order, depth, data, rule = None):
			if not rule:
				rule = self.rule_heirarchy
			pass
	
	class xmlPrototype:
		"""
		This package is a breakthrough of XML parsers in Python using
		basic CSS3-selector method, instead of XPath.
		
		This is a prototype.
		"""
		
		trees = {}
		
		def read(self, treeName, source):
			"""
			Read either a string or a file in the XML format and save.
			"""
			tree = None
			treeOrg = None
			try:
				if YotsubaSDKPackage.fs.exists(source):
					treeOrg = xml.dom.minidom.parse(source)
				else:
					treeOrg = xml.dom.minidom.parseString(source)
				tree = self.buildTreeOnTheFly(treeOrg)
				if trees.hasKey(treeName):
					del trees[treeName]
				trees[treeName] = tree
			except:
				core.log.report('[sdk.xml.read] the parameter `source` is neither an existed filename nor a valid XML-formatted string.', core.log.errorLevel)
				return False
			del treeOrg
			return True
		
		def query(self, treeName, selector, useXPath = True):
			if not type(treeName) == str or not type(selector) == str:
				# return nothing if either no treeName or no selector is not a string
				return []
			if not trees.hasKey(treeName):
				# return nothing if there is not a tree called by treeName
				return []
			# Clear out the tab character
			selector = re.sub("\t", " ", selector)
			# Get the path
			selectorList = re.split("\ +", selector.strip())
			if len(selectorList) == 0:
				return []
			selectorPointer = selectorList[0]
			resultList = []
			resultList.extend(traverse(trees[treeName], selectorList))
		
		def traverse(self, node, selector, selectorLevel, includeRootNode = True):
			try:
				resultList = []
				if includeRootNode and node.name() == selector[selectorLevel]:
					selectorLevel += 1
					if len(selector) >= selectorLevel:
						resultList.append(node)
				if selectorLevel >= len(selector) - select.count('>') - select.count('+'):
					return resultList
				for cnode in node.children:
					if cnode.name() == selector[selectorLevel]:
						if len(selector) >= selectorLevel:
							resultList.append(cnode)
						else:
							resultList.extend(self.traverse(cnode, selector, selectorLevel + 1, False))
					resultList.extend(self.traverse(cnode, selector, selectorLevel, False))
				return resultList
			except:
				return []

		def buildTreeOnTheFly(self, rootNode = None, level = 0):
			if not rootNode:
				return None
			if not rootNode.nodeType == rootNode.ELEMENT_NODE:
				# Ignore non-element node
				return None
			treeNode = self.node(rootNode)
			for node in rootNode.childNodes:
				childNode = self.buildTreeOnTheFly(node, level + 1)
				if not childNode:
					# Ignore null-returned node
					continue
				treeNode.children.append(childNode)
			return treeNode

		class node:
			level = 0
			element = None
			children = []

			def __init__(self, element, level = 0):
				self.level = level
				self.element = element

			def name(self):
				return self.element.tagName

			def attr(self, attr = None):
				return self.element.getAttribute(attr)

			def data(self):
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

	class crypt:
		cryptographic_depth_level = 10

		def hash(self, text):
			rstring = ''
			hashdict = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512', 'ripemd160']
			for hashalg in hashdict:
				m = hashlib.new(hashalg)
				m.update(text)
				rstring += m.hexdigest()
			return rstring

		def encrypt(self, text):
			rstring = text
			for loopindex in range(0, self.cryptographic_depth_level):
				rstring = base64.b64encode(rstring)
			return rstring

		def decrypt(self, text):
			rstring = text
			for loopindex in range(0, self.cryptographic_depth_level):
				rstring = base64.b64decode(rstring)
			return rstring

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
			return	os.access(os.path.abspath(destpath), os.F_OK)

		def readable(self, destpath):
			return	os.access(os.path.abspath(destpath), os.R_OK)

		def writable(self, destpath):
			return	os.access(os.path.abspath(destpath), os.W_OK)

		def executable(self, destpath):
			return	os.access(os.path.abspath(destpath), os.X_OK)

		def isfile(self, destpath):
			return 	self.checkType(destpath) == FILE

		def isdir(self, destpath):
			return	self.checkType(destpath) == DIRECTORY

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
				#	os.unlink(filename)
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
				fp = open(filename, mode)
				fp.write(data)
				fp.close()
			else:
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
		DEFAULT_MESSAGE_SUBJECT = 'Untitled Message'
		re_validEmailAddress = re.compile("[a-z0-9\-\+\_]+(\.[a-z0-9\-\+\_]+)*\@[a-z0-9\-\+\_]+(\.[a-z0-9\-\+\_]+)*(\.[a-z]+)+$")

		def validateEmailAddress(self, emailAddr):
			return not self.re_validEmailAddress.match(emailAddr) == None

		class message:
			data = {
				'from':		'',
				'to':		'',
				'cc':		'',
				'bcc':		'',
				'subject':	'',
				'body':		''
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
					ableToSave = not value.strip() == DEFAULT_MESSAGE_SUBJECT
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
					core.log.report("[fw.ec.header] failed to retrieve a value of header %s" % key, core.log.warningLevel)
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
				locationToLoad = sdk.fs.abspath(self.sessionPath + '/' + sid, True)
				if sid and sdk.fs.exists(locationToLoad):
					try:
						self.session = sdk.fs.read(locationToLoad, READ_PICKLE)
						if self.session:
							core.log.report("[fw.ex.session] Session '%s' restored" % sid)
						else:
							localRenewSession = True
							core.log.report("[fw.ex.session] Session '%s' failed to be restored" % sid, core.log.warningLevel)
					except:
						localRenewSession = True
						core.log.report("[fw.ex.session] Session '%s' failed to be restored as sdk.fs threw exception." % sid, core.log.errorLevel)
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
			if not sdk.fs.exists(self.sessionsPath):
				core.log.report("[fw.ec.sessionSave] The session storage does not exist.", core.log.warningLevel)
				if sdk.fs.mkdir(self.sessionPath):
					core.log.report("[fw.ec.sessionSave] The session storage is initialized.")
					if sdk.fs.writable(self.sessionPath):
						core.log.report("[fw.ec.sessionSave] The session storage is confirmed to be accessible.")
				else:
					core.log.report("[fw.ec.sessionSave] The creation of the session storage is not permitted.", core.log.errorLevel)
			# CASE: The session storage is found.
			else:
				core.log.report("[fw.ec.sessionSave] Found the session storage")
			# Prepare the path of the session storage for this session
			locationToSave = sdk.fs.abspath(self.sessionPath + '/' + self.session.id, True)
			# Locate the existed information of this session
			if not sdk.fs.exists(locationToSave):
				core.log.report("[fw.ec.sessionSave] Session ID '%s' does not exists but it will be automatically generated." % self.session.id, core.log.warningLevel)
			# Test writing
			if not sdk.fs.writable(locationToSave):
				core.log.report("[fw.ec.sessionSave] Session ID '%s' is not saved as backing up this session is not permitted." % self.session.id, core.log.warningLevel)
				return False
			# Backup
			if not sdk.fs.write(locationToSave, self.session.data, WRITE_PICKLE):
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
		
		def loadTagLibrary(self, XMLFilename):
			self.tags = sdk.xml.query('TagLibrary > Tag', XMLFilename)
		
		def tag(self, key, newValue = None):
			if not self.tags.has_key(key) and not newValue == None:
				return ''
			if not newValue == None:
				self.tags[key] = '%s' % newValue
			return self.tags[key]
		
		def translate(self, template):
			if not type(template) == str:
				return ''
			if sdk.fs.exists(template):
				template = sdk.fs.read(template)
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
	base = YotsubaCorePackage.base()
	log = YotsubaCorePackage.log()

class YotsubaSDK:
	crypt = YotsubaSDKPackage.crypt()
	fs = YotsubaSDKPackage.fs()
	log = YotsubaSDKPackage.log()
	mail = YotsubaSDKPackage.mail()
	time = YotsubaSDKPackage.time()
	xml = YotsubaSDKPackage.xml()

class YotsubaFW:
	ec = YotsubaFWPackage.ec()

core = YotsubaCore()
sdk = YotsubaSDK()
fw = YotsubaFW()