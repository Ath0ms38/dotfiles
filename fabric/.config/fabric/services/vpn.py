"""
ProtonVPN service.

State is read from NetworkManager, never from the CLI: a single
`protonvpn status` call takes ~8s, far too slow to poll. The official client
drives NM under the hood and names its connection "ProtonVPN <server>", so the
active-connection list gives both the up/down state and the server name
instantly, event-driven. The CLI is used only for connect/disconnect, where
the latency is acceptable because it is a user-initiated action.

The kill-switch connections the client also creates are named with a "pvpn"
prefix, so matching on "ProtonVPN " does not pick them up.
"""

import json
import os
import re
import time

import gi

gi.require_version("NM", "1.0")
from gi.repository import NM, Gio, GLib

from fabric.core.service import Service, Property, Signal

from services.network import get_interface_stats, format_bandwidth


CONNECTION_PREFIX = "ProtonVPN "

# The client always names its tunnel device this, for both WireGuard and
# OpenVPN (VIRTUAL_DEVICE_NAME in the proton backends).
INTERFACE = "proton0"

# Connect can take a while (server pick + handshake); give up well after the
# point where the CLI itself would have errored out.
ACTION_TIMEOUT_S = 90

CACHE_PATH = os.path.expanduser("~/.cache/fabric/protonvpn-countries.json")
CACHE_TTL_S = 7 * 24 * 3600

# `protonvpn countries list` prints a tabulate "simple" table: a header, a row
# of dashes, then "<Country name>  <CODE>". Anything before the dashes is
# progress chatter ("Server list is outdated, updating...").
_COUNTRY_ROW = re.compile(r"^(.+?)\s{2,}([A-Za-z]{2})\s*$")


def parse_countries(output: str) -> list[tuple[str, str]]:
    """Parse the country table into [(name, CODE), ...]."""
    lines = output.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and set(stripped) <= {"-", " "}:
            rows = lines[i + 1:]
            break
    else:
        return []

    countries = []
    for line in rows:
        match = _COUNTRY_ROW.match(line.rstrip())
        if match:
            name, code = match.groups()
            countries.append((name.strip(), code.upper()))
    return countries


class ProtonVpn(Service):
    """Tracks and controls the ProtonVPN connection."""

    @Signal
    def changed(self) -> None: ...

    @Signal
    def countries_changed(self) -> None: ...

    @Signal
    def bandwidth_changed(self) -> None: ...

    def __init__(self, **kwargs):
        self._client: NM.Client | None = None
        self._state = "disconnected"
        self._server = ""
        self._message = ""
        self._busy = False
        self._timeout_id = 0
        self._countries: list[tuple[str, str]] = []
        self._countries_error = ""
        self._fetching_countries = False
        self._cached_at = 0
        self._rx_speed = 0.0
        self._tx_speed = 0.0
        self._last_stats = (0, 0)
        self._last_stats_at = 0.0
        super().__init__(**kwargs)

        NM.Client.new_async(cancellable=None, callback=self._on_client_ready)
        self._load_cached_countries()
        GLib.timeout_add_seconds(1, self._poll_bandwidth)

    # -- NetworkManager side (state) --------------------------------------

    def _on_client_ready(self, source, task):
        try:
            self._client = NM.Client.new_finish(task)
        except Exception as e:
            self._set(state="error", message=f"NetworkManager unavailable: {e}")
            return

        self._client.connect("notify::active-connections", lambda *_: self._sync())
        self._sync()

    def _active_connection(self) -> "NM.ActiveConnection | None":
        if not self._client:
            return None
        for conn in self._client.get_active_connections():
            if (conn.get_id() or "").startswith(CONNECTION_PREFIX):
                return conn
        return None

    def _sync(self):
        """Recompute state from NM, unless an action is still in flight."""
        conn = self._active_connection()

        if conn is None:
            # Keep showing "connecting" until the CLI call actually returns:
            # NM has no proton connection yet while the client picks a server.
            if not self._busy:
                self._set(state="disconnected", server="")
            return

        server = (conn.get_id() or "")[len(CONNECTION_PREFIX):]
        nm_state = conn.get_state()

        if nm_state == NM.ActiveConnectionState.ACTIVATED:
            self._end_action()
            self._set(state="connected", server=server, message="")
        elif nm_state == NM.ActiveConnectionState.ACTIVATING:
            self._set(state="connecting", server=server)
        elif nm_state == NM.ActiveConnectionState.DEACTIVATING:
            self._set(state="disconnecting", server=server)
        elif not self._busy:
            self._set(state="disconnected", server="")

    def _set(self, **fields):
        changed = False
        for name, value in fields.items():
            attr = f"_{name}"
            if getattr(self, attr) != value:
                setattr(self, attr, value)
                changed = True
        if changed:
            self.emit("changed")

    # -- CLI side (actions) ------------------------------------------------

    def toggle(self):
        if self._busy:
            return
        if self._state in ("connected", "connecting"):
            self.disconnect_vpn()
        else:
            self.connect_vpn()

    def connect_vpn(self, country: str = ""):
        self._set(state="connecting", server=country, message="")
        argv = ["protonvpn", "connect"]
        if country:
            argv += ["--country", country]
        self._run(argv)

    def connect_with_args(self, args):
        """Connect using the CLI's own selectors (--p2p, --securecore, …)."""
        self._set(state="connecting", server="", message="")
        self._run(["protonvpn", "connect"] + list(args))

    def disconnect_vpn(self):
        self._set(state="disconnecting", message="")
        self._run(["protonvpn", "disconnect"])

    def open_signin(self):
        """Open the interactive sign-in flow in a terminal.

        Signing in needs a password and possibly 2FA, so it cannot be driven
        from the popup; the country list stays empty until it succeeds.
        """
        terminal = os.environ.get("TERMINAL") or "kitty"
        try:
            Gio.Subprocess.new(
                [terminal, "-e", "protonvpn", "signin"], Gio.SubprocessFlags.NONE
            )
        except GLib.Error as e:
            self._set(state="error", message=str(e))

    def _run(self, argv):
        try:
            proc = Gio.Subprocess.new(
                argv,
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE,
            )
        except GLib.Error as e:
            self._set(state="error", message=str(e))
            return

        self._busy = True
        self._timeout_id = GLib.timeout_add_seconds(ACTION_TIMEOUT_S, self._on_timeout)
        proc.communicate_utf8_async(None, None, self._on_action_done)

    def _on_action_done(self, proc, task):
        try:
            _, stdout, _ = proc.communicate_utf8_finish(task)
        except GLib.Error as e:
            stdout = str(e)

        self._end_action()
        output = (stdout or "").strip()

        if not proc.get_successful():
            # The CLI is the only thing that knows about credentials; surface
            # its own wording rather than guessing at the cause.
            self._set(state="error", server="", message=output or "command failed")
            return

        self._sync()

    def _on_timeout(self):
        self._timeout_id = 0
        self._busy = False
        self._set(state="error", server="", message="timed out")
        return False

    def _end_action(self):
        self._busy = False
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = 0

    # -- Throughput --------------------------------------------------------

    def _poll_bandwidth(self):
        """Sample proton0 counters once a second while the tunnel is up.

        Also re-syncs state: activating -> activated happens on the connection
        object, which does not re-emit notify::active-connections on the client.
        """
        self._sync()

        if self._state != "connected":
            if self._rx_speed or self._tx_speed:
                self._rx_speed = self._tx_speed = 0.0
                self._last_stats_at = 0.0
                self.emit("bandwidth-changed")
            return True

        rx, tx = get_interface_stats(INTERFACE)
        now = time.time()

        # Skip the first sample after connecting: with no previous reading the
        # delta would be the whole session's traffic.
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
        """Human-readable "↓ x ↑ y", zeroed when not connected."""
        return f"↓ {format_bandwidth(self._rx_speed)}  ↑ {format_bandwidth(self._tx_speed)}"

    # -- Country list ------------------------------------------------------

    def _load_cached_countries(self):
        """Seed the list from cache so the menu opens instantly."""
        try:
            with open(CACHE_PATH) as f:
                cache = json.load(f)
        except (OSError, ValueError):
            return

        self._countries = [(name, code) for name, code in cache.get("countries", [])]
        self._cached_at = cache.get("fetched_at", 0)

    def _cache_is_stale(self) -> bool:
        return time.time() - self._cached_at > CACHE_TTL_S

    def refresh_countries(self, force: bool = False):
        """Fetch the country list from the CLI unless a fresh cache exists.

        The call needs an authenticated session and takes several seconds, so
        it runs in the background and the menu renders from cache meanwhile.
        """
        if self._fetching_countries:
            return
        if self._countries and not force and not self._cache_is_stale():
            return

        try:
            proc = Gio.Subprocess.new(
                ["protonvpn", "countries", "list"],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE,
            )
        except GLib.Error as e:
            self._countries_error = str(e)
            self.emit("countries-changed")
            return

        self._fetching_countries = True
        proc.communicate_utf8_async(None, None, self._on_countries_fetched)

    def _on_countries_fetched(self, proc, task):
        self._fetching_countries = False
        try:
            _, stdout, _ = proc.communicate_utf8_finish(task)
        except GLib.Error as e:
            self._countries_error = str(e)
            self.emit("countries-changed")
            return

        output = stdout or ""
        countries = parse_countries(output)

        if not countries:
            # Most likely "Authentication required..."; keep the CLI's wording.
            self._countries_error = output.strip() or "no countries returned"
            self.emit("countries-changed")
            return

        self._countries = countries
        self._countries_error = ""
        self._cached_at = time.time()
        self._write_cache()
        self.emit("countries-changed")

    def _write_cache(self):
        try:
            os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
            with open(CACHE_PATH, "w") as f:
                json.dump(
                    {"fetched_at": self._cached_at, "countries": self._countries}, f
                )
        except OSError:
            pass

    @Property(object, "readable")
    def countries(self) -> list:
        """[(name, CODE), ...], empty until a signed-in fetch succeeds."""
        return self._countries

    @Property(str, "readable")
    def countries_error(self) -> str:
        return self._countries_error

    # -- Properties --------------------------------------------------------

    @Property(str, "readable")
    def state(self) -> str:
        """One of: disconnected, connecting, connected, disconnecting, error."""
        return self._state

    @Property(str, "readable")
    def server(self) -> str:
        """Server name such as "CH#12", empty when not connected."""
        return self._server

    @Property(str, "readable")
    def message(self) -> str:
        """Error text from the last failed action, empty otherwise."""
        return self._message
