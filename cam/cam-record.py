#!/usr/bin/python

import os
import sys
import time
import datetime
import pathlib

# Various files used to control this service.
path_IsStarting = pathlib.Path('/tmp/Cam-IsStarting')
path_IsStarted  = pathlib.Path('/tmp/Cam-IsStarted')
path_IsStopping = pathlib.Path('/tmp/Cam-IsStopping')
path_IsStopped  = pathlib.Path('/tmp/Cam-IsStopped')

# The directory where our external drive is mounted.
# (We modify /etc/fstab to ensure this.)
path_External  = pathlib.Path('/media/Camera')

def NotStopping():
	return not path_IsStopping.exists()

def IsStarting():
	return path_IsStarting.exists()

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

	# Stop recording and unmount the disc.
	print('Camera Service stopping')
	if path_External.is_mount():
		os.system('umount {}'.format(path_External))

	path_IsStarting.unlink(missing_ok=True)
	path_IsStarted.unlink(missing_ok=True)
	path_IsStopping.replace(path_IsStopped)
	print('Camera Service stopped')
	return 0

if __name__ == '__main__':
	sys.exit(ServiceMain())
