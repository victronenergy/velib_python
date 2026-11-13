#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from dbusmonitor import DbusMonitor, MonitoredValue, Service


class QueuedValueChangesTest(unittest.TestCase):
	def setUp(self):
		self.name = 'com.victronenergy.battery.test'
		self.path = '/Soc'
		self.service = Service(':1.10', self.name, 10)
		self.service.paths[self.path] = MonitoredValue(50, '50%', {})
		self.monitor = object.__new__(DbusMonitor)
		self.monitor.servicesByName = {self.name: self.service}
		self.monitor.valueChangedCallback = Mock()
		self.jobs = []

	def queue_change(self, service, value):
		with patch('dbusmonitor.GLib.idle_add',
				side_effect=lambda *args: self.jobs.append(args)):
			self.monitor._handler_value_changes(service, self.path, value, f'{value}%')

	def run_jobs(self):
		for callback, *args in self.jobs:
			callback(*args)

	def test_current_service_change_is_delivered(self):
		self.queue_change(self.service, 51)
		self.run_jobs()
		self.monitor.valueChangedCallback.assert_called_once_with(
			self.name, self.path, {}, {'Value': 51, 'Text': '51%'}, 10)

	def test_removed_service_change_is_discarded(self):
		self.queue_change(self.service, 51)
		del self.monitor.servicesByName[self.name]
		self.run_jobs()
		self.monitor.valueChangedCallback.assert_not_called()

	def test_replaced_service_does_not_receive_old_owners_change(self):
		self.queue_change(self.service, 51)
		replacement = Service(':1.20', self.name, 20)
		replacement.paths[self.path] = MonitoredValue(70, '70%', {})
		self.monitor.servicesByName[self.name] = replacement
		self.queue_change(replacement, 71)
		self.run_jobs()
		self.monitor.valueChangedCallback.assert_called_once_with(
			self.name, self.path, {}, {'Value': 71, 'Text': '71%'}, 20)


if __name__ == '__main__':
	unittest.main()
