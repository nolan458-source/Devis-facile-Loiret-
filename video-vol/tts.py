#!/usr/bin/env python3
"""Generates the voices and the timeline of the video.

Input : script.json (the lines), voice_profile.json (voices, intonation, rhythm, HUSS)
Output: build/audio/<id>.wav and build/timeline.json (start, duration, word timings, lip-sync)
Usage : python3 tts.py [models/kokoro]

Script line format (script.json):
  {"id": "intro", "who": "N", "mood": "excited", "text": "À Boulanville, tout le monde *adore* le foot.", "pad": 0.2}
  - who   : a key of "voices" in voice_profile.json
  - mood  : a key of "moods" (speed multiplier)
  - *...* : emphasised words (yellow in the captions)
  - say   : optional text actually spoken (respelling to force a pronunciation), e.g. "bé-ère" for "BR"
  - at    : optional, the line never starts before this time (seconds)
  - huss  : true -> the line is "*Huss ! Huss !*": one burst of HUSS per "Huss" word
  - chorus: optional list of voice keys -> the line is said by all of them together (a crowd)
"""
import json, os, re, subprocess, sys, wave, zlib
import numpy as np
from kokoro_onnx import Kokoro

KD = sys.argv[1] if len(sys.argv) > 1 else "models/kokoro"
PROFILE = json.load(open("voice_profile.json"))
K = Kokoro(f"{KD}/kokoro-v1.0.onnx", f"{KD}/voices-v1.0.bin")
VOICES = {who: dict(cfg, vec=sum(w * K.voices[n] for n, w in cfg["mix"].items())) for who, cfg in PROFILE["voices"].items()}
MOODS, HUSS, FIXES = PROFILE["moods"], PROFILE["huss"], [tuple(x) for x in PROFILE["ipa_fixes"]]
HUM = PROFILE.get("humanize", {})   # {"jitter": 0.03, "breath": true, "room": true}


def breath(sr, seed):
    """A soft inhale (band-limited noise, ~0.3 s) placed before long sentences."""
    n = int(sr * (.26 + (seed % 5) * .015)); x = np.random.default_rng(seed).standard_normal(n)
    lo = np.convolve(x, np.ones(9) / 9, "same"); band = lo - np.convolve(lo, np.ones(60) / 60, "same")
    u = np.linspace(0, 1, n); env = np.sin(np.pi * u) ** 1.5 * (1 - .35 * u)
    return (band / (np.abs(band).max() + 1e-6) * env * .07).astype(np.float32)
OUT = "build/audio"; os.makedirs(OUT, exist_ok=True)
SR, FPS = 44100, 25


def ipa(text):
    """French phonemes (espeak-ng) + fixes for words espeak reads in English or gets wrong."""
    p = K.tokenizer.phonemize(text, "fr-fr")
    for a, b in FIXES:
        p = p.replace(a, b)
    return re.sub(r"\([a-z-]+\)", "", p)   # drop any remaining language-switch markers


def save(a, sr, path):
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def read(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def remap(x, sr, target_median, down=1.0, up=1.0, formant=1.0):
    """Intonation: sets the median pitch and widens the lows (down) and highs (up), in semitones (WORLD vocoder)."""
    import pyworld as pw
    x = x.astype(np.float64); fp = 5.0
    f0, t = pw.harvest(x, sr, f0_floor=60, f0_ceil=500, frame_period=fp)
    sp = pw.cheaptrick(x, f0, t, sr); ap = pw.d4c(x, f0, t, sr)
    v = f0 > 0; st = np.zeros_like(f0); st[v] = 12 * np.log2(f0[v] / np.median(f0[v]))
    idx = np.where(v)[0]
    for j, i in enumerate(idx):   # octave-error fix
        loc = np.median(st[idx[max(0, j - 40):j + 40]])
        while st[i] - loc > 8: st[i] -= 12
        while loc - st[i] > 8: st[i] += 12
    st = np.where(st < 0, st * down, st * up)
    f0n = np.where(v, target_median * 2 ** (st / 12), 0)
    if formant != 1.0:
        n = sp.shape[1]; src = np.clip(np.arange(n) / formant, 0, n - 1)
        sp = np.array([np.interp(src, np.arange(n), row) for row in sp])
    y = pw.synthesize(f0n, sp, ap, sr, fp)
    return (y / (np.abs(y).max() + 1e-6) * .9).astype(np.float32)


def huss_line(voice, bursts):
    """'HUSS' like the reference: the whole word squeezed (never cut), shouted high, with a crisp 's'.
    Hits at HUSS['offsets'] in every burst, one burst every HUSS['every'] seconds."""
    sr = 24000
    word, _ = K.create(HUSS["ipa"], voice=voice["vec"], speed=1.3, is_phonemes=True)
    nz = np.where(np.abs(word) > .03 * np.abs(word).max())[0]; word = word[nz[0]:nz[-1] + 1]
    import pyworld as pw
    f0, _ = pw.harvest(word.astype(np.float64), sr, f0_floor=60, f0_ceil=500, frame_period=5)
    f0m = float(np.median(f0[f0 > 0])) if (f0 > 0).any() else 150.

    def squeeze(dur, seed):
        tmp_in, tmp_out = f"{OUT}/_huss_in.wav", f"{OUT}/_huss_{dur}.wav"
        save(word / (np.abs(word).max() + 1e-6) * .9, sr, tmp_in)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp_in, "-af",
                        f"rubberband=tempo={len(word) / sr / dur:.3f}:pitch={HUSS['pitch_hz'] / f0m:.3f}:formant=preserved,highpass=f=150",
                        "-ar", str(sr), "-ac", "1", tmp_out], check=True)
        x = read(tmp_out)[: int(sr * dur)]
        env = np.ones(len(x)); env[:int(sr * .004)] = np.linspace(0, 1, int(sr * .004)); env[-int(sr * .015):] = np.linspace(1, 0, int(sr * .015))
        x = x * env / (np.abs(x).max() + 1e-6)
        noise = np.random.default_rng(seed).standard_normal(len(x))
        hiss = np.convolve(np.diff(noise, prepend=0), np.ones(6) / 6, "same")           # band-limited hiss for the final "s"
        u = np.linspace(0, 1, len(x)); shape = np.clip((u - .3) / .3, 0, 1) * np.clip((1 - u) / .15, 0, 1)
        x = x + hiss / (np.abs(hiss).max() + 1e-6) * shape * HUSS["hiss"]
        return x / (np.abs(x).max() + 1e-6)

    first, other = squeeze(HUSS["first_dur"], 1), squeeze(HUSS["other_dur"], 2)
    offs = HUSS["offsets"]; a = np.zeros(int(sr * (HUSS["every"] * (bursts - 1) + offs[-1] + .3)), np.float32)
    for j in range(bursts):
        for k, off in enumerate(offs):
            one = first if k == 0 else other; i0 = int(sr * (HUSS["every"] * j + off))
            a[i0:i0 + len(one)] += one * (1.0, .85, .9)[min(k, 2)]
    return a, sr


lines = json.load(open("script.json")); t = PROFILE["start_s"]; out = []
for ln in lines:
    if ln.get("at") is not None: t = max(t, ln["at"])
    who, mood = ln["who"], ln.get("mood", "normal"); V = VOICES[who]; text = ln["text"].replace("*", "")
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    if ln.get("huss"):
        a, sr = huss_line(VOICES["N"], text.lower().count("huss"))
    else:
        jit = 1 + ((zlib.crc32(ln["id"].encode()) % 7) - 3) / 3 * HUM.get("jitter", 0)   # a human never reads two sentences at the same speed
        a, sr = K.create(ipa(ln.get("say", text)), voice=V["vec"], speed=V["speed"] * MOODS.get(mood, 1.0) * jit, is_phonemes=True)
        a = a / (np.abs(a).max() + 1e-6) * .9
        if V.get("intonation"): a = remap(a, sr, **V["intonation"])
        if ln.get("chorus"):   # several voices saying the same line together (a crowd)
            parts = [a]
            for k, w2 in enumerate(ln["chorus"]):
                if w2 == who: continue
                b2, _ = K.create(ipa(ln.get("say", text)), voice=VOICES[w2]["vec"], speed=VOICES[w2]["speed"] * MOODS.get(mood, 1.0), is_phonemes=True)
                parts.append(np.concatenate([np.zeros(int(sr * .17 * (k + 1)), np.float32), b2 / (np.abs(b2).max() + 1e-6) * (.6 - .08 * k)]))
            n = max(len(x) for x in parts); a = sum(np.pad(x, (0, n - len(x))) for x in parts); a = a / (np.abs(a).max() + 1e-6) * .9
    lead = 0.0
    if HUM.get("breath") and not ln.get("huss") and not ln.get("chorus") and len(text) > 62:
        b = breath(sr, zlib.crc32(ln["id"].encode())); lead = len(b) / sr; a = np.concatenate([b, a])
    save(a, sr, raw)
    room = "aecho=0.85:0.6:23|41:0.09|0.05," if HUM.get("room") else ""
    af = ("aresample=44100,highpass=f=70,equalizer=f=200:t=q:w=1.2:g=1.5,equalizer=f=3200:t=q:w=1.2:g=1.5,deesser=i=0.3," + room +
          "acompressor=threshold=-20dB:ratio=2.5:attack=5:release=90:makeup=2,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "loudnorm=I=-16:TP=-1.5")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", fin], check=True)
    a = read(fin); dur = len(a) / SR; hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[i:i + hop] ** 2))) for i in range(0, len(a), hop)]; m = max(env) or 1
    env = [round(min(1, e / m * 1.4), 2) for e in env]
    raw_words = ln["text"].split(); emph = []; on = False
    for w in raw_words:
        on = on or w.startswith("*"); emph.append(on)
        if w.rstrip(".,!?:…").endswith("*"): on = False
    words = [w.replace("*", "") for w in raw_words]; w8 = [len(w.strip(".,?!:…")) + 2 for w in words]; tot = sum(w8); acc = 0; wt = []; hb = 0
    for w, kk, e in zip(words, w8, emph):
        s = w.strip(".,!:?…")
        if s and ln.get("huss"):
            for off in HUSS["offsets"]: wt.append({"w": s, "t": round(t + .01 + HUSS["every"] * hb + off, 3), "e": True})
            hb += 1
        elif s:
            wt.append({"w": s, "t": round(t + lead + (dur - lead) * acc / tot, 3), "e": e})
        acc += kk
    out.append({**ln, "text": text, "start": round(t, 3), "dur": round(dur, 3), "words": wt, "env": env})
    print(f"{ln['id']:10} {t:6.2f}s  {dur:5.2f}s  {text[:60]}")
    t += dur + PROFILE["gap_s"] + ln.get("pad", 0) * PROFILE["pad_scale"]
json.dump({"total": round(t + 0.8, 2), "lines": out}, open("build/timeline.json", "w"), ensure_ascii=False)
print("total", round(t + 0.8, 2), "s")
