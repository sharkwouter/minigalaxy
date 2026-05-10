import sys

from unittest import TestCase
from unittest.mock import MagicMock

from tests.ui import MockGiRepository


class TestWidgetUtils(TestCase):
    test_data = [
        ["key1", "Label - One"],
        ["key2", "Label - Two"]
    ]

    def setUp(self):
        # need to set up per tests, because the MockGiRepo is a shared instance otherwise
        self.gi_repo = MockGiRepository()
        m_gi = MagicMock()

        m_liststore = MagicMock()
        self.gi_repo.Gtk.ListStore = m_liststore
        self.list_store_instance = []
        m_liststore.return_value = self.list_store_instance

        self.gi_repo.Gtk.CellRendererText = MagicMock()
        self.gi_repo.Gtk.CellRendererText.return_value = self.gi_repo.Gtk.CellRendererText
        self.gi_repo.Gtk.ComboBox = MagicMock()

        sys.modules['gi.repository'] = self.gi_repo
        sys.modules['minigalaxy.ui.window'] = MagicMock()
        sys.modules['gi'] = m_gi

    def test_populate_combo_no_default(self):
        from minigalaxy.ui.widget_utils import populate_combobox

        combo = MagicMock()
        populate_combobox(combo, self.test_data, None)
        combo.set_model.assert_called_once_with(self.list_store_instance)
        combo.set_entry_text_column.assert_called_once_with(1)
        combo.add_attribute.assert_called_once_with(self.gi_repo.Gtk.CellRendererText, "text", 1)

        self.assertEqual(self.test_data, self.list_store_instance)
        combo.set_active.assert_not_called()

    def test_opulate_combo_with_preselect(self):
        from minigalaxy.ui.widget_utils import populate_combobox

        combo = MagicMock()
        populate_combobox(combo, self.test_data, "key2")
        combo.set_active.assert_called_once_with(1)
