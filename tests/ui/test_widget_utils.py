import sys

from unittest import TestCase
from unittest.mock import MagicMock

from tests.ui import MockGiRepository


gi_repo = MockGiRepository()
m_gi = MagicMock()

m_liststore = MagicMock()
gi_repo.Gtk.ListStore = m_liststore
list_store_instance = []
m_liststore.return_value = list_store_instance

gi_repo.Gtk.CellRendererText = MagicMock()
gi_repo.Gtk.CellRendererText.return_value = gi_repo.Gtk.CellRendererText
gi_repo.Gtk.ComboBox = MagicMock()

sys.modules['gi.repository'] = gi_repo
sys.modules['gi'] = m_gi

if 'minigalaxy.ui.widget_utils' in sys.modules:
    del sys.modules['minigalaxy.ui.widget_utils']
from minigalaxy.ui.widget_utils import populate_combobox  # noqa: E402


class TestWidgetUtils(TestCase):
    test_data = [
        ["key1", "Label - One"],
        ["key2", "Label - Two"]
    ]

    def setUp(self):
        list_store_instance.clear()

    def test_populate_combo_no_default(self):
        combo = MagicMock()
        populate_combobox(combo, self.test_data, None)
        combo.set_model.assert_called_once_with(list_store_instance)
        combo.set_entry_text_column.assert_called_once_with(1)
        combo.add_attribute.assert_called_once_with(gi_repo.Gtk.CellRendererText, "text", 1)

        self.assertEqual(self.test_data, list_store_instance)
        combo.set_active.assert_not_called()

    def test_opulate_combo_with_preselect(self):
        combo = MagicMock()
        populate_combobox(combo, self.test_data, "key2")
        combo.set_active.assert_called_once_with(1)


del sys.modules['gi.repository']
del sys.modules['gi']
