#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import Mock, patch

import dbus

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from settingsdevice import VeDbusSettingItem


class SettingsSignalMetadataTest(unittest.TestCase):
	def setUp(self):
		self.tracked = patch.object(VeDbusSettingItem, '_tracked', {}, create=True)
		self.tracked.start()
		self.addCleanup(self.tracked.stop)
		self.callback = Mock()
		self.path = '/Settings/Test/MetadataSignal'
		self.item = VeDbusSettingItem(Mock(), 'com.victronenergy.settings',
			self.path, self.callback, initial_value=5)

	def test_metadata_only_signal_preserves_value_without_callback(self):
		for change in ({'Text': 'Five'}, {}):
			with self.subTest(change=change):
				VeDbusSettingItem._setting_changed_handler(change, path=self.path)
				self.assertEqual(self.item.get_value(), 5)
				self.callback.assert_not_called()

	def test_value_signal_without_text_still_updates(self):
		VeDbusSettingItem._setting_changed_handler({'Value': dbus.Int32(0)}, path=self.path)
		self.assertEqual(self.item.get_value(), 0)
		self.callback.assert_called_once_with('com.victronenergy.settings', self.path,
			{'Value': 0, 'Text': '0'})

	def test_value_and_text_are_forwarded(self):
		VeDbusSettingItem._setting_changed_handler(
			{'Value': dbus.Int32(7), 'Text': 'Seven'}, path=self.path)
		self.callback.assert_called_once_with('com.victronenergy.settings', self.path,
			{'Value': 7, 'Text': 'Seven'})

	def test_unknown_path_is_ignored(self):
		VeDbusSettingItem._setting_changed_handler({'Text': 'Unknown'}, path='/Settings/Other')
		self.callback.assert_not_called()


if __name__ == '__main__':
	unittest.main()
