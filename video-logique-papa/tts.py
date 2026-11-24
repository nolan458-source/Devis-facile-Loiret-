# Generates one WAV per line with Piper, voice-shifted per character, and writes timeline.json
# (start time, duration, per-word timings, 25 fps loudness envelope for lip-sync).
import json, subprocess, sys, wave, numpy as np, os
from tom_tts import Tom
TTS = Tom(sys.argv[1]); OUT = "build/audio"; os.makedirs(OUT, exist_ok=True)
FPS = 25; SR = 44100
from prosody import expressive
# who: (pitch factor, length scale, formant factor, range expansion, energy)
VOICE = {"N": (0.82, 0.90, 1.00, 2.1, 1.2), "T": (1.28, 0.90, 1.08, 2.3, 1.0), "P": (0.78, 1.00, 0.95, 1.8, 1.3)}
GAP = {"N": 0.35, "T": 0.30, "P": 0.40}
lines = json.load(open("script.json"))
def read(p):
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
t = 1.2; out = []
for ln in lines:
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    pitch, ls, fm, k, en = VOICE[ln["who"]]
    a, sr = TTS.say(ln["text"], ls)
    a = expressive(a, sr, TTS.clauses, pitch, fm, k, en)
    with wave.open(raw, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((a * 32767).astype(np.int16).tobytes())
    # pitch shift keeping tempo: resample by pitch then atempo back
    af = f"aresample={SR},highpass=f=70,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=3,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2,silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5"
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
