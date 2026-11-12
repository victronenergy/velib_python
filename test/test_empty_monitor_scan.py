#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from dbusmonitor import AsyncDbusMonitor, DbusMonitor


class EmptyMonitorScanTest(unittest.TestCase):
	def test_empty_startup_scan_completes(self):
		callback = Mock()

		def initialize(monitor, *args, **kwargs):
			monitor._scan_dbus()

		with patch.object(DbusMonitor, '__init__', initialize), \
				patch.object(AsyncDbusMonitor, 'wanted_service_names', return_value=[]):
			monitor = AsyncDbusMonitor({}, scanCompleteCallback=callback)
		callback.assert_called_once_with(monitor)

	def test_empty_rescan_completes(self):
		monitor = object.__new__(AsyncDbusMonitor)
		monitor.wanted_service_names = lambda: []
		callback = Mock()
		monitor.scan_dbus_services_async(callback)
		callback.assert_called_once_with([])

	def test_nonempty_scan_waits_for_all_services(self):
		monitor = object.__new__(AsyncDbusMonitor)
		monitor.wanted_service_names = lambda: ['first', 'second']
		monitor.get_name_owner_async = Mock()
		callback = Mock()
		monitor.scan_dbus_services_async(callback)
		callback.assert_not_called()
		progress = monitor.get_name_owner_async.call_args_list[0].args[0]
		progress.complete('first')
		callback.assert_not_called()
		progress.complete('second')
		callback.assert_called_once_with([])

	def test_empty_rescan_without_callback(self):
		monitor = object.__new__(AsyncDbusMonitor)
		monitor.wanted_service_names = lambda: []
		monitor.scan_dbus_services_async()


if __name__ == '__main__':
	unittest.main()
