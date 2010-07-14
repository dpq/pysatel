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
from new import classobj


def createtable(directory, spacecraft, instrument, cols):
    """Create a new instrument table"""
    h5file = tables.openFile("%s/%s.h5" % (directory, spacecraft), "w", spacecraft)
    group = h5file.createGroup("/", spacecraft, spacecraft)
    fields = { "dt_record": tables.Time32Col(), "microsec": tables.Int32Col() }
    for col in cols:
        fields[col] = tables.Float32Col()
    record = classobj('Record', (), fields)
    table = h5file.createTable(group, instrument, record, instrument)
    table.flush()
    h5file.close()


def droptable(directory, spacecraft, instrument):
    """Remove an instrument table from the spacecraft's HDF5 file."""
    h5file = tables.openFile("%s/%s.h5" % (directory, spacecraft), "w", spacecraft)
    table = h5file.getNode("/%s/%s" % (spacecraft, instrument))
    table.remove()
    h5file.close()


def insert(directory, spacecraft, instrument, columns, values):
    """Insert new measurements into the spacecraft's HDF5 file."""
    h5file = tables.openFile("%s/%s.h5" % (directory, spacecraft), "w", spacecraft)
    table = h5file.getNode("/%s/%s" % (spacecraft, instrument))
    record = table.row
    for val in values:
        for i in range(len(val)):
            record[columns[i]] = val[i]
        record.append()
    table.flush()
    h5file.close()
