#!/usr/bin/python

import os
import sys
import datetime
from gps import *


try:
	gpsd = gps(mode=WATCH_ENABLE)
except:
	print('Error: No GPS device found, time not set.')
	sys.exit()

# Loop endlessly, comparing times
while True:
	gpsd.next()
	gutc = gpsd.utc
	if gutc != None and gutc != '': # Yes!
		# gutc is a string formatted to ISO-8601 format: "2023-07-08T23:00:00.000Z".
		# We can convert that to a time, but we have to omit the Z.
		device_time = datetime.datetime.fromisoformat(gutc[0:23])
		# That was a UTC time, so we want the system time also as UTC
		system_time = datetime.datetime.utcnow()
		# Have we drifted?
		delta = (device_time - system_time).total_seconds()
		if abs(delta) > 5: # Yes, so adjust the system time
			newdate = gutc[0:4] + gutc[5:7] + gutc[8:10] + ' ' + gutc[11:19]
			os.system('sudo date -u --set="%s"' % newdate)
