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
from sqlalchemy.types import DateTime, Integer, Float


class SQLDriver:
    """This SQLAlchemy wrapper exposes only those functions
    that are used by pysatel, and hides all database interaction
    details.

    """
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
    
    
    def createtable(self, spacecraft, instrument, cols):
        """Create a new instrument table"""
        tablename = "%s_%s" % (spacecraft, instrument)
        args = [
            Column("dt_record", DateTime, nullable=False, primary_key=True),
            Column("microsec", Integer, default=0, primary_key=True)]
        for col in cols:
            args.append(Column(col, Float, default=None))
        tbl = Table(tablename, self.meta, *args)
        tbl.create()
        i = Index('%s_index' % tablename, tbl.c.dt_record)
        i.create()
    
    
    def droptable(self, spacecraft, instrument):
        """Drop a table"""
        tablename = "%s_%s" % (spacecraft, instrument)
        tbl = Table(tablename, self.meta, autoload=True)
        tbl.drop()
    
    
    def insert(self, spacecraft, instrument, columns, values):
        """Insert new measurements into connected SQL databases."""
        tablename = "%s_%s" % (spacecraft, instrument)
        conn = self.engine.connect()
        tbl = Table(tablename, self.meta, autoload=True)
        statements = []
        for val in values:
            statements.append(dict([(columns[i], val[i])
                for i in range(len(columns))]))
        conn.execute(tbl.insert(), statements)
        conn.close()
