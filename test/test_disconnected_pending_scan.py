#!/usr/bin/env python3
import os
import sys
import unittest
from collections import defaultdict
from unittest.mock import Mock

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from dbusmonitor import AsyncDbusMonitor, ScanProgress


class DisconnectedPendingScanTest(unittest.TestCase):
	def monitor(self):
		monitor = object.__new__(AsyncDbusMonitor)
		monitor.pendingScans = {}
		monitor.servicesByName = {}
		monitor.servicesById = {}
		monitor.servicesByClass = defaultdict(list)
		monitor.dbusTree = {'com.victronenergy.battery': {}}
		monitor.dbusConn = Mock()
		monitor.deviceAddedCallback = Mock()
		return monitor

	def test_reply_after_disconnect_is_ignored(self):
		monitor = self.monitor()
		name = 'com.victronenergy.battery.test'
		finished = Mock()
		progress = ScanProgress(finished)
		progress.add(name)
		monitor.scan_items_async(progress, name, ':1.10')
		monitor._process_name_owner_changed(name, ':1.10', '')
		monitor.get_items_async_done(progress, name, ':1.10',
			{'/DeviceInstance': {'Value': 0}})
		self.assertNotIn(name, monitor.servicesByName)
		monitor.deviceAddedCallback.assert_not_called()
		finished.assert_called_once_with([])

	def test_current_owner_reply_is_accepted(self):
		monitor = self.monitor()
		name = 'com.victronenergy.battery.test'
		progress = ScanProgress(None)
		progress.add(name)
		monitor.scan_items_async(progress, name, ':1.10')
		monitor.get_items_async_done(progress, name, ':1.10',
			{'/DeviceInstance': {'Value': 0}})
		self.assertEqual(monitor.scanned_owner(name), ':1.10')
		monitor.deviceAddedCallback.assert_called_once_with(name, 0)


if __name__ == '__main__':
	unittest.main()
