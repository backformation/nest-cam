#!/usr/bin/env python3

import os
import sys
import datetime
import pathlib
from gps import *

# Our own shared definitions
from shared import *

class Service :
	def __init__(self) :
		# Our remembered status
		self.lastmode = 0
		self.newMode = "Off?"
		self.newDate = "" # 1st time switch
		self.newText = False
		# Connect to the hardware
		try:
			self.gpsd = gps(mode=WATCH_ENABLE)
		except:
			path_GpsStatus.write_text("No GPS device found, time not set.")
			print('Error: No GPS device found, time not set.')
			sys.exit()

	def next(self) :
		self.gpsd.next()
		# gpsd is derived from gpsdata which has a "fix" property with
		# (amongst other things) the following properties:
		#   gpsd.fix.mode = 0, 1=MODE_NO_FIX, 2=MODE_2D, 3=MODE_3D
		#   gpsd.utc = None, empty string or ISO 8601 string

		if self.lastmode != self.gpsd.fix.mode :
			self.lastmode = self.gpsd.fix.mode
			if self.lastmode == 3 :
				self.newMode = "3D Fix"
			elif self.lastmode == 2 :
				self.newMode = "2D Fix"
			elif self.lastmode == 1 :
				self.newMode = "No Fix"
			else :
				self.newMode = "Off?"
			self.newText = True

		gutc = self.gpsd.utc
		if gutc != None and gutc != "" :
			# gutc is a string formatted to ISO-8601 format: "2023-07-08T23:00:00.000Z".
			# We can convert that to a time, but we have to omit the Z.
			device_time = datetime.datetime.fromisoformat(gutc[0:23])
			# That was a UTC time, so we want the system time also as UTC
			system_time = datetime.datetime.utcnow()
			# Have we drifted?
			delta = (device_time - system_time).total_seconds()
			if self.newDate=="" or abs(delta) > 5 :
				self.newDate = "{0}-{1}-{2}T{3}Z".format(gutc[0:4], gutc[5:7], gutc[8:10], gutc[11:19])
				os.system('sudo date --set="{0}"'.format(self.newDate))
				self.newDate = time.strftime("%Y-%m-%d %H:%M:%S (%z)")
				self.newText = True

		if self.newText :
			if self.newDate == "" :
				status = "No time available yet ({0})".format(self.newMode)
			else :
				status = "Last clock sync {1}".format(self.newMode, self.newDate)
			path_GpsStatus.write_text(status)
			print(status)
			self.newText = False


if __name__ == '__main__' :
	# Loop endlessly, comparing times
	s = Service()
	while True:
		s.next()
