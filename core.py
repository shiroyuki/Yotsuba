# Yotsuba CoE Core "Kernel Base"
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License

import jfs,re,os

# Global variables
# (Initialization at the end of file)
global installed_packages # Dictionary keyed by STRING and valued by PACKAGEPROFILE
global config

# Definitions
PACKAGE_EXPERIMENTAL	= -2
PACKAGE_UNSTABLE	= -1
PACKAGE_TESTING		= 0

# [Class: Package]
# This is to keep tracking packages installed on the system.
class PackageProfile:
	name	= None		# Name of Package
	version = None		# Real Version used officially
	release = None		# Release Version (according to version registered by
				# CVS server right before CVS if existed)
	
	def __init__(self, name, version, release):
		self.name	= name
		self.version	= version
		self.release	= release

def core_load_conf(where):
	global config
	
	data = jfs.fs_read(where)
	lines = re.compile('\n').split(data)
	key = ''
	try:
		for line in lines:
			if re.compile('^#').match(line):
				continue
			if re.compile('^\[.+\]$').match(line):
				key = line[1:len(line)-1]
				config[key] = {}
				continue
			p = re.compile('=').split(line)
			if len(p) > 1:
				config[key][p[0].strip()] = p[1].strip()
	except:
		pass
	
def core_filesize(file_path):
	unit = ['B', 'KB', 'MB', 'GB', 'TB']
	i = 0
	size = jfs.fs_size(os.path.abspath(file_path))
	while size >= 1024.0:
		size /= 1024.0
		i+=1
	size *= 100
	size = int(size)
	size /= 100.0
	return (size, unit[i])

def core_hash(string):
	import sha, md5
	return '%s%s' % (md5.new(string).hexdigest(), sha.new(string).hexdigest())

def core_isEmail(string):
	return re.compile('[a-zA-Z0-9\.\-\+\_]+\@[a-zA-Z0-9\.\-\+\_]+\.[a-zA-Z0-9\.]+$').match(string)

def core_getScript(lines_or_filename):
	data = ''
	if jfs.fs_exists(lines_or_filename):
		data = '// [Loaded] %s\n\n' % lines_or_filename
		data += jfs.fs_read(lines_or_filename)
	else:
		data = lines_or_filename
	return '<script type="text/javascript">\n%s\n</script>' % data

def core_getScriptRelocate(where):
	return core_getScript('window.open("%s","_self");' % where)

def ntext(string):
	return unicode(string, "latin-1")

def utext(string):
	return unicode(string, "utf8")

def get_encoded_timecode(time_tuples = None):
	from time import gmtime, strftime
	if not time_tuples:
		time_tuples = gmtime()
	return int(strftime("%Y%m%d%H%M", time_tuples))

def get_decoded_timecode(timecode):
	result = [0, 0, 0, 0, 0]
	try:
		for i in range(5):
			result[i] = int(timecode/pow(10, 8 - 2*i))
			result.append(str(result[i]))
			red_timecode = int(result[i]*pow(10, 8 - 2*i))
			timecode -= red_timecode
	except:	pass
	return result

installed_packages = {'core': PackageProfile("Core", 4.2, 6)}
installed_packages['jfs'] = PackageProfile("Juti's File System", jfs.VERSION, 5)
config = {}
