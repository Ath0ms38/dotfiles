#!/usr/bin/env python3
"""Nova MCP server — running things.

Two very different modes, and the distinction matters:

  run_command   invisible, no window, the DEFAULT for getting work done
  open_terminal a real kitty window the user can see — only when they ask

Nova used to only have the visible one, so every "check the git status"
spawned a terminal in the user's face. Hence the split, and the wording of
the tool descriptions: the model picks from those.

Commands sent to a visible terminal are verified: a sentinel echoed after
each one carries its exit status back, so Nova reports what actually
happened instead of assuming it worked.
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

from mcp.server import MCPServer

import apps
import kitty

server = MCPServer("nova-shell")


def sh(argv: list[str], timeout: int = 60, limit: int = 800) -> str:
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    out = (p.stdout or "").strip() or (p.stderr or "").strip()
    return out[:limit] if p.returncode == 0 else f"FAILED: {out[:600]}"


# A command that only starts a program, e.g. "nohup firefox &", "setsid code",
# or a bare "discord". Detected loosely on purpose — this only decides whether
# to look the name up, not whether to refuse.
_LAUNCHER = re.compile(
    r"^\s*(?:nohup\s+|setsid\s+|env\s+\S+=\S+\s+|exec\s+)*"
    r"([\w.+-]+)\s*(?:&\s*)?(?:>\s*/dev/null\s*(?:2>&1)?\s*)?(?:&\s*)?$")


def _is_app_launch(command: str) -> str | None:
    """The name of an installed application this command merely starts.

    The model reaches for `nohup firefox &` instead of launch_app, and it
    "works" — a window appears, so nothing looks wrong. What is silently lost
    is everything launch_app exists for: the requested workspace, the silent
    placement that does not steal focus, and the name resolution that turns a
    mangled transcript back into a real application.
    """
    cleaned = re.sub(r"&>\s*/dev/null|>\s*/dev/null(\s+2>&1)?|2>&1", "",
                     command).strip()
    m = _LAUNCHER.match(cleaned)
    if not m:
        return None
    name = m.group(1)
    if name in {"cd", "ls", "echo", "cat", "date", "pwd", "true", "false"}:
        return None
    found, _ = apps.resolve(name)
    return name if found else None


def _resolve_dir(directory: str) -> Path | None:
    d = Path(directory).expanduser()
    if d.is_dir():
        return d
    # fuzzy: "downloads" -> ~/Downloads, "dotfiles" -> ~/dotfiles
    hits = [h for h in Path.home().glob(f"*{Path(directory).name}*") if h.is_dir()]
    return hits[0] if hits else None


@server.tool()
def run_command(command: str, directory: str = "", timeout: int = 15) -> str:
    """Run a shell command invisibly; returns its exit code and output.
    The default way to do anything — opens no window.

    Args:
        command: the shell command line
        directory: working directory, matched loosely against $HOME
        timeout: seconds to allow; raise it only for genuinely slow commands
    """
    app = _is_app_launch(command)
    if app:
        return (f"FAILED: {app!r} is a desktop application — use launch_app, "
                "which places it on the right workspace without stealing "
                "focus. run_command cannot do either.")
    cwd = None
    if directory:
        d = _resolve_dir(directory)
        if d is None:
            return f"FAILED: directory not found: {directory}"
        cwd = str(d)
    # Default 15s, not minutes: an invented command that waits on stdin used
    # to stall a whole voice turn for a minute and a half.
    limit = max(1, min(int(timeout), 300))
    try:
        p = subprocess.run(command, shell=True, capture_output=True, text=True,
                           timeout=limit, cwd=cwd, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return f"FAILED: command timed out after {limit}s"
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    head = f"exit={p.returncode}"
    return f"{head}\n{out[:1500]}" if out else head


def _screen() -> str:
    # Never truncated: the completion sentinel is the LAST line, and clipping
    # the screen to the tool-result limit hid it — that alone made every
    # `git status` wait out the full 30 s timeout before being reported as
    # "still running".
    return kitty.read()


def _wait_ready(timeout: float = 20.0) -> bool:
    """Block until the shell in that terminal actually accepts input.

    kitty answers on its socket long before zsh, starship and the plugins have
    finished loading, and keystrokes sent during that window are simply lost —
    which is why a freshly opened terminal used to take 13 s to run its first
    command while an existing one took 0.2 s. Probing with a throwaway echo is
    the only honest way to know the shell is listening.
    """
    marker = f"NOVAREADY{int(time.time() * 1000) % 10000}"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        kitty.send(f"echo {marker}")
        for _ in range(6):
            time.sleep(0.15)
            if _screen().count(marker) > 1:   # echoed and printed
                kitty.send("clear")
                return True
    return False


def _run_one(cmd: str, timeout: float = 30.0) -> tuple[bool, str]:
    """Send one command to the visible terminal and wait for it to finish.

    The sentinel echoed after the command carries its exit status, which is
    the only reliable way to know a command in someone else's terminal
    actually completed. Interactive programs (btop, vim) never emit it —
    reported as still running rather than hung.
    """
    marker = f"NOVA{int(time.time() * 1000) % 100000}"
    sent = kitty.send(f'{cmd}; echo "{marker}:$?"')
    if sent.startswith("FAILED"):
        return False, sent
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # Reading the screen costs 0.02 s, so poll often — this is dead time in
        # front of the user.
        time.sleep(0.15)
        screen = _screen()
        for line in screen.splitlines():
            if line.startswith(f"{marker}:"):
                code = line.split(":", 1)[1].strip()
                body = screen.split(f'{marker}:$?"')[-1].split(marker)[0]
                body = "\n".join(x for x in body.splitlines() if x.strip())[-800:]
                return True, f"exit={code}" + (f"\n{body}" if body else "")
    tail = "\n".join(x for x in _screen().splitlines() if x.strip())[-500:]
    return False, f"still running (interactive or long) — output so far:\n{tail}"


@server.tool()
def open_terminal(workspace: int | None = None, directory: str = "",
                  commands: list[str] | None = None) -> str:
    """Open a VISIBLE terminal, optionally in a folder, and run commands in it.
    Only when the user asks for a terminal or wants to watch something run.

    Args:
        workspace: Hyprland workspace to place it on
        directory: folder to start in, matched case-insensitively
        commands: commands to run in order once it is open
    """
    out = kitty.open_terminal(workspace, directory)
    if out.startswith("FAILED") or not commands:
        return out
    if not _wait_ready():
        return f"{out}\nFAILED: the shell never became ready"
    return f"{out}\n" + terminal_run(commands)


@server.tool()
def terminal_run(commands: list[str]) -> str:
    """Run more commands in the terminal already opened by open_terminal,
    waiting for each and reporting its exit status. Stops at the first failure.

    Args:
        commands: shell command lines, executed in order
    """
    report = []
    for cmd in commands[:10]:
        finished, out = _run_one(cmd)
        report.append(f"$ {cmd}\n{out}")
        if not finished:
            break
        if out.startswith("exit=") and not out.startswith("exit=0"):
            report.append("(stopped: previous command failed)")
            break
    return "\n".join(report)[:2000]


@server.tool()
def terminal_read() -> str:
    """Read what is currently displayed in that terminal — use it to check
    a long-running command's progress before answering."""
    return _screen()


if __name__ == "__main__":
    server.run()
