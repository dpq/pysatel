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

def desc():
    """Return basic information on the spacecraft described by this SPM.
    Must return a dict with the following keys:\
    * id
    * name
    * instruments
    
    id is the NORAD ID of this spacecraft. \
    See http://www.celestrak.com/satcat/search.asp for details.
    
    name is the human-readable form of the name of the spacecraft. \
    Can only contain alphanumeric characters, underscores and dashes.
    
    instruments is a dict with instrument names as keys and \
    tuples of their channel names as values. Example:
    res["instruments"]["instr1"] = ("channel1", "channel2", "channel3")

    """
    res = {}
    res["id"] = 0
    res["name"] = ""
    res["instruments"] = {}
    return res


def fetchtelemetry(dst):
    """Download and save telemetry files for every instrument \
    separately to dst/instrument/L0/unique_session_file_name.
    Must return a dict object with instrument names as keys and \
    lists of session file paths as values.
    
    Example:
    newfileslist1 = downloadnewfiles("instrument1")
    newfileslist2 = downloadnewfiles("instrument2")
    
    # newfileslist looks like ["absolute_filepath1", "absolute_filepath2"]
    res["instrument1"] = newfileslist1
    res["instrument2"] = newfileslist2
    return res

    """
    res = {}
    return res


def importtelemetry(src, dst):
    """Import telemetry files for every involved instrument from \
    the specified local filesystem path to \
    dst/instrument/L0/unique_session_file_name, and return a dict \
    with instrument names as keys and lists of session file paths \
    as values.
    
    Example:
    res["instrument1"] = ["absolute_filepath1", "absolute_filepath2"]
    return res
    """
    res = {}
    return res


def parse(instrument, path):
    """Feed the file at the specified absolute path to the \
    instrument-specific parser function.
    You are free to implement parser methods however \
    you need, but the parse() function must return the result \
    as follows:
    
    return sessionId, data
    
    * data is a dict mapping datetimes to tuples of channel \
    values, i.e. \
    {datetime: (channel1_value, channel2_value, channel3_value)}
    * sessionId is a unique session identifier (string)

    """
    sessionid = ""
    data = {}
    return sessionid, data
