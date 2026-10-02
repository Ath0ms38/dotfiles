#!/usr/bin/env python3
"""Nova MCP server — recording audio and screen, and reading them back.

The work is in recording.py; this file is only the tool surface. Audio
recording captures the system output and the microphone as separate tracks,
then mixes and transcribes on stop. Transcription of a long recording is the
one place that stays LOCAL (whisper.cpp on the GPU): an hour-long meeting is
not something to ship to an API, and it is not latency-sensitive.
"""
from __future__ import annotations

from pathlib import Path

from mcp.server import MCPServer

import recording

HOME = Path.home()
server = MCPServer("nova-media")


@server.tool()
def record_audio_start(name: str = "call") -> str:
    """Start recording system audio + microphone (e.g. a Discord call).

    Args:
        name: label for the recording, used in the folder name
    """
    return recording.audio_start(name)


@server.tool()
def record_audio_stop() -> str:
    """Stop the audio recording, mix the tracks and transcribe it locally.

    Returns the transcript path. This takes a while on a long recording —
    that is expected, not a hang.
    """
    return recording.audio_stop()


@server.tool()
def record_audio_status() -> str:
    """Is an audio recording currently running, and since when."""
    return recording.audio_status()


@server.tool()
def record_screen_start(name: str = "screen", region: bool = False) -> str:
    """Start recording the screen.

    Args:
        name: label for the recording
        region: True to let the user drag a region; False records the focused
            monitor
    """
    return recording.screen_start(name, region)


@server.tool()
def record_screen_stop(with_audio: str = "") -> str:
    """Stop the screen recording and return the video path.

    Args:
        with_audio: path of an audio file to mux into the video (optional)
    """
    out = recording.screen_stop()
    if with_audio and not out.startswith("FAILED"):
        return f"{out}\n{recording.mux(with_audio)}"
    return out


@server.tool()
def record_screen_status() -> str:
    """Is a screen recording currently running."""
    return recording.screen_status()


@server.tool()
def list_recordings(limit: int = 10) -> str:
    """List the most recent recordings with their contents.

    Args:
        limit: how many to list, newest first
    """
    if not recording.DATA.is_dir():
        return "no recordings yet"
    dirs = sorted((d for d in recording.DATA.iterdir() if d.is_dir()),
                  key=lambda d: d.stat().st_mtime, reverse=True)[:limit]
    lines = [f"{d.name}: {', '.join(sorted(f.name for f in d.iterdir()))}"
             for d in dirs]
    return "\n".join(lines) or "no recordings yet"


@server.tool()
def read_transcript(name: str, max_chars: int = 6000) -> str:
    """Read a recording's transcript, to summarise it or answer questions.

    Args:
        name: the recording folder name, as shown by list_recordings
        max_chars: truncate beyond this many characters
    """
    folder = recording.DATA / name
    if not folder.is_dir():
        matches = sorted(recording.DATA.glob(f"*{name}*"))
        if not matches:
            return f"FAILED: no recording named {name!r}"
        folder = matches[-1]
    txt = next(iter(sorted(folder.glob("*.txt"))), None)
    if txt is None:
        return f"FAILED: {folder.name} has no transcript"
    text = txt.read_text(errors="replace").strip()
    return text[:max_chars] + ("\n…(truncated)" if len(text) > max_chars else "")


if __name__ == "__main__":
    server.run()
