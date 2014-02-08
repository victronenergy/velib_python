#!/usr/bin/env python
# -*- coding: utf-8 -*-

# test(s) to show how the datatypes and variants work in dbus. See also
# comments in vedbus.py.

import dbus
import pprint

a = dbus.Int32(12, variant_level=1)
print 'Comparing first line with next line'
pprint.pprint(a)
pprint.pprint(12)

# and the result will be true
print a == 12

print '------'

# result of this one will also be true.
print 'dbus.Array([]) == dbus.Array([], signature=dbus.Signature(''i''), variant_level=1)'
print  dbus.Array([]) == dbus.Array([], signature=dbus.Signature('i'), variant_level=1)

print '------'

# next statement returns dbus.Array([], signature=None)
pprint.pprint(dbus.Array([]))

# next statement returns dbus.Array([], signature=dbus.Signature('i'), variant_level=1)
pprint.pprint(dbus.Array([], signature=dbus.Signature('i'), variant_level=1))

