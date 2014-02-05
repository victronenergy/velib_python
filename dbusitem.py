## IMPORTANT NOTE - MVA 2015-2-5 
# This file is deprecated. Use the classes in vedbus.py from now on. If you are
# working on some project, please change it, and make it work with the classes
# in vedbus.py


import dbus
# Python imports
from dbus import String
from lxml.etree import XML

# Local imports
import tracing

## Implements a velib dbus item as a local object.
class Dbusitem(object):

	## The constructor introspects the dbus-service.
	# And constructs the tree of dbus-object-paths with their dbus-object.
	# @param bus the bus-object (SESSION or SYSTEM).
	# @param service th dbus-service-name.
	# @param path initially the path is \ (root).
	def __init__(self, bus, service, path):
		#tracing.log.debug('Dbusitem __init__ %s %s %s' % (self, service, path))
		self._children = {}
		self._dbus_name = service
		self._value = None
		self._text = None
		self._valid = None
		self._eventCallback = None
		self._object = bus.get_object(service, path)
		self._add_children(bus, service)
		self._match = None

	def __del__(self):
		tracing.log.debug('Dbusitem __del__ %s %s' % (self, self.object.object_path))

	## Introspects and adds the next dbus-item as a child.
	# This class-method instantiates a Dbusitem-object for all node(s).
	# @param bus the bus-object
	# @param service the dbus-service-name.
	def _add_children(self, bus, service):
		'''Add the child nodes found by introspection'''
		self._children= {};
		xml = self._object.Introspect()
		data = XML(xml)

		# add all child nodes
		for child in data.findall('node'):
			name = child.get('name')
			if name == "/":
				continue

			child_path = self.object.object_path
			# root is reported as /, don't make it //
			if child_path != "/":
				child_path += "/"
			child_path += name
			self._children[name] = Dbusitem(bus, service, child_path)
	
	def _add_to_prop_changed(self):
		if self._match is None:
			self._value = None
			self._text = None
			self._valid = None
			self._match = self.object.connect_to_signal("PropertiesChanged", self._properties_changed_handler)

	def _delete(self):
		for name in self._children:
			self._children[name]._delete()
		tracing.log.debug('Dbusitem _delete %s %s' % (self, self.object.object_path))
		self._children = None
		if self._match:
			self._match.remove()
			del(self._match)

	@property
	def object(self):
		return self._object

	@classmethod
	def traceit(cls, item, ctx):
		print(item.object.object_path + "=" + item.text)

	## Dump the tree to console
	def trace(self):
		self.foreach(self.traceit)

	## Invoke callback for the item and its children
	# @param callback the callback-function.
	def foreach(self, callback):
		callback(self)
		for name in self._children:
			self._children[name].foreach(callback)

	## Allow child nodes be accessed as properties.
	def __getattr__(self, key):
		return self._children[key]

	def AddSetting(self, group, name, defaultValue, itemType, minimum, maximum):
		tracing.log.info('%s AddSetting %s %s %s %s %s %s' % (self.object.object_path, group, name, defaultValue, itemType, minimum, maximum))
		self.object.AddSetting(group, name, defaultValue, itemType, minimum, maximum)

	## Returns the value of the dbus-item.
	def GetValue(self):
		if self._value is None or self._match is None:
			try:
				self._value = self.object.GetValue()
			except Exception, ex:
				tracing.log.error("GetValue %s %s exception %s" % (self._dbus_name, self.object.object_path, ex))
		#tracing.log.debug('value %s %s type %s' % (self.object.object_path, str(self._value), type(self._value)))
		
		return self._value

	def SetValue(self, value):
		# mmm, always use a string for now
		variant = String(str(value), variant_level=1)
		self.object.SetValue(variant)

	value = property(GetValue, SetValue)
	
	def Valid(self):
		value = self.GetValue()
		self._valid = value != dbus.Array([])
		return self._valid

	valid = property(Valid)

	## Sets the callback for the trigger-event.
	# @param eventCallback the event-callback-funciton.	
	def SetEventCallback(self, eventCallback):
		self._eventCallback = eventCallback

	@property
	def text(self):
		if self._text is None or self._match is None:
			try:
				self._text = self.object.GetText()
			except Exception, ex:
				tracing.log.error("GetText %s %s exception %s" % (self._dbus_name, self.object.object_path, ex))
		return self._text

	## Is called the value of a dbus-item changes.
	# When the event-callback is set it calls this function.
	# @param changes the changed properties.
	def _properties_changed_handler(self, changes):
		for prop in changes:
			if prop == "Value":
				self._value = changes[prop]
			elif prop == "Text":
				self._text = changes[prop]
			elif prop == "Valid":
				self._valid = changes[prop]

		if self._eventCallback:
			self._eventCallback(self._dbus_name, self.object.object_path, changes)

		#tracing.log.debug("%s %s changed to %s" % (self.object.bus_name, self.object.object_path, changes))

