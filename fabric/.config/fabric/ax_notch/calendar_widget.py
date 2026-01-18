"""
Calendar Widget
Simple calendar display
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from gi.repository import Gtk, GLib
import datetime


class Calendar(Box):
    """Calendar widget showing current month"""

    def __init__(self, view_mode: str = "month", **kwargs):
        super().__init__(
            name="ax-calendar",
            orientation="v",
            spacing=4,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )

        self.view_mode = view_mode

        # Use GTK Calendar widget
        self.calendar = Gtk.Calendar(
            name="ax-calendar-widget",
        )
        self.calendar.set_display_options(
            Gtk.CalendarDisplayOptions.SHOW_HEADING |
            Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES
        )

        # Date/time header
        self.header = Label(
            name="ax-calendar-header",
            h_align="center",
        )

        self._update_header()

        self.add(self.header)
        self.add(self.calendar)

        # Update header periodically
        GLib.timeout_add_seconds(60, self._update_header)

    def _update_header(self):
        """Update the date/time header"""
        now = datetime.datetime.now()
        self.header.set_label(now.strftime("%A, %B %d"))
        return True
