## IMPORTANT NOTE - MVA 2015-2-5 
# This file is deprecated. Use the classes in vedbus.py from now on. If you are
# working on some project, please change it, and make it work with the classes
# in vedbus.py

import dbus
import logging

# Local imports
import tracing

## Implements a velib bus-item as a local object.
class BusItem(object):

	## The constructor introspects the dbus-service.
	# And constructs the tree of dbus-object-paths with their dbus-object.
	# @param bus the bus-object (SESSION or SYSTEM).
	# @param service the dbus-service-name.
	# @param path the object-path.
	def __init__(self, bus, service, path):
		# MVA 2014-1-5: removed the error handling here. I don't see why an error should only result 
		# in tracing an error. Better to just let the whole thing crash and let Python print callstack etc.
#		try:
			logging.debug("busitem.py.__init()___: service: %s, path: %s" % (service, path))
			self._dbus_name = service
			self._path = path
			self._value = None
			self._text = None
			self._eventCallback = None
			self._object = bus.get_object(service, path)
			self._match = self._object.connect_to_signal("PropertiesChanged", self._properties_changed_handler)
#		except Exception, ex:
#			tracing.log.error("Busitem __init__ exception: %s" % ex)

	def __del__(self):
		logging.debug('Busitem __del__ %s %s' % (self._dbus_name, self._path))

	def delete(self):
		if self._match:
			self._match.remove()
			del(self._match)

	## Returns the value of the dbus-item.
	def GetValue(self):
		if self._value is None:
			try:
				self._value = self._object.GetValue()
			except:
				logging.error("Value exception %s %s" % (self._dbus_name, self._path))
				self._value = dbus.Array([])
		return self._value

	value = property(GetValue)
	
	def Valid(self):
		value = self.GetValue()
		valid = (value != dbus.Array([]))
		return valid

	valid = property(Valid)

	## Sets the callback for the trigger-event.
	# @param eventCallback the event-callback-funciton.	
	def SetEventCallback(self, eventCallback):
		self._eventCallback = eventCallback

	@property
	def text(self):
		if self._text is None or self._match is None:
			try:
				self._text = self._object.GetText()
			except Exception, ex:
				logging.error("GetText exception %s %s" % (self._dbus_name, self._path))
		return self._text

	## Is called when the value of a bus-item changes.
	# When the event-callback is set it calls this function.
	# @param changes the changed properties.
	def _properties_changed_handler(self, changes):
		if "Value" in changes:
			self._value = changes["Value"]
			if self._eventCallback:
				self._eventCallback(self._dbus_name, self._path, changes)

