import os

from minigalaxy.paths import UI_DIR
from minigalaxy.ui.gtk import Gtk
from minigalaxy.translation import _


@Gtk.Template.from_file(os.path.join(UI_DIR, "filterswitch.ui"))
class FilterSwitch(Gtk.Box):
    __gtype_name__ = "FilterSwitch"

    label_category_filter = Gtk.Template.Child()
    switch_category_filter = Gtk.Template.Child()

    def __init__(self, parent, category_name, on_toggle_fn):
        Gtk.Frame.__init__(self)
        self.parent = parent
        self.label_category_filter.set_label(_(category_name))
        self.switch_category_filter.set_active(False)

        def on_click(self):
            on_toggle_fn(category_name, self.get_active())
        self.switch_category_filter.connect('toggled', on_click)
