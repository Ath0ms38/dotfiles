"""
Mixer Section - Audio controls with device selection
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scale import Scale
from fabric.widgets.scrolledwindow import ScrolledWindow
from gi.repository import Gtk, GLib

from . import icons
from .controls import ControlSliders


class Mixer(Box):
    """Audio mixer with volume controls and per-app audio"""

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

        # Main volume controls
        self.controls = ControlSliders()

        # Section header
        header = Label(
            name="ax-mixer-header",
            label=f"{icons.speaker} Audio Mixer",
            h_align="start",
        )

        self.add(header)
        self.add(self.controls)

        # Per-app volume section (placeholder for future)
        self.app_volumes = Box(
            name="ax-mixer-apps",
            orientation="v",
            spacing=8,
        )

        app_header = Label(
            name="ax-mixer-apps-header",
            label="Application Volumes",
            h_align="start",
        )

        self.add(app_header)
        self.add(self.app_volumes)

        # Placeholder
        placeholder = Label(
            name="ax-mixer-placeholder",
            label="Per-app volume controls coming soon...",
            h_align="center",
        )
        placeholder.set_opacity(0.5)
        self.app_volumes.add(placeholder)
