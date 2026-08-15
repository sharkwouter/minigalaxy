import os
import tempfile

from pathlib import Path
from unittest import TestCase

from minigalaxy.compatibility import (
    find_steam_libraries,
    find_steam_proton_tools,
    find_steam_roots,
    parse_libraryfolders,
)


class TestCompatibility(TestCase):
    def test_find_steam_roots_deduplicates_symlink_aliases(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)

            steam_root = home / ".local" / "share" / "Steam"
            steam_root.mkdir(parents=True)

            steam_alias_directory = home / ".steam"
            steam_alias_directory.mkdir()

            os.symlink(steam_root, steam_alias_directory / "root")
            os.symlink(steam_root, steam_alias_directory / "steam")

            observed = find_steam_roots(home=home)

            self.assertEqual([steam_root.resolve()], observed)

    def test_parse_libraryfolders_missing_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_file = Path(temporary_directory) / "libraryfolders.vdf"

            self.assertEqual([], parse_libraryfolders(missing_file))

    def test_find_steam_libraries_parses_secondary_library(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            steam_root = root / "Steam"
            secondary_library = root / "Games" / "Steam Library"

            (steam_root / "steamapps").mkdir(parents=True)
            secondary_library.mkdir(parents=True)

            library_file = steam_root / "steamapps" / "libraryfolders.vdf"
            library_file.write_text(
                '"libraryfolders"\n'
                '{\n'
                '\t"0"\n'
                '\t{\n'
                f'\t\t"path"\t\t"{steam_root}"\n'
                '\t}\n'
                '\t"1"\n'
                '\t{\n'
                f'\t\t"path"\t\t"{secondary_library}"\n'
                '\t}\n'
                '}\n',
                encoding="utf-8",
            )

            observed = find_steam_libraries(steam_roots=[steam_root])

            self.assertEqual(
                [
                    steam_root.resolve(),
                    secondary_library.resolve(),
                ],
                observed,
            )

    def test_find_steam_proton_tools_discovers_valve_tools(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            steam_root = Path(temporary_directory) / "Steam"
            common_directory = steam_root / "steamapps" / "common"
            common_directory.mkdir(parents=True)

            proton_names = [
                "Proton 9.0 (Beta)",
                "Proton - Experimental",
                "Proton Hotfix",
            ]

            for proton_name in proton_names:
                proton_directory = common_directory / proton_name
                proton_directory.mkdir()
                (proton_directory / "proton").touch()

            unrelated_directory = common_directory / "Some Game"
            unrelated_directory.mkdir()
            (unrelated_directory / "proton").touch()

            observed = find_steam_proton_tools(steam_roots=[steam_root])

            self.assertEqual(
                sorted(proton_names, key=str.casefold),
                [tool.name for tool in observed],
            )
            self.assertTrue(all(tool.source == "steam" for tool in observed))

    def test_find_steam_proton_tools_discovers_custom_tools(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            steam_root = Path(temporary_directory) / "Steam"
            steam_root.mkdir()

            compatibility_directory = steam_root / "compatibilitytools.d"
            compatibility_directory.mkdir()

            ge_proton = compatibility_directory / "GE-Proton10-20"
            ge_proton.mkdir()
            (ge_proton / "proton").touch()

            observed = find_steam_proton_tools(steam_roots=[steam_root])

            self.assertEqual(1, len(observed))
            self.assertEqual("GE-Proton10-20", observed[0].name)
            self.assertEqual(ge_proton.resolve(), observed[0].path)
            self.assertEqual("custom", observed[0].source)

    def test_find_steam_proton_tools_deduplicates_steam_aliases(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)

            steam_root = home / ".local" / "share" / "Steam"
            common_directory = steam_root / "steamapps" / "common"
            common_directory.mkdir(parents=True)

            proton_directory = common_directory / "Proton - Experimental"
            proton_directory.mkdir()
            (proton_directory / "proton").touch()

            steam_alias_directory = home / ".steam"
            steam_alias_directory.mkdir()

            os.symlink(steam_root, steam_alias_directory / "root")
            os.symlink(steam_root, steam_alias_directory / "steam")

            observed = find_steam_proton_tools(home=home)

            self.assertEqual(1, len(observed))
            self.assertEqual("Proton - Experimental", observed[0].name)
            self.assertEqual(proton_directory.resolve(), observed[0].path)
