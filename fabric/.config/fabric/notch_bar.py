"""
NotchBar - Simple top bar with workspaces and clock
The ax_notch module provides the separate dashboard/menu system
"""

from gi.repository import Gtk
from fabric.widgets.wayland import WaylandWindow
from fabric.widgets.box import Box
from fabric.widgets.eventbox import EventBox

from services.config import get_config
from notch.compact import CompactBar


class TopBar(WaylandWindow):
    """
    Full-width bar at the top - always visible.
    Contains workspaces, special buttons, and clock.
    """

    def __init__(self, monitor=None, **kwargs):
        self.config = get_config()

        super().__init__(
            layer="top",
            anchor="top left right",
            exclusivity="auto",
            monitor=monitor,
            keyboard_mode="none",
            name="notch",
            visible=True,
            all_visible=True,
            **kwargs
        )

        # Build the compact bar (no menu functionality)
        self.compact = CompactBar()
        self.compact.set_hexpand(True)

        # Content wrapper
        self.content_box = Box(
            name="notch-content",
            orientation="v",
            h_expand=True,
            h_align="fill",
            children=[self.compact],
        )
        self.content_box.set_hexpand(True)
        self.content_box.set_halign(Gtk.Align.FILL)

        # Event box
        self.event_box = EventBox(
            name="notch-eventbox",
            child=self.content_box,
        )
        self.event_box.set_hexpand(True)
        self.event_box.set_halign(Gtk.Align.FILL)

        self.add(self.event_box)


def create_notch_windows(monitor=None):
    """
    Create and return the TopBar window.
    Returns a tuple for compatibility (TopBar, None).
    """
    bar = TopBar(monitor=monitor)
    return bar, None
