# Yotsuba CoE WebEC "Web Environment Control"
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License
try:
	import MySQLdb
except:
	pass
import core

core.installed_packages['sql'] = core.PackageProfile("SQL", 2.05, 2)

# 2.04: Added
def sql_encodeString(data):
	try:
		data = unicode(data, 'latin-1')
	except:
		data = data.encode('latin-1')
	return data

class sql:
	__conn = None
	__cursor = None
	__host = "localhost"
	__user = "root"
	__passwd = ""
	__db = "test"
	
	def __init__(self, host = "localhost", user = "root", passwd = "", db = "test"):
		self.initialize(host, user, passwd, db)
	
	def initialize(self, host = "localhost", user = "root", passwd = "", db = "test"):
		self.__host = host
		self.__user = user
		self.__passwd = passwd
		self.__db = db
	
	def connect(self):
		try:
			self.__conn = MySQLdb.connect(self.__host, self.__user, self.__passwd, self.__db)
			self.__cursor = self.__conn.cursor ()
			self.__cursor.execute('SET NAMES utf8')
			return None
		except MySQLdb.Error, e:
			return "Error %d: %s" % (e.args[0], e.args[1])
		except:
			print "(!)"

	# CoE 1.2: Added
	def explain(self, table, cond = '', order = '', col = '', limit = 0, offset = 0):
		self.connect()
		fetch_range = ''
		if not cond == '':
			cond = ' WHERE %s' % cond
		if not order == '':
			order = ' ORDER BY %s' % order
		if col == '':
			col = '*'
		if offset < 0:
			offset = 0
		if limit < 0:
			limit = 0
		if limit > 0 and offset >= 0:
			fetch_range = ' LIMIT %d,%d' % (offset, limit)
		script = sql_encodeString("EXPLAIN (SELECT DISTINCT %s FROM %s%s%s%s);" % (col, table, cond, order, fetch_range))
		rows = []
		try:
			try:
				import webec
				webec.session_status_add('Execute query: %s' % script)
			except:	pass
			
			self.__cursor.execute (script)
			while True:
				row = self.__cursor.fetchone()
				if row == None: break
				rows.append(row)
		except MySQLdb.Error, e:
			try:
				webec.session_status_add("Error %d: %s (QUERY: %s)" % (e.args[0], e.args[1], script))
			except: pass
		except:
			try:
				webec.session_status_add("Unknown Error on Query: %s)" % (script))
			except:	pass
		self.disconnect()
		return rows

	# CoE 1.1 Added: limit, offset
	# CoE 1.4 / CoE SQL 2.04 Added: requestDistinctRows
	def select(self, table, cond = '', order = '', col = '', limit = 0, offset = 0, requestDistinctRows = True):
		self.connect()
		fetch_range = ''
		select_opts = ''
		if requestDistinctRows:
			select_opts = ' DISTINCT'
		if not cond == '':
			cond = ' WHERE %s' % cond
		if not order == '':
			order = ' ORDER BY %s' % order
		if col == '':
			col = '*'
		if offset < 0:
			offset = 0
		if limit < 0:
			limit = 0
		if limit > 0 and offset >= 0:
			fetch_range = ' LIMIT %d,%d' % (offset, limit)
		script = sql_encodeString("SELECT%s %s FROM %s%s%s%s;" % (select_opts, col, table, cond, order, fetch_range))
		rows = []
		try:
			try:
				import webec
				webec.session_status_add('Execute query: %s' % script)
			except:	pass
			
			self.__cursor.execute (script)
			while True:
				row = self.__cursor.fetchone()
				if row == None: break
				rows.append(row)
			try:
				webec.session_status_add('Finished query: %s' % script)
			except:	pass
		except MySQLdb.Error, e:
			try:
				webec.session_status_add("Error %d: %s (QUERY: %s)" % (e.args[0], e.args[1], script))
			except: pass
		except:
			try:
				webec.session_status_add("Unknown Error on Query: %s)" % (script))
			except:	pass
		self.disconnect()
		return rows
	
	def insert(self, table, col, value):
		self.connect()
		returnee = False
		script = sql_encodeString("INSERT INTO %s (%s) VALUES(%s);" % (table, col, value))
		try:
			try:
				import webec
				webec.session_status_add('Execute query: %s' % script)
			except:	pass
			self.__cursor.execute(script)
			returnee = True
			try:
				webec.session_status_add('Finished query: %s' % script)
			except:	pass
		except MySQLdb.Error, e:
			try:
				webec.session_status_add("Error %d: %s (QUERY: %s)" % (e.args[0], e.args[1], script))
			except: pass
		except:
			try:
				webec.session_status_add("Unknown Error on Query: %s)" % (script))
			except:	pass
		self.disconnect()
		return returnee
	
	def update(self, table, exprs, cond = '', order = ''): # exprs = "col1=val1[, col2=val2 ...] ... See the MySQL document
		self.connect()
		if not cond == '':
			cond = ' WHERE %s' % cond
		if not order == '':
			order = ' ORDER BY %s' % order
		script = sql_encodeString("UPDATE %s SET %s%s%s;" % (table, exprs, cond, order))
		try:
			self.__cursor.execute(script)
			self.disconnect()
			return None
		except MySQLdb.Error, e:
			self.disconnect()
			return "Error %d: %s (QUERY: %s)" % (e.args[0], e.args[1], script)
		except:
			self.disconnect()
			return "Unknown Error on Query: %s)" % (script)
	
	# 2.04: Added
	def delete(self, table, cond = '', order = '', row_count = 0):
		self.connect()
		returnee = False
		limit = ''
		if not cond == '':
			cond = ' WHERE %s' % cond
		if not order == '':
			order = ' ORDER BY %s' % order
		if row_count > 0:
			limit = ' LIMIT %d' % row_count
		script = sql_encodeString("DELETE FROM %s%s%s%s;" % (table, cond, order, limit))
		try:
			try:
				import webec
				webec.session_status_add('Execute query: %s' % script)
			except:	pass
			self.__cursor.execute(script)
			returnee = True
			try:
				webec.session_status_add('Finished query: %s' % script)
			except:	pass
		except MySQLdb.Error, e:
			try:
				webec.session_status_add("Error %d: %s (QUERY: %s)" % (e.args[0], e.args[1], script))
			except: pass
		except:
			try:
				webec.session_status_add("Unknown Error on Query: %s)" % (script))
			except:	pass
		self.disconnect()
		return returnee

	def disconnect(self):
		try:
			self.__cursor.close ()
			self.__conn.close ()
			return 0
		except:
			return 1
