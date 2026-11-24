# Voice lines -> build/audio/*.wav and build/timeline.json (start, duration, word timings, lip-sync envelope).
import json, subprocess, sys, wave, numpy as np, os
from voice import Voice
from prosody import expressive
TTS = Voice(sys.argv[1]); OUT = "build/audio"; os.makedirs(OUT, exist_ok=True)
FPS = 25; SR = 44100
# who: (pitch, length scale, formant, range expansion, energy)
VOICE = {"N": (0.75, 0.86, 1.00, 1.6, 1.2),  # narrator
         "F": (1.00, 0.85, 1.03, 2.2, 1.4),  # crowd / passer-by
         "G": (1.05, 1.05, 0.97, 1.6, 1.0),  # grandma
         "O": (1.18, 0.88, 1.10, 2.2, 1.3),  # Noé (kid)
         "B": (0.95, 0.90, 1.00, 2.0, 1.2),  # baker
         "P": (0.62, 0.95, 0.88, 1.8, 1.2),  # postman
         "X": (0.60, 1.00, 0.86, 1.6, 0.8)}  # Max
GAP = 0.22
lines = json.load(open("script.json"))
def read(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
t = 0.4; out = []
for ln in lines:
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    pitch, ls, fm, k, en = VOICE[ln["who"]]
    a, sr = TTS.say(ln["text"], ls); a = expressive(a, sr, TTS.clauses, pitch, fm, k, en)
    with wave.open(raw, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((a * 32767).astype(np.int16).tobytes())
    af = f"aresample={SR},highpass=f=80,equalizer=f=3200:t=q:w=1.2:g=3,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2,silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", fin], check=True)
    a = read(fin); dur = len(a) / SR; hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[i:i+hop]**2))) for i in range(0, len(a), hop)]
    m = max(env) or 1; env = [round(min(1, e / m * 1.4), 2) for e in env]
    words = ln["text"].split(); w8 = [len(w.strip(".,?!:…")) + 2 for w in words]; tot = sum(w8); acc = 0; wt = []
    for w, kk in zip(words, w8):
        s = w.strip(".,!:?…")
        if s: wt.append({"w": s, "t": round(t + dur * acc / tot, 3)})
        acc += kk
    out.append({**ln, "start": round(t, 3), "dur": round(dur, 3), "words": wt, "env": env})
    t += dur + GAP + ln.get("pad", 0)
json.dump({"total": round(t + 0.8, 2), "lines": out}, open("build/timeline.json", "w"), ensure_ascii=False)
print("total", round(t + 0.8, 2))
