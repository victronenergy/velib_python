#!/usr/bin/env python3
import os
import sys
import unittest

import dbus
from dbus.mainloop.glib import DBusGMainLoop

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from vedbus import VeDbusService


class LocalTreeValueTests(unittest.TestCase):
    def setUp(self):
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus(private=True)
        self.service = VeDbusService('com.victronenergy.localtreetest',
                                     bus=self.bus, register=False)

    def tearDown(self):
        self.service.__del__()
        self.bus.close()

    def test_empty_root(self):
        self.assertEqual(self.service.root.local_get_value(), {})

    def test_root_includes_all_relative_paths(self):
        self.service.add_path('/Dc/0/Voltage', 12.5)
        self.service.add_path('/Ac/Power', 100)
        self.assertEqual(self.service.root.local_get_value(), {
            'Dc/0/Voltage': 12.5, 'Ac/Power': 100})
        self.assertEqual(self.service.root.local_get_value(), self.service.root.GetValue())

    def test_subtree_excludes_siblings_and_reflects_updates(self):
        self.service.add_path('/Dc/0/Voltage', 12.5)
        self.service.add_path('/Dc/0/Current', 2.0)
        self.service.add_path('/DcExtra/Power', 100)
        node = self.service._dbusnodes['/Dc']
        self.assertEqual(node.local_get_value(), {'0/Voltage': 12.5, '0/Current': 2.0})
        self.service['/Dc/0/Current'] = 3.0
        del self.service['/Dc/0/Voltage']
        self.assertEqual(node.local_get_value(), {'0/Current': 3.0})
        self.assertEqual(node.local_get_value(), node.GetValue())


if __name__ == '__main__':
    unittest.main()
