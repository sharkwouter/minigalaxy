import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

css = '.test { border: 1px solid green; }'
CSS_PROVIDER = Gtk.CssProvider()
CSS_PROVIDER.load_from_data(css.encode('utf-8'))
