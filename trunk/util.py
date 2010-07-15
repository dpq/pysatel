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
from datetime import datetime, timedelta, tzinfo

class TZ(tzinfo): # special class to setting timezone
	def __init__(self, strtz="+0000"):
		self.offset = timedelta(seconds = (int(strtz[:3]) * 60 + int(strtz[3:]) ) * 60)

	def utcoffset(self, dt):
		return self.offset

	def dst(self, dt):
		return timedelta(0)
