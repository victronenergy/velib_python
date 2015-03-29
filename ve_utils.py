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
		from sys import exit
		exit(1)
