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
import os
import imp
import pysatel
import pysatel.export
import pysatel.coord
from pysatel import telemetry

# Read the config file and create the exporter
import ConfigParser
config = ConfigParser.SafeConfigParser()
config.read(os.path.join("/etc/pysatel.conf"))
e = pysatel.export.export(config.get("Main", "ArchivePath"))

def Module(satellite):
	globals()["telemetry.%s"%satellite] = imp.load_source(satellite, os.path.join(os.path.dirname(pysatel.__file__), "telemetry", "%s.py"%satellite))
	module = globals()["telemetry.%s"%satellite]
	return module

def totalFileLists(satellite, level = 0):
	module = Module(satellite)
	instruments = module.desc()["instruments"]
	result = {}
	for i in instruments:
		if len(instruments[i]) != 0:
			pathToInstr = os.path.join(config.get("Main", "ArchivePath"), satellite, i, "L" + str(level))
			result[i] = map(lambda f : os.path.join(pathToInstr, f), os.listdir(pathToInstr))
	return result

mode = "fetch"
files = None
res = [] # not result but resource :)

from sys import argv
if len(argv) > 1:
	satellite = argv[1]
	res = [satellite]
else:
	# Compose the list of satellites that must be processed
	for x in os.listdir(os.path.join(os.path.dirname(pysatel.__file__), "telemetry")):
		if x.endswith(".py") and x != "__init__.py":
			res.append(".".join(x.split(".")[:-1]))
if len(argv) > 2:
	if argv[2] in ["processBinary", "L0"]:
		mode = "processBinary"
	elif argv[2] in ["saveToDatabase", "L1"]:
		mode = "saveToDatabase"
 	else:
		pathToBinFiles = argv[2]
		mode = "replenish"
if len(argv) > 3:
	print "len(argv) > 3? \nDO IT YOURSELF :)\n"
#	files = map(lambda f : os.path.abspath(f), argv[3:])

# Parse every instrument of every satellite, append coordinates and write the resulting output to filesystem and MySQL database
for satellite in res:
	module = Module(satellite)
	satelliteName = module.desc()["name"]
	#######################################################
	print "Step 0: getting paths to files of", satellite
	#######################################################
	if mode == "fetch":
		files = module.fetch(config.get("Main", "ArchivePath"))
	elif mode == "replenish":
		if files == None: files = []
		files += module.replenish(pathToBinFiles, config.get("Main", "ArchivePath"))
	elif mode == "processBinary":
		if files == None:
			files = totalFileLists(satellite, level = 0)
	if mode == "saveToDatabase":
		instruments = []
		map(lambda i: instruments.append(i) if len(module.desc()["instruments"][i]) > 0 else None, module.desc()["instruments"].keys())
	else:
		instruments = files.keys()

	for instrumentName in instruments:
		if mode == "saveToDatabase":
			path = os.path.join(config.get("Main", "ArchivePath"), satelliteName, instrumentName, "L1")
			files = { instrumentName : map(lambda f : os.path.join(path, f), os.listdir(path)) }
		for f in files[instrumentName]:

			final = []
			header = ("dt_record",) + module.desc()["instruments"][instrumentName] + pysatel.coord.header()
			if mode != "saveToDatabase":

				###############################################
				print "Step 1: Parsing file", f
				###############################################
				sessionId, data = module.parse(instrumentName, f)

				###############################################
				print "Step 2: calculating coordinates"
				###############################################
				result = dict(map(lambda dt, measurement, coordinate : [dt.strftime("%Y-%m-%d %H:%M:%S"), measurement + coordinate], data.keys(), data.values(), pysatel.coord.coord(module.desc()["id"], data.keys())))
				for k in sorted(result.keys()):
					final.append((k,) + tuple(map(lambda s : str(s) if s != None else s, result[k])))

				###############################################
				print "Step 3: saving to text file ..."
				###############################################
				e.filesys(satelliteName, instrumentName, sessionId, header, result)

			else:
				sessionId = f.split("/")[-1].split(".")[0]
				f = open(f)
				f.readline()
				for line in f:
					final += [[line[:19].replace("T", ' ')] + map(lambda s : s if s != "None" else None, tuple(line[21:].split()))]
				f.close()

			###############################################
			print "Step 4: saving to databases ..."
			###############################################
			e.database(satelliteName, instrumentName, sessionId, header, final)
