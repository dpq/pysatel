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

import tables
import datetime
import time
from new import classobj

class HDFDriver:
    def __init__(self, directory):
        self.directory = directory

    def createtable(self, header, spacecraft, instrument, session = ""):
        """Create a new instrument table"""
        session = "" if session != "" else "_" + session
        h5file = tables.openFile("%s/%s.h5" % (self.directory, spacecraft,),
            "a", spacecraft)
        try:
            group = h5file.createGroup("/", spacecraft, spacecraft)
        except:
            group = h5file.getNode("/%s" % spacecraft)
        fields = {"dt_record": tables.Time32Col(),
            "microsec": tables.Int32Col()}
        for col in header:
            fields[col] = tables.Float32Col()
        record = classobj('Record', (tables.IsDescription,), fields)
        table = h5file.createTable(group, instrument, record, instrument)
        table.flush()
        h5file.close()
    
    
    def droptable(self, spacecraft, instrument, session = ""):
        """Remove an instrument table from the spacecraft's HDF5 file."""
        session = "" if session != "" else "_" + session
        h5file = tables.openFile("%s/%s.h5" % (self.directory, spacecraft,),
            "w", spacecraft)
        table = h5file.getNode("/%s/%s" % (spacecraft, instrument))
        table.remove()
        h5file.close()
    
    
    def insert(self, header, values, spacecraft, instrument, session = ""):
        """Insert new measurements into the spacecraft's HDF5 file."""
        session = "" if session != "" else "_" + session
        h5file = tables.openFile("%s/%s.h5" % (self.directory, spacecraft,),
            "a", spacecraft)
        table = h5file.getNode("/%s/%s" % (spacecraft, instrument))
        record = table.row
        for val in values:
            for i in range(len(val)):
                if type(val[i]).__name__ == "datetime":
                    record[header[i]] = time.mktime(val[i].timetuple())
                else:
                    record[header[i]] = val[i]
            record.append()
        table.flush()
        h5file.close()
