# Nova ✨ — personal voice assistant

Always-on, bilingual (FR/EN), voice-first assistant for this machine
(EndeavourOS + Hyprland). Say "Nova", ask for something, get a notification
back — spoken aloud only when asked.

Everything runs locally except two API calls: speech-to-text and the model
itself, both on Groq.

## Architecture

```
       microphone
           │  pw-record, 16 kHz mono s16
           ▼
  ┌─────────────────┐   Silero VAD cuts the stream into utterances, then a
  │  listener.py    │   French streaming ASR answers one question: does this
  └────────┬────────┘   start with "Nova"?
           │  wav of the whole utterance, only if it did
           ▼
     Groq whisper-large-v3-turbo      (local whisper.cpp if offline)
           │  text
           ▼
  ┌─────────────────┐   unix socket ~/.local/state/nova/novad.sock
  │    novad.py     │   model loop + session (expires after 1 h idle)
  └────────┬────────┘
           │  MCP over stdio, servers kept warm
           ▼
   desktop · shell · files · web · skills   (always available)
   music · media                            (unlocked by their skill)
           │
           ▼
     reply → notification, and speech if the request asked for it
```

Three processes, no framework: a listener, a daemon, and seven small MCP
servers. The daemon exists so the servers start once instead of once per
command, and so a follow-up question lands in the same conversation.

## Files

| Path | What |
|---|---|
| `listener.py` | wake word, endpointing, speech-to-text, speech output |
| `novad.py` | the agent: MCP client, tool loop, session, unix socket |
| `nova.py` | tiny client — `nova.py "ouvre firefox dans le workspace 5"` |
| `mcp.json` | which MCP servers to start, and which skill gates each one |
| `nova.env` | model and thresholds (not secrets) |
| `secrets.env` | `GROQ_API_KEY=…`, gitignored — the repo is public |
| `servers/` | the MCP servers, one per domain |
| `skills/` | markdown procedures, loaded on demand |

| `wakeword/` | test_gate.py — checks the wake word against real speech |

## Why the tools are MCP servers

They were prose-driven shell scripts before, described to the model in a
17 000-token prompt. That prompt alone exceeded Groq's free-tier limit of
12 000 tokens per minute, so every command fell back to a slow model, and the
model composed shell lines from prose — which is where "opened two terminals",
"lost the workspace number" and "launched the wrong app" all came from.

Typed tools fix the composition problem. MCP fixes the reuse problem: the same
seven servers work with any MCP client, and swapping the loop for something
else later does not touch them.

## Skill-gated tools

39 tools cost ~6000 tokens of schema, which blows the per-minute budget on a
two-step turn. So a server can declare a `skill` in `mcp.json`: its tools stay
out of the prompt until the model loads that skill. `music` and `media` are
gated this way, which keeps the resident set at 23 tools / ~2500 tokens.
Loading the skill returns the procedure *and* attaches the tools in the same
step, and the unlock is reset at the start of every turn.

## Latency and quotas

A command is ~0.6 s end to end. Nothing in the tooling is slow — `wpctl`
answers in 7 ms, a verified terminal command in 0.19 s. The only thing that
ever makes Nova wait is Groq's free tier, which is metered in **tokens per
minute, per model**. Four things keep her under it:

- **Schemas are not resent once a tool has run.** The second call only has to
  phrase a sentence, so it goes out without the tool list: ~750 tokens instead
  of ~2500. They come back if the tool failed, so she can still repair.
- **The phrasing call uses a different model**, and therefore a different
  budget. It must still be a capable one — llama-3.1-8b reported "Volume:
  1.00" verbatim and claimed it could not see a window list it had been given.
- **Quota-aware switching.** Every response carries
  `x-ratelimit-remaining-tokens`; when a model runs low the next one in
  `TOOL_MODELS` takes over, so being throttled costs a model change rather
  than a wait.

Free-tier budgets are metered **per minute and per day**, and the two disagree
about which model is best:

  | model | /min | /day | cost per Nova call |
  |---|---|---|---|
  | gpt-oss-120b | 8K | 200K | 2246 |
  | qwen3.6-27b | 8K | 200K | 3783 |
  | llama-3.3-70b | 12K | **100K** | 2300 |
  | gpt-oss-20b | 8K | 200K | (phrasing only) |
  | compound | 70K | — | runs on gpt-oss-120b |

  Ordering by the per-minute column puts llama-3.3 first, and it is then the
  first to die: its daily budget is half everyone else's. Ordering by daily
  budget suggests qwen, which spends 3783 tokens where gpt-oss-120b spends
  2246 and so empties its window in two calls. Cost per call decides.
- **Six turns of history are replayed**, out of the whole conversation that is
  kept and archived.

There is no prompt caching on the free tier — three identical requests each
cost the full prompt, verified. Reorganising the prompt saves nothing; only
sending less does.

One collision worth knowing: `groq/compound`, which powers web search, runs on
gpt-oss-120b underneath. A search therefore competes with tool selection for
the same budget, which is why `web.py` retries on 429 rather than failing.

## Voice

Two different models, deliberately. The local one is a **gate**: it is only
ever asked whether an utterance opens with the name, so the fact that it hears
"quelle heure est-il" as "KELLART EST IL" costs nothing. Whisper, which is
accurate, is only called on utterances that passed the gate — so ordinary
conversation, calls and videos never leave the machine and cost neither a
request nor any latency.

- **Endpointing** — Silero VAD answers "is this speech", which is the actual
  question. Energy thresholds needed recalibrating for every mic and room.
  ~1 % of one core at idle.
- **Wake gate** — `sherpa-onnx-streaming-zipformer-fr`, a pretrained French
  ASR, run over each utterance (25× real time on CPU). Matching is fuzzy: one
  edit from "nova", since both recognisers mangle proper nouns. Scored 12/12 on
  a set of six real commands and six ordinary sentences including "nouveau",
  "ne va pas", "novembre", and a mid-sentence mention of Nova.
- **Speech-to-text** — Groq's API. A resident local whisper cost 922 MB of VRAM
  permanently; whisper.cpp stays as the offline fallback and for long
  recordings, where latency does not matter and the audio should not leave the
  machine.
- **Speaking** — Kokoro, and only when the request asked for it.

### Why not a trained wake-word model

The first attempt trained an openWakeWord detector on the name. It never fired:
final recall 1 %. The cause was not the training recipe but the data. The piper
sample generator ships no French checkpoint config, and the one reconstructed
by hand fed the model wrong phoneme ids — so it emitted five seconds of babble
per clip instead of the word. Both classes were babble, which is why a linear
probe separated them at only 65 %.

The lesson is cheap to state and was expensive to learn: **verify what
generated audio says, not that it exists**. Clip duration alone was the tell —
0.6 s for one word, 5.3 s for the broken ones — and it was visible from the
first six samples.

A pretrained ASR sidesteps the whole problem. There is no dataset, no
augmentation, no training; changing the wake word is changing a string. The
price is 400 MB of model on disk against 84 KB, and CPU instead of near-zero.

## Setup on a fresh machine

```bash
cd ~/dotfiles && stow nova

# runtime venv
uv venv ~/.local/share/nova/venv --python 3.12
uv pip install --python ~/.local/share/nova/venv/bin/python \
    mcp numpy onnxruntime websockets kokoro-onnx sherpa-onnx \
    "openwakeword @ file://$HOME/.local/share/oww-train/oww-src"
# only for the Silero VAD it bundles
~/.local/share/nova/venv/bin/python -c \
    "from openwakeword.utils import download_models; download_models()"

# French ASR used as the wake gate (~400 MB)
cd ~/.local/share/nova && curl -LO \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-fr-2023-04-14.tar.bz2 \
  && tar xjf sherpa-onnx-streaming-zipformer-fr-2023-04-14.tar.bz2

# secrets (chmod 600) — never committed
printf 'GROQ_API_KEY=…\n' > ~/.config/nova/secrets.env

systemctl --user enable --now novad nova-voice
```

## Changing the wake word

Set `WAKE_WORD` in `listener.py`. There is nothing else to do — no data, no
training. Check it against ordinary speech first: `wakeword/` holds the script
that runs candidate phrases through the gate and reports accept/reject.

Words to avoid: anything within one edit of a common French word. "Nova" is
already close to "ne va", which is why the two-word glue rule demands an exact
match rather than a fuzzy one.

## Troubleshooting

| Symptom | Cause |
|---|---|
| novad starts, logs nothing, never opens its socket | an exception escaping the MCP startup block; the stdio task groups then never exit and the process hangs in asyncio shutdown, silently |
| No log output at all | the MCP SDK installs a root log handler at import — `basicConfig` needs `force=True` |
| `ModuleNotFoundError: mcp.server.fastmcp` | a local directory named `mcp/` shadows the package; that is why the servers live in `servers/` |
| Tool result is invalid JSON | a truncation limit applied to `hyprctl -j` output |
| `LLM error 429` | 12 000 tokens/minute on the free tier; the daemon waits and retries |
| Wake word never fires | check `journalctl --user -u nova-voice`: the gate logs what it heard, so you can see whether the ASR caught the name or the VAD never cut an utterance |
