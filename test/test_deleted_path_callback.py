#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from vedbus import VeDbusService


class Item:
	def __init__(self, bus, path, value, description, writeable, on_change,
			gettextcallback, deletecallback, valuetype):
		self.path = path
		self.deletecallback = deletecallback

	def __del__(self):
		if self.deletecallback is not None:
			callback, self.deletecallback = self.deletecallback, None
			callback(self.path)


class DeletedPathCallbackTest(unittest.TestCase):
	def test_readded_path_drops_old_write_validator(self):
		service = object.__new__(VeDbusService)
		service._dbusconn = None
		service._dbusname = None
		service._dbusobjects = {}
		service._dbusnodes = {}
		service._onchangecallbacks = {}
		old_validator = Mock(return_value=False)
		service.add_path('/Test', 12, writeable=True,
			onchangecallback=old_validator, itemtype=Item)
		self.assertFalse(service._value_changed('/Test', 13))
		old_validator.reset_mock()

		del service['/Test']
		service.add_path('/Test', 14, writeable=True, itemtype=Item)
		self.assertTrue(service._value_changed('/Test', 15))
		old_validator.assert_not_called()


if __name__ == '__main__':
	unittest.main()
