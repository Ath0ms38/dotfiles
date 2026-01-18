"""
Control Sliders - Volume, Microphone with proper mute state handling
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scale import Scale
from gi.repository import GLib

from . import icons

# Try to import audio service
try:
    from fabric.audio.service import Audio
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False


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

        slider_row.add(self.icon_btn)
        slider_row.add(self.slider)

        self.add(header_row)
        self.add(slider_row)

    def set_value(self, value: float, muted: bool = False):
        """Set slider value (0-100) and update display"""
        self._is_muted = muted

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

    def _update_icon(self, value: float, muted: bool):
        """Update icon based on state"""
        if muted:
            self.icon_label.set_label(self.icon_muted)
        else:
            self.icon_label.set_label(self.icon_normal)

    def get_muted(self) -> bool:
        """Return current mute state"""
        return self._is_muted


class ControlSliders(Box):
    """Container for volume and microphone sliders"""

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

        # Connect to audio service
        if HAS_AUDIO:
            self.audio = Audio()
            self._setup_audio_bindings()
        else:
            self.audio = None

    def disable_audio_service(self):
        """Disable the audio service temporarily to avoid Cvc crashes during BT profile switch"""
        if self.audio:
            try:
                # Close the underlying Cvc MixerControl to disconnect from PulseAudio/PipeWire
                if hasattr(self.audio, '_control') and self.audio._control:
                    self.audio._control.close()
            except Exception:
                pass
            self.audio = None

    def enable_audio_service(self):
        """Re-enable the audio service after BT profile switch"""
        if HAS_AUDIO and not self.audio:
            try:
                self.audio = Audio()
                self._setup_audio_bindings()
            except Exception:
                pass

    def _setup_audio_bindings(self):
        """Connect to audio service signals"""
        if not self.audio:
            return

        # Initial values after a small delay to ensure service is ready
        GLib.timeout_add(100, self._update_volume)
        GLib.timeout_add(100, self._update_mic)

        # Connect to speaker/mic property changes
        self.audio.connect("notify::speaker", lambda *_: GLib.idle_add(self._update_volume))
        self.audio.connect("notify::microphone", lambda *_: GLib.idle_add(self._update_mic))

        # Also connect to the stream objects directly when available
        GLib.timeout_add(200, self._connect_stream_signals)

    def _connect_stream_signals(self):
        """Connect to individual stream change signals"""
        if self.audio and self.audio.speaker:
            try:
                self.audio.speaker.connect("changed", lambda *_: GLib.idle_add(self._update_volume))
            except Exception:
                pass

        if self.audio and self.audio.microphone:
            try:
                self.audio.microphone.connect("changed", lambda *_: GLib.idle_add(self._update_mic))
            except Exception:
                pass

        return False  # Don't repeat

    def _update_volume(self):
        """Update volume slider from audio service"""
        if self.audio and self.audio.speaker:
            try:
                vol = self.audio.speaker.volume
                muted = self.audio.speaker.muted
                self.volume_slider.set_value(vol, muted)
            except Exception:
                pass
        return False

    def _update_mic(self):
        """Update mic slider from audio service"""
        if self.audio and self.audio.microphone:
            try:
                vol = self.audio.microphone.volume
                muted = self.audio.microphone.muted
                self.mic_slider.set_value(vol, muted)
            except Exception:
                pass
        return False

    def _on_volume_changed(self, scale):
        """Handle volume slider change"""
        if self.audio and self.audio.speaker:
            value = scale.get_value() * 100
            self.audio.speaker.volume = value
            # Update label immediately for responsiveness
            if not self.volume_slider.get_muted():
                self.volume_slider.value_label.set_label(f"{int(value)}%")

    def _on_volume_mute(self, btn):
        """Toggle volume mute"""
        if self.audio and self.audio.speaker:
            self.audio.speaker.muted = not self.audio.speaker.muted
            # Force immediate update
            GLib.idle_add(self._update_volume)

    def _on_mic_changed(self, scale):
        """Handle mic slider change"""
        if self.audio and self.audio.microphone:
            value = scale.get_value() * 100
            self.audio.microphone.volume = value
            # Update label immediately for responsiveness
            if not self.mic_slider.get_muted():
                self.mic_slider.value_label.set_label(f"{int(value)}%")

    def _on_mic_mute(self, btn):
        """Toggle mic mute"""
        if self.audio and self.audio.microphone:
            self.audio.microphone.muted = not self.audio.microphone.muted
            # Force immediate update
            GLib.idle_add(self._update_mic)
