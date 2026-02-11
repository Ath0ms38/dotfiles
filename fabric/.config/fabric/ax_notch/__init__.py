"""
Ax-Shell Style Notch Module
"""

from .notch import AxNotch, create_ax_notch
from .dashboard import Dashboard
from .widgets import Widgets
from .wallpapers import WallpaperSelector
from .player import Player, PlayerSmall
from .metrics import Metrics
from .calendar_widget import Calendar
from .controls import ControlSliders
from .mixer import Mixer
from .connectivity import Connectivity
from .utilities import Utilities

__all__ = [
    "AxNotch",
    "create_ax_notch",
    "Dashboard",
    "Widgets",
    "WallpaperSelector",
    "Player",
    "PlayerSmall",
    "Metrics",
    "Calendar",
    "ControlSliders",
    "Mixer",
    "Connectivity",
    "Utilities",
]
