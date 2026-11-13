#!/usr/bin/env python3
import os
import sys
import unittest

import dbus
from dbus.lowlevel import MethodCallMessage

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from ve_utils import unwrap_dbus_value, wrap_dbus_value


class UnsignedIntegerWrapTest(unittest.TestCase):
	def test_full_unsigned_range(self):
		for value in (2**63, 2**64 - 1):
			for input_value in (value, dbus.UInt64(value)):
				with self.subTest(value=input_value, type=type(input_value)):
					wrapped = wrap_dbus_value(input_value)
					self.assertIsInstance(wrapped, dbus.UInt64)
					self.assertEqual(wrapped.variant_level, 1)
					self.assertEqual(unwrap_dbus_value(wrapped), value)
					message = MethodCallMessage('com.victronenergy.test', '/Test',
						'com.victronenergy.BusItem', 'SetValue')
					message.append(wrapped, signature='v')
					self.assertEqual(int(message.get_args_list()[0]), value)

	def test_existing_signed_types(self):
		for value, expected_type in ((-2**31, dbus.Int32), (0, dbus.Int32),
				(2**31 - 1, dbus.Int32), (-2**63, dbus.Int64),
				(2**31, dbus.Int64), (2**63 - 1, dbus.Int64)):
			with self.subTest(value=value):
				wrapped = wrap_dbus_value(value)
				self.assertIsInstance(wrapped, expected_type)
				self.assertEqual(int(wrapped), value)

	def test_out_of_range_still_rejected(self):
		for value in (-2**63 - 1, 2**64):
			with self.subTest(value=value):
				with self.assertRaises(OverflowError):
					wrap_dbus_value(value)


if __name__ == '__main__':
	unittest.main()
