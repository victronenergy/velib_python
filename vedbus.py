#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus
import dbus.service
import logging
import platform

# vedbus contains three classes:
# VeDbusItemImport -> use this to read data from the dbus, ie import
# VeDbusItemExport -> use this to export data to the dbus (one value)
# VeDbusService -> use that to create a service and export several values to the dbus

# Code for VeDbusItemImport is copied from busitem.py and thereafter modified.
# All projects that used busitem.py need to migrate to this package. And some
# projects used to define there own equivalent of VeDbusItemExport. Better to
# use VeDbusItemExport, or even better the VeDbusService class that does it all for you.

# TODOS
# 1 check for datatypes, it works now, but not sure if all is compliant with
#	com.victronenergy.BusItem interface definition. See also the files in
#	tests_and_examples. And see 'if type(v) == dbus.Byte:' on line 102. Perhaps
#	something similar should also be done in VeDbusBusItemExport?
# 2 Shouldn't VeDbusBusItemExport inherit dbus.service.Object?
# 7 Make hard rules for services exporting data to the D-Bus, in order to make tracking
#   changes possible. Does everybody first invalidate its data before leaving the bus?
#   And what about before taking one object away from the bus, instead of taking the
#   whole service offline?
#   They should! And after taking one value away, do we need to know that someone left
#   the bus? Or we just keep that value in invalidated for ever? Result is that we can't
#   see the difference anymore between an invalidated value and a value that was first on
#   the bus and later not anymore.
# 9 there are probably more todos in the code below.

# Some thoughts with regards to the data types:
#
#   Text from: http://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html#data-types
#   ---
#   Variants are represented by setting the variant_level keyword argument in the
#   constructor of any D-Bus data type to a value greater than 0 (variant_level 1
#   means a variant containing some other data type, variant_level 2 means a variant
#   containing a variant containing some other data type, and so on). If a non-variant
#   is passed as an argument but introspection indicates that a variant is expected,
#   it'll automatically be wrapped in a variant.
#   ---
#
#   Also the different dbus datatypes, such as dbus.Int32, and dbus.UInt32 are a subclass
#   of Python int. dbus.String is a subclass of Python standard class unicode, etcetera
#
#   So all together that explains why we don't need to explicitly convert back and forth
#   between the dbus datatypes and the standard python datatypes. Note that all datatypes
#   in python are objects. Even an int is an object.

#   The signature of a variant is 'v'.

VEDBUS_INVALID = dbus.Array([])

# Export ourselves as a D-Bus service.
class VeDbusService(object):
	def __init__(self, servicename):
		# dict containing the VeDbusItemExport objects, with their path as the key.
		self._dbusobjects = {}

		# dict containing the onchange callbacks, for each object. Object path is the key
		self._onchangecallbacks = {}

		# For a PC, connect to the SessionBus
		# For a CCGX, connect to the SystemBus
		self._dbusconn = dbus.SystemBus() if (platform.machine() == 'armv7l') else dbus.SessionBus()

		# Register ourserves on the dbus
		self._dbusname = dbus.service.BusName(servicename, self._dbusconn)

		logging.info("registered ourselves on D-Bus as %s" % servicename)

	# @param callbackonchange	function that will be called when this value is changed. First parameter will
	#							be the path of the object, second the new value. This callback should return
	#							True to accept the change, False to reject it.
	def add_path(self, path, value, isvalid=True, description="", writeable=False,
					onchangecallback=None, gettextcallback=None):
		if onchangecallback is not None:
			self._onchangecallbacks[path] = onchangecallback

		self._dbusobjects[path] = VeDbusItemExport(
				self._dbusconn, path, value, isvalid, description, writeable,
				self._value_changed, gettextcallback)

	# Callback function that is called from the VeDbusItemExport objects when a value changes. This function
	# maps the change-request to the onchangecallback given to us for this specific path.
	def _value_changed(self, path, newvalue):
		if path not in self._onchangecallbacks:
			return True

		return self._onchangecallbacks[path](path, newvalue)

	def get_value(self, path):
		return self._dbusobjects[path].GetValue()

	def is_valid(self, path):
		return self._dbusobjects[path].local_is_valid()

	def set_value(self, path, newvalue, isvalid=True):
		self._dbusobjects[path].local_set_value(newvalue, isvalid)


class VeDbusItemImport(object):
	## Constructor
	# And constructs the tree of dbus-object-paths with their dbus-object.
	# @param bus			the bus-object (SESSION or SYSTEM).
	# @param serviceName	the dbus-service-name (string).
	# @param path			the object-path.
	# @param eventCallback	function that you want to be called on a value change
	def __init__(self, bus, serviceName, path, eventCallback=None):
		# TODO: is it necessary to store _serviceName and _path? Isn't it
		# stored in the bus_getobjectsomewhere?
		self._serviceName = serviceName
		self._path = path
		self._object = bus.get_object(serviceName, path)
		self._match = None
		self.eventCallback = eventCallback

		# store the current value in _cachedvalue. When it doesnt exists set _cachedvalue to None.
		self._cachedvalue = self._object.GetValue() if self.exists else None

	## delete(self)
	def __del__(self):
		if self._match:
			# remove the signal match from the dbus connection.
			self._match.remove()
			del(self._match)

	## Do the conversions that are necessary when getting something from the D-Bus.
	def _fixtypes(self, value):
		# For some reason, str(dbus.Byte(84)) == 'T'. Bytes on the dbus are not meant to be a char.
		# so, fix that.
		if type(value) == dbus.Byte:
			value = int(value)

		return value

	## Returns the path as a string, for example '/AC/L1/V'
	@property
	def path(self):
		return self._path

	## Returns the dbus service name as a string, for example com.victronenergy.vebus.ttyO1
	@property
	def serviceName(self):
		return self._serviceName

	## Returns the value of the dbus-item.
	# the type will be a dbus variant, for example dbus.Int32(0, variant_level=1)
	# this is not a property to keep the name consistant with the com.victronenergy.busitem interface
	# returns None when the property doesn't exist.
	def GetValue(self):
		return self._fixtypes(self._cachedvalue) if self._cachedvalue is not None else None

	## Writes a new value to the dbus-item
	def SetValue(self, newvalue):
		r = self._object.SetValue(newvalue)

		# instead of just saving the value, go to the dbus and get it. So we have the right type etc.
		if r == 0:
			self._cachedvalue = self._object.GetValue()

		return r

	## Returns False if the value is invalid. Otherwise returns True
	# In the interface com.victronenergy.BusItem, the definition is that invalid
	# values are represented as an empty array.
	@property
	def isValid(self):
		return self.GetValue() != VEDBUS_INVALID

	## Returns true of object path exists, and false if it doesn't
	@property
	def exists(self):
		# TODO: do some real check instead of this crazy thing.
		r = False
		try:
			r = self._object.GetValue()
			r = True
		except dbus.exceptions.DBusException:
			pass

		return r

	## Returns the text representation of the value.
	# For example when the value is an enum/int GetText might return the string
	# belonging to that enum value. Another example, for a voltage, GetValue
	# would return a float, 12.0Volt, and GetText could return 12 VDC.
	#
	# Note that this depends on how the dbus-producer has implemented this.
	def GetText(self):
		return self._object.GetText()

	## callback for the trigger-event.
	# @param eventCallback the event-callback-function.
	@property
	def eventCallback(self):
		return self._eventCallback

	@eventCallback.setter
	def eventCallback(self, eventCallback):

		# remove the signalMatch from the dbus connection if we no longer need it
		if eventCallback is None and self._match is not None:
			self._match.remove()

		# add the signalMatch to the dbus connection if we do need it and didn't have it yet
		if eventCallback is not None and self._match is None:
			self._match = self._object.connect_to_signal("PropertiesChanged", self._properties_changed_handler)

		self._eventCallback = eventCallback

	## Is called when the value of the imported bus-item changes.
	# Stores the new value in our local cache, and calls the eventCallback, if set.
	def _properties_changed_handler(self, changes):
		if "Value" in changes:
			self._cachedvalue = changes['Value']
			changes['Value'] = self._fixtypes(changes['Value'])
			if self._eventCallback:
				self._eventCallback(self._serviceName, self._path, changes)


class VeDbusItemExport(dbus.service.Object):
	## Constructor of VeDbusItemExport
	#
	# Use this object to export (publish), values on the dbus
	# Creates the dbus-object under the given dbus-service-name.
	# @param bus		  The dbus object.
	# @param objectPath	  The dbus-object-path.
	# @param value		  Value to initialize ourselves with, defaults to 0
	# @param isValid	  Should we initialize with a valid value, defaults to False
	# @param description  String containing a description. Can be called over the dbus with GetDescription()
	# @param writeable	  what would this do!? :).
	# @param callback	  Function that will be called when someone else changes the value of this VeBusItem
	#                     over the dbus. First parameter passed to callback will be our path, second the new
	#					  value. This callback should return True to accept the change, False to reject it.
	def __init__(self, bus, objectPath, value=0, isValid=True, description=None, writeable=False,
					onchangecallback=None, gettextcallback=None):
		dbus.service.Object.__init__(self, bus, objectPath)
		self._onchangecallback = onchangecallback
		self._gettextcallback = gettextcallback
		self._value = value if isValid else VEDBUS_INVALID
		self._description = description
		self._writeable = writeable

	## Returns true when the local stored value is valid, and if not, it will return false
	def local_is_valid(self):
		return self._value != VEDBUS_INVALID

	## Sets the value. And in case the value is different from what it was, a signal
	# will be emitted to the dbus. This function is to be used in the python code that
	# is using this class to export values to the dbus
	def local_set_value(self, value, isValid=True):
		# when invalid, set value to the definition of invalid
		if not isValid:
			value = VEDBUS_INVALID

		self._value = value

		changes = {}
		changes['Value'] = value
		changes['Text'] = self.GetText()
		self.PropertiesChanged(changes)

	# ==== ALL FUNCTIONS BELOW THIS LINE WILL BE CALLED BY OTHER PROCESSES OVER THE DBUS ====

	## Dbus exported method SetValue
	# Function is called over the D-Bus by other process. It will first check (via callback) if new
	# value is accepted. And it is, stores it and emits a changed-signal.
	# @param value The new value.
	# @return completion-code When successful a 0 is return, and when not a -1 is returned.
	@dbus.service.method('com.victronenergy.BusItem', in_signature='v', out_signature='i')
	def SetValue(self, value):
		if not self._writeable:
			return 1  # NOT OK

		if value == self._value:
			return 0  # OK

		# call the callback given to us, and check if new value is OK.
		if (self._onchangecallback is None or
				(self._onchangecallback is not None and self._onchangecallback(self.__dbus_object_path__, value))):

			self.local_set_value(value)
			return 0  # OK

		return 1  # NOT OK

	## Dbus exported method GetDescription
	#
	# Returns the a description.
	# @param language A language code (e.g. ISO 639-1 en-US).
	# @param length Lenght of the language string.
	# @return description
	@dbus.service.method('com.victronenergy.BusItem', in_signature='si', out_signature='s')
	def GetDescription(self, language, length):
		return self._description if self._description is not None else 'No description given'

	## Dbus exported method GetValue
	# Returns the value.
	# @return the value when valid, and otherwise an empty array
	@dbus.service.method('com.victronenergy.BusItem', out_signature='v')
	def GetValue(self):
		return self._value

	## Dbus exported method GetText
	# Returns the value as string of the dbus-object-path.
	# @return text A text-value. '---' when local value is invalid
	@dbus.service.method('com.victronenergy.BusItem', out_signature='s')
	def GetText(self):
		if not self.local_is_valid():
			return '---'

		if self._gettextcallback is None:
			return str(self._value)

		return self._gettextcallback(self.__dbus_object_path__, self._value)

	## The signal that indicates that the value has changed.
	# Other processes connected to this BusItem object will have subscribed to the
	# event when they want to track our state.
	@dbus.service.signal('com.victronenergy.BusItem', signature='a{sv}')
	def PropertiesChanged(self, changes):
		pass
