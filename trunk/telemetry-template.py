#!/user/bin/python

def desc():
	res = {}
	res["id"] = 0 # the NORAD ID. See http://celestrak.com/satcat/search.asp for details
	res["name"] = "" # you should know it
	res["instruments"] = {} # dictionary like: { instrumentName : tuple_Of_Channel_Names, ... }
	res["instruments"]["instr1"] = ( "channel1", "channel2", "channel3" )
	return res

def fetch(path):
	# Download and save telemetry files for every instrument separately to path/instrument/L0/unique_session_file_name
	res = {}
	res["instrument1"] = [ "absolute_filepath1", "absolute_filepath2", "absolute_filepath3" ]
	res["instrument2"] = [ "absolute_filepath4", "absolute_filepath5", "absolute_filepath6" ]
	return res

def parse(instrument, path):
	# Feed the file at the specified absolute path to the appropriate parser function, determined by instrument.
	# You are free to implement parser functions however you need, but the parse() function must return a specific type of result:
	sessionId = ""
	data = {}
	return sessionId, data
	# Here data is a dictionary of  { datetime : ( channel1_value, channel2_value, channel3_value ) }, and sessionId is a unique session identifier as a string
