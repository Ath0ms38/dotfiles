"""
Widgets Section - Compact layout: Player | Calendar | Controls+Metrics, Connectivity in bottom
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from gi.repository import Gtk, GLib

from . import icons
from .player import Player
from .metrics import Metrics
from .calendar_widget import Calendar
from .controls import ControlSliders
from .connectivity import Connectivity


class BluetoothCodecSelector(Box):
    """Bluetooth audio codec selector for headsets (mSBC for voice, SBC-XQ for music)"""

    def __init__(self, **kwargs):
        import subprocess

        super().__init__(
            name="ax-bt-codec",
            orientation="h",
            spacing=12,
            h_expand=True,
            **kwargs,
        )

        self._subprocess = subprocess

        # Header
        header = Label(
            name="ax-bt-codec-header",
            label="󰋎 Headset:",
        )
        self.add(header)

        # Discord button (mSBC)
        self.discord_btn = Button(name="ax-bt-codec-msbc")
        discord_content = Box(orientation="h", spacing=6)
        discord_content.add(Label(label="󰍬"))
        discord_content.add(Label(label="Discord"))
        self.discord_btn.add(discord_content)
        self.discord_btn.set_tooltip_text("mSBC - Voice mode with microphone")
        self.discord_btn.connect("clicked", self._on_discord_clicked)
        self.add(self.discord_btn)

        # Solo button (SBC-XQ)
        self.solo_btn = Button(name="ax-bt-codec-sbc-xq")
        solo_content = Box(orientation="h", spacing=6)
        solo_content.add(Label(label="󰎆"))
        solo_content.add(Label(label="Solo"))
        self.solo_btn.add(solo_content)
        self.solo_btn.set_tooltip_text("SBC-XQ - High quality audio")
        self.solo_btn.connect("clicked", self._on_solo_clicked)
        self.add(self.solo_btn)

    def _set_profile(self, profile_type):
        """Set Bluetooth profile using pw-cli."""
        try:
            import re

            # Find the Bluetooth device ID using wpctl
            result = self._subprocess.run(
                ["wpctl", "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            device_id = None
            for line in result.stdout.split("\n"):
                # Look for bluez5 device in the Devices section
                if "[bluez5]" in line:
                    # Extract the device ID - format is like "│      90. Razer Barracuda X (BT)              [bluez5]"
                    match = re.search(r"(\d+)\.", line)
                    if match:
                        device_id = match.group(1)
                        break

            if not device_id:
                return False

            # Map profile types to PipeWire profile index
            if profile_type == "hfp":
                profile_index = "196865"  # headset-head-unit (mSBC)
            elif profile_type == "a2dp":
                profile_index = "131074"  # a2dp-sink-sbc_xq
            else:
                return False

            # Run the profile switch directly (no Cvc to worry about now)
            self._subprocess.Popen(
                ["pw-cli", "set-param", device_id, "Profile", f"{{ index: {profile_index} }}"],
                stdout=self._subprocess.DEVNULL,
                stderr=self._subprocess.DEVNULL,
                start_new_session=True,
            )

            return True

        except Exception:
            return False

    def _on_discord_clicked(self, btn):
        """Switch to mSBC/HFP profile for Discord"""
        if self._set_profile("hfp"):
            self.discord_btn.add_style_class("active")
            self.solo_btn.remove_style_class("active")

    def _on_solo_clicked(self, btn):
        """Switch to SBC-XQ/A2DP profile for high quality audio"""
        if self._set_profile("a2dp"):
            self.solo_btn.add_style_class("active")
            self.discord_btn.remove_style_class("active")


class Widgets(Box):
    """Main widgets section with compact layout"""

    def __init__(self, notch=None, **kwargs):
        super().__init__(
            name="ax-widgets",
            orientation="v",
            spacing=10,
            h_align="fill",
            v_align="start",  # Anchor to top, don't fill
            h_expand=True,
            v_expand=False,  # Don't expand - use natural height
            visible=True,
            all_visible=True,
        )

        self.notch = notch

        # Create widgets
        self.player = Player()
        self.calendar = Calendar()
        self.controls = ControlSliders()
        self.bt_codec = BluetoothCodecSelector()
        self.metrics = Metrics()
        self.connectivity = Connectivity()

        # TOP ROW: Player | Calendar | Controls+Metrics stacked
        top_row = Box(
            name="ax-widgets-top",
            orientation="h",
            spacing=10,
            h_expand=True,
            v_expand=False,  # Don't expand - use natural height
        )

        # Player (left)
        top_row.add(self.player)

        # Calendar + Bluetooth codec (center, expanding horizontally)
        calendar_box = Box(
            name="ax-widgets-calendar",
            orientation="v",
            spacing=10,
            h_expand=True,
            v_expand=False,
            v_align="start",
            children=[self.calendar],
        )
        calendar_box.add(self.bt_codec)
        top_row.add(calendar_box)

        # Right column: Controls on top, Metrics below
        right_column = Box(
            name="ax-widgets-right",
            orientation="v",
            spacing=10,
            v_expand=False,
            v_align="start",
        )
        right_column.add(self.controls)
        right_column.add(self.metrics)
        top_row.add(right_column)

        # BOTTOM ROW: Connectivity (compact, spans full width)
        self.add(top_row)
        self.add(self.connectivity)
