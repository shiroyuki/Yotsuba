# Yotsuba CoE Kotonoha "Word Processing"
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License

import re
import core

core.installed_packages['kotonoha'] = core.PackageProfile("Kotonoha", 3.02, core.PACKAGE_UNSTABLE)

def addslashes(data):
	return re.sub("'", "\\'", data)

def make_wiki_content(data):
	raw_lines = re.split('(\n|\r)', data)
	lines = []
	result = []
	for line in raw_lines:
		lines.append(re.split('( |<.*>)', line))
		for i in range(0, len(lines[-1])):
			if re.match('(http|https|ftp|sftp|irc)\://', lines[-1][i]):
				temp = re.sub('^\.+', '', lines[-1][i])
				temp = re.sub('\.+$', '', temp)
				temp_link = '<a href="%s">%s</a>' % (temp, temp)
				data = re.sub(temp, temp_link, data)
	return data