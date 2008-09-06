# Yotsuba CoE Spirale "Mail"
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License

import core, jfs
import re

core.installed_packages['spirale'] = core.PackageProfile('Spirale', 2.00, core.PACKAGE_EXPERIMENTAL)

DEFAULT_MESSAGE_SUBJECT = 'Untitled Message'

class EmailAddressValidator:
	regexp = re.compile("[a-z0-9\-\+\_]+(\.[a-z0-9\-\+\_]+)*\@[a-z0-9\-\+\_]+(\.[a-z0-9\-\+\_]+)*(\.[a-z]+)+$")
	def validate(self, emailAddr):
		return not regexp.match(emailAddr) == None

class MailMessage:
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
			ableToSave = not value.strip() == '' and EmailAddressValidator.validate(value.strip())
		elif key.strip() == 'to' or key.strip() == 'cc' or key.strip() == 'bcc':
			receivers = value.split(',')
			for receiver in receivers:
				if receiver.strip() == '':
					continue
				
				if not EmailAddressValidator.validate(receiver.strip()):
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