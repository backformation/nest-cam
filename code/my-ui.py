#!/usr/bin/env python3

import os
import time
import pathlib
import datetime
import json
import curses
from curses import wrapper

# Our own shared definitions
from shared import *

# Which "child window" has the focus?
ID_NONE = 0
ID_PAWS = 1
ID_FLIP = 2
ID_DAWN = 3
ID_DUSK = 4
ID_BITS = 5
ID_LAST = 5

def tweakTime(t, key) :
	day = datetime.date.today()
	when = datetime.datetime.combine(day, t)
	if key==curses.KEY_LEFT or key==curses.KEY_UP :
		# move "when" earlier, but not before 00:00
		when -= datetime.timedelta(minutes=15)
		if when.date() != day :
			when += datetime.timedelta(minutes=15)
	if key==curses.KEY_RIGHT or key==curses.KEY_DOWN :
		# move "when" later, but not after 23:59
		when += datetime.timedelta(minutes=15)
		if when.date() != day :
			when -= datetime.timedelta(minutes=15)
	t = when.time()
	return t

class Window :
	def __init__(self, screen) :
		self.isClosing = False
		self.focus = ID_NONE
		self.window = screen
		(self.height,self.width) = self.window.getmaxyx()
		self.cfg = Config()
		self.cfg.load()
		self.cfg.save()
		self.draw()

	def drawRow(self, text, row) :
		if row <= self.height-2 :
			self.window.redrawln(row, 1)
			self.window.addstr(row, 3, text)

	def drawTitle(self) :
		text = "Babbler-Cam Control".center(self.width-2)
		self.window.addstr(0,1,text,curses.A_REVERSE)

	def drawStatus(self) :
		if self.focus==ID_BITS :
			text = "Use arrow keys (up/down) to change the quality."
		elif self.focus==ID_DUSK :
			text = "Use arrow keys (up/down) to change the stop time."
		elif self.focus==ID_DAWN :
			text = "Use arrow keys (up/down) to change the start time."
		elif self.focus==ID_FLIP :
			text = "Press SPACE or ENTER to flip the camera image."
		elif self.focus==ID_PAWS :
			text = "Press SPACE or ENTER to pause or resume recording."
		else :
			text = "Press 'x' to exit, 'TAB' to move around."
		self.window.addstr(self.height-2,1,text.ljust(self.width-2))

	def drawGPS(self, row) :
		try :
			text = "GPS:  " + path_GpsStatus.read_text()
		except :
			text = "GPS:  The service is not running, which is bad."
		self.drawRow(text, row)
		text = "      Current time is {0}".format( time.strftime("%Y-%m-%d %H:%M:%S (%z)") )
		self.drawRow(text, row+1)
		return 2 # two rows of text

	def drawCamera(self, row) :
		t0 = self.cfg.start.strftime("%H:%M")
		t1 = self.cfg.stop.strftime("%H:%M")
		#
		if path_IsStarted.exists() :
			if path_IsPaused.exists() :
				text = "Cam:  Paused."
			elif path_IsPausing.exists() :
				text = "Cam:  Pausing, please wait."
			elif path_Recording.exists() :
				mp4 = path_Recording.read_text()
				text = "Cam:  Running, recording " + mp4
			else :
				text = "Cam:  Running, but not recording."
		else :
			text = "Cam:  Missing, which is bad."
		self.drawRow(text, row)
		if self.focus==ID_PAWS :
			self.window.chgat(row, 9, 7, curses.A_REVERSE)
		#
		text = "      Flip image:    [{0}]".format("yes" if self.cfg.flip else "no")
		self.drawRow(text, row+1)
		if self.focus==ID_FLIP :
			self.window.chgat(row+1, 25, 3 if self.cfg.flip else 2, curses.A_REVERSE)
		#
		text = "      Morning start: [{0}]".format(t0)
		self.drawRow(text, row+2)
		if self.focus==ID_DAWN :
			self.window.chgat(row+2, 25, 5, curses.A_REVERSE)
		#
		text = "      Evening stop:  [{0}]".format(t1)
		self.drawRow(text, row+3)
		if self.focus==ID_DUSK :
			self.window.chgat(row+3, 25, 5, curses.A_REVERSE)
		#
		text = "      Quality:       [{0:.1f}] Mbit/s".format(self.cfg.bitrate/1000000)
		self.drawRow(text, row+4)
		if self.focus==ID_BITS :
			self.window.chgat(row+4, 25, 3, curses.A_REVERSE)
		perHour = (self.cfg.bitrate*3600)/(8*1024*1024*1024)
		text = "                   = {0:.2f} GB/hour".format(perHour)
		self.drawRow(text, row+5)
		day = (self.cfg.stop.hour - self.cfg.start.hour)*3600 + (self.cfg.stop.minute - self.cfg.start.minute)*60
		perDay = (self.cfg.bitrate*day)/(8*1024*1024*1024)
		text = "                   = {0:.1f} GB for the day {1}-{2}".format(perDay,t0,t1)
		self.drawRow(text, row+6)
		return 7

	def drawDisc(self, row) :
		# Disc contents
		stat = os.statvfs(path_Media)
		pcUsed = 100 * (1-stat.f_bfree/stat.f_blocks)
		gbFree = (stat.f_bfree * stat.f_frsize) / (1024*1024*1024)
		text = "Disc: {0:.0f}% full, {1:.1f} GB free".format(pcUsed, gbFree )
		self.drawRow(text, row)
		# Directory contents
		nFiles = 0
		for file in path_Media.glob("*.mp4"):
			if file.is_file() :
				nFiles += 1
		nMinutes = nFiles * 5
		text = "      {0} hours {1} minutes stored".format(nMinutes // 60, nMinutes % 60)
		self.drawRow(text, row+1)
		return 2

	def draw(self) :
		self.window.clear()
		self.window.box()
		self.drawTitle()
		row = 2
		row += 1 + self.drawGPS(row)
		row += 1 + self.drawCamera(row)
		row += 1 + self.drawDisc(row)
		self.drawStatus()
		self.window.refresh()

	def onInput(self, key) :
		if key==ord('x') or key==ord('X') :
			self.isClosing = True
			return
		isChanged = False
		if key==9 : # TAB
			self.focus += 1
			if self.focus > ID_LAST :
				self.focus = ID_NONE
		elif self.focus==ID_PAWS :
			if key==curses.KEY_ENTER or key==10 or key==13 or key==32 :
				if path_IsPausing.exists():
					path_IsPausing.unlink(missing_ok=True)
				else:
					path_IsPausing.touch(exist_ok=True)
		elif self.focus==ID_FLIP :
			flip = self.cfg.flip
			if key==curses.KEY_ENTER or key==10 or key==13 or key==32 :
				flip = not flip
			if self.cfg.flip != flip :
				self.cfg.flip = flip
				isChanged = True
		elif self.focus==ID_DAWN :
			dawn = self.cfg.start
			dawn = tweakTime(dawn, key)
			if self.cfg.start != dawn :
				self.cfg.start = dawn
				isChanged = True
		elif self.focus==ID_DUSK :
			dusk = self.cfg.stop
			dusk = tweakTime(dusk, key)
			if self.cfg.stop != dusk :
				self.cfg.stop = dusk
				isChanged = True
		elif self.focus==ID_BITS :
			rate = self.cfg.bitrate
			if key==curses.KEY_LEFT or key==curses.KEY_UP :
				# lower the bitrate, but not below 1 Mbit/s
				if rate >= 1100000 :
					rate -= 100000
			if key==curses.KEY_RIGHT or key==curses.KEY_DOWN :
				# raise the bitrate, but not above 10 Mbit/s
				if rate <= 9800000 :
					rate += 100000
			if self.cfg.bitrate != rate :
				self.cfg.bitrate = rate
				isChanged = True
		# If configuration parameters changed, we update the JSON
		if isChanged :
			self.cfg.save()
		# It's always harmless to re-draw
		self.draw()

	def onTimer(self, t) :
		if int(t) % 5 == 0 :
			self.draw()
		else :
			self.drawGPS(2)

def main(stdscr) :
	# Initial sanity check
	(height,width) = stdscr.getmaxyx()
	if height<18 or width<60 :
		return -1
	# Hide the cursor
	curses.curs_set(0)
	# Set the input timeout to 1s
	curses.halfdelay(10)
	# Set the epoch
	started = time.monotonic()
	# Create our main window
	w = Window(stdscr)
	# Message loop
	while not w.isClosing :
		key = stdscr.getch()
		if key == curses.ERR :
			tick = time.monotonic()-started
			w.onTimer(tick)
		elif key == curses.KEY_RESIZE :
			(w.height,w.width) = w.window.getmaxyx()
			w.draw()
		else :
			w.onInput(key)
	return 0

if __name__ == '__main__' :
	ret = wrapper(main)
	if ret < 0 :
		print("The terminal window is too small.")
		print("It needs to be at least 18 rows and 60 columns or else this user interface won't fit.")
