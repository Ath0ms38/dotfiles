"""
Widgets Section - Compact layout: Player | Calendar | Controls+Metrics, Connectivity in bottom
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from gi.repository import Gtk, GLib

from . import icons
from .player import Player
from .metrics import Metrics
from .calendar_widget import Calendar
from .controls import ControlSliders
from .connectivity import Connectivity


class Widgets(Box):
    """Main widgets section with compact layout"""

    def __init__(self, notch=None, **kwargs):
        super().__init__(
            name="ax-widgets",
            orientation="v",
            spacing=10,
            h_align="fill",
            v_align="start",  # Anchor to top, don't fill
            h_expand=True,
            v_expand=False,  # Don't expand - use natural height
            visible=True,
            all_visible=True,
        )

        self.notch = notch

        # Create widgets
        self.player = Player()
        self.calendar = Calendar()
        self.metrics = Metrics()
        self.controls = ControlSliders()
        self.connectivity = Connectivity()

        # TOP ROW: Player | Calendar | Controls+Metrics stacked
        top_row = Box(
            name="ax-widgets-top",
            orientation="h",
            spacing=10,
            h_expand=True,
            v_expand=False,  # Don't expand - use natural height
        )

        # Player (left)
        top_row.add(self.player)

        # Calendar (center, expanding horizontally)
        calendar_box = Box(
            name="ax-widgets-calendar",
            orientation="v",
            h_expand=True,
            v_expand=False,
            v_align="start",
            children=[self.calendar],
        )
        top_row.add(calendar_box)

        # Right column: Controls on top, Metrics below
        right_column = Box(
            name="ax-widgets-right",
            orientation="v",
            spacing=10,
            v_expand=False,
            v_align="start",
        )
        right_column.add(self.controls)
        right_column.add(self.metrics)
        top_row.add(right_column)

        # BOTTOM ROW: Connectivity (compact, spans full width)
        self.add(top_row)
        self.add(self.connectivity)
