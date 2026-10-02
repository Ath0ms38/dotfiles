#!/usr/bin/env python3
"""Nova's music control for Apple Music via Sidra (desktop app, not a browser).

Two channels:
  * transport/state  -> MPRIS (playerctl -p sidra) : instant, no page work
  * selection        -> CDP into Sidra's Electron renderer : play any
                        track/album/playlist from Apple Music or the library

Sidra must run with --remote-debugging-port; `ensure` starts it that way.

Usage:
  music.py status
  music.py play | pause | next | prev
  music.py volume <0-100|+N|-N>
  music.py play-query <text>        # search Apple Music, play best match
  music.py play-playlist <name>     # play a playlist from your library
  music.py list-playlists
  music.py ensure                   # start Sidra (silent) if needed
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

import websockets

PORT = int(os.environ.get("SIDRA_CDP_PORT", "9333"))
PLAYER = "sidra"
STORE = "fr"  # Apple Music storefront used by the desktop app


# ------------------------------------------------------------------ MPRIS
def pctl(*args: str) -> str:
    r = subprocess.run(["playerctl", "-p", PLAYER, *args],
                       capture_output=True, text=True, timeout=10)
    return r.stdout.strip() or r.stderr.strip()


def sidra_running() -> bool:
    return subprocess.run(["pgrep", "-f", "/sidra"], capture_output=True).returncode == 0


def ensure(workspace: str | None = None) -> str:
    """Start Sidra with CDP enabled, silently, if it isn't running."""
    if sidra_running():
        if cdp_ok():
            return "READY (already running)"
        return ("RUNNING_WITHOUT_CDP: restart Sidra to enable selection "
                "(quit it, then run: music.py ensure)")
    target = f"[workspace {workspace} silent] " if workspace else ""
    subprocess.run(["hyprctl", "dispatch", "exec",
                    f"{target}sidra --remote-debugging-port={PORT}"],
                   capture_output=True, timeout=10)
    for _ in range(40):
        time.sleep(0.5)
        if cdp_ok():
            return "STARTED"
    return "STARTED (CDP not ready yet)"


def cdp_ok() -> bool:
    try:
        return bool(page_targets())
    except Exception:
        return False


# -------------------------------------------------------------------- CDP
def page_targets() -> list[dict]:
    data = json.load(urllib.request.urlopen(
        f"http://127.0.0.1:{PORT}/json/list", timeout=4))
    return [t for t in data
            if t.get("type") == "page" and "music.apple.com" in t.get("url", "")]


async def _eval(ws, expr: str, mid: int, timeout: float = 30.0):
    await ws.send(json.dumps({
        "id": mid, "method": "Runtime.evaluate",
        "params": {"expression": expr, "awaitPromise": True,
                   "returnByValue": True, "userGesture": True},
    }))
    while True:
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout))
        if msg.get("id") == mid:
            res = msg.get("result", {})
            if "exceptionDetails" in res:
                raise RuntimeError(res["exceptionDetails"].get("text", "JS error"))
            return res.get("result", {}).get("value")


async def _navigate_and_run(url: str | None, script: str, settle: float = 1.5):
    """Navigate (optional), wait for the page to settle, then run script.

    Navigation destroys the JS context, so it must be a separate CDP command
    from the script that acts on the new page.
    """
    target = page_targets()
    if not target:
        raise SystemExit("ERROR: Sidra not reachable — run: music.py ensure")
    async with websockets.connect(target[0]["webSocketDebuggerUrl"],
                                  max_size=None) as ws:
        if url:
            await ws.send(json.dumps({"id": 100, "method": "Page.navigate",
                                      "params": {"url": url}}))
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                await asyncio.sleep(0.5)
                try:
                    ready = await _eval(ws, WAIT_READY, 101, timeout=8)
                except Exception:
                    continue
                if ready:
                    break
            await asyncio.sleep(settle)
        return await _eval(ws, script, 1)


WAIT_READY = """
(() => document.readyState === 'complete' &&
        document.querySelectorAll('button[data-testid="play-button"]').length > 0)()
"""

CLICK_FIRST = """
(() => {
  const btns = [...document.querySelectorAll('button[data-testid="play-button"]')];
  if (!btns.length) return {ok:false, reason:'no results'};
  btns[0].click();
  return {ok:true, label: btns[0].getAttribute('aria-label') || '', url: location.href};
})()
"""

LIST_PLAYLISTS = """
(() => {
  const links = [...document.querySelectorAll('a[href*="/library/playlist/"]')];
  const seen = new Set(), out = [];
  for (const a of links) {
    const name = (a.getAttribute('aria-label') || a.innerText || '').trim().split('\\n')[0];
    if (name && !seen.has(name)) { seen.add(name); out.push({name, href: a.getAttribute('href')}); }
  }
  return out.slice(0, 40);
})()
"""


def PLAY_PLAYLIST(name: str) -> str:
    return """
(async () => {
  const want = %s.toLowerCase();
  const norm = s => (s||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');
  const links = [...document.querySelectorAll('a[href*="/library/playlist/"]')];
  let best = null;
  for (const a of links) {
    const name = (a.getAttribute('aria-label') || a.innerText || '').trim().split('\\n')[0];
    if (!name) continue;
    const n = norm(name), w = norm(want);
    if (n === w) { best = {a, name}; break; }
    if (!best && (n.includes(w) || w.includes(n))) best = {a, name};
  }
  if (!best) return {ok:false, reason:'playlist not found',
                     available: links.slice(0,10).map(a =>
                       (a.getAttribute('aria-label')||a.innerText||'').trim().split('\\n')[0])};
  best.a.click();
  await new Promise(r => setTimeout(r, 2500));
  const btns = [...document.querySelectorAll('button[data-testid="play-button"]')];
  if (btns.length) btns[0].click();
  return {ok:true, playlist: best.name, played: btns.length > 0};
})()
""" % json.dumps(name)


# ------------------------------------------------------------------- main
def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd, args = sys.argv[1], sys.argv[2:]

    if cmd == "ensure":
        print(ensure(args[0] if args else None))
        return 0

    if cmd == "status":
        if not sidra_running():
            print("STOPPED (Sidra not running)")
            return 0
        state = pctl("status")
        meta = pctl("metadata", "--format", "{{artist}} — {{title}} ({{album}})")
        print(f"{state}: {meta}" if meta else state)
        return 0

    if cmd in ("play", "pause", "play-pause", "toggle"):
        pctl("play-pause" if cmd in ("play-pause", "toggle") else cmd)
        print(pctl("status"))
        return 0
    if cmd in ("next", "prev", "previous"):
        pctl("next" if cmd == "next" else "previous")
        time.sleep(0.6)
        print(pctl("metadata", "--format", "{{artist}} — {{title}}"))
        return 0

    if cmd == "volume":
        if not args:
            print(subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                                 capture_output=True, text=True).stdout.strip())
            return 0
        v = args[0]
        if v.startswith(("+", "-")):
            arg = f"{abs(int(v))}%{'+' if v[0] == '+' else '-'}"
        else:
            arg = f"{max(0, min(100, int(v))) / 100:.2f}"
        subprocess.run(["wpctl", "set-volume", "-l", "1",
                        "@DEFAULT_AUDIO_SINK@", arg], capture_output=True)
        print(subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                             capture_output=True, text=True).stdout.strip())
        return 0

    # ---- selection commands (need CDP)
    if cmd == "play-query":
        if not args:
            print("ERROR: play-query needs text", file=sys.stderr)
            return 2
        ensure()
        term = " ".join(args)
        url = f"https://music.apple.com/{STORE}/search?term={urllib.parse.quote(term)}"
        out = asyncio.run(_navigate_and_run(url, CLICK_FIRST))
        print(json.dumps(out, ensure_ascii=False))
        return 0 if (out or {}).get("ok") else 1

    if cmd == "list-playlists":
        ensure()
        out = asyncio.run(_navigate_and_run(
            f"https://music.apple.com/{STORE}/library/playlists", LIST_PLAYLISTS))
        for p in out or []:
            print(p["name"])
        return 0

    if cmd == "play-playlist":
        if not args:
            print("ERROR: play-playlist needs a name", file=sys.stderr)
            return 2
        ensure()
        out = asyncio.run(_navigate_and_run(
            f"https://music.apple.com/{STORE}/library/playlists",
            PLAY_PLAYLIST(" ".join(args))))
        print(json.dumps(out, ensure_ascii=False))
        return 0 if (out or {}).get("ok") else 1

    print(f"ERROR: unknown command '{cmd}'", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
