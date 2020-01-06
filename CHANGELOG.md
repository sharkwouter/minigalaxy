**0.9.2 (unreleased)**
- Added a button to installed games which allow you to:
    - Uninstall a game.
    - Open the directory in which the game is installed.
- Added translation support. The following additional languages are now supported:
    - Dutch
    - Taiwanese Mandarin (thanks to s8321414)
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
