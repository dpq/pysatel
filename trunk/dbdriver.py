#!/usr/bin/python

""" 
usage:
db = Db("$TYPE", {"host" : , "db" : , "user" : , "passwd"})
"""

import os
import cx_Oracle
import MySQLdb
from MySQLdb import MySQLError

class MyDict(dict):
	def __missing__(self, key):
		return key

class Db:
	def __init__(self, dbtype, params): # params is a dict
		self.types = {
			# ["datetime", "timestamp"] :(((
			"oracle" : MyDict([["int", "number"], ["datetime", "date"]]),
			"mysql"  : MyDict()
		}
		self.type = dbtype
		if self.type == "oracle":
			print 'self.conn = cx_Oracle.connect(' + "%s/%s@%s"%(params["user"], params["passwd"], params["tns"]) + ')'
			self.conn = cx_Oracle.connect("%s/%s@%s"%(params["user"], params["passwd"], params["tns"]))
			self.maxAllowedPacked = 1024*1024 # TODO
		elif self.type == "mysql":
			self.conn = MySQLdb.connect(host = params["host"], user = params["user"], passwd = params["passwd"], db = params["db"])
		self.dbname = params["db"]
		self.cursor = self.conn.cursor()
		if self.type == "mysql":
			self.cursor.execute("show variables;")
			self.maxAllowedPacked = int(dict(self.cursor.fetchall())["max_allowed_packet"])

	def createTable(self, table, cols, primarykey):
		if self.type == "oracle":
			# "colname" $TYPE other_comments, ...
			cols = ",".join(map(lambda col : '"%s" %s '%(col, self.types[self.type][cols[col].pop("type")]) + " ".join(map(lambda cl: cl + " " + cols[col][cl],cols[col])), sorted(cols.keys())))
			self.cursor.execute('CREATE TABLE "%s" (%s, PRIMARY KEY ("%s"))'%(table, cols, primarykey))
		elif self.type == "mysql":
			cols = ",".join(map(lambda col : "`%s` %s "%(col, self.types[self.type][cols[col].pop("type")]) + " ".join(map(lambda cl: cl + " " + cols[col][cl],cols[col])), sorted(cols.keys())))
			self.cursor.execute('CREATE TABLE %s.`%s` (%s, PRIMARY KEY (`%s`));'%(self.dbname, table, cols, primarykey))

	def dropTable(self, table):
		if self.type == "oracle":
			self.cursor.execute('DROP TABLE "%s"'%(table))
		elif self.type == "mysql":
			self.cursor.execute("DROP TABLE %s.`%s`;"%(self.dbname, table))

	def insert(self, table, header, valueslists):
		if len(valueslists) == 0:
			print "KAKOGO??? Valueslists is empty :("
			return
		if self.type == "oracle":
			columns = ",".join(map(lambda h : '"%s"'%h, header))
			placeholders = ",".join(map(lambda i : ":" + str(i+1), range(len(header))))
			request = 'INSERT INTO smdc."%s"('%table + columns + ') VALUES (to_date(:1, \'yyyy-mm-dd hh24:mi:ss\'),' + placeholders[3:] + ')'
			self.cursor.prepare(request)
			try:
				self.cursor.executemany(None, valueslists)
				self.conn.commit()
			except cx_Oracle.Error, strerror:
				print strerror[:-1]
		elif self.type == "mysql":
			columns = ",".join(header)
			placeholders = ("%s,"*len(header))[:-1]
			trying = 0
			try:
				maxRows = self.maxAllowedPacked / len(" ".join(map(lambda v : str(v), valueslists[0]))) / 2
				i = 0
				while i < len(valueslists):
					self.cursor.executemany("insert into `" + table + "` ("+columns+") values ("+placeholders+")", valueslists[i:i+maxRows])
					i += maxRows
			except MySQLError, strerror:
				print "MySQLError :", strerror, "trying ..."
				trying = 1
			if trying:
				print "Trying row by row... (", len(valueslists), ") rows" 
				for i in range(len(valueslists)):
					try:
#						print  "insert into `%s` (%s) values (%s)"%(table, columns, )
#						print len(placeholders.split("s")), placeholders
#						print len(valueslists[i])
						print "insert into `" + table + "` ("+columns+") values ('%s',"%(valueslists[0]) + placeholders[:-2]%(",".join(valueslists[i][1:]))+");"
						self.cursor.execute(("insert into `" + table + "` ("+columns+") values ("+placeholders+");")%valueslists[i])
					except MySQLError, strerror:
						print "MySQLError :", strerror
#						1/0
					except:
						pass
#			2/0
		return 0

	def __del__(self):
		self.cursor.close()
		self.conn.close()


