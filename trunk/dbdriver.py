#!/usr/bin/python

import cx_Oracle
import MySQLdb
from MySQLdb import MySQLError

class MyDict(dict):
	def __missing__(self, key):
		return key

class Db:
	def __init__(self, dbtype, params): # params is a dict
		self.type = dbtype
		if self.type == "oracle":
			self.conn = cx_Oracle.connect("%s/%s@%s"%(params["user"], params["passwd"], params["tns"]))
		elif self.type == "mysql":
			self.conn = MySQLdb.connect(host = params["host"], user = params["user"], passwd = params["passwd"], db = params["db"])
		self.dbname = params["db"]
        
		self.cursor = self.conn.cursor()
		self.types = {
			"oracle" : MyDict([["int", "number"], ["datetime", "timestamp"]]),
			"mysql"  : MyDict()
		}

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

	def insert(self, table, cols, valueslists):
		if self.type == "oracle":
			placeholders = ",".join(map(lambda i : ":" + str(i+1), range(len(m.description))))
			self.cursor.prepare('INSERT INTO smdc."' + tblname + '"(' + cols + ') VALUES (' + placeholders + ')')
			try:
				self.cursor.executemany(None, valueslists)
				self.conn.commit()
			except cx_Oracle.Error, (errno, strerror):
				print errno, strerror
				return errno
		elif self.type == "mysql":
			placeholders = ("%s,"*len(values))[:-1]
			try:
				self.cur.executemany("insert into " + table + " (" + cols + ") values (" + placeholders + ")", valueslists)
			except MySQLError, (errno, strerror):
				return errno
		return 0

	def __del__(self):
		self.cursor.close()
		self.conn.close()

# usage:
#db = Db("$TYPE", {"host" : , "db" : , "user" : , "passwd"})

