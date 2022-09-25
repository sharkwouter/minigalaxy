# Minigalaxy

A simple GOG client for Linux.

![screenshot](screenshot.jpg?raw=true)

## Features

The most important features of Minigalaxy:

- Log in with your GOG account
- Download the Linux games you own on GOG
- Launch them!

In addition to that, Minigalaxy also allows you to:

- Update your games
- Install and update DLC
- Select which language you'd prefer to download your games in
- Change where games are installed
- Search your GOG Linux library
- Show all games or just the ones you've installed
- View the error message if a game fails to launch
- Enable displaying the FPS in games
- Use the system's ScummVM or DOSBox installation
- Install Windows games using Wine

## Supported languages

Currently, Minigalaxy can be displayed in the following languages:

- Brazilian Portuguese
- Czech
- English
- Dutch
- French
- Finnish
- German
- Italian
- Norwegian Bokmål
- Norwegian Nynorsk
- Polish
- Russian
- Simplified Chinese
- Spanish
- Swedish
- Taiwanese Mandarin
- Turkish
- Ukranian

## System requirements

Minigalaxy should work on the following distributions:

- Debian 10 or newer
- Ubuntu 18.10 or newer
- Linux Mint 20 or newer
- Arch Linux
- Manjaro
- Fedora Linux 31 or newer
- openSUSE Tumbleweed and Leap 15.2 or newer
- Gentoo Linux
- MX Linux 19 or newer
- Solus
- Void Linux

Minigalaxy does **not** ship for the following distributions because they do not contain the required version of PyGObject:

- Ubuntu 18.04
- Linux Mint 19.3
- openSUSE 15.1

Other Linux distributions may work as well. Minigalaxy requires the following dependencies:

- GTK+
- Python 3
- PyGObject 3.29.1+
- Webkit2gtk with API version 4.0 support
- Python Requests
- gettext

## Installation

<a href="https://repology.org/project/minigalaxy/versions">
    <img src="https://repology.org/badge/vertical-allrepos/minigalaxy.svg" alt="Packaging status" align="right">
</a>

<details><summary>Debian/Ubuntu</summary>

Available in the official repositories since Debian 11 and Ubuntu 21.04. You can install it with:
<pre>
sudo apt install minigalaxy
</pre>

You can also download the latest .deb package from the <a href="https://github.com/sharkwouter/minigalaxy/releases">releases page</a> and install it that way.
</details>

<details><summary>Arch/Manjaro</summary>

Available the <a href="https://aur.archlinux.org/packages/minigalaxy">AUR</a>. You can use an AUR helper or use the following set of commands to install Minigalaxy on Arch:
<pre>
git clone https://aur.archlinux.org/minigalaxy.git
cd minigalaxy
makepkg -si
</pre>
</details>

<details><summary>Fedora</summary>

Available in the <a href="https://src.fedoraproject.org/rpms/minigalaxy">official repositories</a> since Fedora 31. You can install it with:
<pre>
sudo dnf install minigalaxy
</pre>
</details>

<details><summary>openSUSE</summary>

Available in the official repositories for openSUSE Tumbleweed and also Leap since 15.2. You can install it with:
<pre>
sudo zypper in minigalaxy
</pre>

Alternatively, you can use the following set of commands to install Minigalaxy on openSUSE from the devel project on <a href="https://build.opensuse.org/package/show/games:tools/minigalaxy">OBS</a>:
<pre>
sudo zypper ar -f obs://games:tools gamestools
sudo zypper ref
sudo zypper in minigalaxy
</pre>
</details>

<details><summary>Gentoo</summary>

Available in the <a href="https://github.com/metafarion/metahax">Metahax overlay</a>. Follow the instructions in the link to install Minigalaxy on Gentoo.
</details>

<details><summary>MX Linux</summary>

Available in the <a href="http://mxrepo.com/mx/repo/pool/main/m/minigalaxy/">official repository</a>.  Please use MX Package Installer or Synaptic instead of manually installing the .deb from the repo.
</details>

<details><summary>Solus</summary>
 
Available in the official repositories. You can install it with:
<pre>
sudo eopkg it minigalaxy
</pre>
</details>

<details><summary>Void Linux</summary>

Available in the official repositories. You can install it with:
<pre>
sudo xbps-install -S minigalaxy
</pre>
</details>

<details><summary>Other distributions</summary>

On other distributions, Minigalaxy can be downloaded and started with the following commands:
<pre>
git clone https://github.com/sharkwouter/minigalaxy.git
cd minigalaxy
scripts/compile-translations.sh
bin/minigalaxy
</pre>

This will be the development version. Alternatively, a tarball of a specific release can be downloaded from the <a href="https://github.com/sharkwouter/minigalaxy/releases">releases page</a>.
</details>

## Support

If you need any help using Minigalaxy, feel free to join the [Minigalaxy Discord server](https://discord.gg/RC4cXVD).
Bugs reports and feature requests can also be made [here](https://github.com/sharkwouter/minigalaxy/issues).

## Contribute

Currently, help is needed with the following:

- Reporting bugs in the [issue tracker](https://github.com/sharkwouter/minigalaxy/issues).
- Translating to different languages. Instructions [here](https://github.com/sharkwouter/minigalaxy/wiki/Translating-Minigalaxy).
- Testing issues with the ["needs testing"](https://github.com/sharkwouter/minigalaxy/issues?q=is%3Aissue+is%3Aopen+label%3A%22needs+testing%22) tag. 
- Working on or giving input on issues with the ["help wanted"](https://github.com/sharkwouter/minigalaxy/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) or ["good first issue"](https://github.com/sharkwouter/minigalaxy/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) tag. Also check out the [the wiki](https://github.com/sharkwouter/minigalaxy/wiki/Developer-information) for developer information.

Feel free to join the [Minigalaxy Discord](https://discord.gg/RC4cXVD) if you would like to help out.

## Special thanks

Special thanks goes out to all contributors:

- makson96 for multiple code contributions
- Odelpasso for multiple code contributions
- TotalCaesar659 for multiple code contributions
- SvdB-nonp for multiple code contributions
- tim77 for packaging Minigalaxy for Fedora, Flathub and multiple code contributions
- larslindq for multiple code contributions
- graag for multiple code contributions
- lmeunier for multiple code contributions
- BlindJerobine for translating to German and adding the support option
- zweif contributions to code and the German translation
- JoshuaFern for packaging Minigalaxy for NixOS and for contributing code
- stephanlachnit for upstreaming to Debian and multiple code contributions
- sgn for fixing a bug
- otaconix for fixing a bug
- phlash for fixing a bug
- mareksapota for fixing a bug
- zocker-160 for code cleanup
- waltercool for contributing code
- jgerrish for improving the download code
- s8321414 for translating to Taiwanese Mandarin
- fuzunspm for translating to Turkish
- thomansb22 for translating to French
- ArturWroblewski for translating to Polish
- kimmalmo for translating to Norwegian Bokmål
- EsdrasTarsis for translating to Brazilian Portuguese
- protheory8 for translating to Russian
- LordPilum for translating to Norwegian Nynorsk
- dummyx for translating to simplified Chinese
- juanborda, advy99 and LocalPinkRobin for translating to Spanish
- Newbytee for translating to Swedish
- Pyrofanis for translating to Greek
- mbarrio for translating to Spanish
- jubalh for packaging Minigalaxy for openSUSE
- gasinvein for packaging Minigalaxy for flathub
- metafarion for packaging Minigalaxy for Gentoo
- SwampRabbit and Steven Pusser for packaging Minigalaxy for MX Linux
- karaushu for translating to Ukrainian
- koraynilay for translating to Italian
- heidiwenger and jonnelafin for translating to Finnish
- jakbuz23 for translating to Czech
