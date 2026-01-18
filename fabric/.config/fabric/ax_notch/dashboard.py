"""
Dashboard - Main expanded view of the notch
Contains: Widgets, Wallpapers, Mixer, Utilities
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.stack import Stack
from gi.repository import Gtk, GLib

from . import icons


class Dashboard(Box):
    """Main dashboard with tabbed sections"""

    def __init__(self, notch=None, **kwargs):
        super().__init__(
            name="ax-dashboard",
            orientation="v",
            spacing=8,
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
            visible=True,
            all_visible=True,
        )

        self.notch = notch

        # Import sections (lazy to avoid circular imports)
        from .widgets import Widgets
        from .wallpapers import WallpaperSelector
        from .mixer import Mixer
        from .utilities import Utilities

        # Create sections
        self.widgets = Widgets(notch=notch)
        self.wallpapers = WallpaperSelector(notch=notch)
        self.mixer = Mixer(notch=notch)
        self.utilities = Utilities(notch=notch)

        # Create stack for sections
        self.stack = Stack(
            name="ax-dashboard-stack",
            transition_type="crossfade",
            transition_duration=150,
            v_expand=False,  # Don't force expand - adapt to content
            v_align="start",  # Anchor to top
            h_expand=True,
            h_align="fill",
        )
        self.stack.set_homogeneous(False)  # Allow different page sizes
        self.stack.set_interpolate_size(True)  # Smoothly animate size changes

        self.stack.add_titled(self.widgets, "widgets", "Widgets")
        self.stack.add_titled(self.wallpapers, "wallpapers", "Wallpapers")
        self.stack.add_titled(self.mixer, "mixer", "Mixer")
        self.stack.add_titled(self.utilities, "utilities", "Utilities")

        # Create tab switcher
        self.switcher = Gtk.StackSwitcher(
            name="ax-switcher",
            spacing=8,
        )
        self.switcher.set_stack(self.stack)
        self.switcher.set_hexpand(True)
        self.switcher.set_homogeneous(True)

        # Replace switcher button labels with icons
        GLib.idle_add(self._setup_switcher_icons)

        # Inner background box for blur effect
        self.bg_box = Box(
            name="ax-dashboard-bg",
            orientation="v",
            spacing=8,
            h_expand=True,
            v_expand=True,
            children=[self.switcher, self.stack],
        )

        self.add(self.bg_box)

        # Right-click to close
        self.connect(
            "button-release-event",
            lambda widget, event: (
                event.button == 3 and self.notch and self.notch.close_notch()
            ),
        )

        self.show_all()

    def _setup_switcher_icons(self):
        """Replace text labels with icons in switcher"""
        icon_map = {
            "Widgets": icons.widgets,
            "Wallpapers": icons.wallpapers,
            "Mixer": icons.speaker,
            "Utilities": icons.settings,
        }

        buttons = self.switcher.get_children()
        for btn in buttons:
            if isinstance(btn, Gtk.ToggleButton):
                for child in btn.get_children():
                    if isinstance(child, Gtk.Label):
                        label_text = child.get_text()
                        if label_text in icon_map:
                            btn.remove(child)
                            new_label = Label(
                                name=f"ax-switcher-icon-{label_text.lower()}",
                                label=icon_map[label_text],
                            )
                            btn.add(new_label)
                            new_label.show_all()
                        break

        return GLib.SOURCE_REMOVE

    def go_to_section(self, section_name: str):
        """Navigate to a specific section"""
        section_map = {
            "widgets": self.widgets,
            "wallpapers": self.wallpapers,
            "mixer": self.mixer,
            "utilities": self.utilities,
        }
        if section_name in section_map:
            self.stack.set_visible_child(section_map[section_name])

    def go_to_next_child(self):
        """Go to next section"""
        children = self.stack.get_children()
        current = self.stack.get_visible_child()
        if current in children:
            idx = children.index(current)
            next_idx = (idx + 1) % len(children)
            self.stack.set_visible_child(children[next_idx])

    def go_to_previous_child(self):
        """Go to previous section"""
        children = self.stack.get_children()
        current = self.stack.get_visible_child()
        if current in children:
            idx = children.index(current)
            prev_idx = (idx - 1) % len(children)
            self.stack.set_visible_child(children[prev_idx])
