"""Driving a visible kitty terminal, in Python rather than shell.

Ported from three bash scripts. They were small, but each carried the same
`set -euo pipefail` hazard as the launcher: a failed pipe aborted with no
message, and the caller saw an empty error. Here a failure says what failed.

The terminal is opened with remote control on a private socket, so Nova can
type into and read back from the one she opened — never the user's own.
"""
from __future__ import annotations

import apps
import subprocess
import time
from pathlib import Path

STATE_DIR = Path.home() / ".local/state/nova/term"
LAST = STATE_DIR / "last"


def _run(argv: list[str], timeout: int = 30) -> tuple[bool, str]:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    return p.returncode == 0, (p.stdout or p.stderr or "").strip()


def resolve_dir(directory: str) -> Path | None:
    """"~/dev" as given, otherwise a case-insensitive match under $HOME, so
    "download" finds "Downloads"."""
    if not directory:
        return Path.home()
    d = Path(directory).expanduser()
    if d.is_dir():
        return d
    base = d.name.lower()
    for candidate in sorted(Path.home().rglob("*")):
        try:
            if (candidate.is_dir() and not candidate.name.startswith(".")
                    and candidate.name.lower().startswith(base)
                    and len(candidate.relative_to(Path.home()).parts) <= 2):
                return candidate
        except OSError:
            continue
    return None


def socket() -> str | None:
    try:
        return LAST.read_text().strip() or None
    except OSError:
        return None


def open_terminal(workspace: int | None = None, directory: str = "") -> str:
    start = resolve_dir(directory)
    if start is None:
        return f"FAILED: directory not found: {directory}"

    sock = f"unix:@nova-term-{int(time.time())}"
    cmd = (f"kitty -o allow_remote_control=socket-only --listen-on={sock} "
           f"--directory {start}")
    rule = f"[workspace {workspace} silent] " if workspace else ""
    apps.ensure_hypr_env()
    ok, err = _run(["hyprctl", "dispatch", "exec", f"{rule}{cmd}"])
    if not ok:
        return f"FAILED: could not open a terminal: {err[:200]}"

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LAST.write_text(sock)
    # Wait for the socket to answer rather than sleeping a fixed amount: too
    # long when kitty is quick, too short when it is not.
    for _ in range(60):
        if _run(["kitty", "@", "--to", sock, "ls"], timeout=5)[0]:
            where = f" on workspace {workspace}" if workspace else ""
            return f"opened a terminal{where} in {start}"
        time.sleep(0.05)
    return "FAILED: the terminal did not answer on its control socket"


def send(command: str) -> str:
    sock = socket()
    if not sock:
        return "FAILED: no terminal is open — use open_terminal first"
    try:
        p = subprocess.run(["kitty", "@", "--to", sock, "send-text", "--stdin"],
                           input=f"{command}\r", text=True,
                           capture_output=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        return f"FAILED: {exc}"
    if p.returncode != 0:
        return f"FAILED: {(p.stderr or '').strip()[:200]}"
    return "sent"


def read(scrollback: bool = False) -> str:
    sock = socket()
    if not sock:
        return "FAILED: no terminal is open"
    ok, out = _run(["kitty", "@", "--to", sock, "get-text",
                    "--extent", "all" if scrollback else "screen"])
    return out if ok else f"FAILED: {out[:200]}"
