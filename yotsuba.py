#!/usr/bin/python
# Yotsuba SDK and Framework
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License

import os, sys, re, dircache, pickle, cgi, hashlib, base64, xml.parsers.expat

# [+ Common Definitions]
FILE		= 0
DIRECTORY	= 1
LINK		= 2
READ_NORMAL	= 'r'
READ_BINARY	= 'rb'
READ_PICKLE	= 'pickle::read'
WRITE_NORMAL	= 'w'
WRITE_BINARY	= 'wb'
WRITE_PICKLE	= 'pickle::write'

class YotsubaSDKPackage:
	class core:
		name = 'Yotsuba SDK'
		version = 2.0
		
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
		def sym_gettype(self, destpath):
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
			return 	self.sym_gettype(destpath) == FILE
		
		def isdir(self, destpath):
			return	self.sym_gettype(destpath) == DIRECTORY
		
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
		def read_web(self, url):
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
		re_valid_email_Address = re.compile("[a-z0-9\-\+\_]+(\.[a-z0-9\-\+\_]+)*\@[a-z0-9\-\+\_]+(\.[a-z0-9\-\+\_]+)*(\.[a-z]+)+$")
		
		def validate_email_address(self, emailAddr):
			return not self.re_valid_email_Address.match(emailAddr) == None
	
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
					ableToSave = not value.strip() == '' and YotsubaSDKPackage.mail.validate_email_address(value.strip())
				elif key.strip() == 'to' or key.strip() == 'cc' or key.strip() == 'bcc':
					receivers = value.split(',')
					for receiver in receivers:
						if receiver.strip() == '':
							continue
						
						if not YotsubaSDKPackage.mail.validate_email_address(receiver.strip()):
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
					return jfs.fs_write(filename, data, jfs.WRITE_PICKLE)
				except:
					return False
			
			def send(self):
				if data['from'] == '' or data['to'] == '':
					return False

class YotsubaSDK:
	code = YotsubaSDKPackage.core()
	crypt = YotsubaSDKPackage.crypt()
	fs = YotsubaSDKPackage.fs()
	log = YotsubaSDKPackage.log()
	mail = YotsubaSDKPackage.mail()

sdk = YotsubaSDK()