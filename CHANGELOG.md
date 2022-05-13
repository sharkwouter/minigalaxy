**1.2.0**
- Allow DLC to be queued up for downloading (thanks to flagrama)
- Fix signing in with Facebook (thanks to phlash)

**1.1.0**
- Improve integrity check after downloading (thanks to makson96)
- Show an error showing Windows games cannot be enabled 
- Add properties menu for games where game specific actions can be made like setting launch options and opening the store page (thanks to Odelpasso and makson96)
- Add a disk space check before downloading (thanks to SvdB-nonp and makson96)
- Use a different color for the play button for installed games
- Put installed games at the top of the list
- Store saved installers in ``~/GOG Games/installer`` by default again (thanks to makson96)
- Remember if the user had the installed filter enabled (thanks to makson96)
- Extract Windows games in the background if Innoextract is available (thanks to makson96)
- Extract Windows games in the background (thanks to Odelpasso)
- Fix installing DLC for Windows games (thanks to makson96)
- Fix an error showing if the user has no games (thanks to makson96)
- Add option to hide games (thanks to TotalCaesar659)
- Ask user if they are sure when logging out (thanks to TotalCaesar659)
- Add a dark theme (thanks to TotalCaesar659)
- Run post install script after installation. This fixes Full Throttle Remastered (thanks to makson96)
- Fix games being shown twice
- Fix crash when GOG is down (thanks to lmeunier)
- Make the language configurable (thanks to TotalCaesar659 and zweif)

- Add the following translations:
  - Czech (thanks to jakbuz23)
  - Finnish (thanks to heidiwenger and jonnelafin)
  - Italian (thanks to koraynilay)
  - Swedish (thanks to Newbytee)
  - Ukrainian (thanks to karaushu)

- Update the following translations:
  - Dutch
  - German (thanks to zweif)
  - Norwegian Nynorsk (thanks to LordPilum)
  - Polish (thanks to ArturWroblewski)
  - Russian (thanks to TotalCaesar659)
  - Simplified Chinese (thanks to dummyx)
  - Spanish (thanks to LocalPinkRobin and advy99)
  - Turkish (thanks to fuzunspm)

**1.0.2**
- Fix updates sometimes not working
- Fix some games always showing an update is available
- Fix DLC not downloading (thanks to stephanlachnit)
- Fix DLC update option not showing up (thanks to makson96)
- Fix show store page button not showing anymore (thanks to makson96)
- Fix missing thumbnails not being downloaded for already installed games (thanks to makson96)
- Fix the login screen crashing in some cases (thanks to makson96)
- Use the system's icon theme for icons used (thanks to stephanlachnit and makson96)

**1.0.1**
- Open maximized if the window was maximized when last closed (thanks to TotalCaesar659)
- Kept installers are now stored in ~/.cache/minigalaxy/download
- Fix about window displaying wrong version number
- Fix show store page button not showing anymore (thanks to makson96)
- Fix the download manager crashing when an installer has been damaged during downloading (thanks to makson96)
- Fix games showing an update is available while the latest version is installed (thanks to makson96)
- Fix loading the library taking a long time when many games are installed (thanks to makson96)
- Fix Gex not launching

- Add the following translations:
    - Swedish (thanks to Newbytee)

- Update the following translations:
   - Polish (thanks to ArturWroblewski)
   - Russian (thanks to TotalCaesar659)

**1.0.0**
- Games can now be updated (thanks to mdgomes and makson96)
- DLC can now be installed and updated (thanks to makson96)
- The installed filter now also shows games which are downloading (thanks to makson96)
- Fix crash on some systems where /usr/bin is linked to /bin (thanks to sgn)
- Create new config file if old one is unreadable (thanks to SvdB-nonp)
- Fix some Windows games not installing because of the directory name used (thanks to SvdB-nonp)
- Fix some Windows games like Witcher 3 not launching because of the working directory not being set (thanks for kibun1)
- Clean up installation files for cancelled downloads (thanks to SvdB-nonp)
- Fix crash on flaky internet connection (thanks to makson96)
- Use 755 permissions for all directories created by Minigalaxy
- Remove cached files when cancelling a download (thanks to svdB-nonp)
- Installed games should no longer be shown twice (thanks to makson96)

- Add the following translations:
    - Simplified Chinese (thanks to dummyx)
    - Spanish (thanks to juanborda)

- Update the following translations:
    - Brazilian Portuguese (thanks to EsdrasTarsis)
    - Dutch
    - French (thanks to Thomasb22)
    - German (thanks to BlindJerobine)
    - Norwegian Bokmål (thanks to kimmalmo)
    - Russian (thanks to protheory8)
    - Taiwanese Mandarin (thanks to s8321414)
    - Turkish (thanks to fuzunspm)

**0.9.4**
- Added the following translations:
    - Norwegian Nynorsk (thanks to LordPilum)
    - Russian (thanks to protheory8)
- Updated the following translations:
    - Brazilian Portuguese (thanks to EsdrasTarsis)
    - French (thanks to Thomasb22)
    - German (thanks to BlindJerobine)
    - Norwegian Bokmål (thanks to kimmalmo)
    - Polish (thanks to ArturWroblewski)
    - Taiwanese Mandarin (thanks to s8321414)
    - Turkish (thanks to fuzunspm)
- Added support for installing Windows games (with help from Odelpasso).
- Added store page link to game menus (thanks to larslindq).
- Fixed game directories being created without any spaces in the name (thanks to larslindq).
- Fixed thumbnails not being downloaded for already installed games.
- Fixed symlinks to libraries not being created correctly upon installation.
- Made preparations for a Flathub package.
- Added all contributors and translators to the about window.

**0.9.3**
- Added the following translations:
    - German (thanks to BlindJerobine)
    - Turkish (thanks to fuzunspm)
    - Brazilian Portuguese (thanks to EsdrasTarsis)
    - Norwegian Bokmål (thanks to kimmalmo)
    - Polish (thanks to ArturWroblewski)
    - French (thanks to thomansb22)
- Added option to cancel downloads.
- Changed the way games are downloaded to a queue instead of trying to download everything at once.
- Added support option to game specific menus which open the GOG support page (thanks to BlindJerobine).
- Ask for confirmation before uninstalling (thanks to Odelpasso).
- Added option to display FPS in games (thanks to Odelpasso).
- Downloads can now be resumed after having been cancelled before.
- Installers are now verified before installing.
- The active download is now resumed when restarting Minigalaxy.
- Fixed issue with games not downloading.

**0.9.2**
- Added a button to installed games which allow you to:
    - Uninstall a game.
    - Open the directory in which the game is installed.
- Added translation support. The following additional languages are now supported:
    - Dutch
    - Taiwanese Mandarin (thanks to s8321414)
    - German (thanks to BlindJerobine)
- Added offline mode.
- The system's Dosbox and Scummvm installations are now preferred over the ones bundled with games.
- Improved game detection to check in all directories in the installation path.
- Added the option to keep game installers (thanks to Odelpasso).
- Added the option to disable staying logged in (thanks to Odelpasso).
- The preferences menu now uses a file picker for setting the installation path (thanks to Odelpasso).
- Startup time has been reduced.
- Games which aren't installed are now grayed out.
- Fixed FTL not being able to start.
- Fixed issue with thumbnails sometimes not fully loading.
- Fixed potential crash after logging in the first time.
- Fixed close button on about window not working.

**0.9.1**
- Fixed crashes and freezes sometimes happening while downloading and installing games.
- Fixed installation failing when the installation directory is not on same filesystem as ``/home``.
- Fixed downloads crashing when the installation directory is changed or the refresh button is pressed.
- Fixed changing installation directory not loading which games are installed in the new directory.
- Fixed copyright file in deb package not being machine readable.
- Moved binary to ``/usr/games`` in the deb package.
- Add command line options ``--help``, ``--version`` and ``--reset``. The reset option will reset the cache and configuration. 

**0.9.0**
- Initial release.
