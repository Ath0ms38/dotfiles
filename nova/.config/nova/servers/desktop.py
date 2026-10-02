#!/usr/bin/env python3
"""Nova MCP server — desktop control (Hyprland, apps, windows, audio).

Everything here is SILENT by design: Nova acts in the background and must
never steal focus or switch the workspace the user is looking at.

Run standalone for a smoke test:  desktop.py --selftest
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from mcp.server import MCPServer

import apps



server = MCPServer("nova-desktop")


def sh(argv: list[str], timeout: int = 30, limit: int = 800) -> str:
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    out = (p.stdout or "").strip() or (p.stderr or "").strip()
    return out[:limit] if p.returncode == 0 else f"FAILED: {out[:600]}"


def hypr(*args: str) -> str:
    # Recover HYPRLAND_INSTANCE_SIGNATURE if the service started before
    # Hyprland exported it — see apps.ensure_hypr_env.
    if not apps.ensure_hypr_env():
        return "FAILED: Hyprland is not running (no instance socket found)"
    return sh(["hyprctl", *args])


def hypr_json(*args: str) -> list | dict | str:
    """hyprctl -j output, untruncated — clipping it to the tool-result limit
    produces invalid JSON, which is exactly how list_windows used to fail."""
    if not apps.ensure_hypr_env():
        return "FAILED: Hyprland is not running"
    raw = sh(["hyprctl", "-j", *args], limit=1_000_000)
    if raw.startswith("FAILED"):
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return "FAILED: could not parse hyprctl output"


@server.tool()
def launch_app(app: str, workspace: int | None = None) -> str:
    """Launch an app, optionally on a given Hyprland workspace. Any installed
    app works; the window is placed silently, without switching workspace.

    Args:
        app: name as the user said it ("firefox", "antigravity", "terminal")
        workspace: Hyprland workspace number (1-10), optional
    """
    return apps.launch(app, workspace)


# find_app used to exist for checking a name before promising to open it.
# launch_app now resolves mangled names by edit distance and, when it truly
# cannot, answers with the closest installed apps — so the extra tool was
# costing prompt tokens to duplicate what a failure already tells you.


def _find_window(needle: str) -> dict | str:
    """First window whose class or title contains `needle`, or an error string."""
    clients = hypr_json("clients")
    if isinstance(clients, str):
        return clients
    n = needle.lower()
    for c in clients:
        if n in c.get("class", "").lower() or n in c.get("title", "").lower():
            return c
    return f"FAILED: no window matching {needle!r}"


@server.tool()
def list_windows() -> str:
    """List open windows: class, title, workspace and whether it has focus."""
    clients = hypr_json("clients")
    if isinstance(clients, str):
        return clients
    active = hypr_json("activewindow")
    focused = active.get("address") if isinstance(active, dict) else None
    lines = [
        f"ws {c['workspace']['id']}: {c['class']} — {c['title'][:60]}"
        + (" [focused]" if c.get("address") == focused else "")
        for c in clients if c.get("mapped", True)
    ]
    return "\n".join(lines) or "no windows open"


@server.tool()
def window(action: str, window: str, workspace: int = 0) -> str:
    """Act on an open window.

    Args:
        action: "move" (to a workspace, silently), "focus" (steals focus —
            only when asked to be shown something), or "close"
        window: part of the window's class or title, case-insensitive
        workspace: destination, for action="move"
    """
    target = _find_window(window)
    if isinstance(target, str):
        return target
    addr = f"address:{target['address']}"
    if action == "move":
        if not workspace:
            return "FAILED: move needs a workspace number"
        out = hypr("dispatch", "movetoworkspacesilent", f"{workspace},{addr}")
        done = f"moved {target['class']} to workspace {workspace}"
    elif action == "focus":
        out, done = hypr("dispatch", "focuswindow", addr), f"focused {target['class']}"
    elif action == "close":
        out, done = hypr("dispatch", "closewindow", addr), f"closed {target['class']}"
    else:
        return f"FAILED: unknown action {action!r}"
    return out if out.startswith("FAILED") else done


@server.tool()
def switch_workspace(workspace: int) -> str:
    """Switch the user's view to another workspace. Only when explicitly asked.

    Args:
        workspace: workspace number to switch to
    """
    out = hypr("dispatch", "workspace", str(workspace))
    return out if out.startswith("FAILED") else f"switched to workspace {workspace}"


@server.tool()
def volume(level: int | None = None, change: int | None = None,
           mute: bool | None = None) -> str:
    """Read or change the output volume.

    Args:
        level: set volume to this percentage (0-100)
        change: relative change in percent, e.g. 10 or -10
        mute: True to mute, False to unmute; omit to leave unchanged
    """
    sink = "@DEFAULT_AUDIO_SINK@"
    if mute is not None:
        sh(["wpctl", "set-mute", sink, "1" if mute else "0"])
    if level is not None:
        pct = max(0, min(100, level))
        sh(["wpctl", "set-volume", "-l", "1", sink, f"{pct / 100:.2f}"])
    elif change is not None:
        delta = f"{abs(change)}%{'+' if change > 0 else '-'}"
        sh(["wpctl", "set-volume", "-l", "1", sink, delta])
    # wpctl says "Volume: 1.00 [MUTED]" — reported verbatim that becomes
    # "le volume est à 1.00". Answer in the unit the user actually speaks.
    status = sh(["wpctl", "get-volume", sink])
    if status.startswith("FAILED"):
        return status
    try:
        value = float(status.split()[1])
    except (IndexError, ValueError):
        return status
    return f"{round(value * 100)}%" + (" (muted)" if "MUTED" in status else "")


@server.tool()
def notify(message: str, urgency: str = "normal") -> str:
    """Raise a standalone desktop alert the user asked for (a reminder, a
    warning). Never for your own reply — that is delivered automatically.

    Args:
        message: text to display
        urgency: low, normal or critical
    """
    return sh(["notify-send", "-u", urgency, "Nova ✨", message]) or "notified"


@server.tool()
def screenshot(region: str = "screen") -> str:
    """Take a screenshot and return the file path.

    Args:
        region: "screen" for the whole output, "window" for the active window
    """
    out = Path.home() / "Pictures" / "nova"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"shot-{int(time.time())}.png"
    argv = ["grim"]
    if region == "window":
        w = hypr_json("activewindow")
        if isinstance(w, dict) and "at" in w and "size" in w:
            x, y = w["at"]
            width, height = w["size"]
            argv += ["-g", f"{x},{y} {width}x{height}"]
    res = sh([*argv, str(path)])
    return str(path) if path.exists() else res


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        print(list_windows())
        print(volume())
        sys.exit(0)
    server.run()
