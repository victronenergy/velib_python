import dbus
import dbus.service

# vedbus contains two classes:
# VeDbusItemImport -> use this to read data from the dbus
# VeDbusItemExport -> use this to export data to the dbus

# todos (last update mva 2014-2-2)
# 1) check for datatypes, it works now, but not sure if all is compliant with 
#    com.victronenergy.BusItem interface definition.
# 2) Shouldn't VeDbusBusItemExport inherit dbus.service.Object? See
#    

# Below code is copied, and thereafter modified, from busitem.py. All projects 
# that used busitem.py need to migrate to this package.

class VeDbusItemImport(object):

	## Constructor
	# And constructs the tree of dbus-object-paths with their dbus-object.
	# @param bus the bus-object (SESSION or SYSTEM).
	# @param service the dbus-service-name.
	# @param path the object-path.
	def __init__(self, bus, service, path, eventCallback = None):
		self._dbus_name = service
		self._path = path
		self._eventCallback = eventCallback
		self._object = bus.get_object(service, path)
		self._match = None if self._eventCallback == None else self._object.connect_to_signal("PropertiesChanged", self._properties_changed_handler)

	def delete(self):
		if self._match:
			self._match.remove()
			del(self._match)

	def GetPath(self):
		return self._path
		
	## Returns the value of the dbus-item.
	# the type will be a dbus variant, for example dbus.Int32(0, variant_level=1)
	def GetValue(self):
		return self._object.GetValue()

	## Returns a boolean. For com.victronenergy.BusItem, the definition is that invalid values
	# are represented as an empty array.
	def isValid(self):
		return self.GetValue() != dbus.Array([])

	## Returns the text representation of the value. For example when the value is an enum/int
	# GetText might return the string belonging to that enum value. Another example, for a
	# voltage, GetValue would return a float, 12.0Volt, and GetText could return 12 VDC.
	# Note that this depends on how the dbus-producer has implemented this.
	def GetText(self):
		return self._object.GetText()

	## Sets the callback for the trigger-event.
	# @param eventCallback the event-callback-funciton.	
	def SetEventCallback(self, eventCallback):
		self._eventCallback = eventCallback

	## Is called when the value of a bus-item changes.
	# When the event-callback is set it calls this function.
	# @param changes the changed properties.
	def _properties_changed_handler(self, changes):
		if "Value" in changes:
			self._value = changes["Value"]
			if self._eventCallback:
				self._eventCallback(self._dbus_name, self._path, changes)


class VeDbusItemExport(dbus.service.Object):
	## Constructor of VeDbusItemExport
	#
	# Use this object to export (publish), values on the dbus
	# Creates the dbus-object under the given dbus-service-name.
	# @param bus The dbus object.
	# @param objectPath The dbus-object-path.
	# @param callback, a function that will be called when someone else changes the value of this VeBusItem over the dbus
	def __init__(self, bus, objectPath, value = 0, isValid = False, description = '', callback = None):
		dbus.service.Object.__init__(self, bus, objectPath)
		self._callback = callback
		self._value = value
		self._description = description
		self._isValid = isValid
		print 'init ' + objectPath

	## Dbus method GetDescription
	#
	# Returns the a description. Currently not implemented.
	# Alwayes returns 'no description available'.
	# @param language A language code (e.g. ISO 639-1 en-US).
	# @param length Lenght of the language string. 
	# @return description
	@dbus.service.method('com.victronenergy.BusItem', in_signature = 'si', out_signature = 's')
	def GetDescription(self, language, length):
		#print('VeDbusObject.GetDescription %s' % self._object_path)
		return self._description

	## Dbus method GetValue
	# Returns the value.
	# @return the value when valid, and otherwise an empty array
	@dbus.service.method('com.victronenergy.BusItem', out_signature = 'v')
	def GetValue(self):
		#print('VeDbusObject.GetValue %s' % self._object_path)
		if self._isValid:
			value = self._value
		else:
			value = dbus.Array([], signature=dbus.Signature('i'), variant_level=1)
		return value
		
	## Dbus method GetText
	# Returns the value as string of the dbus-object-path.
	# @return text A text-value or '' (error)
	@dbus.service.method('com.victronenergy.BusItem', out_signature = 's')
	def GetText(self):
		#print('VeDbusObject.GetText %s' % self._object_path)
		return str(self._value) if self._isValid else '---'
	
	## Dbus method SetValue
	# Sets the value.
	# @param value The new value.
	# @return completion-code When successful a 0 is return, and when not a -1 is returned.
	@dbus.service.method('com.victronenergy.BusItem', in_signature = 'v', out_signature = 'i')
	def SetValue(self, value):
		changes = {}
		if value != self._value:
			changes['Value'] = value
			self._value = value	
			changes['Text'] = self.GetText()
		
		if len(changes) > 0:
			print ('VeDbusObject.Properties changed, ' + self._object_path + ', changes:' + str(changes))
			self.PropertiesChanged(changes)
		return 0
	
	# Function that sends out a signal to all processes that are connected to this object on the dbus
	@dbus.service.signal('com.victronenergy.BusItem', signature = 'a{sv}')
	def PropertiesChanged(self, changes):
		pass

	# Function to be used in python code. When value is different from before
	# automatically the properties changed signal will be sent to dbus
	def local_set_value(value, isValid):
		self._value = value
		self._isValid = isValid
    	# TODO signal that we have changed. 
