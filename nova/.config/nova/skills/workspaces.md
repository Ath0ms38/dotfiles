---
description: Tidy the Hyprland workspaces — move stray windows back to the slot each app belongs to.
---

# Organising workspaces

The assignment lives in `~/.config/fabric/config.json` under
`special_workspaces`: it maps a name to a workspace id and a window class.
That file is the source of truth — the fabric bar reads it too, so never
invent an assignment that is not in it.

## "organise my workspaces"

1. `read_file("~/.config/fabric/config.json")` and read `special_workspaces`.
2. `list_windows()` to see where everything currently is.
3. For each window whose class has an assigned slot but sits elsewhere,
   `move_window(<class>, <id>)`. This is silent — the user's view does not
   move.
4. Report what you moved, in one sentence. If nothing was out of place, say
   that instead of inventing work.

## Rules

- Never switch the visible workspace or steal focus while tidying.
- Windows whose class has no assignment are left alone — they are not
  "misplaced", they are unassigned.
- If a window matches several assignments, leave it and mention it.
