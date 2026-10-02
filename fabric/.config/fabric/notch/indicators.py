"""
Small bar indicators: battery, power profile, VPN, clipboard history.
Self-contained (read /sys / call CLIs directly) to keep the bar light.
"""

import glob
import os
import subprocess
from fabric.widgets.button import Button
from fabric.utils import exec_shell_command_async
from gi.repository import GLib

from services.vpn import ProtonVpn
from services.wireguard import WireGuard
from widgets.vpn import VpnWidget


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


class VpnButton(Button):
    """Combined VPN status; click opens the Proton / WireGuard picker.

    Proton wins the label when it is doing something, since it is the one that
    changes the exit IP; otherwise the active WireGuard tunnel is shown. The
    button hides itself when neither backend has anything to offer.
    """

    # Shield-and-padlock: the plain nf-md-vpn glyph is an abstract knot that
    # reads as a smudge at bar size. WireGuard gets the knot anyway — it only
    # appears next to a tunnel name, which carries the meaning.
    ICON = "󰦝"
    WG_ICON = "󰖂"

    def __init__(self, **kwargs):
        super().__init__(name="vpn-button", label=self.ICON, **kwargs)

        # Proton is CLI-driven; without it the popup drops that page entirely.
        self._proton = ProtonVpn() if GLib.find_program_in_path("protonvpn") else None
        self._wireguard = WireGuard()

        self._popup = VpnWidget(self._proton, self._wireguard)
        if self._proton:
            self._proton.connect("changed", lambda *_: self._update())
        self._wireguard.connect("changed", lambda *_: self._update())
        self.connect("clicked", lambda *_: self._popup.toggle())
        self._update()

    def _update(self):
        state, icon, text = self._status()

        self.set_label(icon if text is None else f"{icon} {text}")
        self.set_tooltip_text(self._tooltip())

        for cls in ("connected", "connecting", "disconnecting", "error"):
            self.remove_style_class(cls)
        if state != "disconnected":
            self.add_style_class(state)

        # Nothing installed and no tunnel configured: the button is noise.
        # no-show-all keeps the bar's show_all() from bringing it back.
        wanted = bool(self._proton or self._wireguard.tunnels)
        self.set_no_show_all(not wanted)
        self.set_visible(wanted)

    def _status(self):
        """(state, icon, label suffix or None) for whichever VPN is in play."""
        proton_state = self._proton.state if self._proton else "disconnected"

        if proton_state == "connected":
            return "connected", self.ICON, self._proton.server or None
        if proton_state in ("connecting", "disconnecting"):
            return proton_state, self.ICON, "…"
        if proton_state == "error":
            return "error", self.ICON, None

        wg_state = self._wireguard.state
        if wg_state == "connected":
            return "connected", self.WG_ICON, self._wireguard.active_name or None
        if wg_state in ("connecting", "disconnecting"):
            return wg_state, self.WG_ICON, "…"

        return "disconnected", self.ICON, None

    def _tooltip(self) -> str:
        lines = []

        if self._proton:
            server = self._proton.server
            lines.append(
                {
                    "connected": f"Proton: connected to {server}" if server else "Proton: connected",
                    "connecting": "Proton: connecting…",
                    "disconnecting": "Proton: disconnecting…",
                    "error": f"Proton: {self._proton.message}",
                }.get(self._proton.state, "Proton: disconnected")
            )

        name = self._wireguard.active_name
        lines.append(
            {
                "connected": f"WireGuard: {name} up",
                "connecting": "WireGuard: bringing up…",
                "disconnecting": "WireGuard: taking down…",
            }.get(self._wireguard.state, "WireGuard: no tunnel up")
        )

        lines.append("Click to pick a connection")
        return "\n".join(lines)


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
