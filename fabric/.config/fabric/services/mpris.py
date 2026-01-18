"""
MPRIS D-Bus Service for Media Player Control
Provides MprisPlayer and MprisPlayerManager classes
"""

import subprocess
from gi.repository import GLib, Gio, GObject


class MprisPlayer(GObject.Object):
    """Wrapper for an MPRIS media player via D-Bus"""

    __gsignals__ = {
        "changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "closed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, bus_name: str):
        super().__init__()
        self._bus_name = bus_name
        self._player_name = bus_name.split(".")[-1] if "." in bus_name else bus_name

        # Extract clean player name
        if "firefox" in self._player_name.lower():
            self._player_name = "firefox"
        elif "spotify" in self._player_name.lower():
            self._player_name = "spotify"
        elif "chromium" in self._player_name.lower():
            self._player_name = "chromium"
        elif "brave" in self._player_name.lower():
            self._player_name = "brave"

        self._proxy = None
        self._props_proxy = None
        self._metadata = {}
        self._playback_status = "stopped"
        self._position = 0
        self._can_seek = False
        self._can_go_next = False
        self._can_go_previous = False

        self._setup_dbus()

    def _setup_dbus(self):
        """Setup D-Bus proxies"""
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

            # Player interface proxy
            self._proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                self._bus_name,
                "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player",
                None,
            )

            # Properties interface proxy
            self._props_proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                self._bus_name,
                "/org/mpris/MediaPlayer2",
                "org.freedesktop.DBus.Properties",
                None,
            )

            # Connect to property changes
            self._proxy.connect("g-properties-changed", self._on_properties_changed)

            # Initial property fetch
            self._fetch_properties()

        except Exception as e:
            print(f"MPRIS: Error setting up D-Bus for {self._bus_name}: {e}")

    def _on_properties_changed(self, proxy, changed, invalidated):
        """Handle property changes"""
        self._fetch_properties()
        self.emit("changed")

    def _fetch_properties(self):
        """Fetch current player properties"""
        if not self._props_proxy:
            return

        try:
            # Get all properties
            result = self._props_proxy.call_sync(
                "GetAll",
                GLib.Variant("(s)", ("org.mpris.MediaPlayer2.Player",)),
                Gio.DBusCallFlags.NONE,
                1000,
                None,
            )

            if result:
                props = result.unpack()[0]

                self._metadata = props.get("Metadata", {})
                self._playback_status = props.get("PlaybackStatus", "stopped").lower()
                self._position = props.get("Position", 0)
                self._can_seek = props.get("CanSeek", False)
                self._can_go_next = props.get("CanGoNext", False)
                self._can_go_previous = props.get("CanGoPrevious", False)

        except Exception as e:
            pass  # Silently fail on property fetch errors

    @property
    def player_name(self) -> str:
        return self._player_name

    @property
    def bus_name(self) -> str:
        return self._bus_name

    @property
    def title(self) -> str:
        return self._metadata.get("xesam:title", "Unknown")

    @property
    def artist(self) -> str:
        artists = self._metadata.get("xesam:artist", [])
        if isinstance(artists, list) and artists:
            return artists[0]
        return str(artists) if artists else ""

    @property
    def album(self) -> str:
        return self._metadata.get("xesam:album", "")

    @property
    def art_url(self) -> str:
        return self._metadata.get("mpris:artUrl", "")

    @property
    def length(self) -> int:
        """Length in microseconds"""
        return self._metadata.get("mpris:length", 0)

    @property
    def position(self) -> int:
        """Position in microseconds"""
        # Fetch fresh position
        if self._props_proxy:
            try:
                result = self._props_proxy.call_sync(
                    "Get",
                    GLib.Variant("(ss)", ("org.mpris.MediaPlayer2.Player", "Position")),
                    Gio.DBusCallFlags.NONE,
                    500,
                    None,
                )
                if result:
                    return result.unpack()[0]
            except Exception:
                pass
        return self._position

    @position.setter
    def position(self, value: int):
        """Set position (seek)"""
        if self._proxy and self._can_seek:
            try:
                track_id = self._metadata.get("mpris:trackid", "/org/mpris/MediaPlayer2/TrackList/NoTrack")
                self._proxy.call_sync(
                    "SetPosition",
                    GLib.Variant("(ox)", (track_id, value)),
                    Gio.DBusCallFlags.NONE,
                    1000,
                    None,
                )
            except Exception:
                pass

    @property
    def playback_status(self) -> str:
        return self._playback_status

    @property
    def can_seek(self) -> bool:
        return self._can_seek

    @property
    def can_go_next(self) -> bool:
        return self._can_go_next

    @property
    def can_go_previous(self) -> bool:
        return self._can_go_previous

    def play(self):
        """Start playback"""
        if self._proxy:
            try:
                self._proxy.call_sync("Play", None, Gio.DBusCallFlags.NONE, 1000, None)
            except Exception:
                pass

    def pause(self):
        """Pause playback"""
        if self._proxy:
            try:
                self._proxy.call_sync("Pause", None, Gio.DBusCallFlags.NONE, 1000, None)
            except Exception:
                pass

    def play_pause(self):
        """Toggle play/pause"""
        if self._proxy:
            try:
                self._proxy.call_sync("PlayPause", None, Gio.DBusCallFlags.NONE, 1000, None)
                GLib.timeout_add(100, self._fetch_properties)
            except Exception:
                pass

    def stop(self):
        """Stop playback"""
        if self._proxy:
            try:
                self._proxy.call_sync("Stop", None, Gio.DBusCallFlags.NONE, 1000, None)
            except Exception:
                pass

    def next(self):
        """Skip to next track"""
        if self._proxy and self._can_go_next:
            try:
                self._proxy.call_sync("Next", None, Gio.DBusCallFlags.NONE, 1000, None)
            except Exception:
                pass

    def previous(self):
        """Skip to previous track"""
        if self._proxy and self._can_go_previous:
            try:
                self._proxy.call_sync("Previous", None, Gio.DBusCallFlags.NONE, 1000, None)
            except Exception:
                pass


class MprisPlayerManager(GObject.Object):
    """Manager for MPRIS players - tracks available players"""

    __gsignals__ = {
        "player-appeared": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "player-vanished": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__()
        self._players = []
        self._bus = None
        self._dbus_proxy = None

        self._setup_dbus()
        self._scan_players()

    def _setup_dbus(self):
        """Setup D-Bus monitoring"""
        try:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

            # Watch for name changes
            self._dbus_proxy = Gio.DBusProxy.new_sync(
                self._bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus",
                None,
            )

            # Subscribe to NameOwnerChanged signal
            self._bus.signal_subscribe(
                "org.freedesktop.DBus",
                "org.freedesktop.DBus",
                "NameOwnerChanged",
                "/org/freedesktop/DBus",
                None,
                Gio.DBusSignalFlags.NONE,
                self._on_name_owner_changed,
                None,
            )

        except Exception as e:
            print(f"MPRIS Manager: Error setting up D-Bus: {e}")

    def _on_name_owner_changed(self, connection, sender, path, interface, signal, params, user_data):
        """Handle D-Bus name changes"""
        name, old_owner, new_owner = params.unpack()

        if not name.startswith("org.mpris.MediaPlayer2."):
            return

        if new_owner and not old_owner:
            # Player appeared
            if name not in self._players:
                self._players.append(name)
                self.emit("player-appeared", name)
        elif old_owner and not new_owner:
            # Player vanished
            if name in self._players:
                self._players.remove(name)
                self.emit("player-vanished", name)

    def _scan_players(self):
        """Scan for existing MPRIS players"""
        if not self._dbus_proxy:
            return

        try:
            result = self._dbus_proxy.call_sync(
                "ListNames",
                None,
                Gio.DBusCallFlags.NONE,
                1000,
                None,
            )

            if result:
                names = result.unpack()[0]
                for name in names:
                    if name.startswith("org.mpris.MediaPlayer2."):
                        if name not in self._players:
                            self._players.append(name)

        except Exception as e:
            print(f"MPRIS Manager: Error scanning players: {e}")

    @property
    def players(self) -> list:
        """List of MPRIS player bus names"""
        return self._players.copy()

    def get_player(self, bus_name: str) -> MprisPlayer:
        """Get MprisPlayer instance for a bus name"""
        return MprisPlayer(bus_name)
