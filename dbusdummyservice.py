#!/usr/bin/env python

"""
A class to put a simple service on the dbus, according to victron standards, with constantly updating
paths. See example usage below.
"""
import gobject
import platform
import argparse
import logging
import sys
import os

# our own packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '../ext/velib_python'))
from vedbus import VeDbusService

class DbusDummyService:
    def __init__(self, servicename, deviceinstance, paths):
        self._dbusservice = VeDbusService(servicename)
        self._paths = paths

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Management/ProcessName', __file__)
        self._dbusservice.add_path('/Management/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
        self._dbusservice.add_path('/Management/Connection', 'Data taken from mk2dbus')

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        self._dbusservice.add_path('/ProductId', 0)
        self._dbusservice.add_path('/ProductName', 'vebus device with ac sensors')
        self._dbusservice.add_path('/FirmwareVersion', 0)
        self._dbusservice.add_path('/HardwareVersion', 0)
        self._dbusservice.add_path('/Connected', 1)

        for path, settings in self._paths.iteritems():
            self._dbusservice.add_path(path, settings['initial'])

        gobject.timeout_add(1000, self._update)

    def _update(self):
        for path, settings in self._paths.iteritems():
            self._dbusservice[path] = self._dbusservice[path] + settings['update']
            logging.debug("%s: %s" % (path, self._dbusservice[path]))
        return True


def main():
    logging.basicConfig(level=logging.DEBUG)

    from dbus.mainloop.glib import DBusGMainLoop
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    pvac_output = DbusDummyService(
        servicename='com.victronenergy.pvinverter.output',
        deviceinstance=0,
        paths={
            '/Ac/Energy/Forward': {'initial': 0, 'update': 1},
            '/Position': {'initial': 0, 'update': 0}})

    logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
    mainloop = gobject.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()


