"""
Control Sliders - Volume, Microphone using wpctl (avoids Cvc bugs)
"""

import subprocess
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scale import Scale
from gi.repository import GLib

from . import icons


def _run_wpctl(*args):
    """Run wpctl command and return output"""
    try:
        result = subprocess.run(
            ["wpctl", *args],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_volume(sink_type: str) -> tuple[float, bool]:
    """Get volume and mute state for @DEFAULT_AUDIO_SINK@ or @DEFAULT_AUDIO_SOURCE@"""
    try:
        output = _run_wpctl("get-volume", sink_type)
        # Output format: "Volume: 0.50" or "Volume: 0.50 [MUTED]"
        if not output:
            return 50.0, False

        muted = "[MUTED]" in output
        # Extract volume value
        parts = output.replace("[MUTED]", "").split()
        if len(parts) >= 2:
            vol = float(parts[1]) * 100
            return vol, muted
        return 50.0, False
    except Exception:
        return 50.0, False


def _set_volume(sink_type: str, volume: float):
    """Set volume for @DEFAULT_AUDIO_SINK@ or @DEFAULT_AUDIO_SOURCE@"""
    # wpctl expects 0-1.5 range (150% max)
    vol_normalized = volume / 100.0
    _run_wpctl("set-volume", sink_type, str(vol_normalized))


def _toggle_mute(sink_type: str):
    """Toggle mute for @DEFAULT_AUDIO_SINK@ or @DEFAULT_AUDIO_SOURCE@"""
    _run_wpctl("set-mute", sink_type, "toggle")


class ControlSlider(Box):
    """Single control slider with icon, slider, and value display"""

    def __init__(
        self,
        name: str,
        label_text: str,
        icon: str,
        icon_muted: str = None,
        on_value_changed=None,
        on_icon_clicked=None,
        **kwargs
    ):
        super().__init__(
            name=f"ax-control-{name}",
            orientation="v",
            spacing=4,
            h_expand=True,
            **kwargs,
        )

        self.control_name = name
        self.icon_normal = icon
        self.icon_muted = icon_muted or icon
        self._is_muted = False
        self._value_handler = on_value_changed
        self._updating = False  # Prevent feedback loops
        self._dragging = False  # Track if user is dragging
        self._last_value = 0.0  # Track last known value

        # Header row: Label + Value
        header_row = Box(
            name=f"ax-control-{name}-header",
            orientation="h",
            h_expand=True,
        )

        self.label = Label(
            name=f"ax-control-{name}-label",
            label=label_text,
            h_align="start",
        )

        self.value_label = Label(
            name=f"ax-control-{name}-value",
            label="50%",
            h_align="end",
            h_expand=True,
        )

        header_row.add(self.label)
        header_row.add(self.value_label)

        # Slider row: Icon + Slider
        slider_row = Box(
            name=f"ax-control-{name}-slider-row",
            orientation="h",
            spacing=8,
            h_expand=True,
        )

        # Icon button (for mute toggle)
        self.icon_btn = Button(
            name=f"ax-control-{name}-icon",
        )
        self.icon_label = Label(label=icon)
        self.icon_btn.add(self.icon_label)

        if on_icon_clicked:
            self.icon_btn.connect("clicked", on_icon_clicked)

        # Slider
        self.slider = Scale(
            name=f"ax-control-{name}-slider",
            value=0.5,
            h_expand=True,
        )
        self.slider.set_range(0, 1)
        self.slider.set_draw_value(False)

        if on_value_changed:
            self.slider.connect("value-changed", on_value_changed)

        # Track drag state to prevent polling interference
        self.slider.connect("button-press-event", self._on_drag_start)
        self.slider.connect("button-release-event", self._on_drag_end)

        slider_row.add(self.icon_btn)
        slider_row.add(self.slider)

        self.add(header_row)
        self.add(slider_row)

    def _on_drag_start(self, widget, event):
        """Called when user starts dragging the slider"""
        self._dragging = True
        return False  # Allow event to propagate

    def _on_drag_end(self, widget, event):
        """Called when user stops dragging the slider"""
        self._dragging = False
        return False  # Allow event to propagate

    def is_dragging(self) -> bool:
        """Check if user is currently dragging"""
        return self._dragging

    def set_value(self, value: float, muted: bool = False):
        """Set slider value (0-100) and update display"""
        # Don't update while user is dragging
        if self._dragging:
            return

        self._is_muted = muted
        self._updating = True
        self._last_value = value

        # Update slider
        self.slider.set_value(value / 100.0)

        # Update value label
        if muted:
            self.value_label.set_label("Muted")
        else:
            self.value_label.set_label(f"{int(value)}%")

        # Update icon based on mute state
        self._update_icon(value, muted)

        # Update style classes
        if muted:
            self.add_style_class("muted")
            self.icon_btn.add_style_class("muted")
        else:
            self.remove_style_class("muted")
            self.icon_btn.remove_style_class("muted")

        self._updating = False

    def _update_icon(self, value: float, muted: bool):
        """Update icon based on state"""
        if muted:
            self.icon_label.set_label(self.icon_muted)
        else:
            self.icon_label.set_label(self.icon_normal)

    def get_muted(self) -> bool:
        """Return current mute state"""
        return self._is_muted

    def is_updating(self) -> bool:
        """Check if currently updating from external source"""
        return self._updating


class ControlSliders(Box):
    """Container for volume and microphone sliders using wpctl"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-controls",
            orientation="v",
            spacing=12,
            h_expand=True,
            **kwargs,
        )

        # Volume slider
        self.volume_slider = ControlSlider(
            name="volume",
            label_text="󰕾 Speaker",
            icon=icons.speaker,
            icon_muted=icons.speaker_muted,
            on_value_changed=self._on_volume_changed,
            on_icon_clicked=self._on_volume_mute,
        )

        # Microphone slider
        self.mic_slider = ControlSlider(
            name="mic",
            label_text="󰍬 Microphone",
            icon=icons.microphone,
            icon_muted=icons.microphone_muted,
            on_value_changed=self._on_mic_changed,
            on_icon_clicked=self._on_mic_mute,
        )

        self.add(self.volume_slider)
        self.add(self.mic_slider)

        # Initial update
        GLib.timeout_add(100, self._update_volume)
        GLib.timeout_add(100, self._update_mic)

        # Poll for changes periodically (every 1 second)
        GLib.timeout_add(1000, self._poll_audio_state)

    def _poll_audio_state(self):
        """Poll audio state periodically"""
        self._update_volume()
        self._update_mic()
        return True  # Continue polling

    def _update_volume(self):
        """Update volume slider from wpctl"""
        vol, muted = _get_volume("@DEFAULT_AUDIO_SINK@")
        self.volume_slider.set_value(vol, muted)
        return False

    def _update_mic(self):
        """Update mic slider from wpctl"""
        vol, muted = _get_volume("@DEFAULT_AUDIO_SOURCE@")
        self.mic_slider.set_value(vol, muted)
        return False

    def _on_volume_changed(self, scale):
        """Handle volume slider change"""
        if self.volume_slider.is_updating():
            return
        value = scale.get_value() * 100
        _set_volume("@DEFAULT_AUDIO_SINK@", value)
        # Update label immediately for responsiveness
        if not self.volume_slider.get_muted():
            self.volume_slider.value_label.set_label(f"{int(value)}%")

    def _on_volume_mute(self, btn):
        """Toggle volume mute"""
        _toggle_mute("@DEFAULT_AUDIO_SINK@")
        # Force immediate update
        GLib.idle_add(self._update_volume)

    def _on_mic_changed(self, scale):
        """Handle mic slider change"""
        if self.mic_slider.is_updating():
            return
        value = scale.get_value() * 100
        _set_volume("@DEFAULT_AUDIO_SOURCE@", value)
        # Update label immediately for responsiveness
        if not self.mic_slider.get_muted():
            self.mic_slider.value_label.set_label(f"{int(value)}%")

    def _on_mic_mute(self, btn):
        """Toggle mic mute"""
        _toggle_mute("@DEFAULT_AUDIO_SOURCE@")
        # Force immediate update
        GLib.idle_add(self._update_mic)
