import dbus


# Simulation a DbusMonitor object, without using the D-Bus (intended for unit tests). Instead of changes values
# on the D-Bus you can use the set_value function. set_value will automatically expand the service list. Note
# that all simulated D-Bus paths passed to set_value must be part of the dbusTree passed to the constructor of
# the monitor.
class MockDbusMonitor(object):
    def __init__(self, dbusTree, valueChangedCallback=None, deviceAddedCallback=None,
            deviceRemovedCallback=None, mountEventCallback=None, vebusDeviceInstance0=False):
        self._services = {}
        self._tree = {}
        self._valueChangedCallback = valueChangedCallback
        self._deviceRemovedCallback = deviceRemovedCallback
        self._deviceAddedCallback = deviceAddedCallback
        for s, sv in dbusTree.items():
            service = self._tree.setdefault(s, set())
            service.update(['/Connected', '/ProductName', '/Mgmt/Connection', '/DeviceInstance'])
            for p in sv:
                service.add(p)

    # Gets the value for a certain servicename and path, returns the default_value when
    # request service and objectPath combination does not not exists or when it is invalid
    def get_value(self, serviceName, objectPath, default_value=None):
        if serviceName not in self._services:
            return default_value

        if objectPath not in self._services[serviceName]:
            return default_value

        r = self._services[serviceName][objectPath]
        return r if r is not None else default_value

    def get_item(self, serviceName, objectPath):
        if serviceName not in self._services:
            return None

        if objectPath not in self._tree[_class_name(serviceName)]:
            return None

        return MockImportItem(self, serviceName, objectPath)

    # returns a dictionary, keys are the servicenames, value the instances
    # optionally use the classfilter to get only a certain type of services, for
    # example com.victronenergy.battery.
    def get_service_list(self, classfilter=None):
        r = {}
        for servicename,items in self._services.items():
            if not classfilter or _class_name(servicename) == classfilter:
                r[servicename] = items.get('/DeviceInstance', None)

        return r

    def add_value(self, service, path, value):
        class_name = _class_name(service)
        s = self._tree.get(class_name, None)
        if s is None:
            raise Exception('service not found')
        if path not in s:
            raise Exception('path not found')
        s = self._services.setdefault(service, {})
        s[path] = value

    def set_value(self, service, path, value):
        s = self._services.get(service)
        if s == None:
            raise dbus.exceptions.DBusException('org.freedesktop.DBus.Error.ServiceUnknown')
        if path not in s:
            raise dbus.exceptions.DBusException('org.freedesktop.DBus.Error.UnknownObject')
        s[path] = value
        if self._valueChangedCallback != None:
            self._valueChangedCallback(service, path, None, None, None)

    def add_service(self, service, values):
        if service not in self._services:
            self._services[service] = values
            if self._deviceAddedCallback != None:
                self._deviceAddedCallback(service, values.get('/DeviceInstance', 0))
        else:
            for k,v in values.items():
                self.add_value(service, k, v)

    def remove_service(self, service):
        if service not in self._services:
            return
        instance = self._services[service].get('/DeviceInstance', 0)
        self._services.pop(service)
        if self._deviceRemovedCallback != None:
            self._deviceRemovedCallback(service, instance)

    @property
    def dbusConn(self):
        raise dbus.DBusException("No Connection")


class MockImportItem(object):
    def __init__(self, monitor, service, path):
        self._monitor = monitor
        self._service = service
        self._path = path

    def get_value(self):
        return self._monitor.get_value(self._service, self._path)

    def set_value(self, value):
        self._monitor.set_value(self._service, self._path, value)


def _class_name(service):
    return '.'.join(service.split('.')[:3])
