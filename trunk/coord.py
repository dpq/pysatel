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
from datetime import datetime, timedelta
from time import mktime
import os
from math import pow
from scipy import mat, cos, sin, arctan, sqrt, degrees, radians, pi, arctan2

def cbrt(x):
	if x >= 0: 
		return pow(x, 1.0/3.0)
	else:
		return -pow(abs(x), 1.0/3.0)

# Constants defined by the World Geodetic System 1984 (WGS84)
a = 6378.137
b = 6356.7523142
esq = 6.69437999014*0.001
e1sq = 6.73949674228*0.001
f = 1/298.257223563

def geodetic2ecef(lat, lon, alt):
	lat, lon = radians(lat), radians(lon)
	xi = sqrt(1 - esq*sin(lat))
	x = (a/xi + alt)*cos(lat)*cos(lon)
	y = (a/xi + alt)*cos(lat)*sin(lon)
	z = (a/xi*(1 - esq) + alt)*sin(lat)
	return x, y, z

def enu2ecef(lat, lon, alt, n, e, d):
	x, y, z = e, n, -d
	lat, lon = radians(lat), radians(lon)
	X, Y, Z = geodetic2ecef(lat, lon, alt)
	mx = mat('[%f %f %f; %f %f %f; %f %f %f]'%(-sin(lon), -sin(lat)*cos(lon), cos(lat)*cos(lon), cos(lon), -sin(lat)*sin(lon), cos(lat)*sin(lon), 0, cos(lat), sin(lat)))
	enu = mat('[%f; %f; %f]'%(x, y, z))
	geo = mat('[%f; %f; %f]'%(X, Y, Z))
	res = mx*enu + geo
	return float(res[0]), float(res[1]), float(res[2])

# J. Zhu, "Conversion of Earth-centered Earth-fixed coordinates to geodetic coordinates," Aerospace and Electronic Systems, IEEE Transactions on, vol. 30, pp. 957-961, 1994.
def ecef2geodetic(x, y, z):
	r = sqrt(x*x + y*y)
	Esq = a*a - b*b
	F = 54*b*b*z*z
	G = r*r + (1 - esq)*z*z - esq*Esq
	C = (esq*esq*F*r*r)/(pow(G, 3))
	S = cbrt(1 + C + sqrt(C*C + 2*C))
	P = F/(3* pow((S + 1/S + 1), 2)*G*G)
	Q = sqrt(1 + 2*esq*esq*P)
	r_0 =  -(P*esq*r)/(1 + Q) + sqrt(0.5*a*a*(1 + 1.0/Q) - P*(1 - esq)*z*z/(Q*(1 + Q)) - 0.5*P*r*r)
	U = sqrt(pow((r - esq*r_0), 2) + z*z)
	V = sqrt(pow((r - esq*r_0), 2) + (1 - esq)*z*z)
	Z_0 = b*b*z/(a*V)
	h = U*(1 - b*b/(a*V))
	lat = arctan((z + e1sq*Z_0)/r)
	lon = arctan2(y, x)
	return degrees(lat), degrees(lon)

import ConfigParser

def getTle(idSatellite, dtSession):
	config = ConfigParser.SafeConfigParser()
	config.read(os.path.join("/etc/pysatel.conf"))
	tleList = sorted(os.listdir(os.path.join(config.get("Main", "TlePath"), str(idSatellite))))
	if len(tleList) == 0:
		return None
	for i in range(len(tleList)):
		dtTle = datetime.strptime(tleList[i], "%Y%m%d%H%M%S.tle")
		if dtTle > dtSession:
			return open(os.path.join(config.get("Main", "TlePath"), str(idSatellite), tleList[i - 1])).read()				# Return the latest file that came before the session
	return open(os.path.join(config.get("Main", "TlePath"), str(idSatellite), tleList[-1])).read()							# Or the last one if there isn't one

import ephem
import igrf
import cxform

def daysInYear(year):
	if (year%4 == 0 and year%100 != 0) or year%400 == 0:
		return 366
	else:
		return 365

def dddmmss2dec(lat, lon):
	lat, lon = lat.split(":"), lon.split(":")
	lat = float(lat[0]) + float(lat[1])/60 + float(lat[2])/3600
	lon = float(lon[0]) + float(lon[1])/60 + float(lon[2])/3600
	return lat, lon

# Caution: for performance considerations, we only retrieve TLE file once per coord() call, so avoid processing very long time intervals (during which the orbit may
# significantly drift) with a single call
def coord(idSatellite, dtList):
	res = []
	if len(dtList) == 0:
		return res
	tle = getTle(idSatellite, dtList[0]).split("\n")[:-1]			# [:-1] strips the trailing newline
	sat = ephem.readtle(tle[0], tle[1], tle[2])
	for dt in dtList:
		sat.compute(dt)
		lat, lon, alt = sat.sublat, sat.sublong, float(sat.elevation)/1000
		lat, lon = dddmmss2dec(str(lat), str(lon))
		if lon < 0:
			lon += 360

		year = dt.year + float(dt.strftime("%j"))/daysInYear(dt.year)
	
		# Cartesian geographic coordinates, magnetic field components, magnetic field magnitude and L-shell
		icode, l, b = igrf.lb(lat, lon, alt, year)
		bnorth, beast, bdown, b = igrf.b(lat, lon, alt, year)
		bx, by, bz = enu2ecef(lat, lon, alt, bnorth, beast, bdown)
		x, y, z = geodetic2ecef(lat, lon, alt)
		
		# Local time
		lt = dt + timedelta(hours = (float(lon)/15))
		lt = lt.hour + lt.minute/60.0 + lt.second/3600.0 + lt.microsecond/(3600000000.0)
		
		# Geomagnetic
		x, y, z = cxform.transform("GEO", "MAG", x, y, z, dt.year, dt.month, dt.day, dt.hour, dt.minute, int(round(dt.second + (dt.microsecond + 0.0)/1000)))
		mlat, mlon = ecef2geodetic(x, y, z)

		# TODO Add CGM, invariant magnetic coords, MLT. Maybe something else.
		res.append((lat, lon, alt, x, y, z, mlat, mlon, l, b, bx, by, bz, lt))
	return res


def header():
	return "lat", "lon", "alt", "x", "y", "z", "mlat", "mlon", "l", "b", "b_x", "b_y", "b_z", "lt"
