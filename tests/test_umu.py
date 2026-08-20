import hashlib
import io
import os
import tarfile
import tempfile
from unittest import TestCase, mock
from unittest.mock import MagicMock

from minigalaxy import umu


class TestUmu(TestCase):
    def test_parse_umu_version(self):
        output = (
            "umu-launcher version 1.4.4 "
            "(3.12.3 (main, Jun 19 2026, 12:46:00))"
        )

        self.assertEqual(
            (1, 4, 4),
            umu.parse_umu_version(output),
        )

    def test_parse_umu_version_rejects_unknown_output(self):
        self.assertIsNone(
            umu.parse_umu_version("Python 3.12.3")
        )

    def test_installation_compatibility_accepts_newer_umu(self):
        installation = umu.UmuInstallation(
            path="/usr/bin/umu-run",
            version=(1, 5, 0),
            source="path",
        )

        self.assertTrue(installation.compatible)

    def test_installation_compatibility_rejects_old_umu(self):
        installation = umu.UmuInstallation(
            path="/usr/bin/umu-run",
            version=(1, 4, 3),
            source="path",
        )

        self.assertFalse(installation.compatible)

    @mock.patch(
        "minigalaxy.umu.get_umu_version",
        return_value=(1, 4, 4),
    )
    @mock.patch(
        "minigalaxy.umu.os.access",
        return_value=True,
    )
    @mock.patch(
        "minigalaxy.umu.os.path.isfile",
        return_value=True,
    )
    @mock.patch(
        "minigalaxy.umu.shutil.which",
        return_value=None,
    )
    def test_user_local_bin_is_discovered_when_path_omits_it(
        self,
        mock_which,
        mock_isfile,
        mock_access,
        mock_version,
    ):
        expected = os.path.expanduser(
            "~/.local/bin/umu-run"
        )

        installations = umu.find_umu_installations()

        self.assertEqual(expected, installations[0].path)
        self.assertEqual("user", installations[0].source)

    def test_find_compatible_umu_skips_old_candidate(self):
        old = umu.UmuInstallation(
            "/usr/bin/umu-run",
            (1, 4, 3),
            "path",
        )
        managed = umu.UmuInstallation(
            "/home/test/umu-run",
            (1, 4, 4),
            "managed",
        )

        with mock.patch(
            "minigalaxy.umu.find_umu_installations",
            return_value=[old, managed],
        ):
            observed = umu.find_compatible_umu()

        self.assertEqual(managed, observed)

    def test_get_umu_status_returns_old_install_when_no_compatible_exists(self):
        old = umu.UmuInstallation(
            "/usr/bin/umu-run",
            (1, 3, 0),
            "path",
        )

        with mock.patch(
            "minigalaxy.umu.find_umu_installations",
            return_value=[old],
        ):
            observed = umu.get_umu_status()

        self.assertEqual(old, observed)

    def test_managed_path_honors_xdg_data_home(self):
        with mock.patch.dict(
            os.environ,
            {"XDG_DATA_HOME": "/test/data"},
        ):
            observed = umu.get_managed_umu_path()

        self.assertEqual(
            "/test/data/minigalaxy/umu/umu-run",
            observed,
        )

    def test_install_managed_umu_reuses_compatible_existing_install(self):
        existing = umu.UmuInstallation(
            "/usr/bin/umu-run",
            (1, 5, 0),
            "path",
        )

        with mock.patch(
            "minigalaxy.umu.find_compatible_umu",
            return_value=existing,
        ), mock.patch(
            "minigalaxy.umu._download_managed_umu_archive",
        ) as mock_download:
            observed = umu.install_managed_umu()

        self.assertEqual(existing, observed)
        mock_download.assert_not_called()

    def test_download_rejects_bad_checksum(self):
        response = MagicMock()
        response.iter_content.return_value = [b"bad archive"]
        response.raise_for_status.return_value = None

        with mock.patch(
            "minigalaxy.umu.requests.get",
            return_value=response,
        ), self.assertRaises(umu.UmuInstallError) as error:
            umu._download_managed_umu_archive()

        self.assertIn(
            "checksum verification failed",
            str(error.exception),
        )
        response.close.assert_called_once_with()

    def test_install_managed_umu_writes_verified_zipapp(self):
        zipapp_payload = b"#!/usr/bin/env python3\nprint('umu')\n"

        tar_buffer = io.BytesIO()

        with tarfile.open(
            fileobj=tar_buffer,
            mode="w",
        ) as archive:
            info = tarfile.TarInfo(
                umu.MANAGED_UMU_ARCHIVE_MEMBER
            )
            info.size = len(zipapp_payload)
            archive.addfile(
                info,
                io.BytesIO(zipapp_payload),
            )

        archive_payload = tar_buffer.getvalue()

        with tempfile.TemporaryDirectory() as temp_dir:
            destination = os.path.join(
                temp_dir,
                "minigalaxy",
                "umu",
                "umu-run",
            )

            with mock.patch(
                "minigalaxy.umu.find_compatible_umu",
                return_value=None,
            ), mock.patch(
                "minigalaxy.umu._download_managed_umu_archive",
                return_value=archive_payload,
            ), mock.patch(
                "minigalaxy.umu.get_managed_umu_path",
                return_value=destination,
            ), mock.patch(
                "minigalaxy.umu.get_umu_version",
                return_value=(1, 4, 4),
            ):
                observed = umu.install_managed_umu()

            self.assertEqual(destination, observed.path)
            self.assertEqual((1, 4, 4), observed.version)
            self.assertEqual("managed", observed.source)
            self.assertTrue(os.access(destination, os.X_OK))

            with open(destination, "rb") as installed_file:
                self.assertEqual(
                    zipapp_payload,
                    installed_file.read(),
                )

    def test_download_accepts_exact_pinned_checksum(self):
        payload = b"official-test-payload"
        response = MagicMock()
        response.iter_content.return_value = [payload]
        response.raise_for_status.return_value = None

        with mock.patch(
            "minigalaxy.umu.MANAGED_UMU_SHA256",
            hashlib.sha256(payload).hexdigest(),
        ), mock.patch(
            "minigalaxy.umu.requests.get",
            return_value=response,
        ):
            observed = umu._download_managed_umu_archive()

        self.assertEqual(payload, observed)
