# Yotsuba CoE JFS "Juti's File System"
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License

# Note:
# This package is just to simplify any simple file operations that any web
# developers might want to do in general.

# 1.01: fs_create is depreciated and fs_mkdir is added.

import os, sys, re, dircache, pickle, cgi

# [Definitions]
# [+ Package Profile]
NAME		= 'JFS'
VERSION		= 1.02
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

# Future Interfaces
def fs_copy(source_filename, dest_filename, request_safe_move = False):
	# Safe Move: simuteneously read the source and write the destination at the same time
	# Alternative: just use system call CP/SCP
	return False
def fs_move(original_destpath, new_destpath, request_safe_move = False):
	# Safe Move: Copy first and delete the original path
	# Alternative: just use system call MV
	return False
def fs_change_mode(destpath, new_mode, request_recursive_mode = False):
	# Not compatible with Windows servers
	return False
def fs_change_user(destpath, new_user, request_recursive_mode = False):
	# Not compatible with Windows servers
	return False
def fs_change_group(destpath, new_group, request_recursive_mode = False):
	# Not compatible with Windows servers
	return False

# [Completed]
# Make directory
def fs_mkdir(destpath):
	try:
		os.mkdir(destpath)
		return True
	except:
		return False

# return size in bytes
def fs_size(destpath):
	size = int(os.stat(destpath)[6])
	return size

# Friendly Path Identifier
def fs_abspath(destpath, request_relative_path_fixed = False):
	if request_relative_path_fixed:
		if not re.compile('^/').match(destpath):
			destpath = '/' + destpath
		return os.path.abspath( os.getcwd() + destpath )
	else:
		return os.path.abspath( destpath )

# Symbol-instance checker
def fs_sym_gettype(destpath):
	if not os.path.exists(destpath):
		return -1
	if os.path.isfile( fs_abspath( destpath) ) \
	    or (os.path.islink( fs_abspath( destpath ) ) and\
	    os.path.isfile( fs_abspath( destpath) ) ):
		return FILE
	return DIRECTORY

def fs_exists(destpath):
	return	os.access(os.path.abspath(destpath), os.F_OK)

def fs_readable(destpath):
	return	os.access(os.path.abspath(destpath), os.R_OK)

def fs_writable(destpath):
	return	os.access(os.path.abspath(destpath), os.W_OK)

def fs_executable(destpath):
	return	os.access(os.path.abspath(destpath), os.X_OK)

def fs_isfile(destpath):
	return 	fs_sym_gettype(destpath) == FILE

def fs_isdir(destpath):
	return	fs_sym_gettype(destpath) == DIRECTORY

# Browsing Function
def fs_browse(destpath, request_abspath_shown = False, filter = None, filterToSearch = False):
	# Check if this is a directory
	if not fs_isdir( fs_abspath( destpath ) ) or not fs_readable( fs_abspath(destpath) ):
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
		if fs_isfile( destpath + '/' + item ):
			if request_abspath_shown:
				files.append(fs_abspath(destpath + '/' + item))
			else:
				files.append(item)
			#end if
		elif fs_isdir( destpath + '/' + item ):
			if request_abspath_shown:
				directories.append(fs_abspath(destpath + '/' + item))
			else:
				directories.append(item)
			#end if
		else:
			pass
		#end if
	files.sort()
	directories.sort()
	return {'files':files, 'directories':directories}

# Reading Function (supporting all encodings)
def fs_read(filename = '', mode = READ_NORMAL):
	if filename == '':
		# read stdin by default
		return sys.stdin.read()
	if mode == READ_PICKLE:
		# use pickle for reading
		if not fs_size(filename) > 0:
			return None
		fp = open(filename, 'rb')
		try:
			data = pickle.load(fp)
		except:
			return None
		fp.close()
		return data
	
	# This part does not use pickle.
	data = ''
	if fs_isfile(filename):
		fp = open(filename, mode)
		data = fp.read()
		fp.close()
	else:
		return None
	return data

# (Web) Data Fetching Function (Added in 1.1)
def fs_web_read(url):
	#try:
		import pycurl
		rp = pycurl.Curl()
		rp.setopt(pycurl.URL, url)
		rp.perform()
		return rp.getinfo(pycurl.HTTP_CODE)
	#except:
	#	return None

# Writing Function
def fs_write(filename, data, mode = WRITE_NORMAL):
	if mode == WRITE_PICKLE:
		# use pickle for writing
		#if fs_exists(filename):
		#	os.unlink(filename)
		try:
			fp = open(filename, 'wb')
			pickle.dump(data, fp)
			fp.close()
			return True
		except:
			return False
	
	# This part does not use pickle.
	if fs_isfile(filename):
		os.unlink(filename)
		fp = open(filename, mode)
		fp.write(data)
		fp.close()
	else:
		return False
	return True

# Removal Function 
def fs_remove(destpath):
	if fs_isdir(destpath):
		os.removedirs(destpath)
		return True
	elif fs_isfile(destpath, True):
		os.unlink(destpath)
		return True
	return False