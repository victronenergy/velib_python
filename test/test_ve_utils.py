#!/usr/bin/env python3
import os
import sys
import unittest

import dbus

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from ve_utils import unwrap_dbus_value


class UnwrapByteArrayTest(unittest.TestCase):
	def test_byte_arrays(self):
		for value in (b'', b'ABC', b'\x00\xff'):
			with self.subTest(value=value):
				result = unwrap_dbus_value(dbus.ByteArray(value))
				self.assertEqual(result, value)
				self.assertIs(type(result), bytes)

	def test_nested_byte_array(self):
		value = dbus.Dictionary({'data': dbus.ByteArray(b'\x00\xff')})
		self.assertEqual(unwrap_dbus_value(value), {'data': b'\x00\xff'})


if __name__ == '__main__':
	unittest.main()
