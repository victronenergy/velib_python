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

VEDBUS_INVALID =dbus.Array([], signature=dbus.Signature('i'), variant_level=1)

# Export ourselves as a D-Bus service.
class VeDbusService(object):
	def __init__(self, servicename):
		# dict containing the VeDbusItemExport objects, with their path as the key.
		self._dbusobjects = {}

		# dict containing the onchange callbacks, for each object. Object path is the key
		self._onchangecallbacks = {}

		# For a PC, connect to the SessionBus
		# For a CCGX, connect to the SystemBus
		self._dbusconn = dbus.SystemBus(True) if (platform.machine() == 'armv7l') else dbus.SessionBus(True)

		# make the dbus connection available to outside, could make this a true property instead, but ach..
		self.dbusconn = self._dbusconn

		# Register ourserves on the dbus
		self._dbusname = dbus.service.BusName(servicename, self._dbusconn)

		logging.info("registered ourselves on D-Bus as %s" % servicename)

	# Invalidate all values before going off the dbus
	def __del__(self):
		for sensor in self._dbusobjects.values():
			sensor.local_set_value(None)

	# @param callbackonchange	function that will be called when this value is changed. First parameter will
	#							be the path of the object, second the new value. This callback should return
	#							True to accept the change, False to reject it.
	def add_path(self, path, value, description="", writeable=False,
					onchangecallback=None, gettextcallback=None):

		if onchangecallback is not None:
			self._onchangecallbacks[path] = onchangecallback

		self._dbusobjects[path] = VeDbusItemExport(
				self._dbusconn, path, value, description, writeable,
				self._value_changed, gettextcallback)

	# Add the mandatory paths, as per victron dbus api doc
	def add_mandatory_paths(self, processname, processversion, connection,
			deviceinstance, productid, productname, firmwareversion, hardwareversion, connected):
		self.add_path('/Management/ProcessName', processname)
		self.add_path('/Management/ProcessVersion', processversion)
		self.add_path('/Management/Connection', connection)

		# Create rest of the mandatory objects
		self.add_path('/DeviceInstance', deviceinstance)
		self.add_path('/ProductId', productid)
		self.add_path('/ProductName', productname)
		self.add_path('/FirmwareVersion', firmwareversion)
		self.add_path('/HardwareVersion', hardwareversion)
		self.add_path('/Connected', connected)

	# Callback function that is called from the VeDbusItemExport objects when a value changes. This function
	# maps the change-request to the onchangecallback given to us for this specific path.
	def _value_changed(self, path, newvalue):
		if path not in self._onchangecallbacks:
			return True

		return self._onchangecallbacks[path](path, newvalue)

	def __getitem__(self, path):
		return self._dbusobjects[path].local_get_value()

	def __setitem__(self, path, newvalue):
		self._dbusobjects[path].local_set_value(newvalue)

	def __delitem__(self, path):
		# Set value to invalid first, will cause signal change to be emitted when value was not None
		self[path] = None

		# Todo, check that this is the right command to delete an item.
		del self[path]

	def __contains__(self, path):
		return path in self._dbusobjects


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

		# store the current value in _cachedvalue. When it doesnt exists set _cachedvalue to
		# None, same as when a value is invalid
		self._cachedvalue = None
		if self.exists:
			self._refreshcachedvalue()

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

		if value == VEDBUS_INVALID:
			value = None

		return value

	def _refreshcachedvalue(self):
		self._cachedvalue = self._fixtypes(self._object.GetValue())

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
	# returns None when the property is invalid
	def get_value(self):
		return self._cachedvalue

	## Writes a new value to the dbus-item
	def set_value(self, newvalue):
		r = self._object.SetValue(newvalue if newvalue is not None else VEDBUS_INVALID)

		# instead of just saving the value, go to the dbus and get it. So we have the right type etc.
		if r == 0:
			self._refreshcachedvalue()

		return r

	## Returns the text representation of the value.
	# For example when the value is an enum/int GetText might return the string
	# belonging to that enum value. Another example, for a voltage, GetValue
	# would return a float, 12.0Volt, and GetText could return 12 VDC.
	#
	# Note that this depends on how the dbus-producer has implemented this.
	def get_text(self):
		return self._object.GetText()

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
			changes['Value'] = self._fixtypes(changes['Value'])
			self._cachedvalue = changes['Value']
			if self._eventCallback:
				self._eventCallback(self._serviceName, self._path, changes)


class VeDbusItemExport(dbus.service.Object):
	## Constructor of VeDbusItemExport
	#
	# Use this object to export (publish), values on the dbus
	# Creates the dbus-object under the given dbus-service-name.
	# @param bus		  The dbus object.
	# @param objectPath	  The dbus-object-path.
	# @param value		  Value to initialize ourselves with, defaults to None which means Invalid
	# @param description  String containing a description. Can be called over the dbus with GetDescription()
	# @param writeable	  what would this do!? :).
	# @param callback	  Function that will be called when someone else changes the value of this VeBusItem
	#                     over the dbus. First parameter passed to callback will be our path, second the new
	#					  value. This callback should return True to accept the change, False to reject it.
	def __init__(self, bus, objectPath, value=None, description=None, writeable=False,
					onchangecallback=None, gettextcallback=None):
		dbus.service.Object.__init__(self, bus, objectPath)
		self._onchangecallback = onchangecallback
		self._gettextcallback = gettextcallback
		self._value = value
		self._description = description
		self._writeable = writeable

	## Sets the value. And in case the value is different from what it was, a signal
	# will be emitted to the dbus. This function is to be used in the python code that
	# is using this class to export values to the dbus.
	# set value to None to indicate that it is Invalid
	def local_set_value(self, newvalue):
		if self._value == newvalue:
			return

		self._value = newvalue

		changes = {}
		changes['Value'] = newvalue if newvalue is not None else VEDBUS_INVALID
		changes['Text'] = self.GetText()
		self.PropertiesChanged(changes)

	def local_get_value(self):
		return self._value

	# ==== ALL FUNCTIONS BELOW THIS LINE WILL BE CALLED BY OTHER PROCESSES OVER THE DBUS ====

	## Dbus exported method SetValue
	# Function is called over the D-Bus by other process. It will first check (via callback) if new
	# value is accepted. And it is, stores it and emits a changed-signal.
	# @param value The new value.
	# @return completion-code When successful a 0 is return, and when not a -1 is returned.
	@dbus.service.method('com.victronenergy.BusItem', in_signature='v', out_signature='i')
	def SetValue(self, newvalue):
		if not self._writeable:
			return 1  # NOT OK

		if newvalue is VEDBUS_INVALID:
			newvalue = None

		if newvalue == self._value:
			return 0  # OK

		# call the callback given to us, and check if new value is OK.
		if (self._onchangecallback is None or
				(self._onchangecallback is not None and self._onchangecallback(self.__dbus_object_path__, newvalue))):

			self.local_set_value(newvalue)
			return 0  # OK

		return 2  # NOT OK

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
		return self._value if self._value is not None else VEDBUS_INVALID

	## Dbus exported method GetText
	# Returns the value as string of the dbus-object-path.
	# @return text A text-value. '---' when local value is invalid
	@dbus.service.method('com.victronenergy.BusItem', out_signature='s')
	def GetText(self):
		if self._value is None:
			return '---'

		# See VeDbusItemImport._fixtypes for why we int() an dbus.Byte
		if self._gettextcallback is None and type(self._value) == dbus.Byte:
			return str(int(self._value))

		if self._gettextcallback is None:
			return str(self._value)

		return self._gettextcallback(self.__dbus_object_path__, self._value)

	## The signal that indicates that the value has changed.
	# Other processes connected to this BusItem object will have subscribed to the
	# event when they want to track our state.
	@dbus.service.signal('com.victronenergy.BusItem', signature='a{sv}')
	def PropertiesChanged(self, changes):
		pass
