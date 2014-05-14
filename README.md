velib_python
============
This is the general python library within Victron. It contains code that is related to dbus and the Color
Control GX. See http://www.victronenergy.com/panel-systems-remote-monitoring/colorcontrol/ for more
infomation about that panel.

Files  busitem.py, dbusitem.py and tracing.py are deprecated.

The main files are vedbus.py, dbusmonitor.py and settingsdevice.py.

- Use VeDbusService to put your process on dbus and let other services interact with you.
- Use VeDbusItemImport to read a single value from other processes the dbus, and monitor its signals.
- Use DbusMonitor to monitor multiple values from other processes
- Use SettingsDevice to store your settings in flash, via the com.victronenergy.settings dbus service. See
https://github.com/victronenergy/localsettings for more info.

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

