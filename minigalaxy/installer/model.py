from enum import Enum, auto


class InstallResultType(Enum):
    """checksum verification has started"""
    VERIFY_START = auto()
    """A file has been verified successfully"""
    VERIFY_PROGRESS = auto()
    """The real installation has started"""
    INSTALL_START = auto()
    """Installation ended with success"""
    SUCCESS = auto()
    """Installation ended in failure"""
    FAILURE = auto()
    """Checksum verification failed"""
    CHECKSUM_ERROR = auto()
    """An error happened during post installation actions"""
    POST_INSTALL_FAILURE = auto()


class InstallResult:

    def __init__(self, install_id, result_type: InstallResultType, reason, details=None):
        """Data class that will be passed to result_callback of InstallTask
        reason is a type-dependent string:
        - INSTALL_START: game name
        - VERIFY_START: game name
        - VERIFY_PROGRESS: verified file
        - SUCCESS: install directory path
        - FAILURE and CHECKSUM_ERROR: string error message
        - POST_INSTALL_FAILURE: error message

        the "details" field provides additional context information:
        - VERIFY_START: InstallerInventory
        - VERIFY_PROGRESS: the md5 of the file
        - FAILURE: depending on the failing step, usually a directory path
        - CHECKSUM_ERROR: dict {abs_file: calculated_checksum} of all failed files
        """
        self.install_id = install_id
        self.type = result_type
        self.reason = reason
        self.details = details
        self.installation_terminated = result_type in [
            InstallResultType.SUCCESS,
            InstallResultType.FAILURE,
            InstallResultType.CHECKSUM_ERROR,
            InstallResultType.POST_INSTALL_FAILURE
        ]

    def __str__(self):
        return f"InstallResult(id={self.install_id}, type={self.type}), reason={self.reason})"

    def __eq__(self, other):
        """mainly used for testing, therefore not the most efficient implementation"""
        return str(self) == str(other)


class InstallException(Exception):

    def __init__(self, message, fail_type=InstallResultType.FAILURE, data=None):
        self.fail_type = fail_type
        self.message = message
        self.data = data
