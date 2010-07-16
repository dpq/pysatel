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
from datetime import datetime, timedelta
import ConfigParser
from optparse import OptionParser

import pysatel
from pysatel import coord, sqldriver, hdfdriver


def Module(spacecraft):
    # TODO Check if the file exists and can be loaded
    globals()["telemetry.%s" % spacecraft] = imp.load_source(spacecraft,
        os.path.join(os.path.dirname(pysatel.__file__),
        "telemetry", "%s.py" % spacecraft))
    module = globals()["telemetry.%s" % spacecraft]
    return module


def allfiles(spacecraft, level=0):
    module = Module(spacecraft)
    instruments = module.desc()["instruments"]
    result = {}
    for i in instruments:
        if len(instruments[i]) != 0:
            path = os.path.join(config.get("Main", "ArchivePath"), spacecraft,
            i, "L" + str(level))
            result[i] = (os.path.join(path, f) for f in os.listdir(path))
    return result


if __name__ == "__main__":
    config = ConfigParser.SafeConfigParser()
    config.read("/etc/pysatel.conf")

    resource = []

    parser = OptionParser()
    parser.add_option("-m", "--mode", type="string",
        dest="mode", default="fetch")
    parser.add_option("-s", "--spacecraft", type="string",
        dest="spacecraft", default="")
    parser.add_option("-p", "--path", type="string", dest="path", default="")

    (options, args) = parser.parse_args()

    if options.mode == "import":
        if options.path == "":
            exit()
        # TODO Add support for importing a single file
        if os.path.isdir(options.path):
            pass
        else:
            exit()
    elif options.mode in ["fetch", "parse"]:
        # TODO Add support for specifying a single instrument onboard
        if options.spacecraft == "":
            for x in os.listdir(os.path.join(
                os.path.dirname(pysatel.__file__), "telemetry")):
                if x.endswith(".py") and x != "__init__.py":
                    resource.append(x.rstrip(".py"))
        else:
            resource.append(options.spacecraft)

    hdf = hdfdriver.HDFDriver(config.get("Main", "ArchivePath"))
    connections = config.get("Database", "connections").\
    replace(" ", "").replace("\t", "").split(",")
    sql = []
    for conn in connections:
        try:
            sql.append(sqldriver.SQLDriver(config.get(conn, "DatabaseType"), {
            "host": config.get(conn, "Host"),
            "db": config.get(conn, "Database"),
            "user": config.get(conn, "User"),
            "passwd": config.get(conn, "Password"),
            "tns": config.get(conn, "TnsName")}))
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError,
            ConfigParser.MissingSectionHeaderError, ConfigParser.ParsingError):
            print "[E] Missing or malformed configuration file"
            exit()

    # Parse every instrument of every spacecraft, append coordinates and write
    # the resulting output to filesystem and MySQL database
    for spacecraft in resource:
        module = Module(spacecraft)
        satellitename = module.desc()["name"]
        if options.mode == "fetch":
            files = module.fetchtelemetry(config.get("Main", "ArchivePath"))
        elif options.mode == "import":
            files = module.importtelemetry(options.path,
                config.get("Main", "ArchivePath"))
        elif options.mode == "parse":
            files = allfiles(spacecraft, 0)

        instruments = files.keys()
        if len(instruments) == 0:
            print datetime.now().strftime("%d %b, %Y %H:%M:%S"), \
                "No new telemetry from %s." % spacecraft

        for instrumentname in instruments:
            for f in files[instrumentname]:
                print "Processing ", f
                header = ("dt_record", "microsec") + \
                    tuple(module.desc()["instruments"][instrumentname]) + \
                    coord.header()
                sessionid, data = module.parse(instrumentname, f)
                if len(data) == 0:
                    print "No records; skipped."
                    continue

                coordinates = coord.coord(module.desc()["id"], data.keys())
                result = []
                for dt in sorted(data.keys()):
                    res = (dt - timedelta(microseconds = dt.microsecond),
                        dt.microsecond) + data[dt] + coordinates[dt]
                    result.append(res)

                for db in sql:
                    db.insert(header, result, satellitename, instrumentname,
                        sessionid)
                hdf.insert(header, result, satellitename, instrumentname,
                    sessionid)