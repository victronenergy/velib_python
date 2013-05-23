import dbus
# Local imports
from dbusitem import Dbusitem
import tracing

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
	def __init__(self, bus, name, tree, mainGroup, supportedSettings, eventCallback):
		self._bus = bus
		self._dbus_name = name
		self._eventCallback = eventCallback
		self._mainGroup = mainGroup
		self._addGroup = None
		self._supportedSettings = supportedSettings
		self._settings = {}
		self._tree = tree
		tree.foreach(self.__add_item)
		
	def __del__(self):
		tracing.log.debug('SettingsDevice __del__')
		self._settings = {}
		self._tree._delete()

	def refreshTree(self):
		#self._tree.updateChildNodes(self._bus, self._dbus_name)
		self._settings = {}
		self._tree._delete()
		self._tree = Dbusitem(self._bus, self._dbus_name, '/')
		self._tree.foreach(self.__add_item)

	## Adds the dbus-item to the _settings (if supported).
	# And sets the callback per dbus-item.
	# @param dbusitem the dbus-item.
	def __add_item(self, dbusitem):
		if dbusitem.object.object_path in self._supportedSettings:
			tracing.log.info("Found setting: %s" % dbusitem.object.object_path)
			self._settings[dbusitem.object.object_path] = dbusitem
			if self._eventCallback:
				dbusitem.SetEventCallback(self._eventCallback)
		elif dbusitem.object.object_path == self._mainGroup:
			self._addGroup = dbusitem

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

