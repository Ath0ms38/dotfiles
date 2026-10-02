#!/usr/bin/env python3
"""Nova — always-on French voice listener.

  pw-record (16 kHz mono s16)
    -> Silero VAD cuts the stream into utterances
    -> French streaming ASR (sherpa-onnx zipformer) answers ONE question:
       does this utterance start with "Nova"?
    -> if it does, the same audio goes to Groq whisper for the real
       transcription, and the command goes to novad
    -> reply as a notification, spoken aloud only when asked

The gate and the transcription are deliberately different models. The local
one is only ever asked for a yes/no on the first word, so its mangling of the
rest ("KELLART EST IL" for "quelle heure est-il") costs nothing; whisper, which
is accurate, is only called on utterances that passed the gate. Everything that
does not start with the name — conversations, calls, videos — never leaves the
machine and costs neither a request nor any latency.

This replaces a trained openWakeWord detector. Training one needs tens of
thousands of synthetic examples of the word, and the French speech synthesiser
available for that produced five seconds of babble per clip instead of the
word, which no amount of tuning could rescue. A pretrained French ASR sidesteps
the whole problem: changing the wake word here is changing a string.
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.request
import uuid
import wave
from collections import deque
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------- config
RATE = 16000
FRAME = 1280                      # 80 ms
VAD_FRAME = 640                   # 40 ms, divides FRAME exactly

NOVA_DIR = Path.home() / ".config/nova"
STATE_DIR = Path.home() / ".local/state/nova"
PAUSE_FILE = STATE_DIR / "paused"
SECRETS = NOVA_DIR / "secrets.env"

sys.path.insert(0, str(NOVA_DIR))
from nova import ask  # noqa: E402  — talks to novad over its unix socket

ASR_DIR = Path(os.environ.get(
    "NOVA_ASR_MODEL",
    Path.home() / ".local/share/nova/sherpa-onnx-streaming-zipformer-fr-2023-04-14"))
ASR_SUFFIX = "epoch-29-avg-9-with-averaged-model.int8.onnx"

WAKE_WORD = "nova"
# Whisper and the local ASR both mangle proper nouns; anything one edit away
# from the name counts. Bounded by length so "novembre" cannot match.
WAKE_MAX_EDITS = int(os.environ.get("NOVA_WAKE_EDITS", "1"))
WAKE_LEAD_WORDS = 2               # how far into the utterance to look

# After answering "Oui ?" she is explicitly waiting, so the next utterance is
# taken without the name — saying "Nova" twice in a row is not how anyone
# talks.
FOLLOWUP_SECONDS = float(os.environ.get("NOVA_FOLLOWUP", "12"))

# Which microphone to hold open. "default" follows the system default source,
# which is the headset when it is on — that is what you want, since it hears
# you best. Set to a node name from `pactl list sources short` to pin one.
MIC = os.environ.get("NOVA_MIC", "default")

# Listening permanently keeps a wireless headset awake: its power-off timer
# only runs once nothing holds its microphone. So when the machine goes idle,
# the capture is released entirely and reopened on the first sign of activity.
# hypridle writes this file (see hypridle.conf).
IDLE_FILE = Path.home() / ".local/state/nova/idle"

PREROLL = 0.5                     # s of audio kept before speech starts
# How long a pause may last before the sentence is treated as finished. 0.8 s
# cut people off mid-thought — "va dans mes documents… crée un dossier" is one
# instruction with a pause in it, not two. Longer when she has answered "Oui ?"
# and is expecting a whole instruction rather than a short follow-up.
SILENCE_HANGOVER = float(os.environ.get("NOVA_SILENCE", "1.3"))
SILENCE_HANGOVER_AWAITED = SILENCE_HANGOVER + 0.7
MIN_UTTERANCE = 0.4               # s — shorter than this is a cough
MAX_UTTERANCE = 20.0
SPEECH_PROB = float(os.environ.get("NOVA_VAD_PROB", "0.35"))
SPEECH_FRAMES = 2                 # consecutive voiced frames to start
# Quiet speech is the hard case: the VAD scores it low and both recognisers
# hear it badly. A fixed gain on every frame helps the VAD notice you at all;
# normalising the finished utterance to a healthy level is what makes the
# recognisers read it. Gain is applied with clipping guarded, so a shout does
# not turn to distortion.
MIC_GAIN = float(os.environ.get("NOVA_MIC_GAIN", "3.0"))
NORMALISE_PEAK = 0.7              # of full scale, before recognition

# Whisper invents these out of near-silence — never act on them.
_HALLUCINATIONS = re.compile(
    r"^\W*(?:thank you|thanks(?: for watching)?|merci(?: beaucoup"
    r"| d'avoir regard[ée].*)?|sous-titr\w+.*|subtitles?.*|amara\.org.*"
    r"|you|vous|\d{1,3}|bye|au revoir|\.\.\.|music|musique|applause"
    r"|applaudissements)\W*$", re.I)

# Speak replies aloud only when asked (NOVA_SPEAK=off|auto|always)
SPEAK_MODE = os.environ.get("NOVA_SPEAK", "auto")
SPEAK_RE = re.compile(
    r"(voix haute|à voix|a voix|à l'oral|a l'oral|oralement|vocalement|"
    r"en parlant|dis[- ]le|dis[- ]moi|réponds[- ]moi à|out loud|aloud|"
    r"say it|tell me out|speak)", re.IGNORECASE)

STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
STT_MODEL = os.environ.get("NOVA_STT_MODEL", "whisper-large-v3-turbo")
# Vocabulary bias. A bare word list is not enough — "dans le workspace cinq"
# came back as "dans les espèces sains" — so the terms appear in context. But
# full commands are dangerous here: with "Nova, déplace Discord sur le
# workspace onze" in the prompt, 1.4 s of audio came back as "Nова, misère
# Discord sur le workspace, Nova" and that fabricated order was executed.
# Fragments give the vocabulary without handing whisper a command to echo.
STT_PROMPT = ("Nova. Le workspace cinq, le workspace onze. Firefox, Vivaldi, "
              "Antigravity, kitty, btop, Discord, Sidra, OBS, Hyprland, "
              "EndeavourOS.")
# Speech runs at roughly 15 characters a second, 18 when hurried; well past
# that the model is inventing rather than transcribing. Catches hallucinations
# whatever their wording, which an exact-echo test cannot. Tuned so the real
# case above (44 characters out of 1.4 s) is rejected.
MAX_CHARS_PER_SECOND = 22
WHISPER_MODEL = Path.home() / ".local/share/whisper/ggml-large-v3-turbo-q5_0.bin"

KOKORO_DIR = Path.home() / ".local/share/kokoro"
KOKORO_VOICES = {"fr": ("ff_siwis", "fr-fr"), "en": ("af_heart", "en-us")}
_FR_HINTS = (" le ", " la ", " les ", " est ", " je ", " tu ", " pas ", " une ",
             " des ", " et ", " à ", " que ", "ç", "é", "è", "ê", " d'", " l'")

log = logging.getLogger("nova")

# While Nova is speaking, ignore what the microphone hears of her own voice.
_suppress_until = 0.0
# Set after "Oui ?": until then, the next utterance needs no wake word.
_awaiting_until = 0.0


# ---------------------------------------------------------------- output
_notif_id: str | None = None


def notify(body: str, urgency: str = "low") -> None:
    """One evolving notification bubble: each message replaces the previous."""
    global _notif_id
    cmd = ["notify-send", "-p", "-u", urgency, "Nova ✨", body]
    if _notif_id:
        cmd += ["-r", _notif_id]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    nid = out.stdout.strip()
    if nid.isdigit():
        _notif_id = nid


def amplify(pcm: bytes, gain: float) -> bytes:
    """Scale 16-bit PCM, saturating instead of wrapping around."""
    if gain == 1.0:
        return pcm
    samples = np.frombuffer(pcm, np.int16).astype(np.float32) * gain
    return np.clip(samples, -32768, 32767).astype(np.int16).tobytes()


def normalise(pcm: bytes) -> bytes:
    """Bring an utterance up to a healthy level before recognition.

    Speaking quietly used to be enough to lose a command: the audio was
    perfectly intelligible, just low, and both the wake gate and whisper do
    noticeably worse on it. Silence is left alone — amplifying it would only
    raise the noise floor.
    """
    samples = np.frombuffer(pcm, np.int16).astype(np.float32)
    peak = float(np.abs(samples).max()) if samples.size else 0.0
    if peak < 200:                       # nothing but room noise
        return pcm
    gain = min(NORMALISE_PEAK * 32767 / peak, 8.0)
    if gain <= 1.0:
        return pcm
    return np.clip(samples * gain, -32768, 32767).astype(np.int16).tobytes()


def to_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm)
    return buf.getvalue()


# ------------------------------------------------------------ wake gate
def _fold(word: str) -> str:
    """lowercase, strip accents and punctuation."""
    return "".join(c for c in unicodedata.normalize("NFD", word.lower())
                   if c.isalpha() and unicodedata.category(c) != "Mn")


def _edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _is_name(word: str) -> bool:
    w = _fold(word)
    if not (3 <= len(w) <= len(WAKE_WORD) + 1):
        return False
    return _edit_distance(w, WAKE_WORD) <= WAKE_MAX_EDITS


def starts_with_wake(text: str) -> bool:
    """Does this utterance open with the name?

    Only the first couple of words are considered: "Nova, mets la musique" is
    for her, "je pense que Nova pourrait" is not. An optional "hey" or "ok" is
    allowed in front, and the name split in two ("no va") is accepted since
    both recognisers do that.
    """
    words = [w for w in re.split(r"[\s,.!?:;–—]+", text) if w]
    if not words:
        return False
    start = 1 if _fold(words[0]) in ("hey", "he", "ok", "okay", "eh") else 0
    for i in range(start, min(start + WAKE_LEAD_WORDS, len(words))):
        if _is_name(words[i]):
            return True
        # Two words glued back together, for when the recogniser splits the
        # name into "No va". This one must match exactly: at one edit of
        # tolerance it also swallows "Ne va pas trop vite", which is an
        # ordinary French sentence and was firing on it.
        if i + 1 < len(words) and _fold(words[i] + words[i + 1]) == WAKE_WORD:
            return True
        # The recogniser sometimes runs the name into what follows —
        # "NOVADISCAR" for "Nova, déplace Discord". Only the opening word is
        # allowed to match this way, so "novembre" (nov-, not nova-) and a
        # mid-sentence mention are both still rejected.
        if i == start and _fold(words[i]).startswith(WAKE_WORD):
            return True
    return False


def strip_wake(text: str) -> str:
    """Remove the leading name so the agent gets the command alone."""
    parts = re.split(r"([\s,.!?:;–—]+)", text)
    out, dropped = [], False
    for part in parts:
        if not dropped and part.strip() and _is_name(part):
            dropped = True
            continue
        if dropped or not part.strip() or out:
            out.append(part)
    return "".join(out).lstrip(" ,.!?:;–—").strip()


class WakeGate:
    """The local French ASR, used only to decide whether an utterance is
    addressed to Nova."""

    def __init__(self) -> None:
        import sherpa_onnx
        self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=str(ASR_DIR / "tokens.txt"),
            encoder=str(ASR_DIR / f"encoder-{ASR_SUFFIX}"),
            decoder=str(ASR_DIR / f"decoder-{ASR_SUFFIX}"),
            joiner=str(ASR_DIR / f"joiner-{ASR_SUFFIX}"),
            num_threads=2, provider="cpu", decoding_method="greedy_search",
        )

    def transcribe(self, pcm: bytes) -> str:
        audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
        # Silence on both sides. Trailing, because a streaming transducer will
        # not commit to its last word without audio after it. Leading, because
        # without it the encoder is still settling when speech starts and whole
        # utterances decode to the empty string — that alone was two of three
        # missed wakes in testing.
        audio = np.concatenate([np.zeros(RATE // 2, np.float32), audio,
                                np.zeros(RATE, np.float32)])
        stream = self.recognizer.create_stream()
        for i in range(0, len(audio), FRAME):
            stream.accept_waveform(RATE, audio[i:i + FRAME])
            while self.recognizer.is_ready(stream):
                self.recognizer.decode_stream(stream)
        stream.input_finished()
        while self.recognizer.is_ready(stream):
            self.recognizer.decode_stream(stream)
        return self.recognizer.get_result(stream)


# ---------------------------------------------------------------- STT
def api_key() -> str | None:
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    try:
        for line in SECRETS.read_text().splitlines():
            if line.startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return None


def _multipart(fields: dict[str, str], wav: bytes) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; '
                     f'name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; '
                 f'name="file"; filename="command.wav"\r\n'
                 f'Content-Type: audio/wav\r\n\r\n'.encode())
    parts.append(wav)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def _transcribe_api(pcm: bytes) -> tuple[str, str | None] | None:
    key = api_key()
    if not key:
        return None
    body, content_type = _multipart(
        {"model": STT_MODEL, "response_format": "verbose_json",
         "temperature": "0", "prompt": STT_PROMPT},
        to_wav(pcm))
    req = urllib.request.Request(
        STT_URL, data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": content_type,
                 # default python-urllib UA gets 403'd by Cloudflare (1010)
                 "User-Agent": "nova-listener/0.2"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            meta = json.load(r)
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        log.warning("Groq STT unavailable (%s) — falling back to local", exc)
        return None
    lang = str(meta.get("language", "")).lower()
    lang = {"fr": "fr", "french": "fr", "français": "fr",
            "en": "en", "english": "en"}.get(lang)
    return (meta.get("text") or "").strip(), lang


def _transcribe_local(pcm: bytes) -> tuple[str, str | None]:
    """Offline fallback — whisper.cpp, loaded on demand (no resident GPU)."""
    binary = shutil.which("whisper-cli") or shutil.which("whisper-cpp")
    if binary is None or not WHISPER_MODEL.exists():
        notify("Pas de réseau et whisper.cpp indisponible.", "critical")
        return "", None
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    base = STATE_DIR / f"cmd-{int(time.time() * 1000)}"
    base.with_suffix(".wav").write_bytes(to_wav(pcm))
    try:
        subprocess.run(
            [binary, "-m", str(WHISPER_MODEL), "-l", "auto",
             "-f", str(base.with_suffix(".wav")), "-otxt", "-oj",
             "-of", str(base)],
            check=True, capture_output=True, timeout=120)
        text = base.with_suffix(".txt").read_text().strip()
        lang = None
        try:
            meta = json.loads(base.with_suffix(".json").read_text())
            lang = meta.get("result", {}).get("language")
        except (OSError, json.JSONDecodeError):
            pass
        return text, lang if lang in ("fr", "en") else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        log.error("local whisper failed: %s", exc)
        return "", None
    finally:
        for suffix in (".wav", ".txt", ".json"):
            base.with_suffix(suffix).unlink(missing_ok=True)


def _is_prompt_echo(text: str) -> bool:
    """Did whisper read our own vocabulary bias back to us? Only a
    near-complete recitation counts — a real command legitimately overlaps the
    bias, which is the whole point of it."""
    def letters(s: str) -> str:
        return " ".join("".join(c for c in s.lower()
                                if c.isalnum() or c == " ").split())

    t, p = letters(text), letters(STT_PROMPT)
    return len(t) > 0.6 * len(p) and t in p


def transcribe(pcm: bytes) -> tuple[str, str | None]:
    t0 = time.monotonic()
    result = _transcribe_api(pcm)
    where = "api"
    if result is None:
        result, where = _transcribe_local(pcm), "local"
    log.info("stt(%s) %.2fs -> %r", where, time.monotonic() - t0, result[0])
    return result


# ---------------------------------------------------------------- TTS
def guess_lang(text: str) -> str:
    padded = f" {text.lower()} "
    return "fr" if sum(h in padded for h in _FR_HINTS) >= 2 else "en"


_kokoro = None


def _get_kokoro():
    global _kokoro
    if _kokoro is None:
        model = KOKORO_DIR / "kokoro-v1.0.onnx"
        voices = KOKORO_DIR / "voices-v1.0.bin"
        if model.exists() and voices.exists():
            from kokoro_onnx import Kokoro
            _kokoro = Kokoro(str(model), str(voices))
        else:
            _kokoro = False
    return _kokoro


def wants_speech(command: str) -> bool:
    if SPEAK_MODE == "off":
        return False
    if SPEAK_MODE == "always":
        return True
    return bool(SPEAK_RE.search(command))


def speak(text: str, lang: str | None = None) -> float:
    """Speak the reply. Returns its duration in seconds (0 if unavailable)."""
    kokoro = _get_kokoro()
    if not kokoro:
        log.warning("kokoro unavailable — reply not spoken")
        return 0.0
    voice, kl = KOKORO_VOICES[lang or guess_lang(text)]
    samples, sr = kokoro.create(text, voice=voice, speed=1.0, lang=kl)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = STATE_DIR / "reply.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())
    subprocess.run(["pw-play", str(wav_path)], check=False)
    return len(samples) / sr


# ---------------------------------------------------------------- agent
def dispatch(text: str, lang: str | None) -> float:
    """Send the command to novad. Returns seconds of speech played."""
    log.info("command: %r", text)
    out = ask(text)
    if out.get("error"):
        log.error("agent failed: %s", out["error"])
        notify("L'agent a échoué — voir les logs.", "critical")
        return 0.0
    reply = out.get("reply", "").strip()
    log.info("agent %ss, %s tokens", out.get("elapsed"), out.get("tokens"))
    if not reply:
        notify("Pas de réponse du modèle.")
        return 0.0
    global _awaiting_until
    notify(reply[:400], "normal")
    spoken = 0.0
    if wants_speech(text):
        try:
            spoken = speak(reply, lang)          # blocks until played
        except Exception:                                    # noqa: BLE001
            log.exception("tts failed")
    # If she asked something, listen for the answer instead of making the user
    # say the name again — being asked "which playlist?" and having to reply
    # "Nova, the sport one" is not a conversation. Opened after speaking, so
    # the window is not spent talking.
    if reply.rstrip().endswith("?"):
        _awaiting_until = time.monotonic() + FOLLOWUP_SECONDS
        log.info("question asked — listening for the answer")
    return spoken


def handle_utterance(pcm: bytes, awaited: bool = False) -> None:
    """Transcribe properly, then act. Runs in a thread — an agent turn can take
    a while and the listener must never go deaf during it."""
    global _suppress_until, _awaiting_until
    duration = len(pcm) / 2 / RATE
    try:
        text, lang = transcribe(pcm)
        too_long = len(text) > duration * MAX_CHARS_PER_SECOND + 8
        if (not text or _HALLUCINATIONS.match(text) or _is_prompt_echo(text)
                or too_long):
            log.info("nothing usable heard in %.1fs (%r) — staying silent",
                     duration, text[:80])
            if awaited:              # keep waiting rather than dropping it
                _awaiting_until = time.monotonic() + FOLLOWUP_SECONDS
            return
        # An awaited utterance is the command itself; only a wake-word one has
        # a name to remove.
        command = text.strip() if awaited else strip_wake(text)
        if not command:
            notify("Oui ?")           # called by name with nothing after it
            _awaiting_until = time.monotonic() + FOLLOWUP_SECONDS
            return
        spoken = dispatch(command, lang)
        if spoken:
            # speak() already blocked until the audio finished, so only a short
            # tail is needed. Adding the full duration again used to leave her
            # deaf for as long as she had just spoken — which swallowed the
            # answer to her own question.
            _suppress_until = time.monotonic() + 0.4
    except Exception:                                        # noqa: BLE001
        log.exception("command handling failed")
        notify("La commande vocale a échoué — voir les logs.", "critical")


# ---------------------------------------------------------------- main
def start_capture() -> subprocess.Popen:
    argv = ["pw-record", "--rate", str(RATE), "--channels", "1",
            "--format", "s16"]
    if MIC != "default":
        argv += ["--target", MIC]
    return subprocess.Popen([*argv, "-"], stdout=subprocess.PIPE)


def should_release() -> bool:
    """Give the microphone back: the machine is idle, or Nova was paused.
    Either way there is no reason to keep a wireless headset from sleeping."""
    return IDLE_FILE.exists() or PAUSE_FILE.exists()


def main() -> int:
    global _awaiting_until
    logging.basicConfig(level=logging.INFO, force=True,
                        format="%(asctime)s %(levelname)s %(message)s")
    if not (ASR_DIR / "tokens.txt").exists():
        log.error("French ASR model missing: %s", ASR_DIR)
        notify("Modèle de reconnaissance vocale introuvable.", "critical")
        return 1

    from openwakeword.vad import VAD          # bundles Silero

    vad = VAD()
    gate = WakeGate()
    log.info("listening — wake word %r, speak=%s", WAKE_WORD, SPEAK_MODE)

    log.info("microphone: %s", MIC)
    proc = start_capture()
    assert proc.stdout is not None

    preroll: deque[bytes] = deque(maxlen=max(1, int(PREROLL * RATE / FRAME)))
    frames: list[bytes] = []
    speaking = False
    voiced_run = 0
    silence = 0.0
    started_at = 0.0
    frame_s = FRAME / RATE
    idle_checked = 0.0

    try:
        while True:
            # Hand the microphone back while the machine is idle, so the
            # headset can reach its own power-off timer. Checked once a second:
            # a stat() per 80 ms frame would be pure waste.
            now = time.monotonic()
            if now - idle_checked > 1.0:
                idle_checked = now
                if should_release():
                    log.info("idle — releasing the microphone")
                    proc.terminate()
                    proc.wait(timeout=5)
                    while should_release():
                        time.sleep(2.0)
                    log.info("active again — reopening the microphone")
                    proc = start_capture()
                    assert proc.stdout is not None
                    speaking, voiced_run, silence = False, 0, 0.0
                    preroll.clear()
                    frames = []
                    vad.reset_states()
                    continue

            raw = proc.stdout.read(FRAME * 2)
            if not raw:
                log.error("pw-record stream ended (exit %s)", proc.poll())
                return 1
            raw = amplify(raw, MIC_GAIN)

            prob = float(vad.predict(np.frombuffer(raw, np.int16), VAD_FRAME))
            voiced = prob >= SPEECH_PROB

            if not speaking:
                preroll.append(raw)
                voiced_run = voiced_run + 1 if voiced else 0
                if voiced_run >= SPEECH_FRAMES:
                    speaking = True
                    silence = 0.0
                    started_at = time.monotonic()
                    frames = list(preroll)
                    preroll.clear()
                continue

            frames.append(raw)
            if voiced:
                silence = 0.0
            else:
                silence += frame_s
            hangover = (SILENCE_HANGOVER_AWAITED
                        if time.monotonic() < _awaiting_until
                        else SILENCE_HANGOVER)
            over = time.monotonic() - started_at > MAX_UTTERANCE
            if silence < hangover and not over:
                continue

            # Utterance complete.
            speaking = False
            voiced_run = 0
            pcm = b"".join(frames)
            frames = []
            duration = len(pcm) / 2 / RATE
            if duration < MIN_UTTERANCE:
                continue
            if PAUSE_FILE.exists() or time.monotonic() < _suppress_until:
                continue
            samples = np.frombuffer(pcm, np.int16)
            peak_pct = int(100 * abs(int(np.abs(samples).max())) / 32767)
            pcm = normalise(pcm)

            # She just said "Oui ?" and is waiting: this utterance is the
            # command, no name needed and no point running the gate on it.
            awaited = time.monotonic() < _awaiting_until
            if awaited:
                _awaiting_until = 0.0
                log.info("follow-up (%.1fs)", duration)
            else:
                heard = gate.transcribe(pcm)
                if not starts_with_wake(heard):
                    # At INFO, not debug: when Nova "does not react", this line
                    # is the difference between "never heard you" and "heard
                    # you but not the name".
                    log.info("ignored (%.1fs, peak %d%%): %r", duration,
                             peak_pct, heard[:70])
                    continue
                log.info("wake (%.1fs, peak %d%%) %r", duration, peak_pct,
                         heard[:80])
            threading.Thread(target=handle_utterance, args=(pcm, awaited),
                             daemon=True).start()
    finally:
        proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
