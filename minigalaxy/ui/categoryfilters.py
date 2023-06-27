import os
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR
from minigalaxy.ui.gtk import Gtk


@Gtk.Template.from_file(os.path.join(UI_DIR, "categoryfilters.ui"))
class CategoryFilters(Gtk.Dialog):
    __gtype_name__ = "CategoryFilters"

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, title=_("Category Filters"), parent=parent, modal=True)
        self.parent = parent

        # Center information window
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

