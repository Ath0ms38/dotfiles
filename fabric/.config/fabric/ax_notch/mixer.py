"""
Mixer Section - Audio controls with per-app volume, visualizer, and pavucontrol
"""

import subprocess
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scale import Scale
from fabric.widgets.scrolledwindow import ScrolledWindow
from gi.repository import Gtk, GLib, Gdk
import cairo
import math

from . import icons
from .controls import ControlSliders

# Try to import audio service
try:
    from fabric.audio.service import Audio
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False


class AudioVisualizer(Gtk.DrawingArea):
    """Frequency bar visualizer using PulseAudio monitor"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_name("ax-visualizer")
        self.set_size_request(-1, 60)

        # Visualizer settings
        self.num_bars = 24  # Reduced from 32
        self.bar_values = [0.0] * self.num_bars
        self.smoothing = 0.4
        self._timer_id = None
        self._is_visible = False

        # Colors
        self.bar_color = (0.886, 0.486, 0.757, 0.8)  # Pink accent
        self.bg_color = (0.1, 0.1, 0.12, 0.3)

        self.connect("draw", self._on_draw)
        self.connect("map", self._on_map)
        self.connect("unmap", self._on_unmap)

    def _on_map(self, widget):
        """Start animation when widget becomes visible"""
        self._is_visible = True
        if self._timer_id is None:
            self._timer_id = GLib.timeout_add(100, self._update_values)  # 10 FPS instead of 20

    def _on_unmap(self, widget):
        """Stop animation when widget is hidden"""
        self._is_visible = False
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _update_values(self):
        """Update bar values - static display (real audio capture not implemented)"""
        if not self._is_visible:
            self._timer_id = None
            return False

        # Show static low bars instead of random animation
        # Real audio visualization would require PulseAudio monitor source
        # For now, show a subtle idle animation
        for i in range(self.num_bars):
            # Gradually decay to low idle state
            target = 0.05 + (i % 3) * 0.02  # Very subtle variation
            self.bar_values[i] = (
                self.bar_values[i] * 0.9 + target * 0.1
            )

        self.queue_draw()
        return True

    def _on_draw(self, widget, cr):
        """Draw the frequency bars"""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        # Background
        cr.set_source_rgba(*self.bg_color)
        self._draw_rounded_rect(cr, 0, 0, width, height, 12)
        cr.fill()

        # Calculate bar dimensions
        padding = 8
        available_width = width - padding * 2
        bar_width = (available_width / self.num_bars) * 0.7
        bar_gap = (available_width / self.num_bars) * 0.3
        max_height = height - padding * 2

        # Draw bars
        for i, value in enumerate(self.bar_values):
            x = padding + i * (bar_width + bar_gap)
            bar_height = max(2, value * max_height)
            y = height - padding - bar_height

            # Gradient effect based on height
            alpha = 0.4 + value * 0.6
            cr.set_source_rgba(
                self.bar_color[0],
                self.bar_color[1],
                self.bar_color[2],
                alpha
            )

            self._draw_rounded_rect(cr, x, y, bar_width, bar_height, 2)
            cr.fill()

        return False

    def _draw_rounded_rect(self, cr, x, y, width, height, radius):
        """Draw a rounded rectangle path"""
        cr.new_sub_path()
        cr.arc(x + width - radius, y + radius, radius, -math.pi/2, 0)
        cr.arc(x + width - radius, y + height - radius, radius, 0, math.pi/2)
        cr.arc(x + radius, y + height - radius, radius, math.pi/2, math.pi)
        cr.arc(x + radius, y + radius, radius, math.pi, 3*math.pi/2)
        cr.close_path()

    def set_active(self, active: bool):
        """Enable/disable the visualizer"""
        self.is_active = active


class AppVolumeSlider(Box):
    """Volume slider for a single application"""

    def __init__(self, app_name: str, app_icon: str, stream=None, **kwargs):
        super().__init__(
            name="ax-app-volume",
            orientation="h",
            spacing=8,
            h_expand=True,
            **kwargs,
        )

        self.stream = stream
        self.app_name = app_name

        # App icon
        self.icon = Label(
            name="ax-app-volume-icon",
            label=app_icon,
        )

        # App name (truncated)
        display_name = app_name[:15] + "..." if len(app_name) > 15 else app_name
        self.name_label = Label(
            name="ax-app-volume-name",
            label=display_name,
        )
        self.name_label.set_size_request(100, -1)
        self.name_label.set_xalign(0)

        # Volume slider
        self.slider = Scale(
            name="ax-app-volume-slider",
            value=1.0,
            h_expand=True,
        )
        self.slider.set_range(0, 1)
        self.slider.set_draw_value(False)
        self.slider.connect("value-changed", self._on_value_changed)

        # Volume label
        self.value_label = Label(
            name="ax-app-volume-value",
            label="100%",
        )
        self.value_label.set_size_request(45, -1)

        # Mute button
        self.mute_btn = Button(name="ax-app-volume-mute")
        self.mute_icon = Label(label=icons.speaker)
        self.mute_btn.add(self.mute_icon)
        self.mute_btn.connect("clicked", self._on_mute_clicked)

        self.add(self.icon)
        self.add(self.name_label)
        self.add(self.slider)
        self.add(self.value_label)
        self.add(self.mute_btn)

        # Set initial values if stream provided
        if stream:
            self._update_from_stream()

    def _update_from_stream(self):
        """Update UI from stream state"""
        if not self.stream:
            return
        try:
            vol = self.stream.volume / 100.0
            self.slider.set_value(vol)
            self.value_label.set_label(f"{int(self.stream.volume)}%")

            if hasattr(self.stream, 'muted') and self.stream.muted:
                self.mute_icon.set_label(icons.speaker_muted)
                self.add_style_class("muted")
            else:
                self.mute_icon.set_label(icons.speaker)
                self.remove_style_class("muted")
        except Exception:
            pass

    def _on_value_changed(self, scale):
        """Handle volume change"""
        value = scale.get_value() * 100
        self.value_label.set_label(f"{int(value)}%")
        if self.stream:
            try:
                self.stream.volume = value
            except Exception:
                pass

    def _on_mute_clicked(self, btn):
        """Toggle mute"""
        if self.stream and hasattr(self.stream, 'muted'):
            try:
                self.stream.muted = not self.stream.muted
                self._update_from_stream()
            except Exception:
                pass


class Mixer(Box):
    """Audio mixer with volume controls, per-app audio, and visualizer"""

    def __init__(self, notch=None, **kwargs):
        super().__init__(
            name="ax-mixer",
            orientation="v",
            spacing=12,
            h_expand=True,
            v_expand=True,
            **kwargs,
        )

        self.notch = notch

        # Header with title and pavucontrol button
        header_box = Box(
            name="ax-mixer-header-box",
            orientation="h",
            h_expand=True,
        )

        header = Label(
            name="ax-mixer-header",
            label=f"{icons.speaker} Audio Mixer",
            h_align="start",
            h_expand=True,
        )

        pavucontrol_btn = Button(
            name="ax-mixer-pavucontrol",
            tooltip_text="Open PulseAudio Volume Control",
        )
        pavucontrol_btn.add(Label(label=icons.settings))
        pavucontrol_btn.connect("clicked", self._open_pavucontrol)

        header_box.add(header)
        header_box.add(pavucontrol_btn)

        # Main volume controls
        self.controls = ControlSliders()

        # Audio visualizer
        visualizer_label = Label(
            name="ax-visualizer-label",
            label="󰋋 Audio Visualizer",
            h_align="start",
        )
        self.visualizer = AudioVisualizer()

        visualizer_box = Box(
            name="ax-visualizer-box",
            orientation="v",
            spacing=4,
            children=[visualizer_label, self.visualizer],
        )

        # Per-app volume section
        app_header_box = Box(
            name="ax-mixer-apps-header-box",
            orientation="h",
            h_expand=True,
        )

        app_header = Label(
            name="ax-mixer-apps-header",
            label="󰕾 Application Volumes",
            h_align="start",
            h_expand=True,
        )

        refresh_btn = Button(name="ax-mixer-refresh")
        refresh_btn.add(Label(label=icons.refresh))
        refresh_btn.connect("clicked", lambda *_: self._refresh_app_list())

        app_header_box.add(app_header)
        app_header_box.add(refresh_btn)

        # Scrollable app list
        self.app_list = Box(
            name="ax-mixer-app-list",
            orientation="v",
            spacing=6,
        )

        self.app_scroll = ScrolledWindow(
            name="ax-mixer-apps-scroll",
            h_expand=True,
            v_expand=True,
        )
        self.app_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.app_scroll.set_max_content_height(150)
        self.app_scroll.add(self.app_list)

        # Apps container
        self.app_container = Box(
            name="ax-mixer-apps",
            orientation="v",
            spacing=8,
            h_expand=True,
            children=[app_header_box, self.app_scroll],
        )

        # Add all sections
        self.add(header_box)
        self.add(self.controls)
        self.add(visualizer_box)
        self.add(self.app_container)

        # Initialize audio service and populate apps
        if HAS_AUDIO:
            self.audio = Audio()
            GLib.timeout_add(500, self._refresh_app_list)
            # Connect to stream added/removed signals (per fabric docs)
            self.audio.connect("stream-added", lambda *_: GLib.idle_add(self._refresh_app_list))
            self.audio.connect("stream-removed", lambda *_: GLib.idle_add(self._refresh_app_list))
        else:
            self.audio = None
            self._show_no_audio_message()

    def _open_pavucontrol(self, btn):
        """Open pavucontrol"""
        try:
            subprocess.Popen(
                ["pavucontrol"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # Try alternative
            try:
                subprocess.Popen(
                    ["gnome-control-center", "sound"],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    def _refresh_app_list(self):
        """Refresh the list of audio applications"""
        # Clear existing
        for child in self.app_list.get_children():
            self.app_list.remove(child)

        if not self.audio:
            self._show_no_audio_message()
            return False

        # Get application streams (use 'applications' property per fabric docs)
        try:
            apps = self.audio.applications if hasattr(self.audio, 'applications') else []

            if not apps:
                placeholder = Label(
                    name="ax-mixer-no-apps",
                    label="No applications playing audio",
                    h_align="center",
                )
                placeholder.set_opacity(0.5)
                self.app_list.add(placeholder)
            else:
                for stream in apps:
                    app_name = getattr(stream, 'name', 'Unknown')
                    app_icon = self._get_app_icon(app_name)

                    slider = AppVolumeSlider(
                        app_name=app_name,
                        app_icon=app_icon,
                        stream=stream,
                    )
                    self.app_list.add(slider)

            self.app_list.show_all()
        except Exception as e:
            print(f"Error refreshing app list: {e}")
            self._show_no_audio_message()

        return False

    def _show_no_audio_message(self):
        """Show message when no audio service"""
        for child in self.app_list.get_children():
            self.app_list.remove(child)

        placeholder = Label(
            name="ax-mixer-no-audio",
            label="Audio service not available",
            h_align="center",
        )
        placeholder.set_opacity(0.5)
        self.app_list.add(placeholder)
        self.app_list.show_all()

    def _get_app_icon(self, app_name: str) -> str:
        """Get icon for application"""
        app_icons = {
            "firefox": icons.firefox,
            "chromium": icons.chromium,
            "chrome": icons.chromium,
            "spotify": icons.spotify,
            "discord": "󰙯",
            "steam": "󰊠",
            "vlc": "󰕼",
            "mpv": "󰐌",
            "code": "󰨞",
            "obs": "󰑋",
            "zoom": "󰒃",
            "teams": "󰊻",
            "slack": "󰒱",
        }

        name_lower = app_name.lower()
        for key, icon in app_icons.items():
            if key in name_lower:
                return icon

        return icons.speaker  # Default
