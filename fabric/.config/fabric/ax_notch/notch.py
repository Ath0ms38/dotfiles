"""
Ax-Shell Style Notch Bar
A center notch with dropdown dashboard containing:
- Widgets section (calendar, metrics, player)
- Wallpaper picker with matugen
- Mixer (audio controls)
- App shortcuts
"""

import os
import json
import subprocess
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.stack import Stack
from fabric.widgets.revealer import Revealer
from fabric.widgets.wayland import WaylandWindow
from fabric.hyprland.service import Hyprland
from gi.repository import Gdk, GLib, Gtk

from .dashboard import Dashboard
from .player import PlayerSmall


class AxNotch(WaylandWindow):
    """
    Ax-Shell style notch that sits at top center.
    Shows compact view by default, expands to dashboard on click/hover.
    """

    def __init__(self, monitor: int = 0, **kwargs):
        super().__init__(
            name="ax-notch",
            title="ax-notch",  # Sets Wayland layer namespace for hyprland rules
            layer="overlay",  # Above the main bar
            anchor="top",  # Center only
            margin="-50px 8px 8px 8px",  # Negative top margin to overlap bar's exclusive zone
            keyboard_mode="none",
            exclusivity="none",
            visible=True,
            all_visible=True,
            monitor=monitor,
        )

        self._is_open = False
        self._is_hovered = False
        self._is_fullscreen = False

        # Connect to Hyprland for fullscreen detection
        self.hyprland = Hyprland()
        self.hyprland.connect("event::fullscreen", self._on_fullscreen_change)
        self.hyprland.connect("event::activewindow", self._on_active_window_change)

        # Check initial fullscreen state
        GLib.idle_add(self._check_fullscreen)

        # Build compact view (default state)
        self.compact = self._build_compact()

        # Build dashboard (expanded state)
        self.dashboard = Dashboard(notch=self)

        # Main content stack
        self.stack = Stack(
            name="ax-notch-content",
            transition_type="crossfade",
            transition_duration=200,
            children=[self.compact, self.dashboard],
        )
        self.stack.set_homogeneous(False)
        self.stack.set_interpolate_size(True)

        # Set sizes
        self.compact.set_size_request(180, 32)
        self.dashboard.set_size_request(900, 450)

        # Revealer for slide animation
        self.revealer = Revealer(
            name="ax-notch-revealer",
            transition_type="slide-down",
            transition_duration=250,
            child_revealed=True,
            child=self.stack,
        )

        # Wrap in event box for hover detection
        self.hover_box = Gtk.EventBox(name="ax-notch-hover")
        self.hover_box.add(self.revealer)
        self.hover_box.set_size_request(180, 8)  # Minimum hover area
        self.hover_box.add_events(
            Gdk.EventMask.ENTER_NOTIFY_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK
        )
        self.hover_box.connect("enter-notify-event", self._on_enter)
        self.hover_box.connect("leave-notify-event", self._on_leave)

        # Main container with notch styling
        self.notch_box = Box(
            name="ax-notch-box",
            orientation="v",
            h_align="center",
            children=[self.hover_box],
        )

        self.add(self.notch_box)
        self.show_all()

        # Keybinding to close
        self.add_keybinding("Escape", lambda *_: self.close_notch())

    def _build_compact(self) -> Box:
        """Build the compact view shown when notch is closed"""

        # Player small widget (shows media info or user@host)
        self.player_small = PlayerSmall()

        # User label - static display instead of active window
        username = os.getlogin()
        hostname = os.uname().nodename
        self.user_label = Label(
            name="ax-compact-user",
            label=f"{username}@{hostname}",
        )

        # Stack to switch between player/user
        self.compact_stack = Stack(
            name="ax-compact-stack",
            transition_type="slide-up-down",
            transition_duration=100,
            children=[
                self.user_label,
                self.player_small,
            ],
        )
        self.compact_stack.set_visible_child(self.user_label)

        # Wrap in clickable event box
        compact_event = Gtk.EventBox(name="ax-compact")
        compact_event.add(self.compact_stack)
        compact_event.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        compact_event.connect("button-press-event", lambda *_: self.toggle_notch())

        return Box(
            name="ax-compact-box",
            h_align="center",
            v_align="center",
            children=[compact_event],
        )


    def _on_enter(self, widget, event):
        """Mouse entered notch area"""
        self._is_hovered = True
        self.revealer.set_reveal_child(True)
        return False

    def _on_leave(self, widget, event):
        """Mouse left notch area"""
        if event.detail == Gdk.NotifyType.INFERIOR:
            return False

        self._is_hovered = False

        # Don't hide if notch is open
        if not self._is_open:
            # Small delay before checking if we should hide
            GLib.timeout_add(200, self._check_hide)

        return False

    def _check_hide(self):
        """Check if we should hide the notch after mouse leave"""
        if not self._is_hovered and not self._is_open:
            # Keep revealed but could add occlusion logic here
            pass
        return False

    def toggle_notch(self):
        """Toggle between compact and expanded state"""
        if self._is_open:
            self.close_notch()
        else:
            self.open_notch()

    def open_notch(self, section: str = "widgets"):
        """Open the notch to dashboard view"""
        self._is_open = True
        self.set_keyboard_mode("on-demand")  # Allow clicking elsewhere while menu is open
        self.stack.add_style_class("open")
        self.notch_box.add_style_class("open")
        self.stack.set_visible_child(self.dashboard)

        # Navigate to section if specified
        if section:
            self.dashboard.go_to_section(section)

    def close_notch(self):
        """Close the notch back to compact view"""
        self._is_open = False
        self.set_keyboard_mode("none")
        # Hide the entire dashboard first to avoid any flash
        self.dashboard.set_visible(False)
        # Switch view immediately
        self.stack.set_visible_child(self.compact)
        self.stack.remove_style_class("open")
        self.notch_box.remove_style_class("open")
        # Re-show dashboard after a delay (for next open)
        GLib.timeout_add(100, self._restore_dashboard)

    def _restore_dashboard(self):
        """Restore dashboard visibility after close"""
        self.dashboard.set_visible(True)
        return False

    def open_section(self, section_name: str):
        """Open a specific section of the dashboard"""
        self.open_notch(section_name)

    def _on_fullscreen_change(self, _hyprland, _event):
        """Handle fullscreen state changes"""
        GLib.idle_add(self._check_fullscreen)

    def _on_active_window_change(self, _hyprland, _event):
        """Handle active window changes - recheck fullscreen"""
        GLib.idle_add(self._check_fullscreen)

    def _check_fullscreen(self):
        """Check if any window on current monitor is fullscreen"""
        try:
            output = subprocess.check_output(
                ["hyprctl", "activewindow", "-j"],
                text=True
            )
            data = json.loads(output)
            is_fullscreen = data.get("fullscreen", 0) != 0

            if is_fullscreen != self._is_fullscreen:
                self._is_fullscreen = is_fullscreen
                self._update_visibility()
        except Exception:
            pass
        return False

    def _update_visibility(self):
        """Update notch visibility based on fullscreen state"""
        if self._is_fullscreen and not self._is_open:
            # Hide the notch when fullscreen (but not if dashboard is open)
            self.set_visible(False)
        else:
            self.set_visible(True)


def create_ax_notch(monitor: int = 0) -> AxNotch:
    """Factory function to create an AxNotch instance"""
    return AxNotch(monitor=monitor)
