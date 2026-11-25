# Narration with Kokoro (82M, ONNX): fluid French voice "ff_siwis", whole sentences synthesised at once from
# corrected IPA (gn -> ɲ, ui -> ɥi), speed per mood for rhythm. The mayor keeps the male Piper "tom" voice.
import json, re, subprocess, sys, wave, os, numpy as np
from kokoro_onnx import Kokoro
KD, PD = sys.argv[1], sys.argv[2]
K = Kokoro(f"{KD}/kokoro-v1.0.onnx", f"{KD}/voices-v1.0.bin")
sys.path.insert(0, "."); from voice2 import PiperFR
TOM = PiperFR(f"{PD}/fr_FR-tom-medium.onnx")
OUT = "build/audio"; os.makedirs(OUT, exist_ok=True)
SPEED = {"normal": 1.06, "excited": 1.1, "hype": 1.14, "sad": .96, "deadpan": 1.0, "suspense": 1.0}
FIXES = [("ɡanjˈe", "ɡaɲˈe"), ("ɡanj", "ɡaɲ"), ("nyˈi", "nɥˈi"), ("syˈi", "sɥˈi"), ("pyˈi", "pɥˈi"), ("pyˌi", "pɥˌi"), ("lyˈi", "lɥˈi")]
FPS = 25; SR = 44100; GAP = 0.08
def ipa(text):
    p = K.tokenizer.phonemize(text, "fr-fr")
    for a, b in FIXES: p = p.replace(a, b)
    return p
def save(a, sr, path):
    with wave.open(path, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
lines = json.load(open("script.json")); t = 0.35; out = []; log = []
for ln in lines:
    text = ln["text"].replace("*", ""); who = ln["who"]; mood = ln.get("mood", "normal")
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    if who == "A":
        a = np.concatenate([np.concatenate([TOM.synth(c[0], .92), np.zeros(int(TOM.sr * (.12 if c[2] else .05)), np.float32)]) for c in TOM.clauses(text)])
        save(a / (np.abs(a).max() + 1e-6) * .9, TOM.sr, raw); pre = ""
    else:
        ph = ipa(text); log.append(f"{ln['id']}: {ph}")
        a, sr = K.create(ph, voice="ff_siwis", speed=SPEED[mood] * (1.04 if who == "L" else 1.0), is_phonemes=True)
        save(a / (np.abs(a).max() + 1e-6) * .9, sr, raw)
        pre = ("rubberband=pitch=1.19:formant=preserved:pitchq=quality," if who == "L"      # Lina: younger
               else "rubberband=pitch=0.794:formant=preserved:pitchq=quality,equalizer=f=140:t=q:w=0.9:g=2.5,")  # narrator: 4 semitones deeper
    af = (f"aresample={SR},{pre}highpass=f=70,equalizer=f=3200:t=q:w=1.2:g=1.5,deesser=i=0.3,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=90:makeup=2,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", fin], check=True)
    with wave.open(fin) as w: a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    dur = len(a) / SR; hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[i:i+hop]**2))) for i in range(0, len(a), hop)]; m = max(env) or 1; env = [round(min(1, e / m * 1.4), 2) for e in env]
    raw_words = ln["text"].split(); emph = []; on = False
    for w_ in raw_words:
        on = on or w_.startswith("*"); emph.append(on)
        if w_.rstrip(".,!?:…").endswith("*"): on = False
    words = [w_.replace("*", "") for w_ in raw_words]; w8 = [len(w_.strip(".,?!:…")) + 2 for w_ in words]; tot = sum(w8); acc = 0; wt = []
    for w_, kk, e in zip(words, w8, emph):
        s = w_.strip(".,!:?…")
        if s: wt.append({"w": s, "t": round(t + dur * acc / tot, 3), "e": e})
        acc += kk
    out.append({**ln, "text": text, "start": round(t, 3), "dur": round(dur, 3), "words": wt, "env": env})
    t += dur + GAP + ln.get("pad", 0) * .45
json.dump({"total": round(t + 0.8, 2), "lines": out}, open("build/timeline.json", "w"), ensure_ascii=False)
open("build/ipa.txt", "w").write("\n".join(log)); print("total", round(t + 0.8, 2))
