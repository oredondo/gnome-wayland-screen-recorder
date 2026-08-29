import gi
try:
    gi.require_version('Gtk', '3.0')
except ValueError:
    pass
from gi.repository import Gtk


class DialogUtils:
    """Helper class for creating consistent GTK 3 dialog windows."""

    @staticmethod
    def show_info(parent: Gtk.Window, title: str, message: str) -> None:
        """Display an informational dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    @staticmethod
    def show_error(parent: Gtk.Window, title: str, message: str) -> None:
        """Display an error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    @staticmethod
    def ask_confirmation(parent: Gtk.Window, title: str, message: str) -> bool:
        """Display a confirmation question dialog (Yes/No)."""
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=title
        )
        dialog.format_secondary_text(message)
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.YES
