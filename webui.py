# Yotsuba CoE WebUI "Web User Interface"
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License
import sys, re, xml.parsers.expat	# Default libraries
import core				# Yotsuba Core Library
import jfs				# Juti's Web-based File System

core.installed_packages['webui'] = core.PackageProfile("WebUI", 2.02, 5)

global tag_init
global dictionary
global dictionary_raw
global extra_dictionary

tag_init = ''				# Initial Keyword for each tag
dictionary = {}				# Keyword Dictionary
dictionary_raw = {}			# Keyword Dictionary
extra_dictionary = {}				# Hyperlink Dictionary

# [Definitions]
P_TOP = 0
P_LEFT = 1
P_RIGHT = 2
P_BOTTOM = 3

class webui_browser:
	width = 100
	width_unit = "%"
	height = 100
	height_unit = "%"

class webui_browser_panel:
	auto_hide = False
	position = P_TOP

class webui_browser_display:
	items = None

class webui_browser_item:
	name = None
	cmd = None

# [XML Handlers and the special variables]
opened_tags = []
def webui_load_dict_xml_start_element(name, attrs):
	global opened_tags, dictionary, dictionary_raw, tag_init
	name = name.encode('ascii', 'ignore')
	opened_tags.append(name)
	# Updated in 2.2: Allow multiple dictionaries to be loaded.
	if len(opened_tags) == 1 and tag_init == '':
		tag_init = attrs['init']
	elif len(opened_tags) > 1:
		dictionary[name] = ''
		dictionary_raw[name] = []
# enddef webui_load_dict_xml_start_element

def webui_load_dict_xml_end_element(name):
	global opened_tags, dictionary, dictionary_raw, tag_init
	name = name.encode('ascii', 'ignore')
	if len(opened_tags) > 0:
		name_tmp = opened_tags.pop()
		if not name_tmp == name:
			opened_tags.append(name_tmp)
		else:
			if len(opened_tags) > 0:
				dictionary[name] = " ".join(dictionary_raw[name])
	if len(opened_tags) < 0:
		print "[CODE/WEBUI] the dictionary file is malformed."
		sys.exit()
# enddef webui_load_dict_xml_end_element

def webui_load_dict_xml_char_data(data):
	global opened_tags, dictionary, dictionary_raw, tag_init
	if len(opened_tags) < 2: return
	callid = opened_tags.pop()
	callid = callid.encode('ascii', 'ignore')
	dictionary_raw[callid].append(data)
	opened_tags.append(callid)
# enddef webui_load_dict_xml_char_data

# [Automatic Configuration]
# webui_load_dict
# Description:	load the dictionary file and put it in the dictionary
# Arguments:	char *dict_file and dictionary<char*, char*> dict_list
# Return:	nothing
def webui_load_dict(dict_file = None, dict_list = None):
	global opened_tags, dictionary, dictionary_raw, tag_init
	
	if dict_file:
		data = jfs.fs_read(dict_file)
		p = xml.parsers.expat.ParserCreate()
		p.StartElementHandler = webui_load_dict_xml_start_element
		p.EndElementHandler = webui_load_dict_xml_end_element
		p.CharacterDataHandler = webui_load_dict_xml_char_data
		p.Parse(data,1)
	if dict_list:
		for k in dict_list.keys():
			dictionary[k] = '%s' % dict_list[k]
# enddef webui_load_dict

# webui_load_conf
def webui_load_conf(conf_file = None, conf_dict = None):
	global extra_dictionary
	
	if conf_dict:
		for k in conf_dict.keys():
			extra_dictionary[k] = conf_dict[k]
	if conf_file:
		webui_load_dict(conf_file)
# enddef webui_load_conf

# [Tag transformation]
# webui_tag_transform
# Description:	replace the given data with Yotsuba special tags
# Arguments:	char *data
# Return:	char *transformed_data
def webui_tag_transform(data, is_hyperlink = False):
	global dictionary, extra_dictionary, tag_init

	#if not data:
	#	return ''

	replace_w = None	# Dictionary for the replacement of tags
	
	if is_hyperlink and len(extra_dictionary) > 0:
		replace_w = extra_dictionary
	# endif is_hyperlink and len(extra_dictionary) > 0

	if not is_hyperlink and len(dictionary) > 0:
		replace_w = dictionary
	# endif not is_hyperlink and len(dictionary) > 0
	
	if replace_w and len(replace_w) > 0:
		for key in replace_w:
			try:
				data = re.compile('<%s%s/>' % (tag_init, key)).sub(replace_w[key], core.utext(data))
			except:
				#data = re.compile('<%s%s/>' % (tag_init, key)).sub(replace_w[key], data.encode('utf8').decode('utf8'))
				try:
					data = re.compile('<%s%s/>' % (tag_init, key)).sub(replace_w[key], core.ntext(data))
				except:
					data = re.compile('<%s%s/>' % (tag_init, key)).sub(replace_w[key], data)
		
	return data
# enddef webui_tag_transform

# [Template Processing]
# webui_read_template
# Description:	read a template file and replace with Yotsuba special tags
# Arguments:	char *template_data
# Return:	char *translated_data
# Dependencies:	jfs
def webui_read_template(template_data, from_string = False, enable_optimization = False):
	if from_string:
		data = template_data.decode('utf8')
	else:
		data = jfs.fs_read(template_data)
	
	# [Do substitution]
	# Note: UI tags must be ALWAYS replaced before URL tags
	data = webui_tag_transform(data)
	data = webui_tag_transform(data, is_hyperlink = True)
	
	if enable_optimization:
		data = re.sub("( )+", " ", re.sub("\n|\r|\t", " ", data))

	try:
		return data.encode('utf-8')
	except:
		return data
# enddef webui_read_template

# webui_print_template
# Description:	read a template file, replace with Yotsuba special tags and print out the input
# Arguments:	char *template_data
# Return:	nothing
def webui_print_template(template_data, from_string = False, enable_optimization = False):
	print webui_read_template(template_data, from_string, enable_optimization)
# enddef webui_print_template

# webui_dict
# Description:	return a word from the dictionary consisting Yotsuba special tags
# Arguments:	char *key
# Return:	OK:		char *translated_data
#		Failure:	an empty string
# Dependencies:	jfs
def webui_dict(key):
	string = webui_read_template('<Yotsuba%s/>' % key, True)
	if re.match('^<.+/>$', string):
		return ''
	return string
# enddef webui_dict

# webui_remove_html_elements
# Added in version 1.1
# Remove all HTML tags from the given text
def webui_remove_html_elements(text):
	return re.sub('<|>', '', re.sub('<.*>', '', text))
# enddef webui_remove_html_elements

# webui_text_to_html
# Added in version 1.1
# Convert the given (assumedly plain) text to HTML-formatted text.
# If `full_mode`, then the null space will be replaced to `&nbsp;`.
# This function does not work with East-Asian languages.
def webui_text_to_html(text, full_mode = False):
	try:
		text = re.sub('\n', '<br/>', text)
		if full_mode:
			text = re.sub(' ', '&nbsp;', text)
	except:
		pass
	return text
# enddef webui_text_to_html
