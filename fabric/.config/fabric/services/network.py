"""
Network service for managing WiFi and Ethernet connections
Based on NetworkManager (NM) via GObject introspection
"""

from typing import Any, List, Literal
import gi
import time

gi.require_version('NM', '1.0')
from gi.repository import NM, GLib, Gio
from fabric.core.service import Service, Property, Signal
from fabric.utils import bulk_connect, exec_shell_command_async


def get_interface_stats(interface_name: str) -> tuple[int, int]:
    """Get current RX/TX bytes for an interface from /sys/class/net"""
    try:
        with open(f"/sys/class/net/{interface_name}/statistics/rx_bytes") as f:
            rx_bytes = int(f.read().strip())
        with open(f"/sys/class/net/{interface_name}/statistics/tx_bytes") as f:
            tx_bytes = int(f.read().strip())
        return rx_bytes, tx_bytes
    except (FileNotFoundError, ValueError):
        return 0, 0


def format_bandwidth(bytes_per_sec: float) -> str:
    """Format bandwidth in human-readable format"""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.0f} B/s"
    elif bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    elif bytes_per_sec < 1024 * 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"
    else:
        return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"


class Wifi(Service):
    """Service to manage WiFi connection"""

    @Signal
    def changed(self) -> None: ...

    @Signal
    def enabled(self) -> bool: ...

    def __init__(self, client: NM.Client, device: NM.DeviceWifi, **kwargs):
        self._client: NM.Client = client
        self._device: NM.DeviceWifi = device
        self._ap: NM.AccessPoint | None = None
        self._ap_signal: int | None = None

        # Bandwidth monitoring
        self._interface_name = device.get_iface()
        self._last_rx_bytes = 0
        self._last_tx_bytes = 0
        self._last_time = time.time()
        self._rx_speed = 0.0
        self._tx_speed = 0.0

        super().__init__(**kwargs)

        self._client.connect(
            "notify::wireless-enabled",
            lambda *args: self.notifier("enabled", args),
        )

        if self._device:
            bulk_connect(
                self._device,
                {
                    "notify::active-access-point": lambda *args: self._activate_ap(),
                    "access-point-added": lambda *args: self.emit("changed"),
                    "access-point-removed": lambda *args: self.emit("changed"),
                    "state-changed": lambda *args: self.ap_update(),
                },
            )
            self._activate_ap()

            # Start bandwidth monitoring
            self._update_bandwidth_stats()
            GLib.timeout_add(1000, self._update_bandwidth_stats)

    def ap_update(self):
        self.emit("changed")
        for sn in [
            "enabled",
            "internet",
            "strength",
            "frequency",
            "access-points",
            "ssid",
            "state",
            "icon-name",
        ]:
            self.notify(sn)

    def _activate_ap(self):
        if self._ap:
            self._ap.disconnect(self._ap_signal)
        self._ap = self._device.get_active_access_point()
        if not self._ap:
            return

        self._ap_signal = self._ap.connect(
            "notify::strength", lambda *args: self.ap_update()
        )

    def toggle_wifi(self):
        self._client.wireless_set_enabled(not self._client.wireless_get_enabled())

    def scan(self):
        self._device.request_scan_async(
            None,
            lambda device, result: [
                device.request_scan_finish(result),
                self.emit("changed"),
            ],
        )

    def notifier(self, name: str, *args):
        self.notify(name)
        self.emit("changed")
        return

    def _update_bandwidth_stats(self):
        """Update bandwidth statistics"""
        try:
            current_time = time.time()
            rx_bytes, tx_bytes = get_interface_stats(self._interface_name)

            if self._last_rx_bytes > 0:
                time_delta = current_time - self._last_time
                if time_delta > 0:
                    self._rx_speed = (rx_bytes - self._last_rx_bytes) / time_delta
                    self._tx_speed = (tx_bytes - self._last_tx_bytes) / time_delta
                    self.notify("download-speed")
                    self.notify("upload-speed")
                    self.notify("bandwidth")

            self._last_rx_bytes = rx_bytes
            self._last_tx_bytes = tx_bytes
            self._last_time = current_time
        except Exception as e:
            print(f"Error updating bandwidth stats: {e}")

        return True  # Continue timeout

    @Property(bool, "read-write", default_value=False)
    def enabled(self) -> bool:
        return bool(self._client.wireless_get_enabled())

    @enabled.setter
    def enabled(self, value: bool):
        self._client.wireless_set_enabled(value)

    @Property(int, "readable")
    def strength(self):
        return self._ap.get_strength() if self._ap else -1

    @Property(str, "readable")
    def icon_name(self):
        if not self._ap:
            return "network-wireless-disabled-symbolic"

        if self.internet == "activated":
            return {
                80: "network-wireless-signal-excellent-symbolic",
                60: "network-wireless-signal-good-symbolic",
                40: "network-wireless-signal-ok-symbolic",
                20: "network-wireless-signal-weak-symbolic",
                0: "network-wireless-signal-none-symbolic",
            }.get(
                min(80, 20 * round(self._ap.get_strength() / 20)),
                "network-wireless-no-route-symbolic",
            )
        if self.internet == "activating":
            return "network-wireless-acquiring-symbolic"

        return "network-wireless-offline-symbolic"

    @Property(int, "readable")
    def frequency(self):
        return self._ap.get_frequency() if self._ap else -1

    @Property(str, "readable")
    def internet(self):
        active_conn = self._device.get_active_connection()
        if not active_conn:
            return "disconnected"

        return {
            NM.ActiveConnectionState.ACTIVATED: "activated",
            NM.ActiveConnectionState.ACTIVATING: "activating",
            NM.ActiveConnectionState.DEACTIVATING: "deactivating",
            NM.ActiveConnectionState.DEACTIVATED: "deactivated",
        }.get(active_conn.get_state(), "unknown")

    @Property(object, "readable")
    def access_points(self) -> List[dict]:
        points: list[NM.AccessPoint] = self._device.get_access_points()

        def make_ap_dict(ap: NM.AccessPoint):
            # Determine security type
            flags = ap.get_flags()
            wpa_flags = ap.get_wpa_flags()
            rsn_flags = ap.get_rsn_flags()

            # Check security flags (0 means NONE)
            if rsn_flags != 0:
                security = "WPA2"
            elif wpa_flags != 0:
                security = "WPA"
            elif flags & NM.AccessPointFlags.PRIVACY:
                security = "WEP"
            else:
                security = "Open"

            return {
                "bssid": ap.get_bssid(),
                "last_seen": ap.get_last_seen(),
                "ssid": NM.utils_ssid_to_utf8(ap.get_ssid().get_data())
                if ap.get_ssid()
                else "Unknown",
                "active-ap": self._ap,
                "strength": ap.get_strength(),
                "frequency": ap.get_frequency(),
                "security": security,
                "requires_password": security != "Open",
                "icon-name": {
                    80: "network-wireless-signal-excellent-symbolic",
                    60: "network-wireless-signal-good-symbolic",
                    40: "network-wireless-signal-ok-symbolic",
                    20: "network-wireless-signal-weak-symbolic",
                    0: "network-wireless-signal-none-symbolic",
                }.get(
                    min(80, 20 * round(ap.get_strength() / 20)),
                    "network-wireless-no-route-symbolic",
                ),
            }

        return list(map(make_ap_dict, points))

    @Property(str, "readable")
    def ssid(self):
        if not self._ap:
            return "Disconnected"
        ssid = self._ap.get_ssid()
        if not ssid:
            return "Unknown"
        ssid_data = ssid.get_data()
        return NM.utils_ssid_to_utf8(ssid_data) if ssid_data else "Unknown"

    @Property(str, "readable")
    def state(self):
        return {
            NM.DeviceState.UNMANAGED: "unmanaged",
            NM.DeviceState.UNAVAILABLE: "unavailable",
            NM.DeviceState.DISCONNECTED: "disconnected",
            NM.DeviceState.PREPARE: "prepare",
            NM.DeviceState.CONFIG: "config",
            NM.DeviceState.NEED_AUTH: "need_auth",
            NM.DeviceState.IP_CONFIG: "ip_config",
            NM.DeviceState.IP_CHECK: "ip_check",
            NM.DeviceState.SECONDARIES: "secondaries",
            NM.DeviceState.ACTIVATED: "activated",
            NM.DeviceState.DEACTIVATING: "deactivating",
            NM.DeviceState.FAILED: "failed",
        }.get(self._device.get_state(), "unknown")

    @Property(str, "readable")
    def download_speed(self) -> str:
        """Current download speed formatted"""
        return format_bandwidth(self._rx_speed)

    @Property(str, "readable")
    def upload_speed(self) -> str:
        """Current upload speed formatted"""
        return format_bandwidth(self._tx_speed)

    @Property(str, "readable")
    def bandwidth(self) -> str:
        """Combined bandwidth info"""
        return f"↓ {format_bandwidth(self._rx_speed)} ↑ {format_bandwidth(self._tx_speed)}"


class Ethernet(Service):
    """Service to manage Ethernet connection"""

    @Signal
    def changed(self) -> None: ...

    def __init__(self, client: NM.Client, device: NM.DeviceEthernet, **kwargs):
        super().__init__(**kwargs)
        self._client: NM.Client = client
        self._device: NM.DeviceEthernet = device

        # Bandwidth monitoring
        self._interface_name = device.get_iface()
        self._last_rx_bytes = 0
        self._last_tx_bytes = 0
        self._last_time = time.time()
        self._rx_speed = 0.0
        self._tx_speed = 0.0

        for pn in ("active-connection", "state"):
            self._device.connect(f"notify::{pn}", lambda *_: self.notifier(pn))

        # Start bandwidth monitoring
        self._update_bandwidth_stats()
        GLib.timeout_add(1000, self._update_bandwidth_stats)

    def notifier(self, pn):
        self.notify(pn)
        self.emit("changed")

    def _update_bandwidth_stats(self):
        """Update bandwidth statistics"""
        try:
            current_time = time.time()
            rx_bytes, tx_bytes = get_interface_stats(self._interface_name)

            if self._last_rx_bytes > 0:
                time_delta = current_time - self._last_time
                if time_delta > 0:
                    self._rx_speed = (rx_bytes - self._last_rx_bytes) / time_delta
                    self._tx_speed = (tx_bytes - self._last_tx_bytes) / time_delta
                    self.notify("download-speed")
                    self.notify("upload-speed")
                    self.notify("bandwidth")

            self._last_rx_bytes = rx_bytes
            self._last_tx_bytes = tx_bytes
            self._last_time = current_time
        except Exception as e:
            print(f"Error updating Ethernet bandwidth stats: {e}")

        return True  # Continue timeout

    @Property(int, "readable")
    def speed(self) -> int:
        """Link speed in Mb/s"""
        return self._device.get_speed()

    @Property(str, "readable")
    def state(self) -> str:
        device_state = self._device.get_state()
        return {
            NM.DeviceState.ACTIVATED: "activated",
            NM.DeviceState.PREPARE: "activating",
            NM.DeviceState.CONFIG: "activating",
            NM.DeviceState.IP_CONFIG: "activating",
            NM.DeviceState.IP_CHECK: "activating",
            NM.DeviceState.DEACTIVATING: "deactivating",
            NM.DeviceState.DISCONNECTED: "disconnected",
            NM.DeviceState.UNAVAILABLE: "unavailable",
            NM.DeviceState.UNMANAGED: "unmanaged",
            NM.DeviceState.FAILED: "failed",
        }.get(device_state, "unknown")

    @Property(str, "readable")
    def icon_name(self) -> str:
        state = self.state
        if state == "activated":
            return "network-wired-symbolic"
        elif state == "activating":
            return "network-wired-acquiring-symbolic"
        return "network-wired-disconnected-symbolic"

    @Property(str, "readable")
    def download_speed(self) -> str:
        """Current download speed formatted"""
        return format_bandwidth(self._rx_speed)

    @Property(str, "readable")
    def upload_speed(self) -> str:
        """Current upload speed formatted"""
        return format_bandwidth(self._tx_speed)

    @Property(str, "readable")
    def bandwidth(self) -> str:
        """Combined bandwidth info"""
        return f"↓ {format_bandwidth(self._rx_speed)} ↑ {format_bandwidth(self._tx_speed)}"


class NetworkClient(Service):
    """Service to manage network connections"""

    @Signal
    def device_ready(self) -> None: ...

    def __init__(self, **kwargs):
        self._client: NM.Client | None = None
        self.wifi_device: Wifi | None = None
        self.ethernet_device: Ethernet | None = None
        super().__init__(**kwargs)
        NM.Client.new_async(
            cancellable=None,
            callback=self._init_network_client,
        )

    def _init_network_client(self, source, task, **kwargs):
        try:
            self._client = NM.Client.new_finish(task)
            wifi_device: NM.DeviceWifi | None = self._get_device(NM.DeviceType.WIFI)
            ethernet_device: NM.DeviceEthernet | None = self._get_device(NM.DeviceType.ETHERNET)

            if wifi_device:
                self.wifi_device = Wifi(self._client, wifi_device)
                self.emit("device-ready")

            if ethernet_device:
                self.ethernet_device = Ethernet(self._client, ethernet_device)
                self.emit("device-ready")

            self.notify("primary-device")
        except Exception as e:
            print(f"Error initializing NetworkClient: {e}")

    def _get_device(self, device_type) -> Any:
        if not self._client:
            return None
        devices: List[NM.Device] = self._client.get_devices()

        # First try to find device with active connection
        device_with_conn = next(
            (
                x
                for x in devices
                if x.get_device_type() == device_type
                and x.get_active_connection() is not None
            ),
            None,
        )

        if device_with_conn:
            return device_with_conn

        # Otherwise return first device of this type
        return next(
            (x for x in devices if x.get_device_type() == device_type),
            None,
        )

    def _get_primary_device(self) -> Literal["wifi", "wired"] | None:
        if not self._client:
            return None
        primary_conn = self._client.get_primary_connection()
        if not primary_conn:
            return None
        conn_type = str(primary_conn.get_connection_type())
        if "wireless" in conn_type:
            return "wifi"
        elif "ethernet" in conn_type:
            return "wired"
        return None

    def connect_wifi_bssid(self, bssid, password=None):
        """Connect to WiFi network by BSSID with optional password"""
        if password:
            exec_shell_command_async(
                f"nmcli device wifi connect {bssid} password '{password}'",
                lambda *args: print(f"WiFi connection result: {args}")
            )
        else:
            exec_shell_command_async(
                f"nmcli device wifi connect {bssid}",
                lambda *args: print(f"WiFi connection result: {args}")
            )

    @Property(str, "readable")
    def primary_device(self) -> Literal["wifi", "wired"] | None:
        return self._get_primary_device()
