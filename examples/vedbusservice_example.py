#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dbus.mainloop.glib import DBusGMainLoop
import gobject
from gobject import idle_add
import dbus
import dbus.service
import inspect
import platform
import pprint

# our own packages
from vedbus import VeDbusService

softwareVersion = '1.0'

def validate_new_value(path, newvalue):
	# Max RPM setpoint = 1000
	return newvalue <= 1000

def get_text_for_rpm(path, value):
	return('%d rotations per minute' % value)

def main(argv):
		global dbusObjects

		print __file__ + " starting up"

		# Have a mainloop, so we can send/receive asynchronous calls to and from dbus
		DBusGMainLoop(set_as_default=True)

		# Put ourselves on to the dbus
		dbusservice = VeDbusService('com.victronenergy.example')

		# Most simple and short way to add an object with an initial value of 5.
		dbusservice.add_path('/Position', value=5)

		# Most advanced wayt to add a path
		dbusservice.add_path('/RPM', value=100, description='RPM setpoint', writeable=True,
			onchangecallback=validate_new_value, gettextcallback=get_text_for_rpm)

		# You can access the paths as if the dbusservice is a dictionary
		print('/Position value is %s' % dbusservice['/Position'])

		# Same for changing it
		dbusservice['/Position'] = 10

		print('/Position value is now %s' % dbusservice['/Position'])

		# To invalidate a value (see com.victronenergy.BusItem specs for definition of invalid), set to None
		dbusservice['/Position'] = None

		print('try changing our RPM by executing the following command from a terminal\n')
		print('dbus-send --print-reply --dest=com.victronenergy.example /RPM com.victronenergy.BusItem.SetValue int32:1200')
		print('Reply should be <> 0, meaning it is not allowed')
		mainloop = gobject.MainLoop()
		mainloop.run()

main("")
