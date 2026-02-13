from minigalaxy.ui.gtk import Gtk, load_ui
from minigalaxy.translation import _


@Gtk.Template(string=load_ui("filterswitch.ui"))
class FilterSwitch(Gtk.Box):
    __gtype_name__ = "FilterSwitch"

    label_category_filter = Gtk.Template.Child()
    switch_category_filter = Gtk.Template.Child()

    def __init__(self, parent, category_name, on_toggle_fn, initial_state=False):
        Gtk.Frame.__init__(self)
        self.parent = parent
        self.label_category_filter.set_label(_(category_name))
        self.switch_category_filter.set_active(initial_state)

        def on_click(self):
            on_toggle_fn(category_name, self.get_active())
        self.switch_category_filter.connect('toggled', on_click)
