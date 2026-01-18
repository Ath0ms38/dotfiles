"""
Control Sliders - Volume, Brightness
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
    """Single control slider with icon and value"""

    def __init__(
        self,
        name: str,
        icon: str,
        icon_muted: str = None,
        on_value_changed=None,
        on_icon_clicked=None,
        **kwargs
    ):
        super().__init__(
            name=f"ax-control-{name}",
            orientation="h",
            spacing=8,
            h_expand=True,
            **kwargs,
        )

        self.icon_normal = icon
        self.icon_muted = icon_muted or icon

        # Icon button (for mute toggle)
        self.icon_btn = Button(
            name=f"ax-control-{name}-icon",
            child=Label(label=icon),
        )
        if on_icon_clicked:
            self.icon_btn.connect("clicked", on_icon_clicked)

        # Slider
        self.slider = Scale(
            name=f"ax-control-{name}-slider",
            value=0.5,
            h_expand=True,
        )
        self.slider.set_range(0, 1)

        if on_value_changed:
            self.slider.connect("value-changed", on_value_changed)

        # Value label
        self.value_label = Label(
            name=f"ax-control-{name}-value",
            label="50%",
        )

        self.add(self.icon_btn)
        self.add(self.slider)
        self.add(self.value_label)

    def set_value(self, value: float, muted: bool = False):
        """Set slider value (0-100) and update display"""
        self.slider.set_value(value / 100.0)
        self.value_label.set_label(f"{int(value)}%")

        # Update icon
        if muted:
            self.icon_btn.get_child().set_label(self.icon_muted)
            self.add_style_class("muted")
        else:
            self.icon_btn.get_child().set_label(self.icon_normal)
            self.remove_style_class("muted")


class ControlSliders(Box):
    """Container for volume and brightness sliders"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-controls",
            orientation="v",
            spacing=8,
            h_expand=True,
            **kwargs,
        )

        # Volume slider
        self.volume_slider = ControlSlider(
            name="volume",
            icon=icons.speaker,
            icon_muted=icons.speaker_muted,
            on_value_changed=self._on_volume_changed,
            on_icon_clicked=self._on_volume_mute,
        )

        # Microphone slider
        self.mic_slider = ControlSlider(
            name="mic",
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

    def _setup_audio_bindings(self):
        """Connect to audio service signals"""
        if not self.audio:
            return

        # Initial values
        GLib.idle_add(self._update_volume)
        GLib.idle_add(self._update_mic)

        # Connect to changes
        self.audio.connect("notify::speaker", lambda *_: self._update_volume())
        self.audio.connect("notify::microphone", lambda *_: self._update_mic())

        if self.audio.speaker:
            self.audio.speaker.connect("changed", lambda *_: self._update_volume())
        if self.audio.microphone:
            self.audio.microphone.connect("changed", lambda *_: self._update_mic())

    def _update_volume(self):
        """Update volume slider from audio service"""
        if self.audio and self.audio.speaker:
            vol = self.audio.speaker.volume
            muted = self.audio.speaker.muted
            self.volume_slider.set_value(vol, muted)

    def _update_mic(self):
        """Update mic slider from audio service"""
        if self.audio and self.audio.microphone:
            vol = self.audio.microphone.volume
            muted = self.audio.microphone.muted
            self.mic_slider.set_value(vol, muted)

    def _on_volume_changed(self, scale):
        """Handle volume slider change"""
        if self.audio and self.audio.speaker:
            value = scale.get_value() * 100
            self.audio.speaker.volume = value
            self.volume_slider.value_label.set_label(f"{int(value)}%")

    def _on_volume_mute(self, btn):
        """Toggle volume mute"""
        if self.audio and self.audio.speaker:
            self.audio.speaker.muted = not self.audio.speaker.muted

    def _on_mic_changed(self, scale):
        """Handle mic slider change"""
        if self.audio and self.audio.microphone:
            value = scale.get_value() * 100
            self.audio.microphone.volume = value
            self.mic_slider.value_label.set_label(f"{int(value)}%")

    def _on_mic_mute(self, btn):
        """Toggle mic mute"""
        if self.audio and self.audio.microphone:
            self.audio.microphone.muted = not self.audio.microphone.muted
