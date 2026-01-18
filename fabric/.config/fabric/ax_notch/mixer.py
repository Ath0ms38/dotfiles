"""
Mixer Section - Audio controls with per-app volume, visualizer, and pavucontrol
Uses pactl commands to avoid Cvc bugs
"""

import subprocess
import json
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


def _run_pactl(*args):
    """Run pactl command and return output"""
    try:
        result = subprocess.run(
            ["pactl", *args],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_sink_inputs():
    """Get list of sink inputs (application audio streams) using pactl"""
    try:
        output = _run_pactl("--format=json", "list", "sink-inputs")
        if not output:
            return []

        data = json.loads(output)
        apps = []

        for item in data:
            app_info = {
                "index": item.get("index"),
                "name": item.get("properties", {}).get("application.name", "Unknown"),
                "volume": 100,  # Default
                "muted": item.get("mute", False),
            }

            # Parse volume - format varies, try to get percentage
            vol_info = item.get("volume", {})
            if vol_info:
                # Get first channel's percentage
                for channel, val in vol_info.items():
                    if isinstance(val, dict) and "value_percent" in val:
                        vol_str = val["value_percent"].replace("%", "")
                        try:
                            app_info["volume"] = int(vol_str)
                        except ValueError:
                            pass
                        break

            apps.append(app_info)

        return apps
    except Exception:
        return []


def _set_sink_input_volume(index: int, volume: int):
    """Set volume for a sink input"""
    _run_pactl("set-sink-input-volume", str(index), f"{volume}%")


def _set_sink_input_mute(index: int, muted: bool):
    """Set mute state for a sink input"""
    _run_pactl("set-sink-input-mute", str(index), "1" if muted else "0")


class AudioVisualizer(Gtk.DrawingArea):
    """Audio visualizer using pw-top for real audio activity"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_name("ax-visualizer")
        self.set_size_request(-1, 60)

        # Visualizer settings
        self.num_bars = 24
        self.bar_values = [0.0] * self.num_bars
        self._timer_id = None
        self._is_visible = False
        self._time = 0.0
        self._audio_activity = 0.0  # Real audio activity from pw-top (0.0 to 1.0)
        self._volume = 0.5  # Current volume for scaling

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
            self._timer_id = GLib.timeout_add(50, self._update_values)  # 20 FPS

    def _on_unmap(self, widget):
        """Stop animation when widget is hidden"""
        self._is_visible = False
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _get_audio_activity(self):
        """Get audio activity level by checking for active (non-corked) sink-inputs"""
        try:
            result = subprocess.run(
                ["pactl", "--format=json", "list", "sink-inputs"],
                capture_output=True,
                text=True,
                timeout=0.5,
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                active_streams = 0
                total_volume = 0.0

                for stream in data:
                    # Check if stream is not corked (paused)
                    if not stream.get("corked", True):
                        active_streams += 1
                        # Get stream volume for intensity
                        vol_info = stream.get("volume", {})
                        for channel, val in vol_info.items():
                            if isinstance(val, dict) and "value_percent" in val:
                                vol_str = val["value_percent"].replace("%", "")
                                try:
                                    total_volume += int(vol_str)
                                except ValueError:
                                    pass
                                break

                if active_streams > 0:
                    # Return activity based on number of active streams and their volume
                    avg_volume = total_volume / active_streams / 100.0
                    # Scale: more streams = more activity, capped at 1.0
                    activity = min(1.0, (0.5 + active_streams * 0.25) * avg_volume)
                    return max(0.3, activity)  # Minimum activity when playing

        except Exception:
            pass
        return 0.0

    def _get_current_volume(self):
        """Get current volume level"""
        try:
            result = subprocess.run(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                capture_output=True,
                text=True,
                timeout=0.5,
            )
            if result.returncode == 0:
                output = result.stdout
                if "[MUTED]" in output:
                    return 0.0
                parts = output.replace("[MUTED]", "").split()
                if len(parts) >= 2:
                    return float(parts[1])
        except Exception:
            pass
        return self._volume

    def _update_values(self):
        """Update bar values based on real audio activity"""
        if not self._is_visible:
            self._timer_id = None
            return False

        self._time += 0.15

        # Poll audio activity and volume (every ~200ms to reduce CPU)
        if int(self._time * 10) % 4 == 0:
            self._audio_activity = self._get_audio_activity()
            self._volume = self._get_current_volume()

        # Generate waveform based on actual audio activity
        activity = self._audio_activity * self._volume

        for i in range(self.num_bars):
            if activity > 0.01:
                # Active audio: animated waveform scaled by activity
                wave1 = math.sin(self._time + i * 0.3) * 0.3
                wave2 = math.sin(self._time * 1.5 + i * 0.2) * 0.2
                wave3 = math.sin(self._time * 0.7 + i * 0.5) * 0.15

                # Add some randomness for more organic feel
                noise = math.sin(self._time * 3.7 + i * 1.3) * 0.1

                target = (0.3 + wave1 + wave2 + wave3 + noise) * activity
                target = max(0.05, min(1.0, target))
            else:
                # No audio: idle state with minimal bars
                target = 0.03 + math.sin(self._time * 0.5 + i * 0.2) * 0.02

            # Smooth transition
            self.bar_values[i] = self.bar_values[i] * 0.7 + target * 0.3

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
        pass  # No external resources to manage


class AppVolumeSlider(Box):
    """Volume slider for a single application using pactl"""

    def __init__(self, app_info: dict, **kwargs):
        super().__init__(
            name="ax-app-volume",
            orientation="h",
            spacing=8,
            h_expand=True,
            **kwargs,
        )

        self.app_info = app_info
        self.index = app_info.get("index")
        self.app_name = app_info.get("name", "Unknown")
        self._updating = False
        self._dragging = False

        # App icon
        app_icon = self._get_app_icon(self.app_name)
        self.icon = Label(
            name="ax-app-volume-icon",
            label=app_icon,
        )

        # App name (truncated)
        display_name = self.app_name[:15] + "..." if len(self.app_name) > 15 else self.app_name
        self.name_label = Label(
            name="ax-app-volume-name",
            label=display_name,
        )
        self.name_label.set_size_request(100, -1)
        self.name_label.set_xalign(0)

        # Volume slider
        self.slider = Scale(
            name="ax-app-volume-slider",
            value=app_info.get("volume", 100) / 100.0,
            h_expand=True,
        )
        self.slider.set_range(0, 1.5)  # Allow up to 150%
        self.slider.set_draw_value(False)
        self.slider.connect("value-changed", self._on_value_changed)
        self.slider.connect("button-press-event", self._on_drag_start)
        self.slider.connect("button-release-event", self._on_drag_end)

        # Volume label
        vol = app_info.get("volume", 100)
        self.value_label = Label(
            name="ax-app-volume-value",
            label=f"{vol}%",
        )
        self.value_label.set_size_request(45, -1)

        # Mute button
        self.mute_btn = Button(name="ax-app-volume-mute")
        muted = app_info.get("muted", False)
        self.mute_icon = Label(label=icons.speaker_muted if muted else icons.speaker)
        self.mute_btn.add(self.mute_icon)
        self.mute_btn.connect("clicked", self._on_mute_clicked)

        if muted:
            self.add_style_class("muted")

        self.add(self.icon)
        self.add(self.name_label)
        self.add(self.slider)
        self.add(self.value_label)
        self.add(self.mute_btn)

    def _on_drag_start(self, widget, event):
        """Called when user starts dragging"""
        self._dragging = True
        return False

    def _on_drag_end(self, widget, event):
        """Called when user stops dragging"""
        self._dragging = False
        return False

    def is_dragging(self):
        """Check if user is dragging"""
        return self._dragging

    def _on_value_changed(self, scale):
        """Handle volume change"""
        if self._updating:
            return
        value = int(scale.get_value() * 100)
        self.value_label.set_label(f"{value}%")
        if self.index is not None:
            _set_sink_input_volume(self.index, value)

    def _on_mute_clicked(self, btn):
        """Toggle mute"""
        if self.index is None:
            return

        # Toggle mute state
        is_muted = "muted" in self.get_style_context().list_classes()
        new_muted = not is_muted

        _set_sink_input_mute(self.index, new_muted)

        if new_muted:
            self.mute_icon.set_label(icons.speaker_muted)
            self.add_style_class("muted")
        else:
            self.mute_icon.set_label(icons.speaker)
            self.remove_style_class("muted")

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

        # Initialize app list and set up polling
        GLib.timeout_add(500, self._refresh_app_list)
        # Poll for app changes every 2 seconds
        GLib.timeout_add(2000, self._poll_apps)

    def _poll_apps(self):
        """Poll for application changes"""
        self._refresh_app_list()
        return True  # Continue polling

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

    def _is_any_slider_dragging(self):
        """Check if any app slider is being dragged"""
        for child in self.app_list.get_children():
            if isinstance(child, AppVolumeSlider) and child.is_dragging():
                return True
        return False

    def _refresh_app_list(self):
        """Refresh the list of audio applications"""
        # Don't refresh while user is dragging a slider
        if self._is_any_slider_dragging():
            return False

        # Clear existing
        for child in self.app_list.get_children():
            self.app_list.remove(child)

        # Get application streams via pactl
        apps = _get_sink_inputs()

        if not apps:
            placeholder = Label(
                name="ax-mixer-no-apps",
                label="No applications playing audio",
                h_align="center",
            )
            placeholder.set_opacity(0.5)
            self.app_list.add(placeholder)
        else:
            for app_info in apps:
                slider = AppVolumeSlider(app_info=app_info)
                self.app_list.add(slider)

        self.app_list.show_all()
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
