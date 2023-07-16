#!/usr/bin/python

import os
import sys
import time
from gps import *


try:
	gpsd = gps(mode=WATCH_ENABLE)
except:
	print('Error: No GPS device found, time not set.')
	sys.exit()

print('Fetching the time from the GPS...', end='')
while True:
	# Wait until the next GPSD time tick
	gpsd.next()
	gutc = gpsd.utc
	# Do we have a proper fix yet?
	if gutc != None and gutc != '': # Yes!
		print('', flush=True)
		# Mangle the time string into the format required by "date"
		newdate = gutc[0:4] + gutc[5:7] + gutc[8:10] + ' ' + gutc[11:19]
		os.system('sudo date -u --set="%s"' % newdate)
		sys.exit()
	print('.', end='', flush=True)
