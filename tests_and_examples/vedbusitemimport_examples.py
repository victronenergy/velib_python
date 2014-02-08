#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note that this file requires vedbusitemexport_examples to be running.

import dbus
import pprint

# our own packages
from vedbus import VeDbusItemExport, VeDbusItemImport

# Connect to the sessionbus. Note that on ccgx we use systembus instead.
dbusConn = dbus.SessionBus()

# dictionary containing the different items
dbusObjects = {}

dbusObjects['string'] = VeDbusItemImport(dbusConn, 'com.victronenergy.dbusexample', '/String')
dbusObjects['float'] = VeDbusItemImport(dbusConn, 'com.victronenergy.dbusexample', '/Float')
dbusObjects['int'] = VeDbusItemImport(dbusConn, 'com.victronenergy.dbusexample', '/Int')
dbusObjects['negativeInt'] = VeDbusItemImport(dbusConn, 'com.victronenergy.dbusexample', '/NegativeInt')

for key in dbusObjects:
	print key, ' corresponds to ', dbusObjects[key]
	pprint.pprint(dbusObjects[key])
	print 'pprint veBusItem.GetValue(): '
	pprint.pprint(dbusObjects[key].GetValue())
	print 'pprint veBusItem.GetText(): '
	pprint.pprint(dbusObjects[key].GetText())
	print '----'
