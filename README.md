# MiniGalaxy
This project is supposed to become a simple client for GOG which works on Linux. Currently it is still work in progress and almost nothing has been implemented yet.

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
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0 python3-requests
git clone https://github.com/sharkwouter/minigalaxy.git
cd minigalaxy
python3 minigalaxy.pi
```

## Resources
For the development of the following resources are being used for reference:

* [Unofficial GOG API documentation](https://gogapidocs.readthedocs.io/en/latest/)
* [The Python GTK+ 3 Tutorial](https://python-gtk-3-tutorial.readthedocs.io/en/latest/)
* [PyGObject documentation](https://pygobject.readthedocs.io/en/latest/index.html)
* [Lutris' implementation](https://github.com/lutris/lutris/blob/gog/lutris/services/gog.py)
* [sys library documentation](https://docs.python.org/3/library/sys.html#sys.platform)
