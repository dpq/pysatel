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
from string import lower
from ftplib import FTP, all_errors
from os import listdir, system, path


class FTPFetcher:
    """Docstr"""


    def __init__(self, localpath, args):
        """Docstr"""
        self.localpath = localpath
        self.remote = args
        self.error = None
        try:
            self.conn = FTP(self.remote["host"])
        except all_errors:
            self.error = "Host is Down"
        try:
            self.conn.login(self.remote["user"], self.remote["passwd"])
        except all_errors:
            self.error = "Cannot Login"
        try:
            self.conn.cwd(remote)
        except all_errors:
            self.error = "Cannot CWD"


    def newfiles(self):
        """Docstr"""
        if self.error != None:
            return None
        remotelist = set()
        self.conn.retrlines('LIST', lambda line:
            remotelist.add(line.split()[-1]) if line != "" else None)
        # TODO try/except here (the server could go away)
        oldlist = map(lambda f : f, listdir(path.join(self.localpath, "L0")))
        newlist = []
        for remotefile in remotelist:
            remotefile = lower(remotefile)
            if remotefile not in oldlist:
                newlist.append(remotefile)
        return newlist

    def download(self, filelist):
        """Docstr"""
        files = []
        for f in filelist:
            # TODO try/except here (the server could go away)
            self.conn.retrbinary('RETR %s' % f,
                open(path.join(self.localpath, lower(f)), 'wb').write)
            files.append(path.join(self.localpath, lower(f)))
        return self.sort(files)


    def sort(self, files):
        """Docstr"""
        result = []
        for f in files:
            newpath = path.join(self.localpath, "L0", lower(f))
            # TODO Check for newpath being writable
            system("mv -f %s %s" % (path.join(self.localpath, f), newpath))
            result.append(newpath)
        return result


    def __del__(self):
        # TODO any checks here?
        self.conn.quit()