#!/usr/bin/env python3
"""Nova MCP server — Apple Music through the Sidra desktop app.

Transport (play/pause/next) goes over MPRIS, which is instant. Actually
*choosing* what to play has no MPRIS equivalent, so sidra.py drives the app's
interface over the Chrome DevTools Protocol — Sidra is Electron, so its
renderer is scriptable. That is why play_track and play_playlist are slower
than the transport controls, and why they can fail if the app is not running.

sidra.py is imported, not run as a subprocess: it used to be a script called
through the venv interpreter, which meant a Python start-up per transport
command and errors that arrived as exit codes rather than messages.
"""
from __future__ import annotations

import asyncio
import time
import urllib.parse

from mcp.server import MCPServer

import sidra

server = MCPServer("nova-music")


def _now_playing() -> str:
    if not sidra.sidra_running():
        return "nothing is playing (Sidra is not running)"
    state = sidra.pctl("status")
    meta = sidra.pctl("metadata", "--format",
                      "{{artist}} — {{title}} ({{album}})")
    return f"{state}: {meta}" if meta else state


@server.tool()
def play() -> str:
    """Resume playback."""
    sidra.ensure()
    sidra.pctl("play")
    return _now_playing()


@server.tool()
def pause() -> str:
    """Pause playback."""
    sidra.pctl("pause")
    return _now_playing()


@server.tool()
def next_track() -> str:
    """Skip to the next track."""
    sidra.pctl("next")
    time.sleep(0.6)
    return _now_playing()


@server.tool()
def previous_track() -> str:
    """Go back to the previous track."""
    sidra.pctl("previous")
    time.sleep(0.6)
    return _now_playing()


@server.tool()
def now_playing() -> str:
    """What is currently playing (title, artist, player state)."""
    return _now_playing()


@server.tool()
def play_track(query: str) -> str:
    """Search Apple Music and play the best match.

    Args:
        query: song, album or artist as the user said it
    """
    sidra.ensure()
    url = (f"https://music.apple.com/{sidra.STORE}/search"
           f"?term={urllib.parse.quote(query)}")
    out = asyncio.run(sidra._navigate_and_run(url, sidra.CLICK_FIRST))
    if not (out or {}).get("ok"):
        return f"FAILED: nothing found for {query!r}"
    time.sleep(0.8)
    return _now_playing()


@server.tool()
def play_playlist(name: str) -> str:
    """Play one of the user's Apple Music playlists by name.

    Args:
        name: playlist name, matched loosely
    """
    sidra.ensure()
    out = asyncio.run(sidra._navigate_and_run(
        f"https://music.apple.com/{sidra.STORE}/library/playlists",
        sidra.PLAY_PLAYLIST(name)))
    if not (out or {}).get("ok"):
        available = list_playlists()
        return (f"FAILED: no playlist called {name!r}. Available: {available}")
    time.sleep(0.8)
    return _now_playing()


@server.tool()
def list_playlists() -> str:
    """List the user's Apple Music playlists."""
    sidra.ensure()
    out = asyncio.run(sidra._navigate_and_run(
        f"https://music.apple.com/{sidra.STORE}/library/playlists",
        sidra.LIST_PLAYLISTS))
    names = [p["name"] for p in (out or []) if isinstance(p, dict)]
    return ", ".join(names) if names else "FAILED: could not read the playlists"


if __name__ == "__main__":
    server.run()
