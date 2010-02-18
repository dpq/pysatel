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
from pysatel.dbdriver import Db
import os
DUPLICATE_ENTRY_ERROR = 1062

# Read the config file
import ConfigParser
class MyConfig(ConfigParser.SafeConfigParser):
	def getValue(self, section, option, raw=False, vars=None):
		try:
			result = self.get(section, option, raw, vars)
		except:
			return None
		return result

class export:
	def __init__(self, path):
		self.path = path
		self.config = MyConfig()
		self.config.read(os.path.join("/etc/pysatel.conf"))

	def stdout(self, satellite, instrument, session, header, records):
		for r in records:
			r = map(lambda entry : str(entry), r)
			print "\t".join(r)
		return

	def database(self, satellite, instrument, session, header, records):
		header = map(lambda h : "`%s`"%h, header)
		table = "%s_%s"%(satellite, instrument)
		columns = ",".join(header)
		placeholders = ("%s,"*len(header))[:-1]
		duplicates = {}
		for conn in self.config.getValue"Database", "connections").replace(" ", "").replace("\t", "").split(","):
			# TODO : what does config parser do if no keyword found?
			db = Db(self.config.getValueconn, "DatabaseType"), {"host" : self.config.getValueconn, "Host"), "db" : self.config.getValueconn, "Database"), "user" : self.config.getValueconn, "User"), "passwd" : self.config.getValueconn, "Password"), "tns" : self.config.getValueconn, "TnsName")})
			duplicates[conn] = db.insert(table, columns, records)
		return duplicates # dict of duplicates

	def filesys(self, satellite, instrument, session, header, records):
		dst = os.path.join(self.path, satellite, instrument, "L1", session + ".xt")
		file = open(dst, "w")
		file.write("\t".join(header) + "\n")
		for r in records:
			r = map(lambda entry : str(entry), r)
			file.write("\t".join(r) + "\n")
		file.close()
		return
