# MiniGalaxy
This project is supposed to become a simple client for GOG which works on Linux. Currently it is still work in progress and almost nothing has been implemented yet.

![screenshot](https://github.com/sharkwouter/minigalaxy/raw/master/screenshot.png)

## Requirements

MiniGalaxy requires the following software to work properly:

* *python3* - versions below 3.6 have not been tested
* *python3-gobject* - python library for GTK+, version 3.30+ is required
* *python3-requests* - python library for making requests to server
* *GTK+* - versions below 3.24 have not been tested
* *webkit2gtk* - a browser engine library used for logging into GOG, a version with support for API version 4.0 is required

## Installation

**Ubuntu 18.10**

```sh
sudo apt-get install git python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0 python3-requests
git clone https://github.com/sharkwouter/minigalaxy.git
cd minigalaxy
python3 minigalaxy.py
```

## Todo

The following changes still need to be made:

* ~~Migrate from unzip commands to zipfile~~ Not desirable, since zipfile doesn't preserve permissions
* Create a Gtk.Application class which is called first
* ~~Move download and install locations~~
* ~~Create settings window~~
* Create about window
* ~~Fix refresh button~~
* ~~Sort games based on name~~
* Add a search bar
* ~~Move minigalaxy.py to the bin directory~~
* Create ``setup.py``
* ~~Move to sqlite~~ A JSON file was chosen instead
* Remove command line output where it isn't needed

## Known issues

Expect to see the following issues:

* Using MiniGalaxy without an internet connection does not work
* Changing the installation directory makes MiniGalaxy unable to detect previously installed games
* After an hour of use, MiniGalaxy may need to be restarted before being able to install games again
* Selected language isn't being used yet
* Sometimes after installing a game MiniGalaxy will crash with the following error:

```
[xcb] Unknown sequence number while processing queue
[xcb] Most likely this is a multi-threaded client and XInitThreads has not been called
[xcb] Aborting, sorry about that.
python3: ../../src/xcb_io.c:263: poll_for_event: Assertion `!xcb_xlib_threads_sequence_lost' failed.
Aborted
```

## Resources
For the development of the following resources are being used for reference:

* [Unofficial GOG API documentation](https://gogapidocs.readthedocs.io/en/latest/)
* [The Python GTK+ 3 Tutorial](https://python-gtk-3-tutorial.readthedocs.io/en/latest/)
* [PyGObject documentation](https://pygobject.readthedocs.io/en/latest/index.html)
* [Lutris' implementation](https://github.com/lutris/lutris/blob/gog/lutris/services/gog.py)
* [sys library documentation](https://docs.python.org/3/library/sys.html#sys.platform)
