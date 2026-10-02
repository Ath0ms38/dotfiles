#!/usr/bin/env python3
"""Nova MCP server — skills.

A skill is a markdown file describing how to carry out one kind of task. Only
the index (name + one-line summary) is ever in the prompt; the body is fetched
when the task actually calls for it. That is the whole point: OpenClaw put
everything in the prompt every turn, 17K tokens, which blew past the free
tier's rate limit before Nova had done anything.

Skills live in ~/.config/nova/skills/*.md with front matter:

    ---
    description: one line, shown in the index
    ---
    the procedure…
"""
from __future__ import annotations

import re
from pathlib import Path

from mcp.server import MCPServer

SKILLS = Path.home() / ".config/nova/skills"
server = MCPServer("nova-skills")

_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def _parse(path: Path) -> tuple[str, str]:
    """Returns (description, body)."""
    text = path.read_text(errors="replace")
    m = _FRONT.match(text)
    if not m:
        return "", text.strip()
    desc = ""
    for line in m.group(1).splitlines():
        if line.lower().startswith("description:"):
            desc = line.split(":", 1)[1].strip()
    return desc, text[m.end():].strip()


def index() -> list[tuple[str, str]]:
    if not SKILLS.is_dir():
        return []
    return sorted((p.stem, _parse(p)[0]) for p in SKILLS.glob("*.md"))


@server.tool()
def list_skills() -> str:
    """List the available skills and what each one covers."""
    entries = index()
    if not entries:
        return "no skills installed"
    return "\n".join(f"{name}: {desc}" for name, desc in entries)


@server.tool()
def load_skill(name: str) -> str:
    """Load a skill's full instructions before doing that kind of task.

    Args:
        name: the skill name as shown by list_skills
    """
    path = SKILLS / f"{name}.md"
    if not path.is_file():
        matches = sorted(SKILLS.glob(f"*{name}*.md"))
        if not matches:
            return (f"FAILED: no skill named {name!r}. Available: "
                    + ", ".join(n for n, _ in index()))
        path = matches[0]
    return _parse(path)[1]


if __name__ == "__main__":
    server.run()
