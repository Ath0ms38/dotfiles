"""
Shortcuts Section - Quick launch buttons for common apps
"""

import subprocess
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from gi.repository import Gtk

from . import icons


class ShortcutButton(Button):
    """A single shortcut button"""

    def __init__(self, icon: str, name: str, command: str, **kwargs):
        super().__init__(
            name="ax-shortcut-btn",
            **kwargs,
        )

        self.command = command

        content = Box(
            orientation="v",
            spacing=4,
            h_align="center",
            children=[
                Label(name="ax-shortcut-icon", label=icon),
                Label(name="ax-shortcut-name", label=name),
            ],
        )

        self.add(content)
        self.connect("clicked", self._on_clicked)

    def _on_clicked(self, *args):
        """Launch the application"""
        try:
            subprocess.Popen(
                self.command.split(),
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"Failed to launch {self.command}: {e}")


class Shortcuts(Box):
    """Shortcuts section with quick launch buttons"""

    def __init__(self, notch=None, **kwargs):
        super().__init__(
            name="ax-shortcuts",
            orientation="v",
            spacing=12,
            h_align="center",
            v_align="center",
            **kwargs,
        )

        self.notch = notch

        # Default shortcuts
        shortcuts = [
            (icons.firefox, "Firefox", "firefox"),
            ("󰨞", "VS Code", "code"),
            ("", "Terminal", "kitty"),
            ("󰉋", "Files", "nautilus"),
            ("󰓇", "Spotify", "spotify"),
            ("󰙯", "Discord", "discord"),
            (icons.settings, "Settings", "gnome-control-center"),
            ("󰊠", "Steam", "steam"),
        ]

        # Create grid of shortcuts
        self.grid = Gtk.FlowBox(
            name="ax-shortcuts-grid",
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=True,
            max_children_per_line=4,
            min_children_per_line=4,
            row_spacing=8,
            column_spacing=8,
        )

        for icon, name, command in shortcuts:
            btn = ShortcutButton(icon, name, command)
            self.grid.add(btn)

        # Header
        header = Label(
            name="ax-shortcuts-header",
            label=f"{icons.pins} Quick Launch",
            h_align="center",
        )

        self.add(header)
        self.add(self.grid)
