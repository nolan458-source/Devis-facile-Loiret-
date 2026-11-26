#!/usr/bin/env python3
"""Checks the pronunciation of every line with Whisper (speech recognition):
compares what Whisper hears with the text of script.json and prints the word error rate.
Usage: python3 check_pronunciation.py   (after tts.py)"""
import json, os, re, subprocess
import numpy as np
from faster_whisper import WhisperModel

asr = WhisperModel("small", device="cpu", compute_type="int8", download_root=os.environ.get("WHISPER_DIR", "models/whisper"))
norm = lambda s: re.sub(r"[^a-zàâçéèêëîïôûùüÿœ' ]", " ", s.lower().replace("-", " ").replace("é", "e")).split()

def wer(ref, hyp):
    r, h = norm(ref), norm(hyp); d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(1, len(r))

bad = 0
for l in json.load(open("build/timeline.json"))["lines"]:
    if l.get("huss"): continue
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f"build/audio/{l['id']}.wav", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    hyp = " ".join(s.text for s in asr.transcribe(a, language="fr", beam_size=5)[0]).strip(); w = wer(l["text"], hyp)
    flag = "  <-- to check" if w > .2 else ""; bad += w > .2
    print(f"{l['id']:10} error {w:4.0%} | heard: {hyp}{flag}")
print(f"\n{bad} line(s) to check. Digits ('6' instead of 'six') and the spelling of invented names are not pronunciation errors.")
