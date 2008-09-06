# Yotsuba CoE WebEC "Web Environment Control"
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License

import sys, os, pickle, re
import Cookie
import jfs, core

core.installed_packages['webec'] = core.PackageProfile("WebEC", 2.07, 9)
# 2.02: [fixed:bug|0805162204] sessions_save fails to save the session object.
# 2.04: [enhancement] with JFS 1.01, auto-creation of the session storage is added.
#	and session_initialize is added by default.
# 2.07.9: [enhancement + bug] xdir is incorrectly interpreted

global xrdi # Executed Root Directory
global xdir # Executed Directory
global xapp # Executed Application Name

xrdi = os.environ['DOCUMENT_ROOT']
xapp = (os.environ['SCRIPT_FILENAME'].split('/')[-1]).split('\\')[-1]
xdir = re.sub(xapp + "$", "", os.environ['SCRIPT_FILENAME'][len(os.environ['DOCUMENT_ROOT']):])

global xrun # Executed screipt (Depreciated)
xrun = ''
try:
	xrun = os.environ['SCRIPT_FILENAME'][len(os.environ['DOCUMENT_ROOT']) + 1:]
except:
	xrun = ''
global headers
headers			= {'Content-Type':'text/html', 'Set-Cookie':{}}
global session
# Caution!
# The session path for Windows should be, for instance, C:\temp before run the code.
session = {'path':'/tmp/sessions/', 'obj':{'ipc':None}, 'id':-1, 'status':[]}
global is_cookies_written
is_cookies_written = False # for set_cookies

# [Implemented Interfaces]
def getExpirationDate():
	import time
	t = time.localtime()
	t = time.mktime((t[0], t[1], t[2] + 1, t[3], t[4], t[5], t[6], t[7], t[8]))
	string = time.strftime("%a %d-%b-%y %H:%M:%S GMT", time.gmtime(t))
	return string

# CoE/WebEC 2.02.7: Added returnString
# CoE/WebEC 2.05.7: charset added by default
def header_toHTML(skip_cookies = False, returnString = False):
	global headers
	output = 'Content-Type: %s;charset=UTF-8\n' % (headers['Content-Type'])
	if skip_cookies:
		return output
	for k in headers['Set-Cookie'].keys():
		output += 'Set-Cookie: %s=%s;expires=%s;path=/;\n' % (k, headers['Set-Cookie'][k], getExpirationDate())
	output += '\n'
	if not returnString:
		print output
		return
	else:
		return output

def cookies(index):
	if headers['Set-Cookie'].has_key(index):
		return headers['Set-Cookie'][index]
	if os.environ.has_key('HTTP_COOKIE') and Cookie.SimpleCookie(os.environ['HTTP_COOKIE']).has_key(index):
		return Cookie.SimpleCookie(os.environ['HTTP_COOKIE'])[index].value
	return None

def cookies_read(index):
	return cookies(index)

def cookies_write(key, value):
	global headers
	headers['Set-Cookie'][key] = value

# 2.04: Auto-create the storage path.
def session_initialize(where_to_save = ''):
	global session
	if not where_to_save == '':
		session['path'] = where_to_save
	if not jfs.fs_exists(session['path']):
		if jfs.fs_mkdir(session['path']):
			session_status_add("System reinitiated.")
		else:
			session_status_add("Error occurred during reinitiation.")
	else:
		session_status_add("Reconnected to the EC server.")

def session_save():
	global session
	if session['id'] == -1:
		print "<p>SID NOT FOUND!</p>"
		session_status_add("Called SID %s" % session['id'])
		return False
	saveTo = os.path.join(session['path'], session['id'])
	if not jfs.fs_exists(session['path']):
		session_status_add("%s does not exists." % session['path'])
	if not jfs.fs_exists(saveTo):
		session_status_add("%s does not exists." % saveTo)
	if not jfs.fs_writable(session['path']):
		session_status_add("Saving failed due to lack of privilege to write the folder!")
	if not jfs.fs_writable(saveTo):
		session_status_add("Saving failed due to lack of privilege to write the file!")
	if not jfs.fs_write(saveTo, session['obj'], mode = jfs.WRITE_PICKLE):
		session_status_add("Saving failed due to error during writing!")
	return True

# 2.3: added
def session_free_key(key):
	try:
		del session['obj'][key]
		return True
	except:
		return False

def sessions(key, value = None):
	global session
	session_status_add("Refer to SID %s." % session['id'])
	if value:
		session_status_add("Session key '%s' in use." % key)
	else:
		session_status_add("Session key '%s' called." % key)
	if not session['obj']:
		session['obj'] = {'ipc':None}
		session_status_add("Session self-restructed!")
	if not session['obj'].has_key(key):
		session_status_add("Session storing failed!")
		session['obj'][key] = None
		session_status_add("Session key '%s' added!" % key)
	if session['obj'].has_key(key):
		if value:
			session['obj'][key] = value
			session_status_add("Session key '%s' assigned!" % key)
		else:
			session_status_add("Session key '%s' retreived!" % key)
		if not session_save():
			session_status_add("Session storing failed!")
		else:
			if value:
				session_status_add("Session key '%s' stored." % key)
		return session['obj'][key]
	else:
		session_status_add("Session key '%s' not stored!" % key)
		return None

def session_restore(renew = False, mkSIDIfFailed = True):
	global session, headers
	session_initialize()
	sid = cookies('sid')
	saveTo = ''
	if sid:
		saveTo = os.path.join(session['path'], sid)
	if not session['obj'] == {'ipc':None}:
		session_status_add('Session re-initiation aborted!')
	elif sid and os.path.exists(saveTo):
		if not renew:
			session['obj'] = jfs.fs_read(saveTo, jfs.READ_PICKLE)
			session_status_add('Loaded.')
		else:
			os.unlink(saveTo)
			session_status_add('Renewed.')
		session['id'] = sid
	else:
		if not os.path.exists(saveTo):
			session_status_add('Session retrival failed!')
		if not sid:
			session_status_add('SID retrival failed!')
			session_status_add('Session renewed!')
			import sha, time
			sid = sha.new(str(time.time())).hexdigest()
			session['id'] = sid
		else:
			session['id'] = sid
	session_save()
	cookies_write('sid',sid)
	return sid

def session_id():
	global session
	return session['id']

def session_status(string = None):
	global session
	if string:
		session['status'] = [string]
	return session['status']

def session_status_add(string = ''):
	global session
	if string:
		session['status'].append(string)
	return session['status']

def make_headers(headers):
	v0 = '\n'
	for k, v in headers.items():
		v0 = ('%s: %s\n' % (k, v)) + v0
	return v0

# Inter-process Communication Channel (CGI)
# |_ Read-only data from IPC buffer
#  |_ LOG 080407: Support the array of input and file input
def ipc(key):
	global session
	ipc = sessions('ipc')
	if ipc and ipc.has_key(key):
		session_status_add("IPC retrieved via the buffered IPC! (key: %s)" % (key))
		if len(ipc[key]) > 1:
			# Return the whole list
			print "(!!)"
			session_status_add("# This key is an array.")
			return ipc[key]
		else:
			session_status_add("# This key is an single data.")
			return ipc[key][0]
	
	import cgi
	ipc = cgi.FieldStorage()
	if ipc.has_key(key):
		session_status_add("IPC retrieved via CGI standard input! (key: %s)" % key)
		try:
			return (ipc[key].filename, ipc[key].file)
		except:
			return ipc[key].value
	else:
		session_status_add("IPC retrival failed! (key: %s)" % key)
	return ''

# |_ Dump the IPC buffer sent from clients to the disk
#  |_LOG 080407: Support the array of input and file input
def ipc_dump(ipc = None, force_dump = False):
	global session
	if sessions('ipc') and not force_dump:
		session_status_add("IPC already established.")
		return
	if not ipc:
		session_status_add("IPC undefined.")
		return
	raw_ipc = {}
	for k in ipc.keys():
		if not raw_ipc.has_key(k):
			session_status_add("# Initialized IPC key '%s'." % (k))
			raw_ipc[k] = []
		if not ipc[k].file == None:
			session_status_add("# Append a File object to IPC key '%s'." % (k))
			#raw_ipc[k].append((ipc[k].filename, ipc[k].file))
			raw_ipc[k].append(ipc[k])
		else:
			session_status_add("# Append a data object to IPC key '%s'." % (k))
			raw_ipc[k].append(ipc[k].value)
	if not raw_ipc == sessions('ipc', raw_ipc):
		session_status_add("IPC dumping failed.")
	else:
		session_status_add("IPC dumpped.")

# |_ Flush the buffer
def ipc_flush():
	global sessions
	try:
		session['obj']['ipc'] = None
		session_status_add('IPC flushed.')
	except:
		session_status_add('IPC resetting failed!')
