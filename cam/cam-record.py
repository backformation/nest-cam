#!/usr/bin/python

import os
import sys
import time
import datetime
import pathlib
import signal
import subprocess

#
# The directory where our external drive is mounted.
# (We modify /etc/fstab to ensure this.)
#
path_External  = pathlib.Path('/media/Camera')

#
# Control of this service.
#
path_IsStarting = pathlib.Path('/tmp/Cam-IsStarting')
path_IsStarted  = pathlib.Path('/tmp/Cam-IsStarted')
path_IsStopping = pathlib.Path('/tmp/Cam-IsStopping')
path_IsStopped  = pathlib.Path('/tmp/Cam-IsStopped')

def NotStopping():
	return not path_IsStopping.exists()

def IsStarting():
	return path_IsStarting.exists()

#
# Control of recording.
#
sec_Recording = 300 # each recording segment is 5 minutes long
pid_Recording = 0
end_Recording = datetime.datetime.utcnow()
tmp_Recording = pathlib.Path('/tmp/Cam-IsRecording') # the name of the mp4 we're writing to, if any

def DuringDaytime(system_time):
	return True

def StartRecording(system_time):
	global pid_Recording
	global end_Recording
	global tmp_Recording

	# Calculate "end_Recording", by rounding down to the previous midnight and then
	# rounding up the total number of seconds to a multiple of the segment length.
	midnight = system_time.replace(hour=0, minute=0, second=0, microsecond=0)
	delta = (system_time - midnight).total_seconds()
	next = ((delta // sec_Recording)+1)*sec_Recording
	end_Recording = midnight + datetime.timedelta(seconds=next)
	# If that is, proportionately, too close to "now" then we add another segment.
	delta = (end_Recording - system_time).total_seconds()
	if delta < (sec_Recording/60):
		end_Recording += datetime.timedelta(seconds=sec_Recording)

	# The file on the SSD: /media/Camera/camera1_2023-07-16_12-00-00.mp4
	host = os.uname().nodename
	when = system_time.strftime('%Y-%m-%d_%H-%M-%S')
	file = '{}_{}.mp4'.format(host,when)
	path = path_External.joinpath(file)

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
			'--bitrate', '5000000',
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
	pid_Recording = proc1.pid

	# Record whether/where we are writing, in /tmp/Cam-Recording.
	# (I suppose if we failed, we could write the last error message to this file instead.)
	if pid_Recording != 0:
		tmp_Recording.write_text(file)

def StopRecording():
	global pid_Recording
	global tmp_Recording

	if pid_Recording != 0:
		os.kill(pid_Recording, signal.SIGINT)
		os.waitpid(pid_Recording, 0)
		pid_Recording = 0
	tmp_Recording.unlink(missing_ok=True)
	pass

#
# The camera service
#
def ServiceMain():
	print('Camera Service starting')
	path_IsStopped.unlink(missing_ok=True)
	path_IsStarted.unlink(missing_ok=True)
	path_IsStarting.touch(exist_ok=True)

	# While starting, wait for the SSD to be mounted.
	while NotStopping() and IsStarting():
		if not path_External.is_mount():
			os.system('mount {}'.format(path_External))
		path_IsStarting.replace(path_IsStarted)
		print('Camera Service started')

	# Once started, start recording to that disc.
	while NotStopping():
		time.sleep(1)
		system_time = datetime.datetime.utcnow()
		if DuringDaytime(system_time) and pid_Recording == 0:
			StartRecording(system_time)
		if pid_Recording != 0 and system_time > end_Recording:
			StopRecording()

	# Stop recording and unmount the disc.
	print('Camera Service stopping')
	if pid_Recording != 0:
		StopRecording()
	if path_External.is_mount():
		os.system('umount {}'.format(path_External))

	path_IsStarting.unlink(missing_ok=True)
	path_IsStarted.unlink(missing_ok=True)
	path_IsStopping.replace(path_IsStopped)
	print('Camera Service stopped')
	return 0

if __name__ == '__main__':
	sys.exit(ServiceMain())
