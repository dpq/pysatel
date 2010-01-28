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
from sys import argv
from pysatel import coord
from pysatel import export
import telemetry

# Compose the list of satellites that must be processed
res = []
for x in os.listdir(os.path.join(os.path.dirname(pysatel.__file__), "telemetry")):
	if x.endswith(".py") and x != "__init__.py":
		res.append(".".join(x.split(".")[:-1]))

# Read the config file and create the exporter
import ConfigParser
config = ConfigParser.SafeConfigParser()
config.read(os.path.join("/etc/pysatel.conf"))
e = pysatel.export.export(config.get("Main", "ArchivePath"), config.get("Main", "MysqlHost"), config.get("Main", "MysqlUser"), config.get("Main", "MysqlPassword"), config.get("Main", "MysqlDatabase"))

# Parse every instrument of every satellite, append coordinates and write the resulting output to filesystem and MySQL database
for satellite in res:
	globals()["telemetry.%s"%satellite] = imp.load_source(satellite, os.path.join(os.path.dirname(pysatel.__file__), "telemetry", "%s.py"%satellite))
	module = globals()["telemetry.%s"%satellite]
	satelliteId, satelliteName = module.desc()["id"], module.desc()["name"]
	files = module.fetch(config.get("Main", "ArchivePath"))
	for instrumentName in files.keys():
		for f in files[instrumentName]:
			sessionId, data = module.parse(instrumentName, f)
			header = module.desc()["instruments"][instrumentName]
			result = dict(map(lambda dt, measurement, coordinate : [dt.strftime("%Y-%m-%dT%H:%M:%SZ"), measurement + coordinate], data.keys(), data.values(), pysatel.coord.coord(satelliteId, data.keys())))
			header = ("dt_record",) + header + pysatel.coord.header()
			final = []
			for k in sorted(result.keys()):
				final.append((k,) + tuple(map(lambda s : str(s), result[k])))
			e.filesys(satelliteName, instrumentName, sessionId, header, final)
			e.mysql(satelliteName, instrumentName, sessionId, header, final)
