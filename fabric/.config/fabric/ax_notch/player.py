"""
Media Player Widgets
- Player: Full player with album art, controls, progress
- PlayerSmall: Compact player for notch compact view
"""

import os
import tempfile
import urllib.parse
import urllib.request

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.label import Label
from fabric.widgets.stack import Stack
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.widgets.overlay import Overlay
from gi.repository import Gdk, Gio, GLib, Gtk

from . import icons

# Try to import MPRIS services
try:
    import sys
    import os
    # Add parent directory to path to find services module
    _parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent_dir not in sys.path:
        sys.path.insert(0, _parent_dir)
    from services.mpris import MprisPlayer, MprisPlayerManager
    HAS_MPRIS = True
except ImportError as e:
    HAS_MPRIS = False
    print(f"MPRIS service not available: {e}")


def get_player_icon(player_name: str) -> str:
    """Get icon for player by name"""
    if player_name:
        pn = player_name.lower()
        if pn == "firefox":
            return icons.firefox
        elif pn == "spotify":
            return icons.spotify
        elif pn in ("chromium", "brave"):
            return icons.chromium
    return icons.disc


class PlayerBox(Box):
    """Full player widget with album art and controls"""

    def __init__(self, mpris_player=None, **kwargs):
        super().__init__(
            name="ax-player-box",
            orientation="v",
            spacing=4,
            h_align="fill",
            v_expand=False,  # Don't expand - use natural height
            v_align="start",
            **kwargs,
        )

        self.mpris_player = mpris_player
        self._progress_timer_id = None

        # Album art placeholder
        self.cover_placeholder = Box(
            name="ax-player-cover-placeholder",
            h_align="center",
            v_align="center",
        )
        self.cover_placeholder.set_size_request(160, 160)

        # Progress ring around album art
        self.progressbar = CircularProgressBar(
            name="ax-player-progress",
            size=180,
            h_align="center",
            v_align="center",
            start_angle=180,
            end_angle=360,
        )
        self.progressbar.set_value(0.0)

        # Overlay progress on cover
        self.cover_overlay = Overlay(
            child=self.cover_placeholder,
            overlays=[self.progressbar],
        )

        # Track info
        self.title = Label(
            name="ax-player-title",
            label="Nothing Playing",
            h_expand=True,
            h_align="center",
        )
        self.title.set_ellipsize(Gtk.pango.EllipsizeMode.END) if hasattr(Gtk, 'pango') else None

        self.artist = Label(
            name="ax-player-artist",
            label="",
            h_expand=True,
            h_align="center",
        )

        self.album = Label(
            name="ax-player-album",
            label="",
            h_expand=True,
            h_align="center",
        )

        # Time display
        self.time_label = Label(
            name="ax-player-time",
            label="--:-- / --:--",
        )

        # Control buttons
        self.btn_prev = Button(
            name="ax-player-btn",
            child=Label(label=icons.prev_track),
            on_clicked=lambda *_: self._on_prev(),
        )
        self.btn_backward = Button(
            name="ax-player-btn",
            child=Label(label=icons.skip_back),
            on_clicked=lambda *_: self._on_backward(),
        )
        self.btn_play = Button(
            name="ax-player-btn-play",
            child=Label(label=icons.play),
            on_clicked=lambda *_: self._on_play_pause(),
        )
        self.btn_forward = Button(
            name="ax-player-btn",
            child=Label(label=icons.skip_forward),
            on_clicked=lambda *_: self._on_forward(),
        )
        self.btn_next = Button(
            name="ax-player-btn",
            child=Label(label=icons.next_track),
            on_clicked=lambda *_: self._on_next(),
        )

        self.controls = Box(
            name="ax-player-controls",
            orientation="h",
            spacing=8,
            h_align="center",
            children=[
                self.btn_prev,
                self.btn_backward,
                self.btn_play,
                self.btn_forward,
                self.btn_next,
            ],
        )

        # Assemble
        self.add(self.cover_overlay)
        self.add(self.title)
        self.add(self.artist)
        self.add(self.album)
        self.add(self.controls)
        self.add(self.time_label)

        # Connect to player if available
        if mpris_player:
            self._apply_mpris_properties()
            mpris_player.connect("changed", lambda *_: self._apply_mpris_properties())
            self._start_progress_timer()
        else:
            self._set_no_player_state()

    def _set_no_player_state(self):
        """Set UI for when no player is available"""
        self.title.set_label("Nothing Playing")
        self.artist.set_label("Enjoy the silence")
        self.album.set_label("")
        self.btn_play.get_child().set_label(icons.stop)
        self.progressbar.set_value(0.0)
        self.time_label.set_label("--:-- / --:--")

    def _apply_mpris_properties(self):
        """Update UI from MPRIS player properties"""
        if not self.mpris_player:
            return

        mp = self.mpris_player

        # Title
        if mp.title:
            self.title.set_label(mp.title)
        else:
            self.title.set_label("Unknown Track")

        # Artist
        if mp.artist:
            self.artist.set_label(mp.artist)
        else:
            self.artist.set_label("")

        # Album
        if mp.album:
            self.album.set_label(mp.album)
        else:
            self.album.set_label("")

        # Play/Pause icon
        if mp.playback_status == "playing":
            self.btn_play.get_child().set_label(icons.pause)
            self.btn_play.add_style_class("playing")
        else:
            self.btn_play.get_child().set_label(icons.play)
            self.btn_play.remove_style_class("playing")

    def _start_progress_timer(self):
        """Start timer to update progress"""
        if self._progress_timer_id:
            GLib.source_remove(self._progress_timer_id)
        self._progress_timer_id = GLib.timeout_add(1000, self._update_progress)

    def _update_progress(self):
        """Update progress bar and time"""
        if not self.mpris_player:
            return False

        try:
            position = self.mpris_player.position
            length = int(self.mpris_player.length or 0)

            if length > 0:
                progress = position / length
                self.progressbar.set_value(progress)
                self.time_label.set_label(
                    f"{self._format_time(position)} / {self._format_time(length)}"
                )
            else:
                self.progressbar.set_value(0.0)
                self.time_label.set_label("--:-- / --:--")
        except Exception:
            pass

        return True

    def _format_time(self, microseconds: int) -> str:
        """Format microseconds to MM:SS"""
        seconds = int(microseconds / 1000000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def _on_prev(self):
        if self.mpris_player:
            self.mpris_player.previous()

    def _on_backward(self):
        if self.mpris_player and self.mpris_player.can_seek:
            new_pos = max(0, self.mpris_player.position - 5000000)
            self.mpris_player.position = new_pos

    def _on_play_pause(self):
        if self.mpris_player:
            self.mpris_player.play_pause()
            GLib.timeout_add(100, self._apply_mpris_properties)

    def _on_forward(self):
        if self.mpris_player and self.mpris_player.can_seek:
            new_pos = self.mpris_player.position + 5000000
            self.mpris_player.position = new_pos

    def _on_next(self):
        if self.mpris_player:
            self.mpris_player.next()


class Player(Box):
    """Player container with stack for multiple players"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-player",
            orientation="v",
            spacing=0,
            h_align="fill",
            v_expand=False,  # Don't expand - use natural height
            v_align="start",
            **kwargs,
        )

        self.player_stack = Stack(
            name="ax-player-stack",
            transition_type="slide-left-right",
            transition_duration=300,
            v_expand=False,
            v_align="start",
        )

        self.switcher = Gtk.StackSwitcher(
            name="ax-player-switcher",
            spacing=4,
        )
        self.switcher.set_stack(self.player_stack)
        self.switcher.set_halign(Gtk.Align.CENTER)

        if HAS_MPRIS:
            self.mpris_manager = MprisPlayerManager()
            players = self.mpris_manager.players

            if players:
                for p in players:
                    mp = MprisPlayer(p)
                    pb = PlayerBox(mpris_player=mp)
                    self.player_stack.add_titled(pb, mp.player_name, mp.player_name)
            else:
                pb = PlayerBox(mpris_player=None)
                self.player_stack.add_titled(pb, "nothing", "Nothing Playing")

            self.mpris_manager.connect("player-appeared", self._on_player_appeared)
            self.mpris_manager.connect("player-vanished", self._on_player_vanished)
        else:
            pb = PlayerBox(mpris_player=None)
            self.player_stack.add_titled(pb, "nothing", "Nothing Playing")

        self.add(self.player_stack)
        self.add(self.switcher)

        GLib.idle_add(self._replace_switcher_labels)

    def _on_player_appeared(self, manager, player):
        """Handle new player appearing"""
        children = self.player_stack.get_children()
        if len(children) == 1 and not getattr(children[0], "mpris_player", None):
            self.player_stack.remove(children[0])

        mp = MprisPlayer(player)
        pb = PlayerBox(mpris_player=mp)
        self.player_stack.add_titled(pb, mp.player_name, mp.player_name)
        GLib.idle_add(self._replace_switcher_labels)

    def _on_player_vanished(self, manager, bus_name):
        """Handle player disappearing"""
        for child in self.player_stack.get_children():
            if hasattr(child, "mpris_player") and child.mpris_player:
                # Check both bus_name and player_name
                if (child.mpris_player.bus_name == bus_name or
                    child.mpris_player.player_name == bus_name):
                    self.player_stack.remove(child)
                    break

        if not self.player_stack.get_children():
            pb = PlayerBox(mpris_player=None)
            self.player_stack.add_titled(pb, "nothing", "Nothing Playing")

        GLib.idle_add(self._replace_switcher_labels)

    def _replace_switcher_labels(self):
        """Replace text labels with icons"""
        buttons = self.switcher.get_children()
        for btn in buttons:
            if isinstance(btn, Gtk.ToggleButton):
                for child in btn.get_children():
                    if isinstance(child, Gtk.Label):
                        player_name = child.get_text()
                        icon = get_player_icon(player_name)
                        btn.remove(child)
                        new_label = Label(name="ax-player-label", label=icon)
                        btn.add(new_label)
                        new_label.show_all()
                        break
        return False


class PlayerSmall(CenterBox):
    """Compact player for notch compact view"""

    def __init__(self, **kwargs):
        super().__init__(
            name="ax-player-small",
            orientation="h",
            h_align="fill",
            v_align="center",
            **kwargs,
        )

        self.mpris_player = None

        # Icon button (click to switch players)
        self.icon_btn = Button(
            name="ax-compact-mpris-icon",
            child=Label(label=icons.disc),
        )

        # Track label
        self.track_label = Label(
            name="ax-compact-mpris-label",
            label="Nothing Playing",
            h_align="center",
        )

        # Play/pause button
        self.play_btn = Button(
            name="ax-compact-mpris-btn",
            child=Label(label=icons.play),
        )

        # Connect signals
        self.play_btn.connect("clicked", self._on_play_pause)

        # Set children
        self.set_start_children(self.icon_btn)
        self.set_center_children(self.track_label)
        self.set_end_children(self.play_btn)

        # Initialize MPRIS
        if HAS_MPRIS:
            self.mpris_manager = MprisPlayerManager()
            players = self.mpris_manager.players

            if players:
                self.mpris_player = MprisPlayer(players[0])
                self._apply_properties()
                self.mpris_player.connect("changed", lambda *_: self._apply_properties())

            self.mpris_manager.connect("player-appeared", self._on_player_appeared)
            self.mpris_manager.connect("player-vanished", self._on_player_vanished)

    def _apply_properties(self):
        """Update UI from player properties"""
        if not self.mpris_player:
            self.track_label.set_label("Nothing Playing")
            self.play_btn.get_child().set_label(icons.stop)
            self.icon_btn.get_child().set_label(icons.disc)
            return

        mp = self.mpris_player

        # Track title
        if mp.title:
            self.track_label.set_label(mp.title)
        else:
            self.track_label.set_label("Unknown Track")

        # Play/pause icon
        if mp.playback_status == "playing":
            self.play_btn.get_child().set_label(icons.pause)
        else:
            self.play_btn.get_child().set_label(icons.play)

        # Player icon
        icon = get_player_icon(mp.player_name if hasattr(mp, "player_name") else "")
        self.icon_btn.get_child().set_label(icon)

    def _on_play_pause(self, *args):
        """Toggle play/pause"""
        if self.mpris_player:
            self.mpris_player.play_pause()
            GLib.timeout_add(100, self._apply_properties)

    def _on_player_appeared(self, manager, player):
        """Handle new player"""
        if not self.mpris_player:
            self.mpris_player = MprisPlayer(player)
            self._apply_properties()
            self.mpris_player.connect("changed", lambda *_: self._apply_properties())

    def _on_player_vanished(self, manager, player_name):
        """Handle player disappearing"""
        if self.mpris_player and self.mpris_player.player_name == player_name:
            players = self.mpris_manager.players
            if players:
                self.mpris_player = MprisPlayer(players[0])
                self.mpris_player.connect("changed", lambda *_: self._apply_properties())
            else:
                self.mpris_player = None
            self._apply_properties()
