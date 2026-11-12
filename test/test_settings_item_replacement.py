#!/usr/bin/env python3
import gc
import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from settingsdevice import VeDbusSettingItem


class SettingsItemReplacementTest(unittest.TestCase):
	def test_replacing_item_keeps_new_change_handler(self):
		path = '/Settings/Test/Voltage'
		bus = Mock()
		old_callback = Mock()
		new_callback = Mock()
		with patch.object(VeDbusSettingItem, '_tracked', {}, create=True):
			old = VeDbusSettingItem(bus, 'com.victronenergy.settings',
				path, old_callback, initial_value=12)
			new = VeDbusSettingItem(bus, 'com.victronenergy.settings',
				path, new_callback, initial_value=13)
			del old
			gc.collect()
			VeDbusSettingItem._setting_changed_handler({'Value': 14}, path)
			self.assertEqual(new.get_value(), 14)
			new_callback.assert_called_once()
			old_callback.assert_not_called()


if __name__ == '__main__':
	unittest.main()
