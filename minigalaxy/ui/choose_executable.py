from minigalaxy.ui.gtk import Gtk, load_ui


@Gtk.Template(string=load_ui("chooseexecutable.ui"))
class ChooseExecutable(Gtk.Dialog):
    __gtype_name__ = "ChooseExecutable"

    radio_button_box = Gtk.Template.Child()
    remember_check_button = Gtk.Template.Child()

    def __init__(self, parent, executable_list: list[str]):
        Gtk.Dialog.__init__(self, title=_("Choose Executable"), parent=parent, modal=True)
        self.executable_list = executable_list
        self.__selected_executable = None

        last_button = None
        for idx, executable in enumerate(self.executable_list):
            last_button = Gtk.RadioButton.new_with_label_from_widget(last_button, executable)
            last_button.connect("toggled", self.on_radio_button_toggle, executable)
            self.radio_button_box.add(last_button)

        # self.__selected_executable = self.radio_button_group[0].name

        # Center filters window
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.show_all()

    def on_radio_button_toggle(self, button, executable):
        self.__selected_executable = executable
        print(f"Executable {executable} selected")

    def get_selected_executable(self):
        return self.__selected_executable

    @Gtk.Template.Callback("on_button_choose_executable_launch_clicked")
    def on_launch_clicked(self, button):
        self.hide()

    @Gtk.Template.Callback("on_button_choose_executable_cancel_clicked")
    def on_cancel_clicked(self, button):
        self.__selected_executable = None
        self.hide()
    #
    # @Gtk.Template.Callback("on_button_category_filters_reset_clicked")
    # def on_reset_clicked(self, button):
    #     logger.debug("Resetting category filters")
    #     for child in self.genre_filtering_grid.get_children():
    #         child.switch_category_filter.set_active(False)
    #     self.library.filter_library(self)
