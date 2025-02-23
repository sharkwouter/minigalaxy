import logging
import os

import minigalaxy.logger  # noqa: F401

from minigalaxy.download import Download, DownloadType
from minigalaxy.download_manager import DownloadManager, DownloadState
from minigalaxy.paths import UI_DIR
from minigalaxy.translation import _
from minigalaxy.ui.gtk import GLib, Gtk


@Gtk.Template.from_file(os.path.join(UI_DIR, "download_list.ui"))
class DownloadManagerList(Gtk.Viewport):
    __gtype_name__ = "DownloadList"

    label_active = Gtk.Template.Child()
    flowbox_active = Gtk.Template.Child()

    label_queued = Gtk.Template.Child()
    flowbox_queued = Gtk.Template.Child()

    label_done = Gtk.Template.Child()
    flowbox_done = Gtk.Template.Child()

    listener_download_types = [DownloadType.GAME, DownloadType.GAME_UPDATE, DownloadType.GAME_DLC]

    def __init__(self, download_manager: DownloadManager):
        Gtk.Viewport.__init__(self)
        self.logger = logging.getLogger('minigalaxy.download_list.DownloadManagerList')
        self.download_manager = download_manager
        self.downloads = {}

        self.change_handler = {
            DownloadState.STARTED: self.download_started,
            DownloadState.COMPLETED: self.download_stopped,
            DownloadState.QUEUED: self.download_queued,
            DownloadState.PROGRESS: self.download_progress,
            DownloadState.FAILED: self.download_stopped,
            DownloadState.CANCELED: self.download_stopped,
            DownloadState.STOPPED: self.download_stopped,
         #   DownloadState.PAUSED : self.download_paused
        }

        self.flowbow_labels = {
            self.flowbox_active: self.label_active,
            self.flowbox_queued: self.label_queued,
            self.flowbox_done: self.label_done
        }

        self.download_manager.add_active_downloads_listener(self.download_manager_listener)
        self.show()

    def download_manager_listener(self, change: DownloadState, download: Download):
        self.logger.debug('Received %s for Download[save_location=%s, progress=%d]',
                          change, download.filename(), download.current_progress)
        if download.download_type not in self.listener_download_types:
            return
        if change not in self.change_handler:
            return

        GLib.idle_add(self.change_handler[change], change, download)

    def download_started(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        self.__move_to_section(self.flowbox_active, download_entry, change)

    def download_queued(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        self.__move_to_section(self.flowbox_queued, download_entry, change)

    def download_stopped(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        self.__move_to_section(self.flowbox_done, download_entry, change)

    def download_paused(self, change, download):
        download_entry = self.__get_create_entry(change, download)
    #    self.__move_to_section(self.flowbox_paused, download_entry, change)

    def download_progress(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        download_entry.update_progress(download.current_progress)

    def __get_create_entry(self, change, download):
        if download.save_location not in self.downloads:
            self.downloads[download.save_location] = OngoingDownloadListEntry(self, download, change)

        return self.downloads[download.save_location]

    def __move_to_section(self, flowbox, entry, new_state: DownloadState):
        entry.remove_from_current_box()
        entry.add_to_box(flowbox)
        entry.update_buttons(new_state)

    def update_group_visibility(self, group_flowbox):
        if group_flowbox.get_children():
            self.flowbow_labels[group_flowbox].show()
            group_flowbox.show()
        else:
            group_flowbox.hide()
            self.flowbow_labels[group_flowbox].hide()


@Gtk.Template.from_file(os.path.join(UI_DIR, "download_list_entry.ui"))
class OngoingDownloadListEntry(Gtk.Box):
    __gtype_name__ = "DownloadListEntry"

    icon = Gtk.Template.Child()
    game_title = Gtk.Template.Child()
    download_progress = Gtk.Template.Child()
    image_start_action = Gtk.Template.Child()
    image_cancel_action = Gtk.Template.Child()

    action_icon_names = {
        DownloadState.QUEUED: ['media-playback-pause', 'dialog-cancel'],
        DownloadState.STARTED: ['media-playback-pause', 'dialog-cancel'],
        DownloadState.PROGRESS: [None, None],
        DownloadState.COMPLETED: [None, 'list-remove'],
        DownloadState.PAUSED: ['media-playback-start', 'edit-delete'],
        DownloadState.STOPPED: [],
        DownloadState.FAILED: ['view-refresh', 'list-remove'],
        DownloadState.CANCELED: ['view-refresh', 'list-remove'],
    }

    tooltip_texts = {
        'media-playback-start': 'Resume',
        'media-playback-pause': 'Pause',
        'view-refresh': 'Retry',
        'dialog-cancel': 'Cancel',
        'edit-delete': 'Delete File',
        'list-remove': 'Remove from list',
    }

    # button actions are defined at the end

    def __init__(self, parent_manager, download: Download, initial_state: DownloadState):
        Gtk.Box.__init__(self)
        self.manager = parent_manager
        self.download = download
        self.state = None
        self.flowbox = None
        self.game_title.set_text(f'{download.game.name}:\n{os.path.basename(download.save_location)}')
        self.update_buttons(initial_state)

    def update_progress(self, percentage):
        self.download_progress.set_fraction(percentage / 100)
        self.download_progress.set_tooltip_text("{}%".format(percentage))

    def update_buttons(self, state: DownloadState):
        self.state = state
        if state not in self.action_icon_names:
            return

        primary, secondary = self.action_icon_names[state]
        if primary:
            self.image_start_action.set_from_icon_name(primary, Gtk.IconSize.LARGE_TOOLBAR)
            self.image_start_action.set_tooltip_text(_(self.tooltip_texts[primary]))
            self.image_start_action.show()
        else:
            self.image_start_action.hide()

        if secondary:
            self.image_cancel_action.set_from_icon_name(secondary, Gtk.IconSize.LARGE_TOOLBAR)
            self.image_cancel_action.set_tooltip_text(_(self.tooltip_texts[secondary]))
            self.image_cancel_action.show()
        else:
            self.image_cancel_action.hide()

    @Gtk.Template.Callback("on_primary_button")
    def primary_button_clicked(self, widget, data):
        if self.state not in self.button_actions:
            return
        action = self.button_actions[self.state][0]
        self.manager.logger.debug('[%s:%s] - Primary button clicked, execute %s', self.state, self.download.filename(), str(action))
        action(self)

    @Gtk.Template.Callback("on_secondary_button")
    def secondary_button_clicked(self, widget, data):
        if self.state not in self.button_actions:
            return
        action = self.button_actions[self.state][1]
        self.manager.logger.debug('[%s:%s] - Secondary button clicked, execute %s', self.state, self.download.filename(), str(action))
        action(self)

    '''----- DOWNLOAD STATE OPERATIONS -----'''

    def restart(self):
        self.manager.download_manager.download(self.download)

    def unpause(self):
        self.manager.download_manager.download(self.download, restart_paused=True)

    def pause_download(self):
        self.manager.download_manager.cancel_download(self.download, cancel_state=DownloadState.PAUSED)

    def stop_download(self):
        self.manager.download_manager.cancel_download(self.download, cancel_state=DownloadState.STOPPED)

    def delete_download(self):
        self.manager.download_manager.undo_download(self.download, cancel_state=DownloadState.CANCELED)

    def NOOP(self):
        '''used for states in which a button should not do anything'''
        pass

    '''----- END DOWNLOAD STATE OPERATIONS -----'''

    '''----- VISIBILITY CONTROL -----'''

    def add_to_box(self, flowbox):
        flowbox.add(self)
        self.flowbox = flowbox
        self.show()
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
        self.manager.update_group_visibility(old_flowbox)

    '''----- END VISIBILITY CONTROL -----'''

    button_actions = {
        DownloadState.STARTED: [pause_download, stop_download],
        DownloadState.QUEUED: [pause_download, stop_download],
        # ChangeType.DOWNLOAD_PROGRESS: [None, None],
        DownloadState.COMPLETED: [NOOP, remove_from_current_box],
        DownloadState.PAUSED: [unpause, delete_download],
        DownloadState.STOPPED: [restart, delete_download],
        DownloadState.FAILED: [restart, remove_from_current_box],
        DownloadState.CANCELED: [restart, remove_from_current_box],
    }
