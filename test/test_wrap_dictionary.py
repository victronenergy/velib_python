#!/usr/bin/env python3
import os
import sys
import unittest

import dbus

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from ve_utils import wrap_dbus_value


class WrapDictionaryTest(unittest.TestCase):
	def test_dictionary_with_array(self):
		result = wrap_dbus_value({'readings': [12, 24]})
		self.assertIsInstance(result, dbus.Dictionary)
		self.assertIsInstance(result['readings'], dbus.Array)
		self.assertEqual(list(result['readings']), [12, 24])

	def test_dictionary_with_dictionary(self):
		result = wrap_dbus_value({'battery': {'voltage': 12.5}})
		self.assertIsInstance(result['battery'], dbus.Dictionary)
		self.assertEqual(result['battery']['voltage'], 12.5)

	def test_scalar_dictionary(self):
		result = wrap_dbus_value({'voltage': 12.5})
		self.assertEqual(result['voltage'], 12.5)
		self.assertEqual(result.variant_level, 1)


if __name__ == '__main__':
	unittest.main()
