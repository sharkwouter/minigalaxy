from enum import Enum, auto


class State(Enum):
    DOWNLOADABLE = auto()
    INSTALLABLE = auto()
    UPDATABLE = auto()
    QUEUED = auto()
    DOWNLOADING = auto()
    INSTALLING = auto()
    INSTALLED = auto()
    NOTLAUNCHABLE = auto()
    UNINSTALLING = auto()
    UPDATING = auto()
    UPDATE_INSTALLABLE = auto()
    VERIFYING = auto()
