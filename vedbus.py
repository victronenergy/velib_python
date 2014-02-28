#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus
import dbus.service
import logging

# vedbus contains two classes:
# VeDbusItemImport -> use this to read data from the dbus, ie import
# VeDbusItemExport -> use this to export data to the dbus

# Code for VeDbusItemImport is copied from busitem.py and thereafter modified.
# All projects that used busitem.py need to migrate to this package. And some
# projects used to define there own equivalent of VeDbusItemExport. Better to
# use that.

# TODOS (last update mva 2014-2-8)
# 1 check for datatypes, it works now, but not sure if all is compliant with
#	com.victronenergy.BusItem interface definition. See also the files in
#	tests_and_examples. And see 'if type(v) == dbus.Byte:' on line 102. Perhaps
#	something similar should also be done in VeDbusBusItemExport?
# 2 Shouldn't VeDbusBusItemExport inherit dbus.service.Object?
# 3	do we want VeDbusItemImport to keep a local copy of the value, so when
#	the python code needs it, it doesn need to go on the dbus to get it?
#	when we do this, also the subscribing to the change signal needs to change,
#	because weĺl need to subscribe always, not only when an eventcallback is
#	given.
# 4 implement a mechanism in VeDbusItemExport to have a GetText that is not
#	just str(GetValue()). I see only one option, and that is to allow py code
#	to register a function for GetText. Another solution that won't work:
#	when supplying a new value, you could also at  that time supply the GetText
#	string. But that won't work when other processes start changing your values
#	over the dbus.
# 6 Consider having a global that specifies the value of invalid. And decide
#   which one is right, see todos in the code.
#
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

	## delete(self)
	def __del__(self):
		if self._match:
			# remove the signal match from the dbus connection.
			self._match.remove()
			del(self._match)

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
	def GetValue(self):
		v = self._object.GetValue()

		# For some reason, str(dbus.Byte(84)) == 'T'. And bytes on the dbus are not meant to be characters
		# so, fix that.
		if type(v) == dbus.Byte:
			v = int(self._object.GetValue())

		return v

	## Returns False if the value is invalid. Otherwise returns True
	# In the interface com.victronenergy.BusItem, the definition is that invalid
	# values are represented as an empty array.
	@property
	def isValid(self):
		# TODO: test is dbus.Array([]) is ok. Or if should be
		# dbus.Array([], signature=dbus.Signature('i'), variant_level=1) instead.

		return self.GetValue() != dbus.Array([])

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
	# calls the eventCallback, if set.
	# @param changes the changed properties.
	def _properties_changed_handler(self, changes):
		if "Value" in changes:
			self._value = changes["Value"]
			if self._eventCallback:
				self._eventCallback(self._serviceName, self._path, changes)


class VeDbusItemExport(dbus.service.Object):
	## Constructor of VeDbusItemExport
	#
	# Use this object to export (publish), values on the dbus
	# Creates the dbus-object under the given dbus-service-name.
	# @param bus			The dbus object.
	# @param objectPath		The dbus-object-path.
	# @param value			Value to initialize ourselves with, defaults to 0
	# @param isValid		Should we initialize with a valid value, defaults to False
	# @param description	String containing a description. Can be called over the dbus with GetDescription()
	# @param callback		Function that will be called when someone else changes the value of this VeBusItem
	#                       over the dbus
	def __init__(self, bus, objectPath, value=0, isValid=False, description='', callback=None):
		dbus.service.Object.__init__(self, bus, objectPath)
		self._callback = callback
		self._value = value
		self._description = description

	## Sets the value. And in case the value is different from what it was, a signal
	# will be emitted to the dbus. This function is to be used in the python code that
	# is using this class to export values to the dbus
	def local_set_value(self, value, isValid=True):
		# when invalid, set value to the definition of invalid
		# TODO: why is this signature and variant_level specified here? I have seen it without
		# also: IsValid in the other class
		newvalue = value if isValid else dbus.Array([], signature=dbus.Signature('i'), variant_level=1)

		# call the same function that is also used to change our value over the dbus
		self.SetValue(newvalue)

	## Returns true when the local stored value is valid, and if not, it will return false
	def local_is_valid(self):
		# TODO: why is this signature and variant_level specified here? I have seen it without
		# also: IsValid in the other class
		return self._value != dbus.Array([], signature=dbus.Signature('i'), variant_level=1)

	# ==== ALL FUNCTIONS BELOW THIS LINE WILL BE CALLED BY OTHER PROCESSES OVER THE DBUS ====

	## Dbus exported method GetDescription
	#
	# Returns the a description. Currently not implemented.
	# Alwayes returns 'no description available'.
	# @param language A language code (e.g. ISO 639-1 en-US).
	# @param length Lenght of the language string.
	# @return description
	@dbus.service.method('com.victronenergy.BusItem', in_signature='si', out_signature='s')
	def GetDescription(self, language, length):
		return self._description

	## Dbus exported method GetValue
	# Returns the value.
	# @return the value when valid, and otherwise an empty array
	@dbus.service.method('com.victronenergy.BusItem', out_signature='v')
	def GetValue(self):
		return self._value

	## Dbus exported method GetText
	# Returns the value as string of the dbus-object-path.
	# @return text A text-value or '' (error)
	@dbus.service.method('com.victronenergy.BusItem', out_signature='s')
	def GetText(self):
		return str(self._value) if self.local_is_valid() else '---'

	## Dbus exported method SetValue
	# Sets the value.
	# will emit a changed-signal when the value is different from before
	# @param value The new value.
	# @return completion-code When successful a 0 is return, and when not a -1 is returned.
	@dbus.service.method('com.victronenergy.BusItem', in_signature='v', out_signature='i')
	def SetValue(self, value):
		changes = {}
		if value != self._value:
			self._value = value
			changes['Value'] = value
			changes['Text'] = self.GetText()

		if len(changes) > 0:
			self.PropertiesChanged(changes)
		return 0

	## The signal that indicates that the value has changed.
	# Other processes connected to this BusItem object will have subscribed to the
	# event when they want to track our state.
	@dbus.service.signal('com.victronenergy.BusItem', signature='a{sv}')
	def PropertiesChanged(self, changes):
		pass
