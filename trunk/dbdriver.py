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

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, MetaData, Index
from sqlalchemy.types import DateTime, Integer


class Driver:
    def __init__(self, dialect, args, driver=""): # params is a dict
        if driver != "":
            dialect = "%s+%s" % (dialect, driver)
        self.engine = create_engine("%s://%s:%s@%s:%s/%s" % (dialect, \
            args["user"], args["passwd"], args["host"], args["port"], \
            args["db"]), pool_recycle = 3600)
        self.meta = MetaData()
        self.meta.bind = self.engine
    
    
    def __del__(self):
        del self.meta
        del self.engine
    
    
    def createtable(self, tablename, cols):
        """Create a new instrument table"""
        columns = [
            Column("dt_record", DateTime, nullable=False, primary_key=True), \
            Column("microsec", Integer, default=0, primary_key=True)]
        for col in cols:
            columns.append(Column(col, Integer, default=None))
        tbl = Table(tablename, self.meta, *columns)
        tbl.create()
        i = Index('%s_index' % tablename, tbl.c.dt_record)
        i.create()
    
    
    def droptable(self, tablename):
        """Drop a table"""
        tbl = Table(tablename, self.meta, autoload=True)
        tbl.drop()
    
    
    #def insert(self, table, header, valueslists):
        #if len(valueslists) == 0:
            #print "KAKOGO??? Valueslists is empty :("
        #return
        #if self.type == "oracle":
        #columns = ",".join(map(lambda h : '"%s"'%h, header))
        #placeholders = ",".join(map(lambda i : ":" + str(i+1), range(len(header))))
        #request = 'INSERT INTO smdc."%s"('%table + columns + ') VALUES (to_date(:1, \'yyyy-mm-dd hh24:mi:ss\'),' + placeholders[3:] + ')'
        #self.cursor.prepare(request)
        #try:
            #self.cursor.executemany(None, valueslists)
            #self.conn.commit()
        #except cx_Oracle.Error, strerror:
            #print strerror[:-1]
        #elif self.type == "mysql":
        #columns = ",".join(header)
        #placeholders = ("%s,"*len(header))[:-1]
        #trying = 0
        #try:
            #maxRows = self.maxAllowedPacked / len(" ".join(map(lambda v : str(v), valueslists[0]))) / 2
            #i = 0
            #while i < len(valueslists):
            #self.cursor.executemany("insert into `" + table + "` ("+columns+") values ("+placeholders+")", valueslists[i:i+maxRows])
            #i += maxRows
        #except MySQLError, strerror:
            #print "MySQLError :", strerror, "trying ..."
            #trying = 1
        #if trying:
            #print "Trying row by row... (", len(valueslists), ") rows" 
            #for i in range(len(valueslists)):
            #try:
                #self.cursor.execute(("insert into `" + table + "` ("+columns+") values ("+placeholders+");")%valueslists[i])
            #except MySQLError, strerror:
                #print "MySQLError :", strerror
            #except:
                #pass
        #return 0

