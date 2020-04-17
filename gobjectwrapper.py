# Wrap gobject so newer versions is also supported
__all__ = ('gobject',)

try:
	import gi
except ImportError:
	import gobject
else:
	gi.require_version('GObject', '2.0')
	from gi.repository import GObject as gobject
