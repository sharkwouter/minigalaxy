import logging
import os
import shutil
import subprocess

import minigalaxy.logger  # noqa: F401

from minigalaxy.download import Download, DownloadType
from minigalaxy.download_manager import DownloadManager, DownloadState
from minigalaxy.paths import UI_DIR
from minigalaxy.translation import _
from minigalaxy.ui.gtk import GLib, Gtk
from gi.overrides.GdkPixbuf import GdkPixbuf


@Gtk.Template.from_file(os.path.join(UI_DIR, "download_list.ui"))
class DownloadManagerList(Gtk.Viewport):
    __gtype_name__ = "DownloadList"

    label_active = Gtk.Template.Child()
    flowbox_active = Gtk.Template.Child()

    label_queued = Gtk.Template.Child()
    flowbox_queued = Gtk.Template.Child()

    label_paused = Gtk.Template.Child()
    flowbox_paused = Gtk.Template.Child()

    label_done = Gtk.Template.Child()
    flowbox_done = Gtk.Template.Child()

    button_manage_installers = Gtk.Template.Child()

    listener_download_types = [DownloadType.GAME, DownloadType.GAME_UPDATE, DownloadType.GAME_DLC]

    def __init__(self, download_manager: DownloadManager, downloads_menu_button, config):
        Gtk.Viewport.__init__(self)
        self.logger = logging.getLogger('minigalaxy.download_list.DownloadManagerList')
        self.download_manager = download_manager
        self.menu_button = downloads_menu_button
        self.config = config
        self.downloads = {}

        self.change_handler = {
            DownloadState.STARTED: self.download_started,
            DownloadState.COMPLETED: self.download_stopped,
            DownloadState.QUEUED: self.download_queued,
            DownloadState.PROGRESS: self.download_progress,
            DownloadState.FAILED: self.download_failed,
            DownloadState.CANCELED: self.download_stopped,
            DownloadState.STOPPED: self.download_stopped,
            DownloadState.PAUSED: self.download_paused
        }

        self.flowbow_labels = {
            self.flowbox_active: self.label_active,
            self.flowbox_queued: self.label_queued,
            self.flowbox_paused: self.label_paused,
            self.flowbox_done: self.label_done
        }

        self.download_manager.add_active_downloads_listener(self.download_manager_listener)
        self.show()

    def download_manager_listener(self, change: DownloadState, download: Download, *additional_params):
        self.logger.debug('Received %s for Download[save_location=%s, progress=%d]',
                          change, download.filename(), download.current_progress)
        if download.download_type not in self.listener_download_types:
            return
        if change not in self.change_handler:
            return

        GLib.idle_add(self.change_handler[change], change, download, *additional_params)

    def download_started(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        self.__move_to_section(self.flowbox_active, download_entry, change)

    def download_queued(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        self.__move_to_section(self.flowbox_queued, download_entry, change)

    def download_stopped(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        self.__move_to_section(self.flowbox_done, download_entry, change)

    def download_failed(self, change, download, error_info="Unknown error"):
        download_entry = self.__get_create_entry(change, download)
        self.__move_to_section(self.flowbox_done, download_entry, change)
        download_entry.update_tooltip(_(error_info))

    def download_paused(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        self.__move_to_section(self.flowbox_paused, download_entry, change)

    def download_progress(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        download_entry.update_progress(download.current_progress)

    def __get_create_entry(self, change, download):
        if download.save_location not in self.downloads:
            self.downloads[download.save_location] = OngoingDownloadListEntry(self, download, change)

        return self.downloads[download.save_location]

    def __move_to_section(self, flowbox, entry, new_state: DownloadState):
        in_done_section = entry.flowbox == self.flowbox_done
        entry.remove_from_current_box()

        '''
        Going from stopped -> cancel or failure -> cancel is set to delete the file.
        No need to keep the Download in the list after that.
        '''
        if in_done_section and flowbox == self.flowbox_done:
            return

        entry.add_to_box(flowbox)
        entry.update_state(new_state)
        entry.update_tooltip(_(new_state.name))

    def update_group_visibility(self, group_flowbox):
        if group_flowbox.get_children():
            self.flowbow_labels[group_flowbox].show()
            group_flowbox.show()
        else:
            group_flowbox.hide()
            self.flowbow_labels[group_flowbox].hide()

        if self.downloads:
            self.menu_button.get_style_context().add_class("suggested-action")
        else:
            self.menu_button.get_style_context().remove_class("suggested-action")

    @Gtk.Template.Callback("on_manage_button")
    def open_file_manager(self, widget, *data):
        # this forks and is not watched by minigalaxy any further
        # users need to manually reload library after changes
        subprocess.Popen([f"xdg-open '{self.config.install_dir}/installer' &"],
                         shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)

    @Gtk.Template.Callback("manage_button_visibility")
    def handle_manage_button(self, widget, *data):
        if self.config.keep_installers and shutil.which("xdg-open"):
            self.button_manage_installers.show()
        else:
            self.button_manage_installers.hide()


@Gtk.Template.from_file(os.path.join(UI_DIR, "download_list_entry.ui"))
class OngoingDownloadListEntry(Gtk.Box):
    __gtype_name__ = "DownloadListEntry"

    icon = Gtk.Template.Child()
    game_title = Gtk.Template.Child()
    download_progress = Gtk.Template.Child()

    def __init__(self, parent_manager, download: Download, initial_state: DownloadState):
        Gtk.Box.__init__(self)
        self.manager = parent_manager
        self.download = download
        self.flowbox = None
        self.label_color_change = None
        self.game_title.set_text(f'{download.game.name}:\n{os.path.basename(download.save_location)}')
        self.buttons = DownloadActionButtons(download, initial_state,
                                             download_manager=parent_manager.download_manager,
                                             remove_panel_action=self.remove_from_current_box,
                                             logger=self.manager.logger)
        self.update_state(initial_state)

        self.manager.logger.debug("trying to pull icon from: %s", download.download_icon)
        if download.download_icon and os.path.exists(download.download_icon):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(download.download_icon, 48, 48)
            self.icon.set_from_pixbuf(pixbuf)

        self.pack_start(self.buttons, False, False, 0)

    def update_progress(self, percentage):
        self.download_progress.set_fraction(percentage / 100)
        self.download_progress.set_tooltip_text("{}%".format(percentage))

    def update_state(self, new_state):
        self.buttons.update_buttons(new_state)

        new_label_color = None
        if new_state in [DownloadState.FAILED, DownloadState.CANCELED, DownloadState.STOPPED]:
            new_label_color = 'red'
        elif new_state in [DownloadState.COMPLETED]:
            new_label_color = 'green'

        if self.label_color_change:
            self.label_color_change = None

        if new_label_color:
            self.game_title.set_markup(f'<span color="{new_label_color}">{self.game_title.get_text()}</span>')
            self.label_color_change = new_label_color
        else:
            self.game_title.set_text(self.game_title.get_text())

    def update_tooltip(self, msg):
        self.game_title.set_tooltip_text(msg)

    '''----- VISIBILITY CONTROL -----'''

    def add_to_box(self, flowbox):
        flowbox.add(self)
        self.flowbox = flowbox
        self.show()
        self.manager.downloads[self.download.save_location] = self
        self.manager.update_group_visibility(flowbox)

    def remove_from_current_box(self):
        if not self.flowbox:
            return

        old_flowbox = self.flowbox
        '''the entry needs to be removed from its parent FlowBoxChild
        or there will be a memory access error hard crashing the application'''
        box_child = self.get_parent()
        box_child.remove(self)
        old_flowbox.remove(box_child)
        box_child.destroy()
        del self.manager.downloads[self.download.save_location]
        self.manager.update_group_visibility(old_flowbox)

    '''----- END VISIBILITY CONTROL -----'''


@Gtk.Template.from_file(os.path.join(UI_DIR, "download_action_buttons.ui"))
class DownloadActionButtons(Gtk.Box):
    __gtype_name__ = "DownloadActionButtons"

    image_primary_action = Gtk.Template.Child()
    image_secondary_action = Gtk.Template.Child()

    tooltip_texts = {
        'media-playback-start': 'Resume',
        'media-playback-pause': 'Pause',
        'view-refresh': 'Retry',
        'dialog-cancel': 'Cancel',
        'edit-delete': 'Delete file',
        'list-remove': 'Remove from list',
    }

    # button actions are defined at the end

    def __init__(self, download, initial_state, download_manager, remove_panel_action=None, logger=None, run_standalone=False):
        super().__init__(self)
        self.download = download
        self.download_manager = download_manager
        self.remove_panel_action = remove_panel_action
        self.state = None
        self.logger = logger
        self.update_buttons(initial_state)
        self.is_standalone = run_standalone
        self.register_dm_listener()

    def register_dm_listener(self, force_registration=False):
        '''
        Default behaviour: Listener will only be registered when in standalone mode (=not part of the DownloadList UI).
        Can be overruled by passing force_registration=True.
        Only useful as utility method when manually wiring stuff together,
        but it's less error-prone to just pass run_standalone to the constructor
        '''
        if self.is_standalone or force_registration:
            self.download_manager.add_active_downloads_listener(self.track_download_state)

    def unregister_dm_listener(self):
        # not registered listeners are silently ignored by download_manager
        self.download_manager.remove_active_downloads_listener(self.track_download_state)

    def track_download_state(self, change: DownloadState, download: Download):
        if download != self.download:
            return
        GLib.idle_add(self.update_buttons, change)

    '''----- WIDGET EVENTS -----'''

    @Gtk.Template.Callback("on_primary_button")
    def primary_button_clicked(self, widget):
        self.__execute_button('Primary', 0)

    @Gtk.Template.Callback("on_secondary_button")
    def secondary_button_clicked(self, widget):
        self.__execute_button('Secondary', 1)

    def __execute_button(self, button_type, action_index):
        if self.state not in self.button_configs:
            return
        action = self.button_configs[self.state]['actions'][action_index]
        if self.logger:
            self.logger.debug('[%s:%s] - %s button clicked, execute %s',
                              button_type, self.state, self.download.filename(), str(action))
        action(self)

    def update_buttons(self, state: DownloadState):
        if state is self.state:
            return

        self.state = state
        if state not in self.button_configs:
            return

        primary, secondary = self.button_configs[state]['icons']
        if primary:
            self.image_primary_action.set_from_icon_name(primary, Gtk.IconSize.LARGE_TOOLBAR)
            self.image_primary_action.set_tooltip_text(_(self.tooltip_texts[primary]))
            self.image_primary_action.get_parent().show()
        else:
            self.image_primary_action.get_parent().hide()

        if secondary:
            self.image_secondary_action.set_from_icon_name(secondary, Gtk.IconSize.LARGE_TOOLBAR)
            self.image_secondary_action.set_tooltip_text(_(self.tooltip_texts[secondary]))
            self.image_secondary_action.get_parent().show()
        else:
            self.image_secondary_action.get_parent().hide()

    '''----- END WIDGET EVENTS -----'''

    def destroy(self):
        self.unregister_dm_listener()
        super().destroy()

    '''----- DOWNLOAD STATE OPERATIONS -----'''

    def restart(self):
        self.download_manager.download(self.download)

    def unpause(self):
        self.download_manager.download(self.download, restart_paused=True)

    def pause_download(self):
        self.download_manager.cancel_download(self.download, cancel_state=DownloadState.PAUSED)

    def stop_download(self):
        self.download_manager.cancel_download(self.download, cancel_state=DownloadState.STOPPED)

    def delete_download(self):
        self.download_manager.cancel_download(self.download, cancel_state=DownloadState.CANCELED)

    def trigger_remove(self):
        if self.remove_panel_action:
            self.remove_panel_action()
        else:
            self.destroy()

    def NOOP(self):
        '''used for states in which a button should not do anything'''
        pass

    '''----- END DOWNLOAD STATE OPERATIONS -----'''

    button_configs = {
        DownloadState.STARTED: {
            'actions': [pause_download, stop_download],
            'icons': ['media-playback-pause', 'dialog-cancel']
        },
        DownloadState.QUEUED: {
            'actions': [pause_download, stop_download],
            'icons': ['media-playback-pause', 'dialog-cancel']
        },
        DownloadState.COMPLETED: {
            'actions': [NOOP, trigger_remove],
            'icons': [None, 'list-remove']
        },
        DownloadState.PAUSED: {
            'actions': [unpause, delete_download],
            'icons': ['media-playback-start', 'edit-delete']
        },
        DownloadState.STOPPED: {
            'actions': [restart, delete_download],
            'icons': ['media-playback-start', 'edit-delete']
        },
        DownloadState.FAILED: {
            'actions': [restart, trigger_remove],
            'icons': ['view-refresh', 'list-remove']
        },
        DownloadState.CANCELED: {
            'actions': [restart, trigger_remove],
            'icons': ['view-refresh', 'list-remove']
        }
    }
