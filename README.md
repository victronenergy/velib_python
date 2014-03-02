velib_python
============
This is the general python library within Victron. Today it only contains code that is related to dbus and the Color
Control GX. 

Files  busitem.py, dbusitem.py and tracing.py are deprecated. See vedbus.py instead.

vedbus.py is still being finished.


Code style
==========

Comply with PEP8, except:
- use tabs instead of spaces, since we use tabs for all projects within Victron.
- max line length = 110

Run this command to set git diff to tabsize is 4 spaces. Replace --local with --global to do it globally for the current
user account.

    git config --local core.pager 'less -x4'

Run this command to check your code agains PEP8

    pep8 --max-line-length=110 --ignore=W191 *.py

