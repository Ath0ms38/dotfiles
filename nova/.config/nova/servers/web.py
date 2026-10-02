#!/usr/bin/env python3
"""Nova MCP server — web search and page reading.

Search goes through Groq's `compound` model, which runs the search server-side
and returns an answer with its sources. That avoids a second API key and a
scraper to maintain, and it costs one request instead of "search, then fetch
five pages, then summarise".
"""
from __future__ import annotations

import json
import re
import time
import os
import urllib.error
import urllib.request
from pathlib import Path

from mcp.server import MCPServer

API_URL = "https://api.groq.com/openai/v1/chat/completions"
SEARCH_MODEL = os.environ.get("NOVA_SEARCH_MODEL", "groq/compound")
SECRETS = Path.home() / ".config/nova/secrets.env"

server = MCPServer("nova-web")


def api_key() -> str:
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    for line in SECRETS.read_text().splitlines():
        if line.startswith("GROQ_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("GROQ_API_KEY not found")


@server.tool()
def search(query: str) -> str:
    """Look something up on the web, or read a page whose URL you have.
    Returns a short answer with its sources. Use it for anything you cannot
    know: current events, versions, prices, weather, documentation.

    Args:
        query: the question, or "summarise <url>" to read a specific page
    """
    body = json.dumps({
        "model": SEARCH_MODEL,
        "messages": [
            {"role": "system",
             "content": "Answer in 2-3 sentences, in the language of the "
                        "question, then list the source URLs."},
            {"role": "user", "content": query},
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": "application/json",
                 # default python-urllib UA gets 403'd by Cloudflare (1010)
                 "User-Agent": "nova-web/0.1"})
    # compound runs on gpt-oss-120b underneath, so a search competes for the
    # very quota the agent spends picking tools — 429 here is routine rather
    # than exceptional, and worth waiting out instead of failing the command.
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            return (data["choices"][0]["message"].get("content") or "").strip()
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:300]
            if e.code == 429 and attempt < 2:
                m = re.search(r"try again in ([\d.]+)s", detail)
                time.sleep(min(float(m.group(1)) + 0.3 if m else 3.0, 25.0))
                continue
            return f"FAILED: search error {e.code}: {detail[:200]}"
        except (urllib.error.URLError, OSError) as e:
            return f"FAILED: no network ({e})"
    return "FAILED: search unavailable (quota) — try again shortly"


if __name__ == "__main__":
    server.run()
