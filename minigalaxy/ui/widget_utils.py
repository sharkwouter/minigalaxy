"""
This file contains a few static utility methods for dealing with repeated task when building or populating
certain types of widgets.
"""

from minigalaxy.ui.gtk import Gtk


def populate_combobox(combo: Gtk.ComboBox, str_tuple_list, active_value: str):
    """
    Populate the given ComboBox with data from str_tuple_list.
    str_tuple_list is expected to be an array/list with 2-value-tuples: 0=key and 1=Label
    active_value is used to preselect a value. Must be a key found in str_tuple_list.
    """
    data_list = Gtk.ListStore(str, str)
    for entry in str_tuple_list:
        data_list.append(entry)

    combo.set_model(data_list)
    combo.set_entry_text_column(1)
    renderer = Gtk.CellRendererText()
    combo.pack_start(renderer, False)
    combo.add_attribute(renderer, "text", 1)

    # Set the active option
    for key in range(len(data_list)):
        if data_list[key][:1][0] == active_value:
            combo.set_active(key)
            break
