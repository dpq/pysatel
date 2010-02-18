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
import pysatel
import pysatel.export
import pysatel.coord
from pysatel import telemetry

# Read the config file and create the exporter
import ConfigParser
config = ConfigParser.SafeConfigParser()
config.read(os.path.join("/etc/pysatel.conf"))
e = pysatel.export.export(config.get("Main", "ArchivePath"))

from pysatel.process import processAll

if len(argv) < 3:
	print "Please, specify: ./replenish.py satellite_name the/path/to/its/files"
	exit()

satellite = argv[1]
binpath = argv[2]
#try:
	# Parse every instrument of the satellite, append coordinates and write the resulting output to filesystem and MySQL database
globals()["telemetry.%s"%satellite] = imp.load_source(satellite, os.path.join(os.path.dirname(pysatel.__file__), "telemetry", "%s.py"%satellite))
module = globals()["telemetry.%s"%satellite]
files = module.replenish(binpath, config.get("Main", "ArchivePath"))
processAll(module, files)
#except:
#	print "Cannot replenish " + satellite