**1.4.0**
- Various improvements to the download manager, including a pause function (thanks to GB609)
- Speed up creation of wine prefixes during installations (thanks to GB609)
- Use regedit to more permanently disable useless shortcut creation by wine from within a prefix (thanks to GB609)
- Introduce a UI to show all active, stopped or failed downloads. Also allows to permanently pause a download (thanks to GB609)
- Make more Windows games able to launch through Minigalaxy
- The download UI also shows a rough size estimate if possible (thanks to GB609)
- fix connection resource leak in DownloadManager (thanks to GB609)
- The number of parallel downloads can now be adjusted dynamically. Previous setting is saved. (thanks to GB609)
- Fixed a bug that would lead to DLCs being recognized as stand-alone games (thanks to GB609)
- Allow more games to be launched via information from goggame.info (thanks to GB609)
- The DLC list will now show a table-like multi-column view where necessary. This fixes issues with games having a high number of DLCs. (thanks to GB609)
- Some bug fixes in DownloadManager related to canceling active and queued downloads (thanks to GB609)
- Fix deletion logic of downloaded installation files. Base installers and DLC will not interfere with each other anymore. (thanks to GB609)
- Failed installs will try to keep as many downloaded parts as possible, even without the keep_installers option enabled. (thanks to GB609)
- Deleting a file in download ui now also provides the option to fully cancel the game download as if cancel on the thumbnail was clicked. (thanks to GB609)
- It's now possible to cancel auto-resume of one of many parallel DLC downloads for a game by clicking delete in the download ui after stopping it first.(thanks to GB609)
- With keep_installers enabled, Minigalaxy can now detect if a game has been fully downloaded. If not, the UI will still show the 'Download' button. (thanks to GB609)
- Installations will now run one at a time through a queue, multiple DLC can be downloaded in quick sequence. (thanks to GB609)
- Large DLC downloads will be resumed automatically on restart. (thanks to GB609)
- Improved shutdown logic of Minigalaxy. If there is an installation running, it will be finished. (thanks to GB609)
- Simple fix progress bar for games consisting of multiple files. (thanks to GB609)
- Fix log in screen remaining blank on some distributions
- Fix Minigalaxy not launching on some setups with older Nvidia cards

**1.3.2**
- Completely reworked windows wine installation. This should solve a lot of problems with failing game installs. Innoextract (if installed) is only used to detect and configure the installation language. (thanks to GB609)
- Variables and arguments in game settings can now contain blanks when quoted shell-style (thanks to GB609)
- Minigalaxy will now create working Desktop Shortcuts for wine games (thanks to GB609)
- Fix games with binaries in a directory not launching in some cases 
- Minor UI change in the dialog for third-party logins (thanks to GB609)
- Desktop shortcuts created by Minigalaxy will now be updated with environment and launch argument changes from the game's property dialog when OK is clicked (thanks to GB609)
- Clean-up and fixes of the code used for grid and list style library views (thanks to GB609)
- Desktop shortcuts for windows games can now have icons, if gog provides them in the game info api 'images' section (thanks to GB609)
- Fixed a bug in download_manager that prevents correct resume of downloads with 50%+ progress after restart (thanks to GB609)
- Make sure all translations are included in releases

**1.3.1**
- Fix Windows games with multiple parts not installing with wine
- Minor AppData fixes (thanks to tim77)
- Added Portuguese translation (thanks to GLSWV)

**1.3.0**
- Fix Remove forward slash from desktop filename for Shenzhen I/O (thanks to slowsage)
- Fix race when preparing download location (thanks to viacheslavka)
- Fix multithreaded downloads of Windows games (thanks to viacheslavka)
- Fix DLC installation for Windows games (thanks to viacheslavka)
- Allow users to specify the download directory (thanks to viacheslavka)

**1.2.6**
- Fix changing the install path causing an exception
- Fix error detection & reporting on wineprefix creation failure (thanks to LeXofLeviafan)

**1.2.5**
- Fix filtering for installed games

**1.2.4**
- Fix packages missing a script

**1.2.3**
- Fix short freeze on startup (thanks to LeXofLeviafan)
- Fix game information not showing in list view (thanks to TotalCaesar659)
- Hide A Plague Tale Digital Goodies Pack (thanks to TotalCaesar659)
- Remove round corners from top of the "play" button (thanks to lmeunier)
- Move the Gametile menu button alongside the Play button (thanks to lmeunier)
- Update Spanish translation (thanks to manurtinez)
- Capitalize first letter of the "play/download/..." button (thanks to lmeunier)
- Update Traditional Chinese translation (thanks to s8321414)
- Added additional tooltips to buttons, labels, menu items and radio buttons (thanks to orende)
- Hide CDPR Goodie Pack Content
- Add notifications on successful download and installation of games (thanks to orende)
- Add category filtering dialog for game library (thanks to orende)
- Parallelize api.can_connect function with threads, futures (thanks to orende)
- Fix available disk space being checked in parent directory (thanks to Unrud)
- Create new config if reading it fails

**1.2.2**
- Fix progress bar not showing up for downloads
- Fix downloads not being cancellable
- Fix incompatibility with python 3.6
- Fix connection error texts (thanks to TotalCaesar659)
- Show DLC titles in English (thanks to TotalCaesar659)
- Fix version not being updated during a release
- Update Norwegian Bokmål translation (thanks to kimmalmo)
- Update Czech translation (thanks to jakbuz23)

**1.2.1**
- Fix downloads failing when content length is not returned by the server
- Allow different types of downloads to happen at the same time (thanks to jgerrish)
- Fix metadata file having releases in wrong order

**1.2.0**
- Split game information and properties into different windows (thanks to TotalCaesar659)
- Add list view (thanks to TotalCaesar659)
- Allow DLC to be queued up for downloading (thanks to flagrama)
- Fix changing library to a directory with special characters in the name (thanks to makson96)
- Fix signing in with Facebook (thanks to phlash)
- Always use cached DLC icons and thumbnails (thanks to TotalCaesar659)
- Cache information covers (thanks to TotalCaesar659)
- Fix installers not being cleaned up like expected (thanks to Kzimir)
- Fix error when opening game properties window when wine is not installed (thanks to lmeunier)
- Fix freeze for games generating a lot of output (thanks to lmeunier)
- Fix extracting rar based games with innoextract (thanks to Kzimir)
- Allow setting wine executable per game (thanks to Kzimir)
- Add GameMode support (thanks to TotalCaesar659)
- Add MangoHud support (thanks to TotalCaesar659)
- Add option to use Winetricks (thanks to TotalCaesar659)
- Fix updates not always being detected directly after opening Minigalaxy (thanks to TotalCaesar659)
- Fix desktop files generated not always being able to launch (thanks to otaconix)
- Show percentage when hovering over download progress bar (thanks to TotalCaesar659)
- Add option to disable update check per game (thanks to TotalCaesar659)
- Add forum, GOG Database and PCGamingWiki URLs to game information (thanks to TotalCaesar659)
- List genre as unknown in game information when none is found (thanks to mareksapota)
- Fix changing installation path causing crashes in rare cases (thanks to makson96)
- Fall back to English when locale cannot be determined (thanks to flagrama)
- Add gettext to build dependencies (thanks to larslindq)
- Improve error handling upon API errors
- Fix several issues with launching Windows games from Minigalaxy
- Fix some games getting stuck on in queue
- Fix Windows game installation not caring about preferred language (thanks to Kzimir)

- Add Greek translation (thanks to Pyrofanis)
- Add Spanish (Spain) translation (thanks to mbarrio)
- Add Romanian (Romania) translation (thanks to xSlendiX)

- Update Norwegian Bokmål translation (thanks to kimmalmo)
- Update Czech translation (thanks to jakbuz23)

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
