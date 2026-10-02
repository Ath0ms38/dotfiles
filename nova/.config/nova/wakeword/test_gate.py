"""End-to-end check of the wake gate, without a microphone.

Synthesises French utterances with Kokoro, runs them through the same
WakeGate the listener uses, and checks the accept/reject decision. Half the
phrases are addressed to Nova and half are ordinary conversation, including
the near-misses that would be embarrassing to trigger on.
"""
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.expanduser("~/.config/nova"))
import listener  # noqa: E402

RATE = 16000
CASES = [
    # (text, voice, should the gate open?)
    ("Nova.", "ff_siwis", True),
    ("Nova, mets la musique en pause.", "am_michael", True),
    ("Nova, quelle heure est-il ?", "bm_george", True),
    ("Nova, ouvre Firefox dans le workspace cinq.", "ff_siwis", True),
    ("Hey Nova, éteins la musique.", "am_adam", True),
    ("Nova, déplace Discord sur le workspace onze.", "af_heart", True),
    ("Il fait beau aujourd'hui, on ne parle pas d'elle.", "ff_siwis", False),
    ("J'ai acheté un nouveau clavier hier soir.", "am_michael", False),
    ("Ne va pas trop vite, je te suis.", "bm_george", False),
    ("On regarde un film ce soir ou pas ?", "af_heart", False),
    ("Le mois de novembre a été pluvieux.", "am_adam", False),
    ("Je pense que Nova pourrait nous aider.", "ff_siwis", False),
]

kokoro = listener._get_kokoro()
gate = listener.WakeGate()

ok = 0
for text, voice, expected in CASES:
    samples, sr = kokoro.create(text, voice=voice, speed=1.0, lang="fr-fr")
    n = int(len(samples) * RATE / sr)
    audio = np.interp(np.linspace(0, len(samples) - 1, n),
                      np.arange(len(samples)), samples)
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()

    heard = gate.transcribe(pcm)
    got = listener.starts_with_wake(heard)
    mark = "ok " if got == expected else "FAIL"
    ok += got == expected
    command = listener.strip_wake(heard) if got else ""
    print(f"{mark} attendu={str(expected):5} obtenu={str(got):5} "
          f"{text!r}\n       -> {heard!r}"
          + (f"\n       commande: {command!r}" if got else ""), flush=True)

print(f"\n{ok}/{len(CASES)} corrects")
