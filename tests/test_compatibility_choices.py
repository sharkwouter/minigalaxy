from pathlib import Path
from unittest import TestCase

from minigalaxy.compatibility import (
    CUSTOM_WINE_CHOICE_ID,
    PROTON_CHOICE_PREFIX,
    SYSTEM_WINE_CHOICE_ID,
    ProtonTool,
    build_compatibility_choices,
    selected_compatibility_choice_id,
)


class TestCompatibilityChoices(TestCase):

    def test_build_choices_includes_wine_and_discovered_proton(self):
        tools = [
            ProtonTool(
                name="Proton - Experimental",
                path=Path("/steam/Proton - Experimental"),
                source="steam",
            ),
            ProtonTool(
                name="GE-Proton10-1",
                path=Path("/steam/compatibilitytools.d/GE-Proton10-1"),
                source="custom",
            ),
        ]

        choices = build_compatibility_choices(
            proton_tools=tools,
        )

        self.assertEqual(
            SYSTEM_WINE_CHOICE_ID,
            choices[0].choice_id,
        )
        self.assertEqual(
            CUSTOM_WINE_CHOICE_ID,
            choices[1].choice_id,
        )

        self.assertEqual("proton", choices[2].kind)
        self.assertEqual("steam", choices[2].source)
        self.assertEqual(
            "/steam/Proton - Experimental",
            choices[2].path,
        )

        self.assertEqual("proton", choices[3].kind)
        self.assertEqual("custom", choices[3].source)
        self.assertEqual(
            "/steam/compatibilitytools.d/GE-Proton10-1",
            choices[3].path,
        )

    def test_missing_configured_proton_is_retained(self):
        choices = build_compatibility_choices(
            proton_tools=[],
            selected_runner="proton",
            selected_proton_path="/removed/Proton 9.0",
        )

        missing = choices[-1]

        self.assertEqual("proton", missing.kind)
        self.assertEqual("missing", missing.source)
        self.assertFalse(missing.available)
        self.assertEqual(
            "/removed/Proton 9.0",
            missing.path,
        )

    def test_system_wine_is_default(self):
        choice_id = selected_compatibility_choice_id(
            selected_runner="",
            selected_proton_path="",
            custom_wine_path="",
            system_wine_path="/usr/bin/wine",
        )

        self.assertEqual(
            SYSTEM_WINE_CHOICE_ID,
            choice_id,
        )

    def test_system_wine_path_is_not_treated_as_custom_wine(self):
        choice_id = selected_compatibility_choice_id(
            selected_runner="",
            selected_proton_path="",
            custom_wine_path="/usr/bin/wine",
            system_wine_path="/usr/bin/wine",
        )

        self.assertEqual(
            SYSTEM_WINE_CHOICE_ID,
            choice_id,
        )

    def test_legacy_custom_wine_is_preserved(self):
        choice_id = selected_compatibility_choice_id(
            selected_runner="",
            selected_proton_path="",
            custom_wine_path="/opt/wine-custom/bin/wine",
            system_wine_path="/usr/bin/wine",
        )

        self.assertEqual(
            CUSTOM_WINE_CHOICE_ID,
            choice_id,
        )

    def test_configured_proton_path_selects_exact_tool(self):
        choice_id = selected_compatibility_choice_id(
            selected_runner="proton",
            selected_proton_path="/steam/Proton - Experimental",
            custom_wine_path="/opt/wine-custom/bin/wine",
            system_wine_path="/usr/bin/wine",
        )

        self.assertEqual(
            f"{PROTON_CHOICE_PREFIX}"
            "/steam/Proton - Experimental",
            choice_id,
        )
