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
