## IMPORTANT NOTE - MVA 2015-2-5 
# Have not really looked at below code yet, but it is highly probable
# that it could be an overload of a class in vedbus.py

import dbus
# Local imports
from busitem import BusItem
import tracing

## Indexes for the setting dictonary.
VALUE = 0
MINIMUM = 1
MAXIMUM = 2

## The Settings Device class.
# Used by python programs, such as the vrm-logger, to read and write settings they
# need to store on disk. And since these settings might be changed from a different
# source, such as the GUI, the program can pass an eventCallback that will be called
# as soon as some setting is changed.
#
# If there are settings in de supportSettings list which are not yet on the dbus, 
# and therefore not yet in the xml file, they will be added through the dbus-addSetting
# interface of com.victronenergy.settings.
class SettingsDevice(object):
	## The constructor processes the tree of dbus-items.
	# @param bus the system-dbus object
	# @param name the dbus-service-name of the settings dbus service, 'com.victronenergy.settings'
	# @param supportedSettings dictionary with all setting-names, and their defaultvalue, min and max.
	# @param eventCallback function that will be called on changes on any of these settings
	def __init__(self, bus, name, supportedSettings, eventCallback):
		self._bus = bus
		self._dbus_name = name
		self._eventCallback = eventCallback
		self._supportedSettings = supportedSettings
		self._settings = {}
		self._addItems(bus, name)
		
	def __del__(self):
		tracing.log.debug('SettingsDevice __del__')
		self._deleteSettings()

	def _deleteSettings(self):
		for setting in self._settings:
			if setting:
				self._settings[setting].delete()
		self._settings = {}

	def refreshTree(self):
		self._deleteSettings()
		self._addItems(self._bus, self._dbus_name)

	## Loops through the supportedSettings dictionary
	# Checks if the path is available, if not adds it.
	# @param bus the system/session bus
	# @param name the service-name
	def _addItems(self, bus, name):
		import pprint
		for path in self._supportedSettings:
			busitem = BusItem(bus, name, path)
			if busitem.valid:
				tracing.log.debug("Setting %s found" % path)
			else:
				tracing.log.debug("Setting %s does not exist yet, adding it" % path)

				# Prepare to add the setting.
				name = path.replace('/Settings/', '', 1)
				value = self._supportedSettings[path][VALUE]
				if type(value) == int or type(value) == dbus.Int16 or type(value) == dbus.Int32 or type(value) == dbus.Int64:
					itemType = 'i'
				elif type(value) == float or type(value) == dbus.Double:
					itemType = 'f'
				else:
					itemType = 's'
				
				# Call the dbus interface AddSetting
				BusItem(self._bus, self._dbus_name, '/Settings')._object.AddSetting('', name, value, itemType, self._supportedSettings[path][MINIMUM], self._supportedSettings[path][MAXIMUM])

				busitem = BusItem(bus, name, path)
			
				if not busitem.valid:
					raise "error, still not valid after trying to add the setting. Something is wrong. Exit."
					
			if self._eventCallback:
					busitem.SetEventCallback(self._eventCallback)
					
			self._settings[path] = busitem
					

	## Returns the dbus-service-name which represents the Victron-Settings-device.
	def __str__(self):
		return "SettingsDevice = %s" % self._dbus_name
	
	## Returns the found dbus-object-paths
	def getPaths(self):
		return list(self._settings)
	
	## Return the value of the specified setting (= dbus-object-path).
	def getValue(self, setting):
		value = self._settings[setting].value
		return value
