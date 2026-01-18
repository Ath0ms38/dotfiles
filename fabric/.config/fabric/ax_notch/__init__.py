"""
Ax-Shell Style Notch Module
"""

from .notch import AxNotch, create_ax_notch
from .dashboard import Dashboard
from .widgets import Widgets
from .wallpapers import WallpaperSelector
from .player import Player, PlayerSmall
from .metrics import Metrics

__all__ = [
    "AxNotch",
    "create_ax_notch",
    "Dashboard",
    "Widgets",
    "WallpaperSelector",
    "Player",
    "PlayerSmall",
    "Metrics",
]
