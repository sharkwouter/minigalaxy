import json
import os

from minigalaxy.logger import logger
from minigalaxy.translation import _
from minigalaxy.paths import UI_DIR, CATEGORIES_FILE_PATH
from minigalaxy.ui.filterswitch import FilterSwitch
from minigalaxy.ui.gtk import Gtk


@Gtk.Template.from_file(os.path.join(UI_DIR, "categoryfilters.ui"))
class CategoryFilters(Gtk.Dialog):
    __gtype_name__ = "CategoryFilters"

    genre_filtering_grid = Gtk.Template.Child()
    filter_dict = {}

    def __init__(self, parent, library):
        Gtk.Dialog.__init__(self, title=_("Category Filters"), parent=parent, modal=True)
        self.parent = parent
        self.library = library

        # load categories from file and create filter switches
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
        for idx, category in enumerate(categories):
            self.filter_dict[category] = False
            self.genre_filtering_grid.attach(FilterSwitch(
                self,
                category,
                lambda key, value: self.filter_dict.__setitem__(key, value)),
                left=idx % 3, top=int(idx / 3), width=1, height=1
            )

        # Center information window
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

    @Gtk.Template.Callback("on_button_category_filters_apply_clicked")
    def on_apply_clicked(self, button):
        logger.debug("inside on_apply_clicked")
        # TODO enable/update category filter in library.py
        # self.library.update_category_filters(self.filter_dict)
        self.library.filter_library()
        self.destroy()

    @Gtk.Template.Callback("on_button_category_filters_cancel_clicked")
    def on_cancel_clicked(self, button):
        self.destroy()

    @Gtk.Template.Callback("on_button_category_filters_reset_clicked")
    def on_reset_clicked(self, button):
        for f in self.filter_dict.keys():
            self.filter_dict[f] = False
