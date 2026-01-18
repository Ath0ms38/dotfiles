"""
Widgets Section - Calendar, Metrics, Player, Controls
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


class Widgets(Box):
    """Main widgets section with calendar, metrics, player, controls"""

    def __init__(self, notch=None, **kwargs):
        super().__init__(
            name="ax-widgets",
            orientation="h",
            spacing=8,
            h_align="fill",
            v_align="fill",
            h_expand=True,
            v_expand=True,
            visible=True,
            all_visible=True,
        )

        self.notch = notch

        # Left column: Player
        self.player = Player()

        # Center column: Calendar + Controls
        self.calendar = Calendar()
        self.controls = ControlSliders()

        self.center_column = Box(
            name="ax-widgets-center",
            orientation="v",
            spacing=8,
            h_expand=True,
            v_expand=True,
            children=[
                self.controls,
                self.calendar,
            ],
        )

        # Right column: Metrics
        self.metrics = Metrics()

        # Assemble columns
        self.add(self.player)
        self.add(self.center_column)
        self.add(self.metrics)
