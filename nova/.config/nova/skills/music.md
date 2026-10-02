---
description: Play anything from Apple Music through the Sidra desktop app — tracks, albums, playlists, transport.
---

# Music (Apple Music via Sidra)

Sidra is the user's Apple Music **desktop app**, not a browser tab. The
`nova-music` tools drive it.

## Which tool to use

- `play` / `pause` / `next_track` / `previous_track` / `now_playing` go over
  MPRIS: instant. When the user just means "pause" or "skip", use these —
  never re-select a track to achieve a transport action.
- `play_track` and `play_playlist` navigate the app's UI, so they take a few
  seconds. Say what you started playing once it worked.
- `list_playlists` when a name doesn't match: offer the closest one instead
  of guessing silently.

## Rules

- Never change what is playing unless asked.
- If Sidra is closed, the play tools start it silently — no need to launch it
  yourself first.
- Volume is not a music tool: use `volume` from `nova-desktop`, it controls
  the system sink.
- Known playlists include: Morceaux préférés, belle, En boucle, josie,
  musiccccccc, sport, ukulele — re-check with `list_playlists` rather than
  trusting this list.
