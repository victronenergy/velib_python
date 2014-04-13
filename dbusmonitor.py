#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package dbus_vrm
# This code takes care of the D-Bus interface (not all of below is implemented yet):
# - on startup it scans the dbus for services we know. For each known service found, it searches for
#   objects/paths we know. Everything we find is stored in items{}, and an event is registered: if a
#   value changes weĺl be notified and can pass that on to our owner. For example the vrmLogger.
#   we know.
# - after startup, it continues to monitor the dbus:
#		1) when services are added we do the same check on that
#		2) when services are removed, we remove any items that we had that referred to that service
#		3) if an existing services adds or removes paths we update ourselves as well (how to do this!?!)
#          answer on how to do this: realize that we are not really adding the object. Making a
#          VeDbusItemImport for a non-existing objectpath is no problem. Just don't call GetValue().
#          Perhaps we'll add PathExists() true/false to the properties of VeDbusItemImport.
#
# Code is used by the vrmLogger, and also the pubsub code. Both are other modules in the dbus_vrm repo.

from dbus.mainloop.glib import DBusGMainLoop
import gobject
from gobject import idle_add
import dbus
import dbus.service
import inspect
import platform
import logging
import argparse
import pprint

# our own packages
from vedbus import VeDbusItemExport, VeDbusItemImport
from conversions import Conversions

# Dictionary containing all devices and paths to look for
from datalist import vrmTree

items = {}

class DbusMonitor(object):
	## Constructor
	# TODO: Remove mountEventCallback, VrmHttpFlash should set up a listener
	def __init__(self, valueChangedCallback=None, deviceAddedCallback=None, deviceRemovedCallback=None, mountEventCallback=None):
		# The callback that we call when something has changed.
		# parameters that will be passed when this function is called are:
		#	dbus-servicename, for example com.victronenergy.dbus.ttyO1
		#	dbus-path, for example /Ac/ActiveIn/L1/V
		#   the dict containing the properties from the vrmTree
		#	the changes, a tuple with GetText() and GetValue()
		self.valueChangedCallback = valueChangedCallback
		self.deviceAddedCallback = deviceAddedCallback
		self.deviceRemovedCallback = deviceRemovedCallback
		self.mountEventCallback = mountEventCallback

		# Dictionary containing all dbus items we monitor (VeDbusItemImport). It contains D-Bus servicenames,
		# objectpaths, and the VEDbusItemImport objects and the details from the excelsheet:
		# {'com.victronenergy.vebus.ttyO1': {'AcSensor/0/Energy': {
		#                                        'dbusObject': <vedbus.VeDbusItemImport object at 0xa3d406c>,
		#                                        'vrmDict': {'code': 'hoi', 'whenToLog': 'sometimes'}
		#                                        },
		#                                    '/AcSensor/0/Power': {
		#                                        'dbusObject': <vedbus.VeDbusItemImport object at 0xa3d450c>,
		#                                        'vrmDict': {'code': 'bg', 'whenToLog': 'always'}
		#                                        }
		#                                   },
		# {'com.victronenergy.battery.socketcan': {'etc. etc. }
		# }
		self.items = {}

		# For a PC, connect to the SessionBus
		# For a CCGX, connect to the SystemBus
		self.dbusConn = dbus.SystemBus() if (platform.machine() == 'armv7l') else dbus.SessionBus()

		# subscribe to NameOwnerChange for bus connect / disconnect events.
		self.dbusConn.add_signal_receiver(self.dbus_name_owner_changed, signal_name='NameOwnerChanged')

		self.dbusConn.add_signal_receiver(self.dbus_mount_event, signal_name='mount')
		self.dbusConn.add_signal_receiver(self.dbus_umount_event, signal_name='umount')

		logging.info('===== Search on dbus for services that we will monitor starting... =====')
		serviceNames = self.dbusConn.list_names()
		for serviceName in serviceNames:
			self.scan_dbus_service(serviceName)
		logging.info('===== Search on dbus for services that we will monitor finished =====')

	def dbus_mount_event(self, device, mountpoint):
		logging.warning('mount event!')
		if self.mountEventCallback is not None:
			self.mountEventCallback('mount', device, mountpoint)

	def dbus_umount_event(self, device, mountpoint):
		logging.warning('umount event!')
		if self.mountEventCallback is not None:
			self.mountEventCallback('umount', device, mountpoint)

	def dbus_name_owner_changed(self, name, oldowner, newowner):
		#decouple, and process in main loop
		idle_add(self.process_name_owner_changed, name, oldowner, newowner)

	def process_name_owner_changed(self, name, oldowner, newowner):
		# logging.debug('D-Bus name owner changed. Name: %s, oldOwner: %s, newOwner: %s'
		#					% (name, oldowner, newowner))

		if newowner != '':
			# so we found some new service. Check if we can do something with it.

			newdeviceadded = self.scan_dbus_service(name)
			if newdeviceadded and self.deviceAddedCallback is not None:
				self.deviceAddedCallback(name, self.get_device_instance(name))

		elif name in self.items:
			# it dissapeared, we need to remove it.

			logging.info("%s dissapeared from the dbus. Removing it from our lists" % name)
			i = self.items[name]['deviceInstance']
			del self.items[name]
			if self.deviceRemovedCallback is not None:
				self.deviceRemovedCallback(name, i)

	# Scans the given dbus service to see if it contains anything interesting for us. If it does, add
	# it to our list of monitored D-Bus services.
	def scan_dbus_service(self, serviceName):

		newDeviceAdded = False

		for s in vrmTree.keys():
			if serviceName.split('.')[0:3] == s.split('.')[0:3]:
				logging.info("Found: %s matches %s, scanning and storing items" % (serviceName, s))
				newDeviceAdded = True

				# we should never be notified to add a D-Bus service that we already have. If this assertion
				# raises, check process_name_owner_changed, and D-Bus workings.
				assert serviceName not in self.items

				self.items[serviceName] = {}

				# create the empty list items.
				whentologoptions = ['configChange', 'onIntervalAlwaysAndOnEvent', 'onIntervalOnlyWhenChanged',
								'onIntervalAlways', 'asDeltaHourly']

				# these lists will contain the VeDbusItemImport objects with that whenToLog setting. Used to
				for whentolog in whentologoptions:
					self.items[serviceName][whentolog] = []

				self.items[serviceName]['paths'] = {}

				# settings doesn't have a deviceInstance
				# gps doesn't have a deviceInstance, fix it at 0.
				# kwhcounters is fixed at deviceInstance 0.
				# And for vebus.ttyO1, this is workaround, since VRM Portal expects the main vebus devices at
				# instance 0. Not sure how to fix this yet.
				if serviceName in ['com.victronenergy.vebus.ttyO1', 'com.victronenergy.settings', 'com.victronenergy.gps',
					'com.victronenergy.kwhcounters']:
					self.items[serviceName]['deviceInstance'] = 0
				else:
					self.items[serviceName]['deviceInstance'] = VeDbusItemImport(self.dbusConn, serviceName, '/DeviceInstance').GetValue()

				logging.info("       %s has device instance %s" % (serviceName, self.items[serviceName]['deviceInstance']))

				for path, options in vrmTree[s].items():
					# path will be the D-Bus path: '/Ac/ActiveIn/L1/V'
					# options will be a dictionary: {'code': 'V', 'whenToLog': 'onIntervalAlways'}

					# check that the whenToLog setting is set to something we expect
					assert options['whenToLog'] in whentologoptions

					# create and store the VeDbusItemImport. Store it both searchable by names, and in the
					# relevant whenToLog list.
					o = VeDbusItemImport(self.dbusConn, serviceName, path, self.handler_value_changes)
					self.items[serviceName][options['whenToLog']].append(o)
					self.items[serviceName]['paths'][path] = {'dbusObject': o, 'vrmDict': options}
					logging.debug("    Added %s%s" % (serviceName, path))

				logging.debug("Finished scanning and storing items for %s" % serviceName)

		return newDeviceAdded

	def handler_value_changes(self, serviceName, objectPath, changes):
		# decouple, and process update in the mainloop
		idle_add(self.execute_value_changes, serviceName, objectPath, changes)

	def execute_value_changes(self, serviceName, objectPath, changes):
		if self.valueChangedCallback is not None:
			self.valueChangedCallback(serviceName, objectPath,
				self.items[serviceName]['paths'][objectPath]['vrmDict'], changes, self.get_device_instance(serviceName))

	def get_device_instance(self, serviceName):
		return self.items[serviceName]['deviceInstance']

	# types is to be a list, containing the types you want (configChange, onIntervalAlways, etc)
	# return a dictionary, keys are codes + instance. For example vvt[0]. And values are the value.
	def get_values(self, types):

		result = {}

		# loop through the D-Bus service that we now
		for serviceName in self.items.keys():
			result.update(self.get_values_for_service(types, serviceName))

		return result

	# same as above, but then for one service only
	def get_values_for_service(self, types, serviceName):
		deviceInstance = self.get_device_instance(serviceName)
		result = {}

		# iterate through the list of types
		for t in types:

			# iterate through the VeDbusItemImport objects and get the data
			serviceDict = self.items[serviceName]
			for d in serviceDict[t]:
				if d.isValid and d.GetValue() is not None:
					code = serviceDict['paths'][d.path]['vrmDict']['code']
					result[code + "[" + str(deviceInstance) + "]"] = Conversions.convert(code, d.GetValue())

		return result

# Example function that can be used as a starting point to use this code
def value_changed_on_dbus(dbusServiceName, dbusPath, dict, changes, deviceInstance):
	logging.debug("0 ----------------")
	logging.debug("1 %s%s changed" % (dbusServiceName, dbusPath))
	logging.debug("2 vrm dict     : %s" % dict)
	logging.debug("3 changes-text: %s" % changes['Text'])
	logging.debug("4 changes-value: %s" % changes['Value'])
	logging.debug("5 deviceInstance: %s" % deviceInstance)
	logging.debug("6 - end")



# We have a mainloop, but that is just for developing this code. Normally above class & code is used from
# some other class, such as vrmLogger or the pubsub Implementation.
def main():
	# Argument parsing
	parser = argparse.ArgumentParser(
		description='dbusMonitor.py demo run'
	)

	parser.add_argument("-d", "--debug", help="set logging level to debug",
					action="store_true")

	args = parser.parse_args()

	# Init logging
	logging.basicConfig(level=(logging.DEBUG if args.debug else logging.INFO))
	logging.info(__file__ + " is starting up")
	logLevel = {0: 'NOTSET', 10: 'DEBUG', 20: 'INFO', 30: 'WARNING', 40: 'ERROR'}
	logging.info('Loglevel set to ' + logLevel[logging.getLogger().getEffectiveLevel()])

	# Have a mainloop, so we can send/receive asynchronous calls to and from dbus
	DBusGMainLoop(set_as_default=True)

	d = DbusMonitor(value_changed_on_dbus)

	logging.info("==configchange values==")
	logging.info(pprint.pformat(d.get_values(['configChange'])))

	logging.info("==onIntervalAlways and onIntervalOnlyWhenChanged==")
	logging.info(pprint.pformat(d.get_values(['onIntervalAlways', 'onIntervalAlwaysAndOnEvent'])))

	# Start and run the mainloop
	#logging.info("Starting mainloop, responding on only events")
	#mainloop = gobject.MainLoop()
	#mainloop.run()

if __name__ == "__main__":
	main()
