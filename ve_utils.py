#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Use this function to make sure the code quits on an unexpected exception. Make sure to use it
# when using gobject.idle_add and also gobject.timeout_add.
# Without this, the code will just keep running, since gobject does not stop the mainloop on an
# exception.
# Example: gobject.idle_add(exit_on_error, myfunc, arg1, arg2)
def exit_on_error(func, *args, **kwargs):
	try:
		return func(*args, **kwargs)
	except:
		from traceback import print_exc
		print_exc()

		# sys.exit() is not used, since that throws an exception, which does not lead to a program
		# halt when used in a dbus callback, see connection.py in the Python/Dbus libraries, line 230.
		import os
		os._exit(1)


__vrm_portal_id = None
def get_vrm_portal_id():
	# For the CCGX, the definition of the VRM Portal ID is that it is the mac address of the onboard-
	# ethernet port (eth0), stripped from its colons (:) and lower case.

	# nice coincidence is that this also works fine when running on your (linux) development computer.

	global __vrm_portal_id

	if __vrm_portal_id:
		return __vrm_portal_id

	# Assume we are on linux
	import fcntl, socket, struct

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', 'eth0'[:15]))
	__vrm_portal_id = ''.join(['%02x' % ord(char) for char in info[18:24]])

	return __vrm_portal_id
