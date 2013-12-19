import dbus

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
		try:
			#tracing.log.info("Busitem %s %s" % (service, path))
			self._dbus_name = service
			self._path = path
			self._value = None
			self._text = None
			self._eventCallback = None
			self._object = bus.get_object(service, path)
			self._match = self._object.connect_to_signal("PropertiesChanged", self._properties_changed_handler)
		except Exception, ex:
			tracing.log.error("Busitem __init__ exception: %s" % ex)

	def __del__(self):
		tracing.log.info('Busitem __del__ %s %s' % (self._dbus_name, self._path))

	def delete(self):
		if self._match:
			self._match.remove()
			del(self._match)

	def AddSetting(self, group, name, defaultValue, itemType, minimum, maximum):
		tracing.log.info('%s AddSetting %s %s %s %s %s %s' % (self._path, group, name, defaultValue, itemType, minimum, maximum))
		self._object.AddSetting(group, name, defaultValue, itemType, minimum, maximum)

	## Returns the value of the dbus-item.
	def GetValue(self):
		if self._value is None:
			try:
				self._value = self._object.GetValue()
			except:
				tracing.log.info("Value exception %s %s" % (self._dbus_name, self._path))
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
				tracing.log.info("GetText exception %s %s" % (self._dbus_name, self._path))
		return self._text

	## Is called when the value of a bus-item changes.
	# When the event-callback is set it calls this function.
	# @param changes the changed properties.
	def _properties_changed_handler(self, changes):
		if "Value" in changes:
			self._value = changes["Value"]
			if self._eventCallback:
				self._eventCallback(self._dbus_name, self._path, changes)

