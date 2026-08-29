import os
import sys
from unittest.mock import MagicMock, patch

import gi
try:
    gi.require_version('Gtk', '3.0')
except ValueError:
    pass

# Ensure the project directory is in the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


class TestGUIComponentsImports:
    """Test suite ensuring GUI components and modular tabs initialize properly."""

    @patch('gi.repository.Gtk.Window')
    def test_gui_components_structure(self, mock_window):
        from gui_components.dialogs import DialogUtils
        from gui_components.recorder_tab import RecorderTab
        from gui_components.eir_notes_tab import EIRNotesTab
        from gui_components.handwritten_tab import HandwrittenTab
        from gui_components.dictation_tab import DictationTab

        assert hasattr(DialogUtils, "show_info")
        assert hasattr(DialogUtils, "show_error")
        assert hasattr(DialogUtils, "ask_confirmation")
        assert hasattr(RecorderTab, "on_record_clicked")
        assert hasattr(EIRNotesTab, "on_video_file_set")
        assert hasattr(HandwrittenTab, "on_select_images_clicked")
        assert hasattr(DictationTab, "on_rec_clicked")
        assert hasattr(DictationTab, "on_stop_clicked")

    @patch('gi.repository.Gtk.Window')
    def test_main_gui_class(self, mock_window):
        with patch('gui_components.recorder_tab.RecorderTab'), \
             patch('gui_components.eir_notes_tab.EIRNotesTab'), \
             patch('gui_components.handwritten_tab.HandwrittenTab'), \
             patch('gui_components.dictation_tab.DictationTab'):
            from gui import ZoomRecorderGUI
            app = ZoomRecorderGUI()
            assert app is not None
