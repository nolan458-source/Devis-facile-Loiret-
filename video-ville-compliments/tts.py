# Voice lines -> build/audio/*.wav and build/timeline.json (start, duration, word timings, lip-sync envelope).
import json, subprocess, sys, wave, numpy as np, os
from voice import Voice, Tom
from prosody import expressive
TTS = Tom(sys.argv[1]) if os.path.isdir(sys.argv[1]) else Voice(sys.argv[1]); OUT = "build/audio"; os.makedirs(OUT, exist_ok=True)
FPS = 25; SR = 44100
# who: (pitch, length scale, formant, range expansion, energy)
# male voice "tom" (~125 Hz natural): light processing to stay human
VOICE = {"N": (1.00, 0.80, 1.00, 1.35, 1.1),  # narrator
         "F": (1.12, 0.82, 1.04, 1.4, 1.2),   # crowd / passer-by
         "G": (1.38, 0.95, 1.12, 1.2, 1.0),   # grandma
         "O": (1.30, 0.82, 1.10, 1.4, 1.2),   # Noé (kid)
         "B": (1.30, 0.85, 1.10, 1.3, 1.1),   # baker
         "P": (0.94, 0.88, 0.98, 1.3, 1.1),   # postman
         "X": (0.90, 0.92, 0.97, 1.2, 0.8)}   # Max
GAP = 0.12
EQ = ""  # timbre match to the reference video
lines = json.load(open("script.json"))
def read(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
t = 0.4; out = []
for ln in lines:
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    pitch, ls, fm, k, en = VOICE[ln["who"]]
    a, sr = TTS.say(ln["text"], ls); a = expressive(a, sr, TTS.clauses, pitch, fm, k, en, TTS.emph, ln.get("mood", "normal"))
    with wave.open(raw, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((a * 32767).astype(np.int16).tobytes())
    af = f"aresample={SR},highpass=f=80,{EQ}equalizer=f=3200:t=q:w=1.2:g=3,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2,silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", fin], check=True)
    a = read(fin); dur = len(a) / SR; hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[i:i+hop]**2))) for i in range(0, len(a), hop)]
    m = max(env) or 1; env = [round(min(1, e / m * 1.4), 2) for e in env]
    words = ln["text"].replace("*", "").split(); w8 = [len(w.strip(".,?!:…")) + 2 for w in words]; tot = sum(w8); acc = 0; wt = []
    for w, kk in zip(words, w8):
        s = w.strip(".,!:?…")
        if s: wt.append({"w": s, "t": round(t + dur * acc / tot, 3)})
        acc += kk
    out.append({**ln, "text": ln["text"].replace("*", ""), "start": round(t, 3), "dur": round(dur, 3), "words": wt, "env": env})
    t += dur + GAP + ln.get("pad", 0)
json.dump({"total": round(t + 0.8, 2), "lines": out}, open("build/timeline.json", "w"), ensure_ascii=False)
print("total", round(t + 0.8, 2))
