#!/usr/bin/python
"""PySatel - a Python framework for automated processing of space satellite scientific data
   Copyright (C) 2010 David Parunakian

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import MySQLdb
import os

from MySQLdb import MySQLError
DUPLICATE_ENTRY_ERROR = 1062

class export:
	def __init__(self, path, host, user, password, database):
		self.path = path
		self.conn = MySQLdb.connect(host, user, password, database)
		self.cur = self.conn.cursor()

	def stdout(self, satellite, instrument, session, header, records):
		for r in records:
			r = map(lambda entry : str(entry), r)
			print "\t".join(r)
		return

	def mysql(self, satellite, instrument, session, header, records):
		header = map(lambda h : "`%s`"%h, header)
		table = "`%s_%s`"%(satellite, instrument)
		columns = ",".join(header)
		placeholders = ("%s,"*len(header))[:-1]
		for r in records:
			try:
				self.cur.execute("insert into " + table + " (" + columns + ") values (" + placeholders + ")", r)
			except MySQLdb.MySQLError, (errno, strerror):
				pass
				#if errno != DUPLICATE_ENTRY_ERROR:
				#	canNotInsert += str(errno) + " (" + insSmallStr + ";) " + strerror + "\n"
				#else:
				#	duplicates += 1
		return

	def filesys(self, satellite, instrument, session, header, records):
		dst = os.path.join(self.path, satellite, instrument, "L1", session + ".xt")
		file = open(dst, "w")
		file.write("\t".join(header) + "\n")
		for r in records:
			r = map(lambda entry : str(entry), r)
			file.write("\t".join(r) + "\n")
		file.close()
		return
