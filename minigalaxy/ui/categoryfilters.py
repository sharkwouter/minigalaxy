import os

from minigalaxy.logger import logger
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR
from minigalaxy.ui.filterswitch import FilterSwitch
from minigalaxy.ui.gtk import Gtk


@Gtk.Template.from_file(os.path.join(UI_DIR, "categoryfilters.ui"))
class CategoryFilters(Gtk.Dialog):
    __gtype_name__ = "CategoryFilters"

    genre_filtering_grid = Gtk.Template.Child()
    filter_dict = {}
    categories = [
        'Action',
        'Adventure',
        'Racing',
        'Role-playing',
        'Shooter',
        'Simulation',
        'Sports',
        'Strategy',
    ]

    def __init__(self, parent, library):
        Gtk.Dialog.__init__(self, title=_("Category Filters"), parent=parent, modal=True)
        self.parent = parent
        self.library = library

        for idx, category in enumerate(self.categories):
            initial_state = category in self.library.category_filters
            self.filter_dict[category] = initial_state
            filter_switch = FilterSwitch(self,
                                         category,
                                         lambda key, value: self.filter_dict.__setitem__(key, value),
                                         initial_state)
            self.genre_filtering_grid.attach(
                filter_switch, left=idx % 3, top=int(idx / 3), width=1, height=1)

        # Center filters window
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

    @Gtk.Template.Callback("on_button_category_filters_apply_clicked")
    def on_apply_clicked(self, button):
        logger.debug("Filtering library according to category filter dict: %s", self.filter_dict)
        self.library.filter_library(self)
        self.destroy()

    @Gtk.Template.Callback("on_button_category_filters_cancel_clicked")
    def on_cancel_clicked(self, button):
        self.destroy()

    @Gtk.Template.Callback("on_button_category_filters_reset_clicked")
    def on_reset_clicked(self, button):
        logger.debug("Resetting category filters")
        for child in self.genre_filtering_grid.get_children():
            child.switch_category_filter.set_active(False)
        self.library.filter_library(self)
