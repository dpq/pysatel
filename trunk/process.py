#!/usr/bin/python
"""PySatel - a Python framework for automated processing of scientific data
   acquired from spacecraft instruments.
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
from datetime import datetime
import ConfigParser
from sys import argv

from pysatel import coord, telemetry, sqldriver, hdfdriver

config = ConfigParser.SafeConfigParser()
config.read(os.path.join("/etc/pysatel.conf"))

def Module(spacecraft):
    # TODO Check if the file exists and can be loaded
    globals()["telemetry.%s" % spacecraft] = imp.load_source(spacecraft,
        os.path.join(os.path.dirname(pysatel.__file__),
        "telemetry", "%s.py" % spacecraft))
    module = globals()["telemetry.%s" % spacecraft]
    return module


def allfiles(spacecraft, level = 0):
    module = Module(spacecraft)
    instruments = module.desc()["instruments"]
    result = {}
    for i in instruments:
        if len(instruments[i]) != 0:
            path = os.path.join(config.get("Main", "ArchivePath"), spacecraft,
            i, "L" + str(level))
            result[i] = (os.path.join(path, f) for f in os.listdir(path))
    return result


mode = "fetch"
files = None
res = [] # not result but resource :)

if len(argv) > 1:
	spacecraft = argv[1]
	res = [spacecraft]
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

# Parse every instrument of every spacecraft, append coordinates and write the resulting output to filesystem and MySQL database
for spacecraft in res:
	module = Module(spacecraft)
	satelliteName = module.desc()["name"]
	#######################################################
	print "Step 0: getting paths to files of", spacecraft
	#######################################################
	if mode == "fetch":
		files = module.fetch(config.get("Main", "ArchivePath"))
	elif mode == "replenish":
		files = module.replenish(pathToBinFiles, config.get("Main", "ArchivePath"))
	elif mode == "processBinary":
		if files == None:
			files = allfiles(spacecraft, level = 0)
	if mode == "saveToDatabase":
		instruments = []
		map(lambda i: instruments.append(i) if len(module.desc()["instruments"][i]) > 0 else None, module.desc()["instruments"].keys())
	else:
		instruments = files.keys()

	if len(instruments) == 0:
		print datetime.now().strftime("%d %b, %Y %H:%M:%S"), "No new telemetry from " + spacecraft
	for instrumentName in instruments:
		dtStart = datetime.now()
		if mode == "saveToDatabase":
			path = os.path.join(config.get("Main", "ArchivePath"), satelliteName, instrumentName, "L1")
			files = { instrumentName : map(lambda f : os.path.join(path, f), os.listdir(path)) }
		for f in files[instrumentName]:
			print "Processing ", f
			final = []
			header = ("dt_record",) + tuple(module.desc()["instruments"][instrumentName]) + pysatel.coord.header()
			if mode != "saveToDatabase":

				###############################################
				print "\nStep 1: Parsing file"
				###############################################
				sessionId, data = module.parse(instrumentName, f)
				if len(data) == 0:
					print "No records; skipped."
					continue

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
		print "Time spent :", datetime.now() - dtStart
