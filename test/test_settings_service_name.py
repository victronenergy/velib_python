#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from settingsdevice import SettingsDevice


class SettingsServiceNameTest(unittest.TestCase):
	def test_custom_service_available(self):
		name = 'com.victronenergy.settings.test'
		bus = Mock()
		bus.list_names.return_value = [name]
		bus.call_blocking.return_value = []
		device = SettingsDevice(bus, {}, None, name=name)
		self.assertEqual(device._dbus_name, name)
		self.assertEqual(bus.call_blocking.call_args.args[0], name)

	def test_default_does_not_mask_missing_custom_service(self):
		bus = Mock()
		bus.list_names.return_value = ['com.victronenergy.settings']
		bus.call_blocking.return_value = []
		with self.assertRaisesRegex(Exception, 'com.victronenergy.settings.test'):
			SettingsDevice(bus, {}, None, name='com.victronenergy.settings.test')
		bus.call_blocking.assert_not_called()

	def test_waits_for_custom_service(self):
		name = 'com.victronenergy.settings.test'
		bus = Mock()
		bus.list_names.side_effect = [[], [name]]
		bus.call_blocking.return_value = []
		with patch('settingsdevice.time.sleep') as sleep:
			SettingsDevice(bus, {}, None, name=name, timeout=1)
		sleep.assert_called_once_with(1)

	def test_default_service(self):
		bus = Mock()
		bus.list_names.return_value = ['com.victronenergy.settings']
		bus.call_blocking.return_value = []
		SettingsDevice(bus, {}, None)
		self.assertEqual(bus.call_blocking.call_args.args[0], 'com.victronenergy.settings')


if __name__ == '__main__':
	unittest.main()
