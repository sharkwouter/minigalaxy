import hashlib
import io
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass

import requests

from minigalaxy.translation import _


MINIMUM_UMU_VERSION = (1, 4, 4)
MINIMUM_UMU_VERSION_TEXT = "1.4.4"

# Accept any compatible UMU already installed by the user/system. When
# MiniGalaxy needs to provision UMU itself, use this pinned, tested upstream
# standalone zipapp release and verify it before installation.
MANAGED_UMU_VERSION = (1, 4, 4)
MANAGED_UMU_VERSION_TEXT = "1.4.4"
MANAGED_UMU_URL = (
    "https://github.com/Open-Wine-Components/umu-launcher/releases/download/"
    "1.4.4/umu-launcher-1.4.4-zipapp.tar"
)
MANAGED_UMU_SHA256 = (
    "eb590691841f7fad3fc3ad8fd5db4ccb"
    "87849fe7948e62b28ece7a4ee48cc851"
)
MANAGED_UMU_ARCHIVE_MEMBER = "umu/umu-run"
MAX_MANAGED_UMU_ARCHIVE_BYTES = 8 * 1024 * 1024


class UmuInstallError(RuntimeError):
    """Raised when MiniGalaxy cannot provision its managed UMU launcher."""


@dataclass(frozen=True)
class UmuInstallation:
    """A discovered UMU launcher and the version reported by that launcher."""

    path: str
    version: tuple[int, int, int] | None
    source: str

    @property
    def compatible(self):
        return (
            self.version is not None
            and self.version >= MINIMUM_UMU_VERSION
        )

    @property
    def version_text(self):
        if self.version is None:
            return _("unknown")

        return ".".join(str(part) for part in self.version)


def get_managed_umu_path():
    """Return the path reserved for MiniGalaxy's private UMU zipapp."""
    data_home = os.getenv(
        "XDG_DATA_HOME",
        os.path.expanduser("~/.local/share"),
    )

    return os.path.join(
        data_home,
        "minigalaxy",
        "umu",
        "umu-run",
    )


def parse_umu_version(output):
    """Parse the version emitted by ``umu-run --version``."""
    if not output:
        return None

    match = re.search(
        r"umu-launcher\s+version\s+"
        r"(\d+)\.(\d+)\.(\d+)",
        output,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return tuple(int(part) for part in match.groups())


def get_umu_version(path):
    """Ask an UMU executable for its semantic version."""
    try:
        result = subprocess.run(
            [path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    return parse_umu_version(result.stdout)


def _candidate_umu_paths():
    """Yield unique UMU candidates in user-preferred discovery order."""
    candidates = [
        ("path", shutil.which("umu-run")),
        (
            "user",
            os.path.expanduser("~/.local/bin/umu-run"),
        ),
        ("managed", get_managed_umu_path()),
    ]

    seen = set()

    for source, path in candidates:
        if not path:
            continue

        canonical_path = os.path.realpath(path)

        if canonical_path in seen:
            continue

        seen.add(canonical_path)

        if (
            os.path.isfile(path)
            and os.access(path, os.X_OK)
        ):
            yield source, path


def find_umu_installations():
    """Return every executable UMU candidate and its reported version."""
    return [
        UmuInstallation(
            path=path,
            version=get_umu_version(path),
            source=source,
        )
        for source, path in _candidate_umu_paths()
    ]


def find_compatible_umu():
    """Return the first UMU installation satisfying MiniGalaxy's minimum."""
    for installation in find_umu_installations():
        if installation.compatible:
            return installation

    return None


def get_umu_status():
    """
    Return the UMU installation most useful to display in the UI.

    A compatible launcher always wins. If only incompatible/unknown launchers
    exist, return the first one so the UI can explain why an update is needed.
    """
    installations = find_umu_installations()

    for installation in installations:
        if installation.compatible:
            return installation

    if installations:
        return installations[0]

    return None


def _download_managed_umu_archive():
    """Download and checksum the pinned upstream UMU standalone archive."""
    response = None

    try:
        response = requests.get(
            MANAGED_UMU_URL,
            stream=True,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        if response is not None:
            response.close()

        raise UmuInstallError(
            _(
                "Could not download UMU Launcher {}: {}"
            ).format(
                MANAGED_UMU_VERSION_TEXT,
                error,
            )
        ) from error

    payload = bytearray()

    try:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue

            payload.extend(chunk)

            if len(payload) > MAX_MANAGED_UMU_ARCHIVE_BYTES:
                raise UmuInstallError(
                    _(
                        "The UMU Launcher download was unexpectedly large "
                        "and was rejected."
                    )
                )
    finally:
        response.close()

    digest = hashlib.sha256(payload).hexdigest()

    if digest != MANAGED_UMU_SHA256:
        raise UmuInstallError(
            _(
                "UMU Launcher checksum verification failed. "
                "The downloaded file was not installed."
            )
        )

    return bytes(payload)


def _read_umu_zipapp(archive_payload):
    """Read only the standalone ``umu-run`` member from the verified tar."""
    try:
        with tarfile.open(
            fileobj=io.BytesIO(archive_payload),
            mode="r:",
        ) as archive:
            member = archive.getmember(
                MANAGED_UMU_ARCHIVE_MEMBER
            )

            if not member.isfile():
                raise UmuInstallError(
                    _("The UMU Launcher archive is invalid.")
                )

            member_file = archive.extractfile(member)

            if member_file is None:
                raise UmuInstallError(
                    _("The UMU Launcher archive is invalid.")
                )

            return member_file.read()

    except (KeyError, tarfile.TarError) as error:
        raise UmuInstallError(
            _("The UMU Launcher archive is invalid.")
        ) from error


def install_managed_umu():
    """
    Ensure that a compatible UMU launcher is available.

    Existing compatible system/user installations are respected. Otherwise,
    MiniGalaxy installs a verified upstream standalone zipapp into its own XDG
    data directory, requiring no root privileges or distro package manager.
    """
    compatible = find_compatible_umu()

    if compatible:
        return compatible

    archive_payload = _download_managed_umu_archive()
    executable_payload = _read_umu_zipapp(archive_payload)

    destination = get_managed_umu_path()
    destination_dir = os.path.dirname(destination)
    os.makedirs(destination_dir, mode=0o755, exist_ok=True)

    temporary_path = ""

    try:
        with tempfile.NamedTemporaryFile(
            dir=destination_dir,
            prefix=".umu-run.",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.write(executable_payload)

        os.chmod(temporary_path, 0o755)
        os.replace(temporary_path, destination)
        temporary_path = ""

    except OSError as error:
        raise UmuInstallError(
            _(
                "Could not install UMU Launcher in {}: {}"
            ).format(
                destination_dir,
                error,
            )
        ) from error

    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)

    version = get_umu_version(destination)

    if (
        version is None
        or version < MINIMUM_UMU_VERSION
    ):
        try:
            os.unlink(destination)
        except OSError:
            pass

        raise UmuInstallError(
            _(
                "The installed UMU Launcher could not be verified as "
                "version {} or newer."
            ).format(MINIMUM_UMU_VERSION_TEXT)
        )

    return UmuInstallation(
        path=destination,
        version=version,
        source="managed",
    )
