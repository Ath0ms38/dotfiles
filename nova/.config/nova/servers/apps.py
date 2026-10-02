#!/usr/bin/env python3
"""Application resolution and launching, in Python rather than shell.

This was a bash script the desktop server shelled out to — a leftover from
before the move to MCP, kept because it worked. It stopped working: under
`set -euo pipefail`, one hiccup from `hyprctl clients -j | jq` aborted the
whole launch, and because the failure came from a pipeline rather than a
message the tool reported a bare "FAILED:" with nothing after it. Antigravity
and Firefox failed that way, repeatedly and unexplainably.

Nothing here needs a shell. Reading .desktop files, matching a mangled name
against them and watching for a window are all things Python does with real
error handling, and a window query that fails is now what it should always
have been: a retry, not the end of the launch.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import unicodedata
from pathlib import Path

APP_DIRS = [
    Path("/usr/share/applications"),
    Path("/usr/local/share/applications"),
    Path.home() / ".local/share/applications",
    Path("/var/lib/flatpak/exports/share/applications"),
]

# Voice-friendly names, and the ones speech-to-text reliably mangles.
ALIASES = {
    "terminal": "kitty", "term": "kitty",
    "fichiers": "nautilus", "files": "nautilus",
    "vscode": "code", "vs code": "code",
    "navigateur": "vivaldi", "browser": "vivaldi",
    "antigravité": "antigravity", "anti-gravity": "antigravity",
    "anti-graffiti": "antigravity", "antigraffiti": "antigravity",
}


def norm(text: str) -> str:
    """Lowercase, strip accents, keep only letters and digits."""
    folded = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in folded
                   if c.isalnum() and unicodedata.category(c) != "Mn")


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


class App:
    __slots__ = ("name", "name_fr", "exec_line", "wm_class", "path")

    def __init__(self, name: str, name_fr: str, exec_line: str,
                 wm_class: str, path: Path):
        self.name = name
        self.name_fr = name_fr
        self.exec_line = exec_line
        self.wm_class = wm_class
        self.path = path

    @property
    def command(self) -> str:
        """Exec without the desktop-entry field codes (%u %U %f %F …)."""
        return re.sub(r"\s+%[a-zA-Z]", "", self.exec_line).strip()

    @property
    def classes(self) -> list[str]:
        """Window classes this app might show up as."""
        out = [self.wm_class] if self.wm_class else []
        first = self.command.split()[0] if self.command else ""
        if first:
            out.append(Path(first).name)
        out.append(self.path.stem.rsplit(".", 1)[-1])
        return [c for c in out if c]


def _parse(path: Path) -> App | None:
    name = name_fr = exec_line = wm_class = ""
    in_entry = False
    try:
        for line in path.read_text(errors="replace").splitlines():
            if line.startswith("["):
                in_entry = line.strip() == "[Desktop Entry]"
                continue
            if not in_entry:
                continue
            if line.startswith("Name=") and not name:
                name = line[5:].strip()
            elif line.startswith("Name[fr]=") and not name_fr:
                name_fr = line[9:].strip()
            elif line.startswith("Exec=") and not exec_line:
                exec_line = line[5:].strip()
            elif line.startswith("StartupWMClass="):
                wm_class = line[15:].strip()
            elif line.startswith("NoDisplay=true"):
                return None
    except OSError:
        return None
    if not exec_line or not name:
        return None
    return App(name, name_fr, exec_line, wm_class, path)


def index() -> list[App]:
    apps = []
    for directory in APP_DIRS:
        if not directory.is_dir():
            continue
        for entry in sorted(directory.glob("*.desktop")):
            app = _parse(entry)
            if app:
                apps.append(app)
    return apps


def resolve(query: str) -> tuple[App | None, list[str]]:
    """Best matching application, plus the near misses worth suggesting.

    Scores exact and prefix matches first, then falls back to edit distance —
    which is what rescues a transcript: "antigraffiti" is two edits from
    "antigravity", far enough that a shared-prefix rule rejects it.
    """
    q = norm(ALIASES.get(query.strip().lower(), query))
    if not q:
        return None, []

    best: tuple[int, App] | None = None
    suggestions: list[str] = []
    for app in index():
        ident = norm(app.path.stem)
        nn = norm(app.name)
        nf = norm(app.name_fr)
        if q in (nn, nf):
            score = 4
        elif ident == q or ident.endswith(q):
            score = 3
        elif nn.startswith(q) or (nf and nf.startswith(q)):
            score = 2
        elif q in nn or (nf and q in nf) or q in ident:
            score = 1
        else:
            score = 0
        if score:
            suggestions.append(app.name)
            if best is None or score > best[0]:
                best = (score, app)
    if best:
        return best[1], suggestions

    # Nothing matched by substring: allow up to 40% of the query to be wrong.
    scored = [(edit_distance(q, norm(a.name)), a) for a in index()]
    scored.sort(key=lambda pair: pair[0])
    if scored and scored[0][0] <= max(1, int(len(q) * 0.4)):
        return scored[0][1], [a.name for _, a in scored[:5]]
    return None, [a.name for _, a in scored[:5]]


# ------------------------------------------------------------- hyprland
def ensure_hypr_env() -> bool:
    """Make sure hyprctl can find the running compositor.

    The services start at login, and on a cold boot that can happen before
    Hyprland has exported HYPRLAND_INSTANCE_SIGNATURE into the systemd user
    environment — so every launch failed with "is hyprland running?" while
    Hyprland was plainly running. Restarting the service by hand fixed it,
    which is why this never showed up in testing.

    The signature is just the name of a directory under $XDG_RUNTIME_DIR/hypr,
    so it can be recovered whenever it is needed instead of being inherited.
    """
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return True
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    base = runtime / "hypr"
    if not base.is_dir():
        return False
    live = [d for d in base.iterdir()
            if d.is_dir() and (d / ".socket.sock").exists()]
    if not live:
        return False
    newest = max(live, key=lambda d: d.stat().st_mtime)
    os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = newest.name
    return True


def hypr(*args: str) -> tuple[bool, str]:
    if not ensure_hypr_env():
        return False, "Hyprland is not running (no instance socket found)"
    try:
        p = subprocess.run(["hyprctl", *args], capture_output=True, text=True,
                           timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    out = (p.stdout or p.stderr or "").strip()
    return p.returncode == 0, out


def clients() -> list[dict]:
    """Open windows. Returns [] rather than raising: hyprctl can hand back
    truncated JSON while a window is being mapped, and losing one poll must
    never abort a launch."""
    for _ in range(4):
        ok, raw = hypr("-j", "clients")
        if ok:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = None
            if isinstance(data, list):
                return data
        time.sleep(0.05)
    return []


def windows_of(app: App) -> list[dict]:
    wanted = [norm(c) for c in app.classes]
    return [c for c in clients()
            if any(w and w in norm(c.get("class", "")) for w in wanted)]


def launch(query: str, workspace: int | None = None) -> str:
    app, suggestions = resolve(query)
    if app is None:
        near = ", ".join(dict.fromkeys(suggestions[:5]))
        return (f"FAILED: no installed application matches {query!r}."
                + (f" Closest: {near}." if near else ""))

    before = {c.get("address") for c in windows_of(app)}
    if workspace:
        ok, err = hypr("dispatch", "exec",
                       f"[workspace {workspace} silent] {app.command}")
    else:
        ok, err = hypr("dispatch", "exec", app.command)
    if not ok:
        return f"FAILED: could not start {app.name}: {err[:200]}"

    # Wait for the window, then tell the truth about where it is. A
    # single-instance application (Firefox, Discord) hands off to the process
    # already running and never opens a new window, which used to be reported
    # as a successful launch onto a workspace it had never moved to.
    deadline = time.monotonic() + 12.0
    while time.monotonic() < deadline:
        fresh = [c for c in windows_of(app) if c.get("address") not in before]
        if fresh:
            win = fresh[0]
            landed = win["workspace"]["id"]
            if workspace and landed != workspace:
                hypr("dispatch", "movetoworkspacesilent",
                     f"{workspace},address:{win['address']}")
                return f"opened {app.name} on workspace {workspace}"
            return (f"opened {app.name} on workspace {landed}"
                    if workspace else f"opened {app.name}")
        time.sleep(0.2)

    existing = windows_of(app)
    if existing:
        win = existing[0]
        landed = win["workspace"]["id"]
        if workspace and landed != workspace:
            ok, err = hypr("dispatch", "movetoworkspacesilent",
                           f"{workspace},address:{win['address']}")
            if not ok:
                return (f"FAILED: {app.name} is already open on workspace "
                        f"{landed} and could not be moved: {err[:150]}")
            return (f"{app.name} was already open on workspace {landed}; "
                    f"moved it to {workspace}")
        return f"{app.name} was already open on workspace {landed}"
    return (f"FAILED: {app.name} was started but no window appeared within "
            "12s — it may still be loading, or it may have crashed")


def find(query: str) -> str:
    app, suggestions = resolve(query)
    if app is None:
        near = ", ".join(dict.fromkeys(suggestions[:5]))
        return (f"FAILED: no installed application matches {query!r}."
                + (f" Closest: {near}." if near else ""))
    return f"{app.name} (command: {app.command}, class: {app.classes[0]})"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--find":
        print(find(" ".join(sys.argv[2:])))
    else:
        ws = int(sys.argv[2]) if len(sys.argv) > 2 else None
        print(launch(sys.argv[1], ws))
