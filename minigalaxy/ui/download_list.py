import logging
import os

import minigalaxy.logger  # noqa: F401

from minigalaxy.download import Download, DownloadType
from minigalaxy.download_manager import DownloadManager, ChangeType
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
            ChangeType.DOWNLOAD_STARTED: self.download_started,
            ChangeType.DOWNLOAD_COMPLETED: self.download_stopped,
            ChangeType.DOWNLOAD_QUEUED: self.download_queued,
            ChangeType.DOWNLOAD_PROGRESS: self.download_progress,
            ChangeType.DOWNLOAD_FAILED: self.download_stopped,
            ChangeType.DOWNLOAD_CANCELLED: self.download_stopped
        }

        self.flowbow_labels = {
            self.flowbox_active: self.label_active,
            self.flowbox_queued: self.label_queued,
            self.flowbox_done: self.label_done
        }

        self.download_manager.add_active_downloads_listener(self.download_manager_listener)
        self.show()

    def download_manager_listener(self, change: ChangeType, download: Download):
        self.logger.debug('Received %s for Download[save_location=%s, progress=%d]',
                          change, download.save_location, download.current_progress)
        if download.download_type not in self.listener_download_types:
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
        download_entry.update_progress(download.current_progress)

    def download_progress(self, change, download):
        download_entry = self.__get_create_entry(change, download)
        download_entry.update_progress(download.current_progress)

    def __get_create_entry(self, change, download):
        if download.save_location not in self.downloads:
            self.downloads[download.save_location] = OngoingDownloadListEntry(self, download, change)

        return self.downloads[download.save_location]

    def __move_to_section(self, flowbox, entry, new_state: ChangeType):
        if entry.flowbox:
            old_flowbox = entry.flowbox
            '''the entry needs to be removed from its parent FlowBoxChild
            or there will be a memory access error hard crashing the application'''
            box_child = entry.get_parent()
            box_child.remove(entry)
            old_flowbox.remove(box_child)
            box_child.destroy()
            self.__change_group_visibility(old_flowbox)

        flowbox.add(entry)
        entry.flowbox = flowbox
        entry.show()
        self.__change_group_visibility(flowbox)
        entry.update_buttons(new_state)

    def __change_group_visibility(self, group_flowbox):
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
        ChangeType.DOWNLOAD_STARTED: ['media-playback-pause', 'dialog-cancel'],
        ChangeType.DOWNLOAD_COMPLETED: [None, 'list-remove'],
        ChangeType.DOWNLOAD_QUEUED: ['media-playback-pause', 'dialog-cancel'],
        ChangeType.DOWNLOAD_PROGRESS: [None, None],
        ChangeType.DOWNLOAD_FAILED: ['view-refresh', 'list-remove'],
        ChangeType.DOWNLOAD_CANCELLED: ['media-playback-start', 'edit-delete']
    }

    tooltip_texts = {
        'media-playback-start': 'Resume',
        'media-playback-pause': 'Pause',
        'view-refresh': 'Retry',
        'dialog-cancel': 'Cancel',
        'edit-delete': 'Delete File',
        'list-remove': 'Remove from list',
    }

    def __init__(self, parent_manager, download: Download, initial_state: ChangeType):
        Gtk.Box.__init__(self)
        self.manager = parent_manager
        self.flowbox = None
        self.game_title.set_text(f'{download.game.name}:\n{os.path.basename(download.save_location)}')
        self.update_buttons(initial_state)

    def update_progress(self, percentage):
        self.download_progress.set_fraction(percentage / 100)
        self.download_progress.set_tooltip_text("{}%".format(percentage))

    def update_buttons(self, state: ChangeType):
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
        print("primary")

    @Gtk.Template.Callback("on_secondary_button")
    def secondary_button_clicked(self, widget, data):
        print("secondary")
