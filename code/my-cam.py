#!/usr/bin/env python3

import os
import sys
import time
import datetime
import pathlib
import signal
import subprocess

# Our own shared definitions
from shared import *


class Service :
	def __init__(self) :
		# Our configuration
		self.cfg = Config()
		self.cfg.load()
		# Control of recording.
		self.sec_Recording = 300 # each recording segment is 5 minutes long
		self.pid_Recording = 0
		self.end_Recording = datetime.datetime.utcnow()

	# Various useful predicates

	def notPausing(self) :
		return not path_IsPausing.exists()

	def notPaused(self) :
		return not path_IsPaused.exists()

	def isDaytime(self, local_time) :
		midnight = local_time.replace(hour=0, minute=0, second=0, microsecond=0)
		delta = (local_time - midnight).total_seconds()
		start = (self.cfg.start.hour*60+self.cfg.start.minute)*60
		stop  = (self.cfg.stop.hour*60+self.cfg.stop.minute)*60
		return delta > start and delta < stop

	def startRecording(self, local_time) :
		# Calculate "end_Recording", by rounding down to the previous midnight and then
		# rounding up the total number of seconds to a multiple of the segment length.
		midnight = local_time.replace(hour=0, minute=0, second=0, microsecond=0)
		delta = (local_time - midnight).total_seconds()
		next = ((delta // self.sec_Recording)+1)*self.sec_Recording
		self.end_Recording = midnight + datetime.timedelta(seconds=next)
		# If that is, proportionately, too close to "now" then we add another segment.
		delta = (self.end_Recording - local_time).total_seconds()
		if delta < (self.sec_Recording/60):
			self.end_Recording += datetime.timedelta(seconds=self.sec_Recording)

		# The file on the SSD: /media/Camera/2023-07-16_12-00-00.mp4
		when = local_time.strftime('%Y-%m-%d_%H-%M-%S')
		file = '{}.mp4'.format(when)
		path = path_Media.joinpath(file)

		# Kick off the capture process and remember "pid_Recording".
		proc1 = subprocess.Popen(
			[ 'raspivid',
			'--nopreview',
				'--mode', '1',
				'--inline',
				'--spstimings',
				'--flicker', 'off',
				'--annotate', '12',
				'--timeout', '0',
				'--bitrate', str(self.cfg.bitrate),
				'--framerate', '30',
				'--intra', '60',
				'--output', '-' ],
			stdout=subprocess.PIPE)
		proc2 = subprocess.Popen(
			[ 'ffmpeg',
			'-hide_banner',
				'-r', '30',
				'-i', '-',
				'-y',
				'-vcodec', 'copy', path ],
			stdin=proc1.stdout)
		proc1.stdout.close()
		self.pid_Recording = proc1.pid

		# Record whether/where we are writing, in /tmp/Cam-Recording.
		# (I suppose if we failed, we could write the last error message to this file instead.)
		if self.pid_Recording != 0:
			path_Recording.write_text(file)

	def stopRecording(self):
		if self.pid_Recording != 0:
			os.kill(self.pid_Recording, signal.SIGINT)
			os.waitpid(self.pid_Recording, 0)
			self.pid_Recording = 0
		path_Recording.unlink(missing_ok=True)

	#
	# The main service loop
	#
	def main(self):
		path_Recording.unlink(missing_ok=True)
		path_IsPaused.unlink(missing_ok=True)
		path_IsStarted.touch(exist_ok=True)
		print('Camera Service started')

		try:
			while True:
				time.sleep(1)
				if self.notPausing():
					# The controller wants us to run
					local_time = datetime.datetime.now()
					if self.isDaytime(local_time) and self.pid_Recording == 0:
						self.startRecording(local_time)
					if self.pid_Recording != 0 and local_time > self.end_Recording:
						self.stopRecording()
					path_IsPaused.unlink(missing_ok=True)
				elif self.notPaused():
					# The controller wants us to pause
					print('Camera Service pausing')
					if self.pid_Recording != 0:
						self.stopRecording()
					path_IsPaused.touch(exist_ok=True)
				else:
					# The controller wants us to remain paused
					pass
		except:
			print('Camera Service interrupted')
			if self.pid_Recording != 0:
				self.stopRecording()
			pass

		path_IsStarted.unlink(missing_ok=True)
		path_IsPaused.unlink(missing_ok=True)
		path_Recording.unlink(missing_ok=True)
		print('Camera Service stopped')
		return 0

if __name__ == '__main__':
	s = Service()
	sys.exit(s.main())
