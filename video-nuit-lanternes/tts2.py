# New narration: medium-quality Piper voices, natural model prosody, clause-level register/speed shaping
# with formant-preserving pitch shift (rubberband), tight rhythm. Writes build/audio/*.wav + build/timeline.json.
import json, subprocess, sys, wave, os, numpy as np
from voice2 import PiperFR
VD = sys.argv[1]; OUT = "build/audio"; os.makedirs(OUT, exist_ok=True); TMP = "build/tmp"; os.makedirs(TMP, exist_ok=True)
VOICES = {"N": PiperFR(f"{VD}/fr_FR-tom-medium.onnx"),
          "L": PiperFR(f"{VD}/fr_FR-upmc-medium.onnx", "jessica"),
          "A": PiperFR(f"{VD}/fr_FR-upmc-medium.onnx", "pierre")}
BASE = {"N": (0.0, 0.76), "L": (2.5, 0.85), "A": (-1.0, 0.9)}          # semitones, length scale
MOOD = {"normal": (0, 1.0), "excited": (1.5, .92), "hype": (2.5, .88), "sad": (-1.8, 1.06), "deadpan": (-1.2, 1.0), "suspense": (-.8, 1.03)}
FPS = 25; SR = 44100; GAP = 0.06
def rb(a, sr, st, path):
    raw = path + ".raw.wav"
    with wave.open(raw, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    f = f"aresample={SR}" + (f",rubberband=pitch={2 ** (st / 12):.4f}:formant=preserved:pitchq=quality" if abs(st) > .05 else "")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", f, "-ar", str(SR), "-ac", "1", path], check=True)
    with wave.open(path) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
lines = json.load(open("script.json")); t = 0.35; out = []
for ln in lines:
    who = ln["who"]; v = VOICES[who]; st0, ls0 = BASE[who]; mst, mls = MOOD.get(ln.get("mood", "normal"), (0, 1))
    cl = v.clauses(ln["text"]); parts = []
    for k, (ipa, term, end, emph) in enumerate(cl):
        first, last = k == 0, k == len(cl) - 1
        st = st0 + mst + (2.0 if emph else 0) + (1.0 if first and len(cl) > 1 else 0) - (1.0 if last and term == "." else 0) + (1.5 if term == "!" else 0)
        ls = ls0 * mls * (1.04 if emph else 1.0)
        a = v.synth(ipa, ls)
        a = a / (np.abs(a).max() + 1e-6) * (0.95 if emph else 0.85)
        parts.append(rb(a, v.sr, st, f"{TMP}/{ln['id']}_{k}.wav"))
        parts.append(np.zeros(int(SR * (0.12 if end else 0.04)), np.float32))
    a = np.concatenate(parts[:-1])
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    with wave.open(raw, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    af = ("highpass=f=70,equalizer=f=180:t=q:w=1:g=1.5,equalizer=f=380:t=q:w=1.4:g=-2,equalizer=f=3200:t=q:w=1.2:g=2.5,deesser=i=0.35,"
          "acompressor=threshold=-20dB:ratio=3:attack=4:release=80:makeup=2,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5")
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
    out.append({**ln, "text": ln["text"].replace("*", ""), "start": round(t, 3), "dur": round(dur, 3), "words": wt, "env": env})
    t += dur + GAP + ln.get("pad", 0) * .45
json.dump({"total": round(t + 0.8, 2), "lines": out}, open("build/timeline.json", "w"), ensure_ascii=False)
print("total", round(t + 0.8, 2))
