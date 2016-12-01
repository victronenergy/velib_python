#!/usr/bin/env python
# -*- coding: utf-8 -*-
from traceback import print_exc
from os import _exit as os_exit
from os import statvfs
import logging
logger = logging.getLogger(__name__)

# Use this function to make sure the code quits on an unexpected exception. Make sure to use it
# when using gobject.idle_add and also gobject.timeout_add.
# Without this, the code will just keep running, since gobject does not stop the mainloop on an
# exception.
# Example: gobject.idle_add(exit_on_error, myfunc, arg1, arg2)
def exit_on_error(func, *args, **kwargs):
	try:
		return func(*args, **kwargs)
	except:
		try:
			print 'exit_on_error: there was an exception. Printing stacktrace will be tryed and then exit'
			print_exc()
		except:
			pass

		# sys.exit() is not used, since that throws an exception, which does not lead to a program
		# halt when used in a dbus callback, see connection.py in the Python/Dbus libraries, line 230.
		os_exit(1)


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


# See VE.Can registers - public.docx for definition of this conversion
def convert_vreg_version_to_readable(version):
	def str_to_arr(x, length):
		a = []
		for i in range(0, len(x), length):
			a.append(x[i:i+length])
		return a

	x = "%x" % version
	x = x.upper()

	if len(x) == 5 or len(x) == 3 or len(x) == 1:
		x = '0' + x

	a = str_to_arr(x, 2);

	# remove the first 00 if there are three bytes and it is 00
	if len(a) == 3 and a[0] == '00':
		a.remove(0);

	# if we have two or three bytes now, and the first character is a 0, remove it
	if len(a) >= 2 and a[0][0:1] == '0':
		a[0] = a[0][1];

	result = ''
	for item in a:
		result += ('.' if result != '' else '') + item


	result = 'v' + result

	return result


def get_free_space(path):
	result = -1

	try:
		s = statvfs(path)
		result = s.f_frsize * s.f_bavail     # Number of free bytes that ordinary users
	except Exception, ex:
		logger.info("Error while retrieving free space for path %s: %s" % (path, ex))

	return result


def get_load_averages():
	c = read_file('/proc/loadavg')
	return c.split(' ')[:3]


# Returns False if it cannot find a machine name. Otherwise returns the string
# containing the name
def get_machine_name():
	c = read_file('/proc/device-tree/model')

	if c != False:
		return c.strip('\x00')

	return read_file('/etc/venus/machine')


# Returns False if it cannot open the file. Otherwise returns its rstripped contents
def read_file(path):
	content = False

	try:
		with open(path, 'r') as f:
			content = f.read().rstrip()
	except Exception, ex:
		logger.info("Error while reading %s: %s" % (path, ex))

	return content
