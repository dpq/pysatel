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
import sys
from sys import argv
import os
import ConfigParser
from pysatel import coord, telemetry
from pysatel.dbdriver import Db

import imp

def help():
	print "PySatel Copyright (C) 2010 David Parunakian"
	print "This program comes with ABSOLUTELY NO WARRANTY."
	print "This is free software, and you are welcome to redistribute it"
	print "under certain conditions; see the LICENSE file for details."
	print ""
	print "=================================="
	print ""
	print "Usage:"
	print "pysatel-admin help"
	print "\tprint this message"
	print ""
	print "pysatel-admin create path/to/spm_file.py"
	print "\tinitialize everything necessary to correctly work with the suppplied SPM, assuming that it conforms to the API"
	print ""
	print "pysatel-admin delete satellite_name"
	print "\tDestroy all tables and archived data of the specified satellite. ***WARNING*** This cannot be undone!!! ***WARNING***"
	print ""
	print "pysatel-admin enable path/to/spm_file.py"
	print "\tAdd a previously disabled SPM back into the processing loop"
	print ""
	print "pysatel-admin disable satellite_name"
	print "\tTemporarily remove the SPM of the specified satellite from the processing loop. No harm is done, only a single symlink is removed. All data files are intact."
	return

class MyConfig(ConfigParser.SafeConfigParser):
	def getValue(self, section, option, raw=False, vars=None):
		try:
			result = self.get(section, option, raw, vars)
		except:
			return None
		return result

def __checkdir(dir):
	if not os.path.exists(dir):
		os.mkdir(dir)
	if not os.path.isdir(dir):
		print "Error: ", dir, " exists and is not a directory"
		return False
	return True

# TODO optimize and add error handling and recreation procedure
def create(src):
	globals()["satellite"] = imp.load_source("satellite", src)
	module = globals()["satellite"]

	satelliteName, instruments = module.desc()["name"], module.desc()["instruments"]
	config = MyConfig()
	config.read(os.path.join("/etc/pysatel.conf"))

	uid, gid = int(config.getValue("Main", "uid")), int(config.getValue("Main", "gid"))
	dst = os.path.join(config.getValue("Main", "ArchivePath"), satelliteName)
	if not __checkdir(dst):
		return
	os.chown(dst, uid, gid)

	for i in instruments.keys():
		if not __checkdir(os.path.join(dst, i)):
			continue
		os.mkdir(os.path.join(dst, i, "L0"))
		os.mkdir(os.path.join(dst, i, "L1"))
		os.mkdir(os.path.join(dst, i, "L2"))
		os.chown(os.path.join(dst, i), uid, gid)
		os.chown(os.path.join(dst, i, "L0"), uid, gid)
		os.chown(os.path.join(dst, i, "L1"), uid, gid)
		os.chown(os.path.join(dst, i, "L2"), uid, gid)

	for conn in config.getValue("Database", "connections").replace(" ", "").replace("\t", "").split(","):
		db = Db(config.getValue(conn, "DatabaseType"), {"host" : config.getValue(conn, "Host"), "db" : config.getValue(conn, "Database"), "user" : config.getValue(conn, "User"), "passwd" : config.getValue(conn, "Password"), "tns" : config.getValue(conn, "TnsName")})
		for i in instruments.keys():
			if len(instruments[i]) > 0:
				dtcols = [("dt_record" , {"type" : "datetime", "NOT" : "NULL"}), ("microsec" , {"type" : "int", "default" : "0"})]
				# dtcols = (("dt_record", {"type": "decimal(16,6)" }))
				thecols = map(lambda cl : (cl, {"type" : "float", "default" : "NULL"}), coord.header() + instruments[i])
				prikey = "dt_record"
				db.createTable(table = "%s_%s"%(satelliteName, i), cols = dict(dtcols + thecols), primarykey = prikey)

	link = os.path.join(os.path.dirname(telemetry.__file__), satelliteName + ".py")
	if not os.path.exists(link):
		os.symlink(os.path.abspath(src), link)

from shutil import rmtree

def delete(satelliteName):
	config = MyConfig()
	config.read(os.path.join("/etc/pysatel.conf"))
	dst = os.path.join(config.getValue("Main", "ArchivePath"), satelliteName)

	globals()["satellite"] = imp.load_source("satellite", os.path.join(os.path.dirname(telemetry.__file__), satelliteName + ".py"))
	instruments = []
	map(lambda i : len(globals()["satellite"].desc()["instruments"][i]) > 0 and instruments.append(i) or None, globals()["satellite"].desc()["instruments"].keys())
	tables = []
	for i in instruments:
		tables.append("%s_%s"%(satelliteName, i))

	passphrase = 'Yes, I am aware that this is a very bad idea'
	print "This action will completely erase directory %s and all files and subdirectories in it."%dst
	print "Also the following MySQL tables will be dropped: %s"%', '.join(tables)
	print "Enter '%s' and press Enter if you know what you're doing."%passphrase
	confirmation = raw_input(">")
	if confirmation != passphrase:
		print "Confirmation not received. Aborting."
		return

	if os.path.exists(dst) and os.path.isdir(dst):
		rmtree(dst)

	for conn in config.getValue("Database", "connections").replace(" ", "").replace("\t", "").split(","):
		db = Db(config.getValue(conn, "DatabaseType"), {"host" : config.getValue(conn, "Host"), "db" : config.getValue(conn, "Database"), "user" : config.getValue(conn, "User"), "passwd" : config.getValue(conn, "Password"), "tns" : config.getValue(conn, "TnsName")})
		for t in tables:
			db.dropTable(t)

	print "Done. You can start hitting your head against the wall if you didn't mean it."
	return

def activate(src):
	globals()["satellite"] = imp.load_source("satellite", src)
	module = globals()["satellite"]
	satelliteName = module.desc()["name"]

	link = os.path.join(os.path.dirname(telemetry.__file__), satelliteName + ".py")
	if not os.path.exists(link):
		os.symlink(os.path.abspath(src), link)
	else:
		print "Error: ", link, "exists."

def deactivate(satelliteName):
	link = os.path.join(os.path.dirname(telemetry.__file__), satelliteName + ".py")
	if os.path.exists(link) and os.path.islink(link):
		os.remove(link)
	else:
		print "Error: ", link, "is not a symbolic link"

from os import listdir, path

def replenish(satelliteName, src):
	res = {}
	for i in listdir(src):
		res[i] = map(lambda f : path.abspath(path.join(src, i, f)), listdir(path.join(src, i)))
	return res

if __name__ == "__main__":
	if len(argv) == 1:
		sys.exit(help())
	else:
		if argv[1] == "help":
			help()
		elif argv[1] == "create":
			create(argv[2])
		elif argv[1] == "delete":
			delete(argv[2])
		elif argv[1] == "enable":
			enable(argv[2])
		elif argv[1] == "disable":
			disable(argv[2])
