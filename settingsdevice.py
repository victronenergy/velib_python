import dbus
# Local imports
from busitem import BusItem
import tracing

## Indexes for the setting dictonary.
VALUE = 0
MINIMUM = 1
MAXIMUM = 2

## The Settings Device class.
#
# The dbus-services are added as a instance of the SettingsDevice-class.
# The tree of dbus-items (dbus-object-path, dbus-object) is processed at
# the constructor.    
class SettingsDevice(object):
	## The constructor processes the tree of dbus-items.
	# @param name the dbus-service-name.
	# @param tree the tree of dbus-items.
	# @param eventCallback the callback function for the trigger-events
	def __init__(self, bus, name, mainGroup, supportedSettings, eventCallback):
		self._bus = bus
		self._dbus_name = name
		self._eventCallback = eventCallback
		self._mainGroup = mainGroup
		self._addGroup = None
		self._supportedSettings = supportedSettings
		self._settings = {}
		self._addItems(bus, name)
		
	def __del__(self):
		tracing.log.info('SettingsDevice __del__')
		self._deleteSettings()

	def _deleteSettings(self):
		for setting in self._settings:
			if setting:
				self._settings[setting].delete()
		self._settings = {}

	def refreshTree(self):
		self._deleteSettings()
		self._addItems(self._bus, self._dbus_name)

	## Adds the dbus-item to the _settings (if supported).
	# And sets the callback per dbus-item.
	# @param bus the system/session bus
	# @param name the service-name
	def _addItems(self, bus, name):
		for path in self._supportedSettings:
			busitem = BusItem(bus, name, path)
			if busitem.valid:
				tracing.log.info("Found setting: %s" % path)
				self._settings[path] = busitem
				if self._eventCallback:
					busitem.SetEventCallback(self._eventCallback)
		self._addGroup = BusItem(bus, name, self._mainGroup)

	## Returns the dbus-service-name which represents the Victron-Settings-device.
	def __str__(self):
		return "SettingsDevice = %s" % self._dbus_name
	
	## Returns the found dbus-object-paths
	def getPaths(self):
		return list(self._settings)
	
	def addSetting(self, setting, value, minimum, maximum):
		name = setting.replace(self._mainGroup + '/', '', 1)
		if type(value) == int or type(value) == dbus.Int16 or type(value) == dbus.Int32 or type(value) == dbus.Int64:
			itemType = 'i'
		elif type(value) == float or type(value) == dbus.Double:
			itemType = 'f'
		else:
			itemType = 's'
		self._addGroup.AddSetting('', name, value, itemType, minimum, maximum)

	## Return the value of the specified setting (= dbus-object-path).
	def getValue(self, setting):
		value = self._settings[setting].value
		return value

## Check the setting device is our setting are available.
#
# Check if settings are missing and adds them.
# After adding new settings the tree of settingsDevice is refreshed.
# @param settingsDevice the dbus settings device
# @param settings the settings dictonary
def checkSettingsDevice(settingsDevice, settings):
	# Check if the required settings are available.
	settingsAdded = False
	paths = settingsDevice.getPaths()
	for setting in settings:
		if setting not in paths:
			settingsDevice.addSetting(setting, settings[setting][VALUE], settings[setting][MINIMUM], settings[setting][MAXIMUM])
			settingsAdded = True
	if settingsAdded is True:
		tracing.log.info("Refresh settings (after adding settings): %s" % settingsDevice)
		settingsDevice.refreshTree()

