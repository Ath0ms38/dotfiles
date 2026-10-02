#!/usr/bin/env python3
"""Nova MCP server — finding and reading files.

`run_command` could do all of this with find/grep, but the model composes
those wrong often enough (quoting, -iname vs -name, missing -type) that a
typed tool is simply more reliable. Results are capped so a bad pattern
cannot flood the context.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from mcp.server import MCPServer

HOME = Path.home()
server = MCPServer("nova-files")

# Never worth searching, always huge.
PRUNE = ["node_modules", ".git", ".cache", "venv", ".venv", "__pycache__",
         "target", "dist", "build"]


def _root(directory: str) -> Path | None:
    if not directory:
        return HOME
    d = Path(directory).expanduser()
    if d.is_dir():
        return d
    hits = [h for h in HOME.glob(f"*{Path(directory).name}*") if h.is_dir()]
    return hits[0] if hits else None


@server.tool()
def find_files(pattern: str, directory: str = "", limit: int = 30) -> str:
    """Find files by name under a directory (case-insensitive).

    Args:
        pattern: name fragment or glob, e.g. "budget", "*.pdf", "config.yaml"
        directory: where to search; defaults to the home directory
        limit: maximum number of results
    """
    root = _root(directory)
    if root is None:
        return f"FAILED: directory not found: {directory}"
    if "*" not in pattern and "?" not in pattern:
        pattern = f"*{pattern}*"
    argv = ["find", str(root), "("]
    for i, name in enumerate(PRUNE):
        argv += ([] if i == 0 else ["-o"]) + ["-name", name]
    argv += [")", "-prune", "-o", "-iname", pattern, "-print"]
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return "FAILED: search timed out — narrow it down with `directory`"
    hits = [line for line in p.stdout.splitlines() if line][:limit]
    if not hits:
        return f"no file matching {pattern!r} under {root}"
    return "\n".join(hits) + (f"\n…({limit} shown)" if len(hits) == limit else "")


@server.tool()
def search_text(text: str, directory: str = "", limit: int = 30) -> str:
    """Search for a string inside files; returns file:line matches.

    Args:
        text: the string to look for
        directory: where to search; defaults to the home directory
        limit: maximum number of matches
    """
    root = _root(directory)
    if root is None:
        return f"FAILED: directory not found: {directory}"
    argv = ["grep", "-rniI", "--color=never"]
    for name in PRUNE:
        argv += [f"--exclude-dir={name}"]
    argv += ["-m", "3", "-e", text, str(root)]
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return "FAILED: search timed out — narrow it down with `directory`"
    hits = [line[:200] for line in p.stdout.splitlines() if line][:limit]
    return "\n".join(hits) if hits else f"no file containing {text!r} under {root}"


@server.tool()
def read_file(path: str, max_chars: int = 4000) -> str:
    """Read a text file.

    Args:
        path: full path, ~ is expanded
        max_chars: truncate beyond this many characters
    """
    f = Path(path).expanduser()
    if not f.is_file():
        return f"FAILED: not a file: {path}"
    try:
        text = f.read_text(errors="replace")
    except OSError as e:
        return f"FAILED: {e}"
    return text[:max_chars] + ("\n…(truncated)" if len(text) > max_chars else "")


@server.tool()
def write_file(path: str, content: str) -> str:
    """Write a text file, creating parent folders as needed. Overwrites.

    Args:
        path: full path, ~ is expanded
        content: the file's new content
    """
    f = Path(path).expanduser()
    try:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
    except OSError as e:
        return f"FAILED: {e}"
    return f"wrote {len(content)} chars to {f}"


@server.tool()
def disk_usage(directory: str = "", limit: int = 12) -> str:
    """Biggest subfolders of a directory.

    Args:
        directory: defaults to the home directory
        limit: how many entries to show
    """
    root = _root(directory)
    if root is None:
        return f"FAILED: directory not found: {directory}"
    p = subprocess.run(["du", "-h", "--max-depth=1", str(root)],
                       capture_output=True, text=True, timeout=120)
    rows = sorted(
        (line.split("\t") for line in p.stdout.splitlines() if "\t" in line),
        key=lambda r: _to_bytes(r[0]), reverse=True)[:limit]
    return "\n".join(f"{size}\t{path}" for size, path in rows) or "nothing found"


def _to_bytes(human: str) -> float:
    units = {"K": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}
    try:
        return float(human[:-1]) * units.get(human[-1], 1)
    except ValueError:
        return 0.0


if __name__ == "__main__":
    server.run()
