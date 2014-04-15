#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file has some tests, to do type checking of vedbus.py
# This file makes it easy to compare the values put on the dbus through
# Python (vedbus.VeDbusItemExport) with items exported in C (the mk2dbus process)

# Note that this file requires vedbusitemexport_examples to be running.

import dbus
import pprint
import platform

# our own packages
from vedbus import VeDbusItemExport, VeDbusItemImport

# Connect to the sessionbus. Note that on ccgx we use systembus instead.
dbusConn = dbus.SystemBus() if (platform.machine() == 'armv7l') else dbus.SessionBus()

# dictionary containing the different items
dbusObjects = {}

# check if the vbus.ttyO1 exists (it normally does on a ccgx, and for linux a pc, there is
# some emulator.
hasVEBus = 'com.victronenergy.vebus.ttyO1' in dbusConn.list_names()

dbusObjects['PyString'] = VeDbusItemImport(dbusConn, 'com.victronenergy.dbusexample', '/String')
if hasVEBus: dbusObjects['C_string'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Mgmt/ProcessName')

dbusObjects['PyFloat'] = VeDbusItemImport(dbusConn, 'com.victronenergy.dbusexample', '/Float')
if hasVEBus: dbusObjects['C_float'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Dc/V')

dbusObjects['PyInt'] = VeDbusItemImport(dbusConn, 'com.victronenergy.dbusexample', '/Int')
if hasVEBus: dbusObjects['C_int'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/State')

dbusObjects['PyNegativeInt'] = VeDbusItemImport(dbusConn, 'com.victronenergy.dbusexample', '/NegativeInt')
if hasVEBus: dbusObjects['C_negativeInt'] = VeDbusItemImport(dbusConn, 'com.victronenergy.vebus.ttyO1', '/Dc/I')

# print the results
for key, o in dbusObjects.items():
	print key + ' at ' + o.serviceName + o.path
	print ''
	pprint.pprint(dbusObjects[key])
	print 'pprint veBusItem.GetValue(): '
	pprint.pprint(dbusObjects[key].GetValue())
	print 'pprint veBusItem.GetText(): '
	pprint.pprint(dbusObjects[key].GetText())
	print '----'
