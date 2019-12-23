# MiniGalaxy

A simple GOG client for Linux. Just click download and play!

![screenshot](screenshot.png?raw=true)

## Requirements

MiniGalaxy requires the following software to work properly:

* *python3* - versions below 3.6 have not been tested
* *python3-gobject* - python library for GTK+, version 3.30+ is required
* *python3-requests* - python library for making requests to server
* *GTK+* - versions below 3.24 have not been tested
* *webkit2gtk* - a browser engine library. It is used for logging into GOG. A version with support for API version 4.0 is required

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

* Create a Gtk.Application class which is called first
* Create ``setup.py``
* Deal with api tokens expiring
* Make users able to remove games
* Show error when failing to launch a game

## Known issues

Expect to see the following issues:

* Using MiniGalaxy without an internet connection does not work
* Changing the installation directory makes MiniGalaxy unable to detect previously installed games
* After an hour of use, MiniGalaxy may need to be restarted before being able to install games again

