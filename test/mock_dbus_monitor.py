# Simulation a DbusMonitor object, without using the D-Bus (intended for unit tests). Instead of changes values
# on the D-Bus you can use the set_value function. set_value will automatically expand the service list. Note
# that all simulated D-Bus paths passed to set_value must be part of the dbusTree passed to the constructor of
# the monitor.
class MockDbusMonitor(object):
    def __init__(self, dbusTree):
        self._services = {}
        self._tree = {}
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

    # returns a dictionary, keys are the servicenames, value the instances
    # optionally use the classfilter to get only a certain type of services, for
    # example com.victronenergy.battery.
    def get_service_list(self, classfilter=None):
        r = {}
        for servicename,items in self._services.items():
            if not classfilter or _class_name(servicename) == classfilter:
                r[servicename] = items.get('/DeviceInstance', None)

        return r

    def set_value(self, service, path, value):
        class_name = _class_name(service)
        s = self._tree.get(class_name, None)
        if s is None:
            raise Exception('service not found')
        if path not in s:
            raise Exception('path not found')
        s = self._services.setdefault(service, {})
        s[path] = value
        
    def remove_service(self, service):
        self._services.pop(service)

def _class_name(service):
    return '.'.join(service.split('.')[:3])
