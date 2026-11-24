# Generates one WAV per line with Piper, voice-shifted per character, and writes timeline.json
# (start time, duration, per-word timings, 25 fps loudness envelope for lip-sync).
import json, subprocess, sys, wave, numpy as np, os
MODEL = sys.argv[1]; OUT = "build/audio"; os.makedirs(OUT, exist_ok=True)
FPS = 25; SR = 44100
VOICE = {"N": (1.00, 1.00), "T": (1.10, 0.95), "P": (0.80, 1.05)}  # (pitch factor, length scale)
GAP = {"N": 0.35, "T": 0.30, "P": 0.40}
lines = json.load(open("script.json"))
def read(p):
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
t = 1.2; out = []
for ln in lines:
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    pitch, ls = VOICE[ln["who"]]
    subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "-f", raw, "--length-scale", str(ls),
                    "--sentence-silence", "0.25"], input=ln["text"].encode(), check=True, capture_output=True)
    # pitch shift keeping tempo: resample by pitch then atempo back
    af = f"asetrate=22050*{pitch},aresample={SR},atempo={1/pitch:.4f},silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", fin], check=True)
    a = read(fin); dur = len(a) / SR
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[i:i+hop]**2))) for i in range(0, len(a), hop)]
    m = max(env) or 1; env = [round(min(1, e / m * 1.4), 2) for e in env]
    words = ln["text"].replace("’", "'").split()
    w8 = [len(w.strip(".,?!:")) + 2 for w in words]; tot = sum(w8); acc = 0; wt = []
    for w, k in zip(words, w8):
        wt.append({"w": w.strip(".,!:").upper(), "t": round(t + dur * acc / tot, 3)}); acc += k
    out.append({**ln, "start": round(t, 3), "dur": round(dur, 3), "words": wt, "env": env})
    t += dur + GAP[ln["who"]] + ln.get("pad", 0)
json.dump({"total": round(t + 2.5, 2), "lines": out}, open("build/timeline.json", "w"), ensure_ascii=False)
print("speech ends at", round(t, 2), "s")
for o in out: print(f"{o['id']:8} {o['start']:6.2f} {o['dur']:5.2f}")
