---
description: Scaffold a new dev project (Python/uv by default) with git, and optionally give it a Hyprland workspace.
---

# New project

## Ask only for what is missing

- **name** — kebab-case.
- **type** — python (default, uses uv), node, rust, other.
- **location** — there is no established projects directory on this machine
  yet. The first time, ask where projects should live (suggest `~/Projects`),
  then record the answer by appending it to this skill file so you never ask
  again.

## Python (default)

```bash
mkdir -p <projects-dir>/<name> && cd <projects-dir>/<name>
uv init --name <name>
git init -b main
git add -A && git commit -m "Initial scaffold"
```

uv writes `pyproject.toml`, `.python-version` and creates the venv on the
first `uv run` / `uv sync` — do not create a `requirements.txt`.

Node is `npm init -y`, Rust is `cargo new`; same git flow.

Add a `README.md` with a one-line description. If you do not know what the
project is for, ask — one question, not a questionnaire.

## Rules

- Run all of this with `run_command`, in the background. Only open a terminal
  if the user asked to watch it happen.
- Never scaffold inside `~/dotfiles`.
- Open an editor only if asked, and silently: `launch_app("code", workspace=12)`.

## Optional: its own workspace

Giving a project a Hyprland workspace slot means editing
`~/.config/fabric/config.json` (`special_workspaces`), and the window rules in
`~/dotfiles/hyprland/.config/hypr/conf/rules.conf` must be kept in sync by
hand. Show the planned edit before applying it. The fabric bar needs
`~/.config/fabric/restart.sh` afterwards — warn that the bar reloads briefly.
