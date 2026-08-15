"""Discovery helpers for Windows compatibility tools installed by Steam."""

from __future__ import annotations

import re

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_LIBRARY_PATH_RE = re.compile(r'^\s*"path"\s*"((?:\\.|[^"])*)"\s*$')


@dataclass(frozen=True)
class ProtonTool:
    """A Proton compatibility tool discovered in a Steam installation."""

    name: str
    path: Path
    source: str


def _canonical_path(path: Path) -> Path:
    """
    Return a normalized absolute path.

    Steam commonly exposes the same installation through several symlinks,
    for example ~/.local/share/Steam, ~/.steam/root and ~/.steam/steam.
    Resolving those aliases prevents duplicate compatibility-tool entries.
    """
    path = path.expanduser()

    try:
        return path.resolve()
    except (OSError, RuntimeError):
        return path.absolute()


def _unique_existing_directories(paths: Iterable[Path]) -> list[Path]:
    """Return existing directories with equivalent paths deduplicated."""
    unique_paths = []
    seen_paths = set()

    for path in paths:
        if not path.is_dir():
            continue

        canonical_path = _canonical_path(path)

        if canonical_path in seen_paths:
            continue

        seen_paths.add(canonical_path)
        unique_paths.append(canonical_path)

    return unique_paths


def find_steam_roots(home: Path | None = None) -> list[Path]:
    """
    Find supported Steam installation roots.

    Native Steam normally uses ~/.local/share/Steam and exposes compatibility
    symlinks at ~/.steam/root and ~/.steam/steam. The Flatpak Steam location is
    also considered so discovery can be reused by environments where that path
    is accessible.
    """
    home = Path.home() if home is None else Path(home)

    candidates = [
        home / ".local" / "share" / "Steam",
        home / ".steam" / "root",
        home / ".steam" / "steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
    ]

    return _unique_existing_directories(candidates)


def _unescape_vdf_string(value: str) -> str:
    """
    Decode the small subset of VDF escaping relevant to filesystem paths.

    We intentionally avoid adding a VDF dependency just to obtain Steam library
    paths. Valve strings may escape a backslash or a double quote.
    """
    result = []
    index = 0

    while index < len(value):
        character = value[index]

        if character == "\\" and index + 1 < len(value):
            next_character = value[index + 1]

            if next_character in ("\\", '"'):
                result.append(next_character)
                index += 2
                continue

        result.append(character)
        index += 1

    return "".join(result)


def parse_libraryfolders(vdf_path: Path) -> list[Path]:
    """
    Parse Steam library paths from steamapps/libraryfolders.vdf.

    Only the ``path`` fields are required for compatibility-tool discovery, so
    a complete KeyValues/VDF parser is unnecessary here.
    """
    vdf_path = Path(vdf_path)

    if not vdf_path.is_file():
        return []

    libraries = []

    try:
        contents = vdf_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    for line in contents.splitlines():
        match = _LIBRARY_PATH_RE.match(line)

        if not match:
            continue

        libraries.append(Path(_unescape_vdf_string(match.group(1))))

    return libraries


def find_steam_libraries(
    steam_roots: Iterable[Path] | None = None,
    home: Path | None = None,
) -> list[Path]:
    """
    Return every accessible Steam library, including secondary libraries.

    The Steam installation root itself is a library and additional locations
    are obtained from steamapps/libraryfolders.vdf.
    """
    roots = list(find_steam_roots(home=home) if steam_roots is None else steam_roots)

    candidates = []

    for steam_root in roots:
        steam_root = Path(steam_root)
        candidates.append(steam_root)

        library_file = steam_root / "steamapps" / "libraryfolders.vdf"
        candidates.extend(parse_libraryfolders(library_file))

    return _unique_existing_directories(candidates)


def _directory_children(path: Path) -> list[Path]:
    """Return directory children safely and in a deterministic order."""
    if not path.is_dir():
        return []

    try:
        return sorted(
            (child for child in path.iterdir() if child.is_dir()),
            key=lambda child: child.name.casefold(),
        )
    except OSError:
        return []


def find_steam_proton_tools(
    steam_roots: Iterable[Path] | None = None,
    home: Path | None = None,
) -> list[ProtonTool]:
    """
    Discover Proton builds installed for Steam.

    Valve Proton builds are normally installed below
    ``steamapps/common/Proton*``. User-installed compatibility tools such as
    GE-Proton are normally installed below ``compatibilitytools.d``.

    A candidate must contain a ``proton`` launcher file. Canonical paths are
    used to prevent Steam symlink aliases from producing duplicate entries.
    """
    roots = list(find_steam_roots(home=home) if steam_roots is None else steam_roots)
    libraries = find_steam_libraries(steam_roots=roots)

    tools = []
    seen_paths = set()

    def add_tool(path: Path, source: str) -> None:
        proton_launcher = path / "proton"

        if not proton_launcher.is_file():
            return

        canonical_path = _canonical_path(path)

        if canonical_path in seen_paths:
            return

        seen_paths.add(canonical_path)
        tools.append(
            ProtonTool(
                name=path.name,
                path=canonical_path,
                source=source,
            )
        )

    for library in libraries:
        common_directory = library / "steamapps" / "common"

        for candidate in _directory_children(common_directory):
            if candidate.name.casefold().startswith("proton"):
                add_tool(candidate, "steam")

    for library in libraries:
        compatibility_directory = library / "compatibilitytools.d"

        for candidate in _directory_children(compatibility_directory):
            add_tool(candidate, "custom")

    return sorted(
        tools,
        key=lambda tool: (
            tool.source != "steam",
            tool.name.casefold(),
            str(tool.path),
        ),
    )
