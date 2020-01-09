# Minigalaxy

A simple GOG client for Linux that lets you download and play your GOG Linux games

![screenshot](screenshot.jpg?raw=true)

## Features

The most important features of Minigalaxy:

- Log in with your GOG account
- Download the Linux games you own on GOG
- Launch them

In addition to that, Minigalaxy also allows you to:

- Select in which language you'd prefer to download your games
- Change where games are installed
- Search your GOG Linux library
- Show all games or just the ones you've installed
- View the error message if a game fails to launch
- Use the system's Scummvm or Dosbox installation

Features **not** in Minigalaxy:

- Installing games meant for other platforms

## Supported languages

Currently Minigalaxy can be displayed in the following languages:
- English
- Dutch
- Taiwanese Mandarin

## System requirements

Minigalaxy should work on the following distributions:

- Debian Buster (10.0) or newer
- Ubuntu 18.10 or newer
- Arch Linux
- Manjaro
- Fedora 31+
- openSUSE Tumbleweed
- Gentoo
- MX Linux 19

Minigalaxy does **not** ship for the following distributions because they do not contain the required version of PyGObject:

- Ubuntu 18.04
- Linux Mint 19.3
- openSUSE 15.1

Other Linux distributions may work as well. Minigalaxy requires the following dependencies:

- GTK+
- Python 3
- PyGObject 3.30+
- Webkit2gtk with API version 4.0 support
- Python Requests

## Installation

**Ubuntu/Debian**

Download the latest deb package from the [releases page](https://github.com/sharkwouter/minigalaxy/releases) and install it.

**Arch/Manjaro**

Available the [AUR](https://aur.archlinux.org/packages/minigalaxy). You can use an AUR helper or use the following set of commands to install Minigalaxy on Arch:

```shell script
git clone https://aur.archlinux.org/minigalaxy.git
cd minigalaxy
makepkg -si
```

**Fedora**

Available in [official repos](https://src.fedoraproject.org/rpms/minigalaxy) (F31+)

```shell script
sudo dnf install minigalaxy
```

**openSUSE**

Available in the [OBS](https://build.opensuse.org/package/show/games:tools/minigalaxy). You can use the following set of commands to install Minigalaxy on openSUSE:
```shell script
sudo zypper ar -f obs://games:tools gamestools
sudo zypper ref
sudo zypper in minigalaxy
```

**Gentoo**

Available in the [in the Metahax overlay](https://github.com/metafarion/metahax). Follow the instructions in the link to install Minigalaxy on Gentoo.

**MX Linux**

Currently available in the [Test Repository](http://mxrepo.com/mx/testrepo/pool/test/m/minigalaxy/).  Please use MX Package Installer or Synaptic instead of manually installing the .deb from the repo.

**Other distributions**

On other distributions Minigalaxy can be downloaded and started with the following commands:
```shell script
git clone https://github.com/sharkwouter/minigalaxy.git
cd minigalaxy
bin/minigalaxy
```

This will be the development version. Alternatively a tarball of a specific release can be downloaded from the [releases page](https://github.com/sharkwouter/minigalaxy/releases).

## Support
If you need any help using Minigalaxy, feel free to join the [Minigalaxy Discord server](https://discord.gg/RC4cXVD).
Bugs reports and feature requests can also be made [here](https://github.com/sharkwouter/minigalaxy/issues).

## Contribute

Currently help is needed with the following:

- Reporting bugs in the [issue tracker](https://github.com/sharkwouter/minigalaxy/issues).
- Translating to different languages. Instructions [here](https://github.com/sharkwouter/minigalaxy/wiki/Translating-Minigalaxy).
- Testing issues with the ["needs testing"](https://github.com/sharkwouter/minigalaxy/issues?q=is%3Aissue+is%3Aopen+label%3A%22needs+testing%22) tag. 
- Working on or giving input on issues with the ["help wanted"](https://github.com/sharkwouter/minigalaxy/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) tag. Also check out the [the wiki](https://github.com/sharkwouter/minigalaxy/wiki/Developer-information) for developer information.

Feel free to join the [Minigalaxy Discord](https://discord.gg/RC4cXVD) if you would like to help out.

## Known issues

Expect to see the following issues:

* Changing the installation directory makes Minigalaxy unable to detect previously installed games
* Updating games has not been implemented yet

## Special thanks

Special thanks goes out to all contributors:

- Odelpasso for multiple code contributions
- s8321414 for translating to Taiwanese Mandarin
- BlindJerobine for translating to German
- jubalh for packaging Minigalaxy for openSUSE
- tim77 for packaging Minigalaxy for Fedora
- metafarion for packaging Minigalaxy for Gentoo
