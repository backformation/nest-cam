#!/usr/bin/env python3

import json
import datetime
import pathlib


path_CamConfig  = pathlib.Path('/tmp/my-cam.json')     # The config file for the camera service
path_Media      = pathlib.Path('/media/Camera')        # The directory where we store video files.
path_IsStarted  = pathlib.Path('/tmp/Cam-IsStarted')   # exists when the service is running
path_IsPausing  = pathlib.Path('/tmp/Cam-IsPausing')   # written by the controller to pause recording
path_IsPaused   = pathlib.Path('/tmp/Cam-IsPaused')    # exists when recording is paused
path_Recording  = pathlib.Path('/tmp/Cam-IsRecording') # exists when the service is writing an MP4
path_GpsStatus  = pathlib.Path('/tmp/GPS-Status')      # written by the GPS service to report its status

class Config :
	def __init__(self) :
		# The default start and stop time allow 7 hours either side of
		# the solar noon at Upington (which is 12:30 +/- 10 minutes).
		self.flip = False
		self.start = datetime.time(hour=5, minute=30)
		self.stop  = datetime.time(hour=19, minute=30)
		self.bitrate = 5000000
	def load(self) :
		try :
			with open(path_CamConfig, 'r') as file:
				data = json.load(file)
				try :
					self.flip = data["flip"]
				except :
					pass
				try :
					self.start = datetime.time.fromisoformat(data["start"])
				except :
					pass
				try :
					self.stop  = datetime.time.fromisoformat(data["stop"])
				except :
					pass
				try :
					self.bitrate = data["bitrate"]
				except :
					pass
		except :
			pass
	def save(self) :
		data = {
			'flip'  : self.flip,
			'start' : self.start.isoformat(timespec='minutes'),
			'stop'  : self.stop.isoformat(timespec='minutes'),
			'bitrate' : self.bitrate
		}
		with open(path_CamConfig, 'w') as file:
			json.dump(data,file, indent=1)

if __name__ == '__main__' :
	# Do nothing
	pass