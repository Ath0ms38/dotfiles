"""
Connectivity Widget - WiFi and Bluetooth status and controls
"""

import subprocess
import json
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scrolledwindow import ScrolledWindow
from gi.repository import Gtk, GLib

from . import icons


class NetworkManager:
    """Interface to NetworkManager via nmcli"""

    @staticmethod
    def get_wifi_status():
        """Get WiFi connection status"""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "WIFI", "radio"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() == "enabled"
        except Exception:
            return False

    @staticmethod
    def get_wifi_connection():
        """Get current WiFi connection info"""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(":")
                    if len(parts) >= 2 and "wireless" in parts[1].lower():
                        return parts[0]
            return None
        except Exception:
            return None

    @staticmethod
    def get_wifi_signal():
        """Get WiFi signal strength (0-100)"""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "IN-USE,SIGNAL", "device", "wifi", "list"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.strip().split("\n"):
                if line.startswith("*"):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        return int(parts[1])
            return 0
        except Exception:
            return 0

    @staticmethod
    def get_available_networks():
        """Get list of available WiFi networks"""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            networks = []
            seen = set()
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(":")
                    if len(parts) >= 3 and parts[0] and parts[0] not in seen:
                        seen.add(parts[0])
                        networks.append({
                            "ssid": parts[0],
                            "signal": int(parts[1]) if parts[1] else 0,
                            "security": parts[2] if parts[2] else "Open",
                        })
            # Sort by signal strength
            networks.sort(key=lambda x: x["signal"], reverse=True)
            return networks[:10]  # Limit to 10
        except Exception:
            return []

    @staticmethod
    def toggle_wifi():
        """Toggle WiFi on/off"""
        try:
            is_enabled = NetworkManager.get_wifi_status()
            cmd = "off" if is_enabled else "on"
            subprocess.run(["nmcli", "radio", "wifi", cmd], timeout=5)
        except Exception:
            pass

    @staticmethod
    def connect_to_network(ssid: str):
        """Connect to a WiFi network"""
        try:
            subprocess.Popen(
                ["nmcli", "device", "wifi", "connect", ssid],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    @staticmethod
    def rescan_wifi():
        """Trigger WiFi rescan"""
        try:
            subprocess.run(
                ["nmcli", "device", "wifi", "rescan"],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass


class BluetoothManager:
    """Interface to Bluetooth via bluetoothctl"""

    @staticmethod
    def get_bluetooth_status():
        """Check if Bluetooth is powered on"""
        try:
            result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return "Powered: yes" in result.stdout
        except Exception:
            return False

    @staticmethod
    def get_connected_devices():
        """Get list of connected Bluetooth devices"""
        try:
            result = subprocess.run(
                ["bluetoothctl", "devices", "Connected"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            devices = []
            for line in result.stdout.strip().split("\n"):
                if line.startswith("Device"):
                    parts = line.split(" ", 2)
                    if len(parts) >= 3:
                        devices.append({
                            "mac": parts[1],
                            "name": parts[2],
                        })
            return devices
        except Exception:
            return []

    @staticmethod
    def toggle_bluetooth():
        """Toggle Bluetooth on/off"""
        try:
            is_powered = BluetoothManager.get_bluetooth_status()
            cmd = "off" if is_powered else "on"
            subprocess.run(
                ["bluetoothctl", "power", cmd],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass

    @staticmethod
    def open_bluetooth_settings():
        """Open Bluetooth settings"""
        try:
            subprocess.Popen(
                ["blueman-manager"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            try:
                subprocess.Popen(
                    ["gnome-control-center", "bluetooth"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass


class NetworkItem(Button):
    """WiFi network item button"""

    def __init__(self, ssid: str, signal: int, security: str, **kwargs):
        super().__init__(
            name="ax-network-item",
            **kwargs,
        )

        self.ssid = ssid

        # Get signal icon
        if signal >= 75:
            signal_icon = icons.wifi_3
        elif signal >= 50:
            signal_icon = icons.wifi_2
        elif signal >= 25:
            signal_icon = icons.wifi_1
        else:
            signal_icon = icons.wifi_0

        # Security icon
        security_icon = "󰌾" if security and security != "Open" else ""

        content = Box(
            orientation="h",
            spacing=8,
            h_expand=True,
        )

        # Signal strength icon
        content.add(Label(name="ax-network-signal", label=signal_icon))

        # Network name
        name_label = Label(
            name="ax-network-name",
            label=ssid[:20] + "..." if len(ssid) > 20 else ssid,
            h_expand=True,
            h_align="start",
        )
        content.add(name_label)

        # Security indicator
        if security_icon:
            content.add(Label(name="ax-network-security", label=security_icon))

        # Signal percentage
        content.add(Label(name="ax-network-percent", label=f"{signal}%"))

        self.add(content)
        self.connect("clicked", self._on_clicked)

    def _on_clicked(self, btn):
        """Connect to this network"""
        NetworkManager.connect_to_network(self.ssid)


class BluetoothItem(Box):
    """Connected Bluetooth device item"""

    def __init__(self, name: str, mac: str, **kwargs):
        super().__init__(
            name="ax-bluetooth-item",
            orientation="h",
            spacing=8,
            h_expand=True,
            **kwargs,
        )

        self.mac = mac

        # Device icon
        self.add(Label(name="ax-bluetooth-icon", label="󰂯"))

        # Device name
        name_label = Label(
            name="ax-bluetooth-name",
            label=name[:20] + "..." if len(name) > 20 else name,
            h_expand=True,
            h_align="start",
        )
        self.add(name_label)


class Connectivity(Box):
    """Compact WiFi and Bluetooth connectivity bar"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-connectivity",
            orientation="h",
            spacing=16,
            h_expand=True,
            **kwargs,
        )

        # WiFi Section (compact)
        self._build_wifi_section()

        # Vertical Separator
        separator = Box(name="ax-connectivity-separator")
        separator.set_size_request(1, -1)
        self.add(separator)

        # Bluetooth Section (compact)
        self._build_bluetooth_section()

        # Start periodic updates
        GLib.timeout_add_seconds(5, self._update_all)
        GLib.idle_add(self._update_all)

    def _build_wifi_section(self):
        """Build compact WiFi section"""
        wifi_box = Box(
            name="ax-wifi-box",
            orientation="h",
            spacing=8,
            h_expand=True,
        )

        self.wifi_icon = Label(
            name="ax-wifi-icon",
            label=icons.wifi_3,
        )

        self.wifi_status = Label(
            name="ax-wifi-status",
            label="WiFi",
            h_expand=True,
            h_align="start",
        )

        # Toggle button
        self.wifi_toggle = Button(name="ax-wifi-toggle")
        self.wifi_toggle_label = Label(label="󰔡")
        self.wifi_toggle.add(self.wifi_toggle_label)
        self.wifi_toggle.connect("clicked", self._toggle_wifi)

        # Settings button
        wifi_settings = Button(name="ax-wifi-settings")
        wifi_settings.add(Label(label=icons.settings))
        wifi_settings.connect("clicked", self._open_network_settings)

        wifi_box.add(self.wifi_icon)
        wifi_box.add(self.wifi_status)
        wifi_box.add(self.wifi_toggle)
        wifi_box.add(wifi_settings)

        self.add(wifi_box)

    def _build_bluetooth_section(self):
        """Build compact Bluetooth section"""
        bt_box = Box(
            name="ax-bluetooth-box",
            orientation="h",
            spacing=8,
            h_expand=True,
        )

        self.bt_icon = Label(
            name="ax-bluetooth-icon",
            label="󰂯",
        )

        self.bt_status = Label(
            name="ax-bluetooth-status",
            label="Bluetooth",
            h_expand=True,
            h_align="start",
        )

        # Toggle button
        self.bt_toggle = Button(name="ax-bluetooth-toggle")
        self.bt_toggle_label = Label(label="󰔡")
        self.bt_toggle.add(self.bt_toggle_label)
        self.bt_toggle.connect("clicked", self._toggle_bluetooth)

        # Settings button
        bt_settings = Button(name="ax-bluetooth-settings")
        bt_settings.add(Label(label=icons.settings))
        bt_settings.connect("clicked", lambda *_: BluetoothManager.open_bluetooth_settings())

        bt_box.add(self.bt_icon)
        bt_box.add(self.bt_status)
        bt_box.add(self.bt_toggle)
        bt_box.add(bt_settings)

        self.add(bt_box)

    def _update_all(self):
        """Update all connectivity info"""
        self._update_wifi()
        self._update_bluetooth()
        return True

    def _update_wifi(self):
        """Update WiFi status"""
        is_enabled = NetworkManager.get_wifi_status()
        connection = NetworkManager.get_wifi_connection()
        signal = NetworkManager.get_wifi_signal()

        # Update icon
        if not is_enabled:
            self.wifi_icon.set_label(icons.wifi_off)
            self.wifi_status.set_label("WiFi Off")
            self.wifi_toggle_label.set_label("󰔢")
            self.wifi_toggle.remove_style_class("active")
        else:
            if signal >= 75:
                self.wifi_icon.set_label(icons.wifi_3)
            elif signal >= 50:
                self.wifi_icon.set_label(icons.wifi_2)
            elif signal >= 25:
                self.wifi_icon.set_label(icons.wifi_1)
            else:
                self.wifi_icon.set_label(icons.wifi_0)

            if connection:
                # Truncate long names
                name = connection[:15] + "..." if len(connection) > 15 else connection
                self.wifi_status.set_label(name)
            else:
                self.wifi_status.set_label("Not Connected")

            self.wifi_toggle_label.set_label("󰔡")
            self.wifi_toggle.add_style_class("active")

    def _update_bluetooth(self):
        """Update Bluetooth status"""
        is_powered = BluetoothManager.get_bluetooth_status()
        devices = BluetoothManager.get_connected_devices()

        if is_powered:
            self.bt_icon.set_label("󰂯")
            if devices:
                # Show first device name
                name = devices[0]["name"]
                name = name[:12] + "..." if len(name) > 12 else name
                self.bt_status.set_label(name)
            else:
                self.bt_status.set_label("No Device")
            self.bt_toggle_label.set_label("󰔡")
            self.bt_toggle.add_style_class("active")
        else:
            self.bt_icon.set_label("󰂲")
            self.bt_status.set_label("BT Off")
            self.bt_toggle_label.set_label("󰔢")
            self.bt_toggle.remove_style_class("active")

    def _toggle_wifi(self, btn):
        """Toggle WiFi"""
        NetworkManager.toggle_wifi()
        GLib.timeout_add(500, self._update_wifi)

    def _toggle_bluetooth(self, btn):
        """Toggle Bluetooth"""
        BluetoothManager.toggle_bluetooth()
        GLib.timeout_add(500, self._update_bluetooth)

    def _open_network_settings(self, btn):
        """Open network settings"""
        try:
            subprocess.Popen(
                ["nm-connection-editor"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            try:
                subprocess.Popen(
                    ["gnome-control-center", "network"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass
