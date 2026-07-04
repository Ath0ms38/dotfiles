"""
Small bar indicators: battery, power profile, clipboard history.
Self-contained (read /sys / call CLIs directly) to keep the bar light.
"""

import glob
import os
import subprocess
from fabric.widgets.button import Button
from fabric.utils import exec_shell_command_async
from gi.repository import GLib


class BatteryIndicator(Button):
    """Battery icon + percentage, read from /sys/class/power_supply.

    Hidden automatically when no battery is present (desktop).
    """

    UPDATE_INTERVAL_S = 30

    def __init__(self, **kwargs):
        super().__init__(name="battery-indicator", label="󰂑", **kwargs)
        batteries = sorted(glob.glob("/sys/class/power_supply/BAT*"))
        self._battery_path = batteries[0] if batteries else None

        self._update()
        if self._battery_path:
            GLib.timeout_add_seconds(self.UPDATE_INTERVAL_S, self._update)

    @staticmethod
    def _icon(percent: int, charging: bool) -> str:
        if charging:
            return "󰂄"
        for threshold, icon in ((90, "󰁹"), (70, "󰂁"), (50, "󰁿"), (30, "󰁽"), (10, "󰁻")):
            if percent >= threshold:
                return icon
        return "󰂃"

    def _update(self):
        if not self._battery_path:
            self.hide()
            return False

        try:
            with open(os.path.join(self._battery_path, "capacity")) as f:
                percent = int(f.read().strip())
            with open(os.path.join(self._battery_path, "status")) as f:
                status = f.read().strip()
        except OSError:
            self.hide()
            return True

        charging = status in ("Charging", "Full")
        self.set_label(f"{self._icon(percent, charging)} {percent}%")
        self.set_tooltip_text(f"Battery: {percent}% ({status})")

        for cls in ("charging", "low"):
            self.remove_style_class(cls)
        if charging:
            self.add_style_class("charging")
        elif percent <= 20:
            self.add_style_class("low")

        return True


class PowerProfileButton(Button):
    """Cycles power-profiles-daemon profiles on click.

    Hidden automatically when powerprofilesctl is not available.
    """

    PROFILES = ["performance", "balanced", "power-saver"]
    ICONS = {"performance": "󰓅", "balanced": "󰾅", "power-saver": "󰾆"}

    def __init__(self, **kwargs):
        super().__init__(
            name="power-profile-button",
            label=self.ICONS["balanced"],
            on_clicked=self._cycle,
            **kwargs,
        )
        self._profile = "balanced"

        if not GLib.find_program_in_path("powerprofilesctl"):
            GLib.idle_add(self.hide)
            return

        exec_shell_command_async("powerprofilesctl get", self._on_profile_read)

    def _on_profile_read(self, output):
        profile = str(output).strip()
        if profile in self.PROFILES:
            self._apply_ui(profile)

    def _cycle(self, *_):
        idx = self.PROFILES.index(self._profile)
        profile = self.PROFILES[(idx + 1) % len(self.PROFILES)]
        exec_shell_command_async(f"powerprofilesctl set {profile}", lambda *_: None)
        self._apply_ui(profile)

    def _apply_ui(self, profile):
        self._profile = profile
        self.set_label(self.ICONS[profile])
        self.set_tooltip_text(f"Power profile: {profile}")
        for p in self.PROFILES:
            self.remove_style_class(p)
        self.add_style_class(profile)


class ClipboardButton(Button):
    """Opens the rofi clipboard-history picker (cliphist)."""

    def __init__(self, **kwargs):
        super().__init__(
            name="clipboard-button",
            label="󰅍",
            on_clicked=self._open,
            tooltip_text="Clipboard history",
            **kwargs,
        )

    def _open(self, *_):
        script = os.path.expanduser("~/.config/rofi/scripts/clipboard.sh")
        subprocess.Popen(
            [script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
