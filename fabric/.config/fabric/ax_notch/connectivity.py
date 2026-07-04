"""
Connectivity Widget - WiFi and Bluetooth status and controls

Event-driven: WiFi state comes from services.network.NetworkClient
(NetworkManager GObject bindings) and Bluetooth from fabric's
BluetoothClient — no nmcli/bluetoothctl subprocess polling.
"""

import subprocess
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.bluetooth import BluetoothClient
from gi.repository import GLib

from services.network import NetworkClient
from . import icons


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

        # WiFi service (async init — device becomes available on device-ready)
        self._network = NetworkClient()
        self._network.connect("device-ready", self._on_wifi_ready)

        # Bluetooth service
        self._bluetooth = BluetoothClient()
        self._bluetooth.connect("changed", lambda *_: self._update_bluetooth())
        self._bluetooth.connect("device-added", lambda *_: self._update_bluetooth())
        self._bluetooth.connect("device-removed", lambda *_: self._update_bluetooth())
        GLib.idle_add(self._update_bluetooth)

    def _on_wifi_ready(self, *_):
        wifi = self._network.wifi_device
        if not wifi:
            return
        wifi.connect("changed", lambda *_: self._update_wifi())
        self._update_wifi()

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
        bt_settings.connect("clicked", self._open_bluetooth_settings)

        bt_box.add(self.bt_icon)
        bt_box.add(self.bt_status)
        bt_box.add(self.bt_toggle)
        bt_box.add(bt_settings)

        self.add(bt_box)

    def _update_wifi(self):
        """Update WiFi status from the network service"""
        wifi = self._network.wifi_device
        if not wifi:
            return

        if not wifi.enabled:
            self.wifi_icon.set_label(icons.wifi_off)
            self.wifi_status.set_label("WiFi Off")
            self.wifi_toggle_label.set_label("󰔢")
            self.wifi_toggle.remove_style_class("active")
            return

        signal = wifi.strength
        if signal >= 75:
            self.wifi_icon.set_label(icons.wifi_3)
        elif signal >= 50:
            self.wifi_icon.set_label(icons.wifi_2)
        elif signal >= 25:
            self.wifi_icon.set_label(icons.wifi_1)
        else:
            self.wifi_icon.set_label(icons.wifi_0)

        ssid = wifi.ssid
        if signal >= 0 and ssid not in ("Disconnected", "Unknown"):
            # Truncate long names
            name = ssid[:15] + "..." if len(ssid) > 15 else ssid
            self.wifi_status.set_label(name)
        else:
            self.wifi_status.set_label("Not Connected")

        self.wifi_toggle_label.set_label("󰔡")
        self.wifi_toggle.add_style_class("active")

    def _update_bluetooth(self):
        """Update Bluetooth status from the bluetooth service"""
        if self._bluetooth.enabled:
            self.bt_icon.set_label("󰂯")
            devices = self._bluetooth.connected_devices
            if devices:
                # Show first device name
                name = devices[0].name or "Device"
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
        """Toggle WiFi (UI refreshes via the service's changed signal)"""
        wifi = self._network.wifi_device
        if wifi:
            wifi.toggle_wifi()

    def _toggle_bluetooth(self, btn):
        """Toggle Bluetooth (UI refreshes via the client's changed signal)"""
        self._bluetooth.powered = not self._bluetooth.powered

    def _open_network_settings(self, btn):
        """Open network settings"""
        for cmd in (["nm-connection-editor"], ["gnome-control-center", "network"]):
            try:
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                continue

    def _open_bluetooth_settings(self, btn):
        """Open Bluetooth settings"""
        for cmd in (["blueman-manager"], ["gnome-control-center", "bluetooth"]):
            try:
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                continue
