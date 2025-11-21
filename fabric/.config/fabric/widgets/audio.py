"""
Audio Management Widget
Controls volume for speakers, microphones, and applications
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scale import Scale
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.wayland import WaylandWindow

# Try to import Audio service, handle if Cvc not available
try:
    from fabric.audio.service import Audio
    AUDIO_AVAILABLE = True
except ImportError as e:
    AUDIO_AVAILABLE = False
    print(f"Audio service not available: {e}")
    print("Install cinnamon-desktop: sudo pacman -S cinnamon-desktop")


class AudioControl(Box):
    """Control for a single audio stream"""

    def __init__(self, stream, **kwargs):
        super().__init__(
            orientation="v",
            spacing=8,
            name="audio-control",
            **kwargs
        )

        self.stream = stream

        # Stream name label
        self.name_label = Label(
            label=stream.name or stream.description or "Unknown",
            name="stream-name"
        )

        # Volume slider
        self.volume_scale = Scale(
            orientation="h",
            min_value=0.0,
            max_value=1.0,
            value=stream.volume,
            draw_value=False,
            h_expand=True,
            name="volume-slider"
        )

        # Volume percentage label
        self.volume_label = Label(
            label=f"{int(stream.volume * 100)}%",
            name="volume-percent"
        )

        # Mute button
        self.mute_button = Button(
            label="🔇" if stream.muted else "🔊",
            name="mute-button",
            on_clicked=self.toggle_mute
        )

        # Connect signals
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        stream.connect("changed", self.on_stream_changed)

        # Build layout
        header = Box(
            orientation="h",
            spacing=8,
            children=[
                self.name_label,
                Box(h_expand=True),  # Spacer
                self.volume_label,
                self.mute_button,
            ]
        )

        self.add(header)
        self.add(self.volume_scale)

    def on_volume_changed(self, scale):
        """Handle volume slider changes"""
        new_volume = scale.get_value()
        self.stream.volume = new_volume
        self.volume_label.set_label(f"{int(new_volume * 100)}%")

    def toggle_mute(self, *args):
        """Toggle mute state"""
        self.stream.muted = not self.stream.muted

    def on_stream_changed(self, stream):
        """Handle stream property changes"""
        # Update volume slider if changed externally
        self.volume_scale.set_value(stream.volume)
        self.volume_label.set_label(f"{int(stream.volume * 100)}%")

        # Update mute button
        self.mute_button.set_label("🔇" if stream.muted else "🔊")


class AudioWidget(WaylandWindow):
    """Audio management popup widget"""

    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="top right",
            margin="50px 20px 0px 0px",
            keyboard_mode="on-demand",
            name="audio-widget",
            visible=False,
            **kwargs
        )

        # Initialize audio service if available
        if AUDIO_AVAILABLE:
            self.audio = Audio()
            # Connect to audio service signals
            self.audio.connect("speaker-changed", lambda *_: self.rebuild_content())
            self.audio.connect("microphone-changed", lambda *_: self.rebuild_content())
            self.audio.connect("stream-added", lambda *_: self.rebuild_content())
            self.audio.connect("stream-removed", lambda *_: self.rebuild_content())
        else:
            self.audio = None

        # Build widget
        self.children = self.build_content()

    def build_content(self):
        """Build the widget content"""
        if not AUDIO_AVAILABLE or self.audio is None:
            # Show error message if audio not available
            content = Box(
                orientation="v",
                spacing=16,
                name="audio-content",
                children=[
                    Label(
                        label="🔊 Audio Control",
                        name="audio-title",
                        style="font-size: 16px; font-weight: bold;"
                    ),
                    Label(
                        label="Audio service not available",
                        name="error-message",
                        style="color: #ff6b6b; font-style: italic;"
                    ),
                    Label(
                        label="Install cinnamon-desktop:",
                        style="font-size: 12px; opacity: 0.8; margin-top: 8px;"
                    ),
                    Label(
                        label="sudo pacman -S cinnamon-desktop",
                        style="font-family: monospace; font-size: 11px; opacity: 0.7;"
                    ),
                ]
            )
        else:
            content = Box(
                orientation="v",
                spacing=16,
                name="audio-content",
                children=[
                    Label(
                        label="🔊 Audio Control",
                        name="audio-title",
                        style="font-size: 16px; font-weight: bold;"
                    ),
                    self.build_speakers_section(),
                    self.build_microphones_section(),
                    self.build_applications_section(),
                ]
            )

        return ScrolledWindow(
            min_content_size=(400, 100),
            max_content_size=(400, 600),
            child=content
        )

    def build_speakers_section(self):
        """Build speakers control section"""
        children = [
            Label(
                label="Speakers",
                name="section-title",
                style="font-size: 14px; font-weight: bold;"
            )
        ]

        # Add default speaker
        if self.audio.speaker:
            children.append(AudioControl(self.audio.speaker))

        # Add other speakers
        for speaker in self.audio.speakers:
            if speaker != self.audio.speaker:
                children.append(AudioControl(speaker))

        return Box(
            orientation="v",
            spacing=8,
            name="speakers-section",
            children=children
        )

    def build_microphones_section(self):
        """Build microphones control section"""
        children = [
            Label(
                label="Microphones",
                name="section-title",
                style="font-size: 14px; font-weight: bold;"
            )
        ]

        # Add default microphone
        if self.audio.microphone:
            children.append(AudioControl(self.audio.microphone))

        # Add other microphones
        for mic in self.audio.microphones:
            if mic != self.audio.microphone:
                children.append(AudioControl(mic))

        return Box(
            orientation="v",
            spacing=8,
            name="microphones-section",
            children=children
        )

    def build_applications_section(self):
        """Build application audio control section"""
        children = [
            Label(
                label="Applications",
                name="section-title",
                style="font-size: 14px; font-weight: bold;"
            )
        ]

        # Add application streams
        if self.audio.applications:
            for app in self.audio.applications:
                children.append(AudioControl(app))
        else:
            children.append(
                Label(
                    label="No applications playing audio",
                    name="empty-message",
                    style="opacity: 0.7; font-style: italic;"
                )
            )

        return Box(
            orientation="v",
            spacing=8,
            name="applications-section",
            children=children
        )

    def rebuild_content(self):
        """Rebuild the widget content"""
        self.children = self.build_content()

    def toggle(self):
        """Toggle widget visibility"""
        if self.get_visible():
            self.hide()
        else:
            self.show_all()


# Create singleton instance
audio_widget = None


def get_audio_widget():
    """Get or create the audio widget singleton"""
    global audio_widget
    if audio_widget is None:
        audio_widget = AudioWidget()
    return audio_widget
