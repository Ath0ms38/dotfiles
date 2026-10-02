---
description: Record a call, meeting or memo (system audio + mic), transcribe it locally and summarise it.
---

# Record & transcribe

Captures **both** what is playing (Discord, Zoom, browser — any app) and the
microphone, so both sides of a conversation end up in the transcript.
Transcription runs locally on the GPU: the audio never leaves the machine.

## "record this" / "record the call"

1. `record_audio_start(name)` — pick a short name from context
   (`discord-alex`, `meeting`).
2. Confirm in your reply. Do not notify separately.
3. Do nothing else. It records until asked to stop.

## "stop recording"

1. `record_audio_stop()` — mixes the tracks and transcribes. This takes a
   while on a long recording; that is normal, not a hang.
2. `read_transcript(<session>)`.
3. Write a summary next to it with `write_file(<dir>/summary.md, …)`:
   topics, decisions, action items with who and when, anything the user
   promised to do. Match the transcript's language — usually French.
4. Reply with a two-line gist. The user reads the full summary later.

## Screen

- `record_screen_start(name)` records the focused monitor.
- `record_screen_start(name, region=True)` shows a crosshair so the **user**
  drags the region — you do not choose it.
- `record_screen_stop()` returns the video path;
  `record_screen_stop(with_audio=<wav>)` muxes an audio track into it.

## Rules

- Never start a recording on your own initiative.
- If asked to record while already recording, check `record_audio_status()`
  and say so instead of starting a second one.
- Recordings live in `~/.local/share/nova/recordings/<session>/`.
