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
		self.focus = 0
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
		if self.focus==4 :
			text = "Use arrow keys (up/down) to change the quality."
		elif self.focus==3 :
			text = "Use arrow keys (up/down) to change the stop time."
		elif self.focus==2 :
			text = "Use arrow keys (up/down) to change the start time."
		elif self.focus==1 :
			text = "Press SPACE or ENTER to flip the camera image"
		else :
			text = "Press 'x' to exit, 'p' to pause, 'TAB' to move around"
		self.window.addstr(self.height-2,1,text.ljust(self.width-2))

	def drawGPS(self, row) :
		try :
			text = "GPS:  " + path_GpsStatus.read_text()
		except :
			text = "GPS:  The service is not running, which is bad."
		self.drawRow(text, row)
		text = "      Current local time is {0}".format( time.strftime("%H:%M:%S") )
		self.drawRow(text, row+1)
		return 2 # two rows of text

	def drawCamera(self, row) :
		text = "Cam:  OK, night mode, not recording."
		self.drawRow(text, row)
		text = "      Flip image:    [{0}]".format("yes" if self.cfg.flip else "no")
		self.drawRow(text, row+1)
		if self.focus==1 :
			self.window.chgat(row+1, 25, 3 if self.cfg.flip else 2, curses.A_REVERSE)
		text = "      Morning start: [{0}] (noon - 7 hours)".format(self.cfg.start.strftime("%H:%M"))
		self.drawRow(text, row+2)
		if self.focus==2 :
			self.window.chgat(row+2, 25, 5, curses.A_REVERSE)
		text = "      Evening stop:  [{0}] (noon + 7 hours)".format(self.cfg.stop.strftime("%H:%M"))
		self.drawRow(text, row+3)
		if self.focus==3 :
			self.window.chgat(row+3, 25, 5, curses.A_REVERSE)
		text = "      Quality:       [{0:.1f}] Mbit/s".format(self.cfg.bitrate/1000000)
		self.drawRow(text, row+4)
		if self.focus==4 :
			self.window.chgat(row+4, 25, 3, curses.A_REVERSE)
		perHour = (self.cfg.bitrate*3600)/(8*1024*1024*1024)
		text = "                   = {0:.2f} GB/hour".format(perHour)
		self.drawRow(text, row+5)
		day = (self.cfg.stop.hour - self.cfg.start.hour)*3600 + (self.cfg.stop.minute - self.cfg.start.minute)*60
		perDay = (self.cfg.bitrate*day)/(8*1024*1024*1024)
		text = "                   = {0:.1f} GB for daytime".format(perDay)
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
			if self.focus > 4 :
				self.focus = 0
		elif self.focus==1 :
			flip = self.cfg.flip
			if key==curses.KEY_ENTER or key==10 or key==13 or key==32 :
				flip = not flip
			if self.cfg.flip != flip :
				self.cfg.flip = flip
				isChanged = True
		elif self.focus==2 :
			dawn = self.cfg.start
			dawn = tweakTime(dawn, key)
			if self.cfg.start != dawn :
				self.cfg.start = dawn
				isChanged = True
		elif self.focus==3 :
			dusk = self.cfg.stop
			dusk = tweakTime(dusk, key)
			if self.cfg.stop != dusk :
				self.cfg.stop = dusk
				isChanged = True
		elif self.focus==4 :
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
		# If stuff changed, we update the JSON
		if isChanged :
			self.cfg.save()
		# It's always harmless to re-draw
		self.draw()

	def onTimer(self, t) :
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
