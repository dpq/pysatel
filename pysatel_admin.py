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

from os import mkdir, chown, symlink
import os
from sys import argv
import sys
import imp
from shutil import rmtree

import ConfigParser

from pysatel import coord, telemetry, dbdriver

def helpmsg():
    """Print the help message"""
    print """PySatel Copyright (C) 2010 David Parunakian
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions; see the LICENSE file for details.
    
    ==================================
    
    Usage:
    pysatel-admin help
    \tprint this message
    
    pysatel-admin create path/to/spm_file.py
    \tinitialize everything necessary to correctly work with the \
suppplied SPM, assuming that it conforms to the API
    
    pysatel-admin delete satellite_name
    \tDestroy all tables and archived data of the specified \
satellite. ***WARNING*** This cannot be undone!!! ***WARNING***
    
    pysatel-admin enable path/to/spm_file.py
    \tAdd a previously disabled SPM back into the processing loop
    
    pysatel-admin disable satellite_name
    \tTemporarily remove the SPM of the specified satellite from the\
processing loop. No harm is done, only a single symlink is removed.\
All data and code remains intact."""
    return


def __checkdir(directory):
    """Check if the specified path can be used as a writable directory."""
    if not os.path.exists(directory):
        try:
            mkdir(directory)
        except OSError, err:
            print "[E] Could not create directory", directory, \
                " (errno = %s)" % err.errno
            return False
    if not os.path.isdir(directory):
        print "[E] Directory", directory, " exists and is not a directory"
        return False
    return True


def create(src):
    """Initialize a new telemetry processing module at the specified path."""
    
    # Load the SPM (spacecraft processing module)
    # TODO Error check: cannot load/parse file
    globals()["satellite"] = imp.load_source("satellite", src)
    module = globals()["satellite"]
    
    # Read the unique satellite name and the list of instruments onboard
    # TODO Error check: no such function or dict keys
    satellitename = module.desc()["name"]
    instruments = module.desc()["instruments"]
    
    # Read the config file and determine the destination directory parameters
    try:
        config = ConfigParser.SafeConfigParser()
        config.read("/etc/pysatel.conf")
        uid = int(config.get("Main", "uid"))
        gid = int(config.get("Main", "gid"))
        dst = os.path.join(config.get("Main", "ArchivePath"), \
            satellitename)
        connections = config.get("Database", "connections").\
            replace(" ", "").replace("\t", "").split(",")
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError, \
        ConfigParser.MissingSectionHeaderError, ConfigParser.ParsingError):
        print "[E] Missing or malformed configuration file"
        return
    
    if not __checkdir(dst):
        return
    # TODO Any error checks here?
    chown(dst, uid, gid)
    
    # Create directories for raw, processed and final results
    for i in instruments.keys():
        if not __checkdir(os.path.join(dst, i)):
            continue
        chown(os.path.join(dst, i), uid, gid)
        for level in range(0, 3):
            directory = os.path.join(dst, i, "L%d" % level)
            mkdir(directory)
            chown(directory, uid, gid)
    
    # Create tables in all the required database systems
    for conn in connections:
        try:
            dbase = dbdriver.Db(config.get(conn, "DatabaseType"), {
            "host": config.get(conn, "Host"),
            "db": config.get(conn, "Database"),
            "user": config.get(conn, "User"),
            "passwd": config.get(conn, "Password"),
            "tns": config.get(conn, "TnsName")})
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError, \
            ConfigParser.MissingSectionHeaderError, ConfigParser.ParsingError):
            print "[E] Missing or malformed configuration file"
            return

        for i in instruments.keys():
            # TODO Validate instrument name (i)
            if len(instruments[i]) > 0:
                # Build the list of columns in the current table
                thecols = [(cl, {"type": "float", "default": "NULL"})
                for cl in  coord.header() + instruments[i]]
                # Data table names conform to the $SATNAME_$INSTRNAME rule
                dbase.createTable(table = "%s_%s" % (satellitename, i),
                cols = dict(thecols), primarykey = "dt_record")
    
    link = os.path.join(os.path.dirname(telemetry.__file__),
        satellitename + ".py")
    if not os.path.exists(link):
        symlink(os.path.abspath(src), link)


def delete(satellitename):
    """Purge this satellite and its all associated data from the system."""
    # Read the config file and determine the destination directory path
    config = ConfigParser.SafeConfigParser()
    config.read(os.path.join("/etc/pysatel.conf"))
    dst = os.path.join(config.get("Main", "ArchivePath"), satellitename)
    
    # Load the SPM
    # TODO Error check: what if we can't load the SPM?
    globals()["satellite"] = imp.load_source("satellite",
        os.path.join(os.path.dirname(telemetry.__file__),
        satellitename + ".py"))
    
    # Build the list of non-empty instrument channels
    instruments = [len(globals()["satellite"].desc()["instruments"][i]) > 0 and
    i or None for i in globals()["satellite"].desc()["instruments"].keys()]
    
    # Build the list of tables to destroy
    # Data table names conform to the $SATELLITENAME_$INSTRUMENTNAME rule
    tables = []
    for i in instruments:
        tables.append("%s_%s" % (satellitename, i))

    # Make sure the admin really understands the implications of his actions
    passphrase = 'Yes, I am aware that this is a very bad idea'
    print "This action will completely erase directory %s and all files and \
        subdirectories in it." % dst
    print "Also the following RDBS tables will be dropped: %s" % \
        ', '.join(tables)
    print "Enter '%s' and press Enter if you know what you're doing." % \
        passphrase
    confirmation = raw_input(">")
    if confirmation != passphrase:
        print "Confirmation not received. Aborting."
        return

    # Delete the data from the filesystem archive
    if os.path.exists(dst) and os.path.isdir(dst):
        rmtree(dst)

    # Delete the data from the RDBS
    for conn in config.get("Database", "connections").replace(" ", "").\
        replace("\t", "").split(","):
        dbase = dbdriver.Db(config.get(conn, "DatabaseType"), {
        "host": config.get(conn, "Host"),
        "db": config.get(conn, "Database"),
        "user": config.get(conn, "User"),
        "passwd": config.get(conn, "Password"),
        "tns": config.get(conn, "TnsName")
        })
        # TODO What if no such table exists or permission is denied?
        for tbl in tables:
            dbase.dropTable(tbl)

    print "Done. You can begin smashing your head against the wall if you \
        didn't mean it."
    return


def enable(src):
    """Enable a previously disabled SPM and put it back into use."""
    # TODO Error check: what if we can't load the SPM?
    globals()["satellite"] = imp.load_source("satellite", src)
    module = globals()["satellite"]
    satellitename = module.desc()["name"]

    link = os.path.join(os.path.dirname(telemetry.__file__),
    satellitename + ".py")
    if not os.path.exists(link):
        # TODO Error check: permission denied or whatever
        symlink(os.path.abspath(src), link)
    else:
        print "Error: ", link, "exists."


def disable(satellitename):
    """Disable an SPM so it isn't invoked by the processing routine."""
    link = os.path.join(os.path.dirname(telemetry.__file__),
    satellitename + ".py")
    # TODO Error check: permission denied or whatever
    if os.path.exists(link) and os.path.islink(link):
        os.remove(link)
    else:
        print "Error: ", link, "is not a symbolic link"


ACTIONS = {"create": create,
    "delete": delete,
    "enable": enable,
    "disable": disable}


if __name__ == "__main__":
    if len(argv) == 1 or argv[1] not in ACTIONS.keys() or argv[1] == "help":
        sys.exit(helpmsg())
    else:
        ACTIONS[argv[1]](argv[2])
