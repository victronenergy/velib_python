#!/usr/bin/env python3
import os
import sys
import unittest

import dbus

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from ve_utils import VEDBUS_INVALID, wrap_dbus_value, unwrap_dbus_value


class EmptyArrayRoundtripTest(unittest.TestCase):
	def test_empty_list_roundtrip(self):
		self.assertEqual(unwrap_dbus_value(wrap_dbus_value([])), [])

	def test_explicitly_typed_empty_arrays(self):
		for signature in ('u', 's', 'v'):
			with self.subTest(signature=signature):
				self.assertEqual(unwrap_dbus_value(dbus.Array([], signature=signature)), [])

	def test_invalid_sentinel(self):
		self.assertIsNone(unwrap_dbus_value(VEDBUS_INVALID))

	def test_nonempty_array(self):
		self.assertEqual(unwrap_dbus_value(wrap_dbus_value([1, 2])), [1, 2])


if __name__ == '__main__':
	unittest.main()
