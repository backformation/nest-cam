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

	def notStopping(self) :
		return not path_IsStopping.exists()

	def isStarting(self) :
		return path_IsStarting.exists()

	def isDaytime(self, local_time) :
		# www.timeanddate.com says local time for "civil twilight" is:
		#    06:25 - 18:44 (12:20)on 1st September
		#    05:50 - 18:59 (13:09) on 1st October
		#    05:18 - 19:19 (14:01) on 1st November
		#    05:03 - 19:44 (14:41) on 1st December
		# and solar noon is +/- 10 minutes around 12:30 local time.
		# (South Africa is always UTC+2, but Upington is a little west.)
		# The simplest strategy is to record 14 hours around solar noon.
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

		# The file on the SSD: /media/Camera/camera1_2023-07-16_12-00-00.mp4
		host = os.uname().nodename
		when = local_time.strftime('%Y-%m-%d_%H-%M-%S')
		file = '{}_{}.mp4'.format(host,when)
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
		print('Camera Service starting')
		path_IsStopped.unlink(missing_ok=True)
		path_IsStarted.unlink(missing_ok=True)
		path_IsStarting.touch(exist_ok=True)

		# While starting, wait for the SSD to be mounted.
		while self.notStopping() and self.isStarting():
			# if not path_Media.is_mount():
			#	os.system('mount {}'.format(path_Media))
			path_IsStarting.replace(path_IsStarted)
			print('Camera Service started')

		# Once started, start recording to that disc.
		while self.notStopping():
			time.sleep(1)
			local_time = datetime.datetime.now()
			if self.isDaytime(local_time) and self.pid_Recording == 0:
				self.startRecording(local_time)
			if self.pid_Recording != 0 and local_time > self.end_Recording:
				self.stopRecording()

		# Stop recording and unmount the disc.
		print('Camera Service stopping')
		if self.pid_Recording != 0:
			self.stopRecording()
		# if path_Media.is_mount():
		#	os.system('umount {}'.format(path_Media))

		path_IsStarting.unlink(missing_ok=True)
		path_IsStarted.unlink(missing_ok=True)
		path_IsStopping.replace(path_IsStopped)
		print('Camera Service stopped')
		return 0

if __name__ == '__main__':
	s = Service()
	sys.exit(s.main())
