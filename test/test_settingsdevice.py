#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Python
import logging
import os
import sqlite3
import sys
import unittest
import subprocess
import time
import dbus
import threading
import fcntl
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

# Local
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '../'))
from settingsdevice import SettingsDevice

# These tests need localsettings to be running, e.g. on a private session bus:
# dbus-run-session -- sh -c 'python3 localsettings.py --path=$(mktemp -d) & sleep 2; python3 test_settingsdevice.py'

logger = logging.getLogger(__file__)

class CreateSettingsTest(unittest.TestCase):
	# The actual code calling VeDbusItemExport is in fixture_vedbus.py, which is ran as a subprocess. That
	# code exports several values to the dbus. And then below test cases check if the exported values are
	# what the should be, by using the bare dbus import objects and functions.

	def setUp(self):
		self.bus = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()
		if 'com.victronenergy.settings' not in self.bus.list_names():
			self.skipTest('com.victronenergy.settings is not running')
		self.changes = []

	def tearDown(self):
		pass

	def test_adding_new_settings(self):
		# to make sure that we make new settings, put something random in its name:
		rnd = os.urandom(16).hex()

		# ofcourse below could be simplified, for now just use all settings from the example:
		settings = SettingsDevice(
			bus=dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus(),
			supportedSettings={
				'loggingenabled': ['/Settings/' + rnd + '/Logscript/Enabled', 1, 0, 1],
				'proxyaddress': ['/Settings/' + rnd + '/Logscript/Http/Proxy', '', 0, 0],
				'proxyport': ['/Settings/' + rnd + '/Logscript/Http/ProxyPort', '', 0, 0],
				'backlogenabled': ['/Settings/' + rnd + '/Logscript/LogFlash/Enabled', 1, 0, 1],
				'backlogpath': ['/Settings/' + rnd + '/Logscript/LogFlash/Path', '', 0, 0],  # When empty, default path will be used.
				'interval': ['/Settings/' + rnd + '/Logscript/LogInterval', 900, 0, 0],
				'url': ['/Settings/' + rnd + '/Logscript/Url', '', 0, 0]  # When empty, the default url will be used.
				},
			eventCallback=self.handle_changed_setting)

		"""
		self.assertIs(type(v), dbus.Double)
		self.assertEqual(self.dbusConn.get_object('com.victronenergy.dbusexample', '/Float').GetText(), '1.5')
		"""

	def handle_changed_setting(self, setting, oldvalue, newvalue):
		self.changes.append((setting, oldvalue, newvalue))

	def make_settings(self):
		rnd = os.urandom(16).hex()
		settings = SettingsDevice(bus=self.bus,
			supportedSettings={
				'int': ['/Settings/' + rnd + '/Int', 1, 0, 1],
				'string': ['/Settings/' + rnd + '/String', '', 0, 0],
			},
			eventCallback=self.handle_changed_setting)
		# handle the signals of adding the settings
		self.run_mainloop()
		self.changes = []
		return settings

	def run_mainloop(self):
		loop = GLib.MainLoop()
		GLib.timeout_add(500, loop.quit)
		loop.run()

	def test_read_after_write(self):
		settings = self.make_settings()
		for v in (0, 1, 0):
			settings['int'] = v
			self.assertEqual(settings['int'], v)

	def test_read_after_write_returns_stored_value(self):
		# localsettings converts the value to the type of the setting
		settings = self.make_settings()
		settings['string'] = 5
		self.assertEqual(settings['string'], '5')

	def test_read_after_set_default(self):
		settings = self.make_settings()
		settings['int'] = 0
		self.run_mainloop()
		settings._settings['int'].set_default()
		self.assertEqual(settings['int'], 1)

	def test_change_by_other_client(self):
		settings = self.make_settings()
		path = settings._settings['int']._path
		other = dbus.SessionBus(private=True) if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus(private=True)
		other.call_blocking('com.victronenergy.settings', path, 'com.victronenergy.BusItem',
			'SetValue', 'v', [dbus.Int32(0, variant_level=1)])
		self.run_mainloop()
		self.assertEqual(settings['int'], 0)
		self.assertEqual(self.changes, [('int', 1, 0)])

if __name__ == "__main__":
	logging.basicConfig(stream=sys.stderr)
	logging.getLogger('').setLevel(logging.WARNING)
	DBusGMainLoop(set_as_default=True)
	unittest.main()
