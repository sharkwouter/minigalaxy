from minigalaxy.launch_command import LaunchCommand
from minigalaxy.translation import _
from minigalaxy.ui.gtk import Gtk, load_ui
from minigalaxy.ui.widget_utils import populate_combobox, get_combo_value


@Gtk.Template(string=load_ui("chooselaunchoption.ui"))
class ChooseLaunchOption(Gtk.Dialog):
    __gtype_name__ = "ChooseLaunchOption"

    choices_combobox = Gtk.Template.Child()

    def __init__(self, parent, launch_command_list: list[LaunchCommand]):
        Gtk.Dialog.__init__(self, title=_("Choose Launch Option"), parent=parent, modal=True)
        self.launch_command_list = launch_command_list
        self.cancelled = True
        self.selection = None

        shown_option = None
        combobox_options = []
        for i, launch_command in enumerate(launch_command_list):
            combobox_options.append(
                [launch_command.name, launch_command.name]
            )
            if shown_option is None:
                shown_option = launch_command.name

        populate_combobox(self.choices_combobox, combobox_options, shown_option)

        # Center window
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.show_all()

    @Gtk.Template.Callback("on_button_choose_executable_launch_clicked")
    def on_launch_clicked(self, button):
        chosen_name = get_combo_value(self.choices_combobox)
        for launch_command in self.launch_command_list:
            print(chosen_name)
            if launch_command.name == chosen_name:
                self.selection = launch_command
                self.cancelled = False
        self.hide()

    @Gtk.Template.Callback("on_button_choose_executable_cancel_clicked")
    def on_cancel_clicked(self, button):
        self.selection = None
        self.hide()

    @staticmethod
    def ask_for_launch_command(parent, launch_command_list: list[LaunchCommand]):
        dialog = ChooseLaunchOption(parent=parent, launch_command_list=launch_command_list)
        dialog.run()
        launch_command = dialog.selection
        dialog.destroy()

        return launch_command
