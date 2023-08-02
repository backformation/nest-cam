#!/usr/bin/env python3

import json
import datetime
import pathlib


path_CamConfig  = pathlib.Path('/tmp/my-cam.json')     # The config file for the camera service
path_Media      = pathlib.Path('/media/Camera')        # The directory where we store video files.
path_IsStarting = pathlib.Path('/tmp/Cam-IsStarting')  # written by the controller to restart recording
path_IsStarted  = pathlib.Path('/tmp/Cam-IsStarted')   # written by the service when recording has begun
path_IsStopping = pathlib.Path('/tmp/Cam-IsStopping')  # written by the controller to pause recording
path_IsStopped  = pathlib.Path('/tmp/Cam-IsStopped')   # written by the service when recording has stopped
path_Recording  = pathlib.Path('/tmp/Cam-IsRecording') # the name of the mp4 we're writing to, if any
path_GpsStatus  = pathlib.Path('/tmp/GPS-Status')      # written by the GPS service to report its status

class Config :
	def __init__(self) :
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