"""Audio and screen recording, in Python rather than shell.

Ported from two bash scripts. The behaviour is unchanged: system audio and
microphone are captured as separate tracks so both sides of a call are kept,
then mixed and transcribed locally on stop; the screen is captured with
wf-recorder and finalised with SIGINT so the container is written properly.

What changes is the failure reporting. The scripts returned bare exit codes,
so "nothing happened" and "ffmpeg is not installed" looked identical from the
tool's side.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import apps
import subprocess
import time
from pathlib import Path

STATE = Path.home() / ".local/state/nova"
DATA = Path.home() / ".local/share/nova/recordings"
AUDIO_STATE = STATE / "record"
SCREEN_STATE = STATE / "screen"
WHISPER_MODEL = Path.home() / ".local/share/whisper/ggml-large-v3-turbo-q5_0.bin"


def _stamp(name: str, kind: str = "") -> str:
    return time.strftime("%Y%m%d-%H%M%S") + (f"-{kind}" if kind else "") + f"-{name}"


def _read(path: Path) -> str:
    try:
        return path.read_text().strip()
    except OSError:
        return ""


def _spawn(argv: list[str], out: Path) -> subprocess.Popen:
    return subprocess.Popen(argv, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)


# ------------------------------------------------------------------ audio
def audio_start(name: str = "call") -> str:
    if (AUDIO_STATE / "session").exists():
        return (f"FAILED: already recording ({_read(AUDIO_STATE / 'session')}) "
                "— stop it first")
    session = _stamp(name)
    folder = DATA / session
    folder.mkdir(parents=True, exist_ok=True)
    AUDIO_STATE.mkdir(parents=True, exist_ok=True)

    # The sink monitor is what the machine is playing (Discord, a video); the
    # default source is the microphone. Both are needed for a conversation.
    system = _spawn(["pw-record", "-P", "{ stream.capture.sink = true }",
                     str(folder / "system.wav")], folder)
    mic = _spawn(["pw-record", str(folder / "mic.wav")], folder)
    (AUDIO_STATE / "pid.system").write_text(str(system.pid))
    (AUDIO_STATE / "pid.mic").write_text(str(mic.pid))
    (AUDIO_STATE / "session").write_text(session)
    return f"recording started ({session})"


def audio_stop() -> str:
    session = _read(AUDIO_STATE / "session")
    if not session:
        return "FAILED: nothing is being recorded"
    folder = DATA / session
    for side in ("system", "mic"):
        pid = _read(AUDIO_STATE / f"pid.{side}")
        if pid.isdigit():
            try:
                os.kill(int(pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
        (AUDIO_STATE / f"pid.{side}").unlink(missing_ok=True)
    (AUDIO_STATE / "session").unlink(missing_ok=True)
    time.sleep(1.0)                      # let pw-record flush the WAV headers

    if not shutil.which("ffmpeg"):
        return f"FAILED: ffmpeg is missing; the raw tracks are in {folder}"
    mixed = folder / "mixed.wav"
    mix = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y",
         "-i", str(folder / "mic.wav"), "-i", str(folder / "system.wav"),
         "-filter_complex", "amix=inputs=2:duration=longest:normalize=1",
         "-ar", "16000", "-ac", "1", str(mixed)],
        capture_output=True, text=True, timeout=600)
    if mix.returncode != 0:
        return f"FAILED: mixing failed: {mix.stderr.strip()[:200]}"

    binary = shutil.which("whisper-cli") or shutil.which("whisper-cpp")
    if not binary or not WHISPER_MODEL.exists():
        return (f"recording saved to {folder}, but whisper.cpp is unavailable "
                "so it was not transcribed")
    out = subprocess.run(
        [binary, "-m", str(WHISPER_MODEL), "-l", "auto", "-f", str(mixed),
         "-otxt", "-of", str(folder / "transcript")],
        capture_output=True, text=True, timeout=3600)
    if out.returncode != 0:
        return (f"recording saved to {folder}, but transcription failed: "
                f"{out.stderr.strip()[:200]}")
    return (f"stopped ({session}); transcript at "
            f"{folder / 'transcript.txt'}")


def audio_status() -> str:
    session = _read(AUDIO_STATE / "session")
    return f"recording since {session}" if session else "not recording"


# ----------------------------------------------------------------- screen
def screen_start(name: str = "screen", region: bool = False) -> str:
    if (SCREEN_STATE / "session").exists():
        return f"FAILED: already recording the screen ({_read(SCREEN_STATE / 'session')})"
    if not shutil.which("wf-recorder"):
        return "FAILED: wf-recorder is not installed"
    session = _stamp(name, "screen")
    folder = DATA / session
    folder.mkdir(parents=True, exist_ok=True)
    SCREEN_STATE.mkdir(parents=True, exist_ok=True)
    video = folder / "video.mp4"

    if region:
        picked = subprocess.run(["slurp"], capture_output=True, text=True,
                                timeout=120)
        if picked.returncode != 0 or not picked.stdout.strip():
            return "FAILED: region selection was cancelled"
        argv = ["wf-recorder", "-g", picked.stdout.strip(), "-f", str(video)]
    else:
        apps.ensure_hypr_env()
        mon = subprocess.run(["hyprctl", "-j", "monitors"], capture_output=True,
                             text=True, timeout=15)
        name_of = ""
        try:
            name_of = next(m["name"] for m in json.loads(mon.stdout)
                           if m.get("focused"))
        except (json.JSONDecodeError, StopIteration, KeyError):
            pass
        argv = ["wf-recorder", "-f", str(video)]
        if name_of:
            argv[1:1] = ["-o", name_of]

    proc = _spawn(argv, folder)
    (SCREEN_STATE / "pid").write_text(str(proc.pid))
    (SCREEN_STATE / "session").write_text(session)
    return f"screen recording started ({session})"


def screen_stop() -> str:
    session = _read(SCREEN_STATE / "session")
    if not session:
        return "FAILED: the screen is not being recorded"
    pid = _read(SCREEN_STATE / "pid")
    if pid.isdigit():
        try:
            # SIGINT, not SIGTERM: wf-recorder needs it to finalise the file.
            os.kill(int(pid), signal.SIGINT)
        except ProcessLookupError:
            pass
        for _ in range(20):
            try:
                os.kill(int(pid), 0)
            except (ProcessLookupError, ValueError):
                break
            time.sleep(0.5)
    (SCREEN_STATE / "pid").unlink(missing_ok=True)
    (SCREEN_STATE / "session").unlink(missing_ok=True)
    return f"stopped ({session}); video at {DATA / session / 'video.mp4'}"


def screen_status() -> str:
    session = _read(SCREEN_STATE / "session")
    return f"recording the screen since {session}" if session else "not recording"


def mux(audio: str) -> str:
    folders = sorted((d for d in DATA.glob("*-screen-*") if d.is_dir()),
                     key=lambda d: d.stat().st_mtime, reverse=True)
    if not folders or not (folders[0] / "video.mp4").exists():
        return "FAILED: no screen recording to add audio to"
    track = Path(audio).expanduser()
    if not track.is_file():
        return f"FAILED: audio file not found: {audio}"
    final = folders[0] / "final.mp4"
    out = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y",
         "-i", str(folders[0] / "video.mp4"), "-i", str(track),
         "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)],
        capture_output=True, text=True, timeout=1800)
    if out.returncode != 0:
        return f"FAILED: muxing failed: {out.stderr.strip()[:200]}"
    return f"combined into {final}"
