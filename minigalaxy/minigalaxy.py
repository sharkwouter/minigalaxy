#!/usr/bin/env python3
import platform
import sys
import os
import argparse
import shutil
import logging
from os.path import realpath, dirname, normpath

import requests

APPLICATION_NAME = "Minigalaxy"
SHUTDOWN_DONE = False

LAUNCH_PATH = dirname(realpath(__file__))
if os.path.isdir(os.path.join(LAUNCH_PATH, "../minigalaxy")):
    SOURCE_PATH = normpath(os.path.join(LAUNCH_PATH, '..'))
    sys.path.insert(0, SOURCE_PATH)
    os.chdir(SOURCE_PATH)

from minigalaxy.version import VERSION  # noqa: E402
from minigalaxy.paths import CONFIG_DIR, CACHE_DIR  # noqa: E402


def conf_reset():
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    shutil.rmtree(CACHE_DIR, ignore_errors=True)


def cli_params():
    parser = argparse.ArgumentParser(description="A simple GOG Linux client")

    parser.add_argument("--reset",
                        dest="reset", action="store_true",
                        help="reset the configuration of Minigalaxy")
    parser.add_argument("-v", "--version",
                        action="version",
                        version=VERSION)

    return parser.parse_args()


def show_installer_notification(installer_item):
    if not installer_item:
        return

    from minigalaxy.ui.gtk import Notify
    from minigalaxy.translation import _

    message = _("The installation of {} will continue in the background")
    popup = Notify.Notification.new("Minigalaxy",
                                    message.format(installer_item.title),
                                    "dialog-information")
    popup.show()


def setup_logging():
    from minigalaxy.paths import LOG_FILE_PATH, LOG_DIR

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    log_level = logging.INFO
    if os.environ.get("MG_DEBUG"):
        log_level = logging.DEBUG

    logging.basicConfig(
        filename=LOG_FILE_PATH,
        filemode="w",
        level=log_level,
        format=logging_format,
        encoding="utf-8",
        force=True
    )

    # Also log to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(logging_format))
    logging.getLogger().addHandler(stdout_handler)


def main():
    cli_args = cli_params()

    if cli_args.reset:
        conf_reset()

    setup_logging()

    # Disable webkit compositing, ensuring the login screen shows
    os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"

    # Disable DMABUF because it causes issues with older Nvidia cards
    os.environ["WEBKIT_DISABLE_DMABUF_RENDERER"] = "1"

    # Import the gi module after parsing arguments
    import signal
    from minigalaxy import installer
    from minigalaxy.ui.gtk import Gtk
    from minigalaxy.ui import Window
    from minigalaxy.config import Config
    from minigalaxy.api import Api
    from minigalaxy.download_manager import DownloadManager
    from minigalaxy.css import load_css

    # Start the application
    load_css()
    config = Config()
    session = requests.Session()
    session.headers.update({'User-Agent': 'Minigalaxy/{} (Linux {})'.format(VERSION, platform.machine())})
    api = Api(config, session)
    download_manager = DownloadManager(session, config)

    window = Window(config, api, download_manager, APPLICATION_NAME)

    def shutdown(*args):
        global SHUTDOWN_DONE
        if SHUTDOWN_DONE:
            return
        SHUTDOWN_DONE = True

        # perform orderly shutdown and stop of download threads to prevent download being killed at random places
        download_manager.shutdown()

        # empty installation queue, but don't stop the currently running installation (if any)
        # so the forked process will resume until the installation is done, then the threads die in an orderly fashion
        # because the queue is empty
        if installer.INSTALL_QUEUE:
            active_item = installer.INSTALL_QUEUE.shutdown()
            show_installer_notification(active_item)

        # gtk quit
        Gtk.main_quit(*args)

    signal.signal(signal.SIGINT, shutdown)
    window.connect("destroy", shutdown)

    window.load_library()
    Gtk.main()


if __name__ == "__main__":
    main()
