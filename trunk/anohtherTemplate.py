#!/usr/bin/python

###############################################################################
#                                                                             #
# This is another template for building your own telemetry processing script. #
# As I've found during my work on writing such scripts for Meteor-M #1 and    #
# Tatyana-2 (Universitetsky), this is quite suitable template. Good luck!     #
#                                              (c) Wera Barinova, 2010        #
#                                                                             #
###############################################################################

from datetime import datetime, timedelta, tzinfo
from binascii import hexlify
from struct import unpack
from string import lower
from ftplib import FTP
from os import listdir, chdir, system, path

class TZ(tzinfo): # special class to setting timezone
	def __init__(self, strtz="+0000"):
		self.offset = timedelta(seconds = (int(strtz[:3]) * 60 + int(strtz[3:]) ) * 60)

	def utcoffset(self, dt):
		return self.offset

	def dst(self, dt):
		return timedelta(0)

# ftp parameters (for ftp fetching data if necessary)
FTPhost   = ""
FTPuser   = ""
FTPpasswd = ""
FTPdir    = "/"

class TelemetryFetcher:
	def __init__(self, thepath, remote = FTPdir):
		self.localpath = path.join(thepath, desc()["name"]) # where to put files
		self.remotepath = remote
		self.Error = None
		try:
			self.conn = FTP(FTPhost)
		except:
			statusReport("[C] Unable to connect to remote host; is %s down?"%FTPhost)
			self.Error = "Host is Down"
		try:
			self.conn.login(FTPuser, FTPpasswd)
		except:
			statusReport("[C] Unable to login to remote host; check the password for user %s"%FTPuser)
			self.Error = "Cannot Login"
		try:
			self.conn.cwd(remote)
		except:
			statusReport("[C] Remote directory not found; contact the administrator of %s."%FTPhost)
			self.Error = "Cannot CWD"

	def listNew(self):
		if self.Error != None:
			exit()
		remoteList = set([])
		self.conn.retrlines('LIST', lambda line: remoteList.add(line.split()[-1]) if line != "" else None)
		oldFiles = []
		for i in instruments:
			oldFiles += map(lambda f : f, listdir( path.join(self.localpath, i, "L0")))
		self.newFiles = []
		for rf in remoteList:
			lrf = lower(rf)
			if lrf not in oldFiles and goodNewFileName(lrf):
				self.newFiles.append(rf)
		return self.newFiles

	def sort(self, fileList):
		for f in fileList:
			lf = lower(f)
			i = ""; # calculate instrument. Binary code inside your file, filename, etc.
			np = path.join(self.localpath, i, "L0", lf) # new path to file. It should be in pysatelPath/satellitename/instrument/L0/filename
			system("mv -f %s %s"%(path.join(self.localpath, f), np))
			result[i] += [np]
		return result

	def download(self, fileList):
		files = []
		for file in fileList:
			self.conn.retrbinary('RETR %s'%file, open(path.join(self.localpath, lower(file)), 'wb').write)
			files += [path.join(self.localpath, lower(file))]
		return self.sort(files)

	def __del__(self):
		try:
			self.conn.quit()
		except:
			statusReport("[W] FTP connection wasn't closed cleanly.")

class Datarecord: # one piece of data, such as counts, flags, etc. Datetime will be stored in another place, but you can save it here too
	def __init__(self):
		self.refresh()

	def refresh(self):
		self.counts = []

instruments = {
#	"instrument" : ["hexcode", instrumentFunction, instrumentTuple(), """SOMETHING ELSE?"""],
}
instrcodes = dict(map(lambda i : (instruments[i][0], i), instruments))

class Dataframe:
	def __init__(self):
		#               checksum,      totalParse
		self.timers = [timedelta(0), timedelta(0)] # time statistics collecting
		self.errmsg = None
		self.length = 0
		self.sync = "" # right synchronisation code. Usually is known in hexadecimal view

	def parse(self, frame):
		self.data = None
		self.errmsg = None
		self.number = 0
		currsync = "" # current synchronization code. Also known as "marker"
		if self.sync != currsync:
			self.errmsg = "[E] (frame %i) : synchronization marker = %s"%(self.number, currsync)
			return # delete this line if it isn't a critical mistake
		self.instrument = "" # instrument code
		if self.instrument not in instrcodes.keys():
			self.errmsg = "[E] (frame %i) : unknown instrument '0x%s'"%(self.number, self.instrument)
			return
		self.dt = self.__parseDt(frame) # or maybe a part of frame? frame[begin:end]
		dtStart = datetime.now()
		checksum = self.__checksum(frame[:]) # [:-2] often
		storedchk = 0 # unpack(">H", frame[-2:])[0] often
		if storedchk != checksum:
			self.errmsg = "[W] (frame %i) : stored checksum [%i] not equal to calculated one [%i]"%(self.number, storedchk, checksum)
			self.timers[0] += datetime.now() - dtStart
			return
		self.timers[0] += datetime.now() - dtStart
		self.instr = instrcodes[self.instrument]
		dtStart = datetime.now()
		self.data = instruments[self.instr[0]][0](frame)
		self.timers[1] += datetime.now() - dtStart

	def __parseDt(self, data):
		dt = datetime()
		return dt

	def __checksum(self, data):
		return 0 # sum(unpack(str(len(data)) + "B", data)) # in the most simple case

	def __del__(self):
		print "Time spent (hh:mm:ss.msxxxxx)"
		print "Checksum calculating =", self.timers[0]
		print "Data Parsing calculating =", self.timers[1]

def desc():
	res = {}
	res["id"] = ""
	res["name"] = ""
	res["instruments"] = dict(map(lambda i : [i, instruments[i][1]], instruments))
	return res

def fetch(thepath):
	# Download and save telemetry files for every instrument separately to thepath/instrument/L0/uniquesessionfilename
	tf = TelemetryFetcher(thepath)
	files = tf.download(tf.listNew())
	return files
	
def replenish(binpath, thepath):
	# same as fetch but without downloading
	tf = TelemetryFetcher(thepath)
	files = []
	map(lambda fn : files.append(path.join(binpath, fn)), listdir(binpath)) # appending ALL files from binpath
	files = tf.sort(files)
	return files

class MyDict(dict): # special inheriting from the dict class to init missing keys using empty list
	def __missing__(self, key):
		return []

def parse(instrument, thepath):
	# Feed the file at the specified absolute path to the appropriate parser function, determined by instrument.
	# You are free to implement parser functions however you need, but the parse() function must return a specific type of result:
	# Here data is a dictionary of  { datetime : [ channel1_value, channel2_value, channel3_value ] }, and sessionId is a unique session id
	filename = thepath.split("/")[-1] # filename itself
	sessionId = 0 # calculate the sessionId. Maybe from filename?
	data = MyDict() # {datetime : counts, ...}
	try:
		fbin = open(thepath, 'rb')
	except:
		statusReport("[E] Cannot open " + thepath)
		return sessionId, data
	# frame by frame
	frame = Dataframe()
	TMP = fbin.read() # is file short enough to read whole of it into memory?
	fbin.close() # delete this line if file is too long and should be read part by part : TMP = fbin.read(frame.length)
	LEN = len(TMP) #  --'--,--'--,--'--
	FilePointer = 0 #  --'--,--'--,--'--
	dtStart = datetime() # starting datetime is often in filename
#	while len(TMP) == frame.length:
	while FilePointer < LEN / frame.length * frame.length:
		FilePointer += frame.length
#		frame.parse(TMP)
		frame.parse(TMP[FilePointer : FilePointer + frame.length])
		if frame.errmsg != None:
			statusReport(frame.errmsg)
		if frame.data == None:
			# TMP = fbin.read(frame.length)
			continue
		dt = datetime() # compilation of frame.dt and dtStart
		data[dt] = frame.data
		# TMP = fbin.read(frame.length)
	return sessionId, data

messages = []
def statusReport(msg):
#	global messages
#	messages += [datetime.now().strftime("%d %b, %Y %H:%M:%S") + " : " + msg]
	print datetime.now().strftime("%d %b, %Y %H:%M:%S") + " : " + msg

def report():
	global messages
	return messages[:]

###############################################################################
#                                                                             #
#  Some useful calls to test your telemetry file before upload it to pysatel  #
#  processing.                                                                #
#                                                                             #
###############################################################################


# TEST FETCHING

#fetch("fetchdir") ## uncomment to test fetching to "fetchdir" in your localdir
# OR
#replenish("binpath", "fetchdir") ## if you have some files in directory "binpath" already


# TEST PARSING (its better to redirect output to a file...)

#id, data =  parse(instrumentname, "path_plus_filename") ## try to parse the path_plus_filename as file of the instrumentname
#print "session id =", id
#print len(data.keys()), "line(s) at all"
#keys = sorted(data.keys())
#for dt in keys:
#	print dt, data.pop(dt)
