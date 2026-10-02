"""
WireGuard service.

Tunnels are driven through NetworkManager, not wg-quick: an NM profile can be
activated by the session user, while `wg-quick up` needs root and would put a
password prompt behind a bar button. Import an existing config once with

    nmcli connection import type wireguard file /etc/wireguard/<name>.conf

and it shows up here as a togglable tunnel.

A tunnel started outside NM (`sudo wg-quick up`) is still visible while it
runs, because NM assumes the external device — but it has no saved profile, so
it disappears when it goes down and cannot be brought back from here. Those are
flagged external so the widget can say so rather than offer a dead switch.
"""

import time
from dataclasses import dataclass

import gi

gi.require_version("NM", "1.0")
from gi.repository import NM, GLib

from fabric.core.service import Service, Property, Signal

from services.network import get_interface_stats, format_bandwidth


WG_TYPE = "wireguard"  # NM.SETTING_WIREGUARD_SETTING_NAME


@dataclass(frozen=True)
class Tunnel:
    """A WireGuard profile and its live state.

    Frozen so a rebuilt list compares equal to the previous one and the service
    only emits on a real change.
    """

    uuid: str
    name: str
    interface: str
    address: str
    state: str  # connected | connecting | disconnecting | disconnected
    external: bool

    @property
    def is_up(self) -> bool:
        return self.state in ("connected", "connecting")


class WireGuard(Service):
    """Lists and toggles the WireGuard connections NetworkManager knows about."""

    @Signal
    def changed(self) -> None: ...

    @Signal
    def bandwidth_changed(self) -> None: ...

    _NM_STATES = {
        NM.ActiveConnectionState.ACTIVATED: "connected",
        NM.ActiveConnectionState.ACTIVATING: "connecting",
        NM.ActiveConnectionState.DEACTIVATING: "disconnecting",
    }

    def __init__(self, **kwargs):
        self._client: NM.Client | None = None
        self._tunnels: list[Tunnel] = []
        self._message = ""
        self._rx_speed = 0.0
        self._tx_speed = 0.0
        self._last_stats = (0, 0)
        self._last_stats_at = 0.0
        self._last_interface = ""
        super().__init__(**kwargs)

        NM.Client.new_async(cancellable=None, callback=self._on_client_ready)
        GLib.timeout_add_seconds(1, self._poll_bandwidth)

    # -- NetworkManager side (state) --------------------------------------

    def _on_client_ready(self, source, task):
        try:
            self._client = NM.Client.new_finish(task)
        except Exception as e:
            self._set_message(f"NetworkManager unavailable: {e}")
            return

        for signal in (
            "notify::active-connections",
            "connection-added",
            "connection-removed",
        ):
            self._client.connect(signal, lambda *_: self._sync())
        self._sync()

    def _sync(self):
        """Rebuild the tunnel list from NM's profiles and active connections."""
        if not self._client:
            return

        active = {
            conn.get_uuid(): conn
            for conn in self._client.get_active_connections()
            if conn.get_connection_type() == WG_TYPE
        }

        tunnels = []
        for conn in self._client.get_connections():
            if conn.get_connection_type() != WG_TYPE:
                continue
            uuid = conn.get_uuid()
            tunnels.append(
                Tunnel(
                    uuid=uuid,
                    name=conn.get_id() or uuid,
                    interface=self._interface_of(conn, active.get(uuid)),
                    address=self._address_of(conn),
                    state=self._state_of(active.get(uuid)),
                    external=False,
                )
            )

        saved = {tunnel.uuid for tunnel in tunnels}
        for uuid, conn in active.items():
            if uuid in saved:
                continue
            name = conn.get_id() or uuid
            devices = conn.get_devices()
            tunnels.append(
                Tunnel(
                    uuid=uuid,
                    name=name,
                    interface=devices[0].get_iface() if devices else name,
                    address="",
                    state=self._state_of(conn),
                    external=True,
                )
            )

        tunnels.sort(key=lambda tunnel: tunnel.name.lower())

        if tunnels != self._tunnels:
            self._tunnels = tunnels
            self.emit("changed")

    def _state_of(self, active) -> str:
        if active is None:
            return "disconnected"
        return self._NM_STATES.get(active.get_state(), "disconnected")

    @staticmethod
    def _interface_of(conn, active) -> str:
        devices = active.get_devices() if active else []
        if devices:
            return devices[0].get_iface()
        setting = conn.get_setting_connection()
        return (setting.get_interface_name() if setting else "") or conn.get_id() or ""

    @staticmethod
    def _address_of(conn) -> str:
        """The tunnel's own IP, shown as the row subtitle."""
        ip4 = conn.get_setting_ip4_config()
        if not ip4 or not ip4.get_num_addresses():
            return ""
        address = ip4.get_address(0)
        return f"{address.get_address()}/{address.get_prefix()}"

    def _set_message(self, message: str):
        if self._message != message:
            self._message = message
            self.emit("changed")

    # -- Actions -----------------------------------------------------------

    def toggle(self, tunnel: Tunnel):
        self.set_active(tunnel, not tunnel.is_up)

    def set_active(self, tunnel: Tunnel, active: bool):
        """Bring a tunnel up or down. External tunnels are read-only."""
        if not self._client or tunnel.external:
            return

        self._set_message("")

        if active:
            conn = self._client.get_connection_by_uuid(tunnel.uuid)
            if conn is None:
                self._set_message(f"{tunnel.name}: profile is gone")
                return
            self._client.activate_connection_async(
                conn, None, None, None, self._on_activated
            )
            return

        for conn in self._client.get_active_connections():
            if conn.get_uuid() == tunnel.uuid:
                self._client.deactivate_connection_async(
                    conn, None, self._on_deactivated
                )
                return

    def _on_activated(self, client, task):
        try:
            client.activate_connection_finish(task)
        except GLib.Error as e:
            self._set_message(e.message)
        self._sync()

    def _on_deactivated(self, client, task):
        try:
            client.deactivate_connection_finish(task)
        except GLib.Error as e:
            self._set_message(e.message)
        self._sync()

    # -- Throughput --------------------------------------------------------

    def _poll_bandwidth(self):
        """Sample the active tunnel's counters once a second.

        Also re-syncs: activating -> activated happens on the connection object,
        which does not re-emit notify::active-connections on the client.
        """
        self._sync()

        interface = self.active_interface
        if not interface:
            if self._rx_speed or self._tx_speed:
                self._rx_speed = self._tx_speed = 0.0
                self._last_stats_at = 0.0
                self.emit("bandwidth-changed")
            self._last_interface = ""
            return True

        # Switching tunnels means switching counters; without the reset the
        # first delta would be the other interface's whole session.
        if interface != self._last_interface:
            self._last_interface = interface
            self._last_stats_at = 0.0

        rx, tx = get_interface_stats(interface)
        now = time.time()

        if self._last_stats_at:
            elapsed = now - self._last_stats_at
            if elapsed > 0:
                self._rx_speed = max(0.0, (rx - self._last_stats[0]) / elapsed)
                self._tx_speed = max(0.0, (tx - self._last_stats[1]) / elapsed)
                self.emit("bandwidth-changed")

        self._last_stats = (rx, tx)
        self._last_stats_at = now
        return True

    @Property(str, "readable")
    def bandwidth(self) -> str:
        """Human-readable "↓ x ↑ y", zeroed when no tunnel is up."""
        return f"↓ {format_bandwidth(self._rx_speed)}  ↑ {format_bandwidth(self._tx_speed)}"

    # -- Properties --------------------------------------------------------

    @Property(object, "readable")
    def tunnels(self) -> list:
        """Every WireGuard tunnel NM knows about, saved profiles first."""
        return self._tunnels

    @Property(str, "readable")
    def state(self) -> str:
        """Aggregate state: connected as soon as any tunnel is up."""
        states = {tunnel.state for tunnel in self._tunnels}
        for state in ("connected", "connecting", "disconnecting"):
            if state in states:
                return state
        return "disconnected"

    @Property(str, "readable")
    def active_name(self) -> str:
        """Name of the tunnel that is up, empty when none is."""
        for tunnel in self._tunnels:
            if tunnel.state == "connected":
                return tunnel.name
        return ""

    @Property(str, "readable")
    def active_interface(self) -> str:
        for tunnel in self._tunnels:
            if tunnel.state == "connected":
                return tunnel.interface
        return ""

    @Property(str, "readable")
    def message(self) -> str:
        """Error text from the last failed action, empty otherwise."""
        return self._message
