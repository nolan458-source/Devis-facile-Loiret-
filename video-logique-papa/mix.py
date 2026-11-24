# Builds the soundtrack: voice lines at their timeline positions, a procedural music bed, and SFX.
import json, wave, numpy as np, subprocess
SR = 44100; tl = json.load(open("build/timeline.json")); T = tl["total"]; N = int(T * SR)
L = {l["id"]: l for l in tl["lines"]}
def read(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
def write(p, a):
    a = np.clip(a, -1, 1); 
    with wave.open(p, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a * 32767).astype(np.int16).tobytes())
def put(buf, sig, t, g=1.0):
    i = int(t * SR); n = min(len(sig), len(buf) - i)
    if n > 0 and i >= 0: buf[i:i + n] += sig[:n] * g
rng = np.random.default_rng(7)
# ---- voice
voice = np.zeros(N, np.float32)
for l in tl["lines"]: put(voice, read(f"build/audio/{l['id']}.wav"), l["start"])
write("build/voice.wav", voice)
# ---- music: 112 bpm, C G Am F, pluck arpeggio + bass + light drums
bpm = 112; beat = 60 / bpm; bar = 4 * beat
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]; roots = [36, 43, 45, 41]
music = np.zeros(N, np.float32)
def tone(f, d, kind="pluck", g=.2):
    n = int(d * SR); t = np.arange(n) / SR
    if kind == "pluck": s = (2 * np.abs(2 * ((t * f) % 1) - 1) - 1) * np.exp(-t * 7) + .3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 12)
    elif kind == "bass": s = np.tanh(2.2 * np.sin(2 * np.pi * f * t)) * np.minimum(1, t * 80) * np.exp(-t * 2.5)
    s[-200:] *= np.linspace(1, 0, 200); return s * g
def kick():
    t = np.arange(int(.25 * SR)) / SR; return np.sin(2 * np.pi * (50 + 110 * np.exp(-t * 30)) * t) * np.exp(-t * 14) * .7
def hat(d=.05, g=.08):
    t = np.arange(int(d * SR)) / SR; n = rng.standard_normal(len(t)); n = np.diff(n, prepend=0); return n * np.exp(-t * 90) * g
def clap():
    t = np.arange(int(.15 * SR)) / SR; return rng.standard_normal(len(t)) * np.exp(-t * 30) * .18
fin = L["fin"]["start"] - .2; end = T - 1.5
nb = int(T / bar) + 1
for b in range(nb):
    t0 = b * bar; ci = b % 4
    if t0 > end + .5: break
    full = t0 >= 1.2
    for i in range(8):  # arpeggio 8ths
        tt = t0 + i * beat / 2
        if tt > end + .8: break
        note = chords[ci][[0, 1, 2, 1, 2, 0, 1, 2][i]] + (12 if i in (3, 6) else 0)
        put(music, tone(midi(note), .45, "pluck", .16), tt)
    for i in range(4):
        tt = t0 + i * beat
        if tt > end: break
        put(music, tone(midi(roots[ci]), beat * .9, "bass", .30), tt)
        if full: put(music, kick(), tt, .9 if i % 2 == 0 else .5)
        if full and i % 2 == 1: put(music, clap(), tt)
        if full: put(music, hat(), tt + beat / 2); put(music, hat(.03, .05), tt)
# final sting
for k, m in enumerate([60, 64, 67, 72]): put(music, tone(midi(m), 1.4, "pluck", .22), end + .15 + k * .02)
put(music, kick(), end + .15)
fade = np.ones(N); fi = int((T - .6) * SR); fade[fi:] = np.linspace(1, 0, N - fi); music *= fade
write("build/music.wav", music * .9)
# ---- sfx
sfx = np.zeros(N, np.float32)
def whoosh(d=.35, up=True):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); a = 0.0
    cut = np.linspace(.02, .35, n) if up else np.linspace(.35, .02, n)
    for i in range(n): a += cut[i] * (x[i] - a); y[i] = a
    return y * np.sin(np.linspace(0, np.pi, n)) * .5
def pop(f=600):
    t = np.arange(int(.12 * SR)) / SR; return np.sin(2 * np.pi * (f + 900 * np.exp(-t * 40)) * t) * np.exp(-t * 35) * .45
def thud():
    t = np.arange(int(.3 * SR)) / SR; return (np.sin(2 * np.pi * 70 * t) + .3 * rng.standard_normal(len(t)) * np.exp(-t * 60)) * np.exp(-t * 12) * .8
def ding(f=1320):
    t = np.arange(int(.8 * SR)) / SR; return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * 2.76 * f * t)) * np.exp(-t * 5) * .22
def boing():
    t = np.arange(int(.45 * SR)) / SR; return np.sin(2 * np.pi * (220 + 120 * np.sin(t * 40) * np.exp(-t * 6)) * t) * np.exp(-t * 6) * .35
for sid in ["froid", "lumiere", "voiture", "champ", "soir", "fin"]: put(sfx, whoosh(), L[sid]["start"] - .45)
for w in [w for w in L["pulls"]["words"] if w["w"] in ("PULL", "DEUX", "TROIS")]: put(sfx, boing(), w["t"])
put(sfx, ding(), L["cache"]["start"] + L["cache"]["dur"] * .75)
put(sfx, ding(1760), L["garage"]["start"] + .3)
put(sfx, thud(), L["thermo"]["start"] - .1)
put(sfx, whoosh(.3, False), L["edf"]["start"] - .32); put(sfx, thud(), L["edf"]["start"] - .05)
put(sfx, pop(300), L["edf"]["start"] + .35)
put(sfx, pop(), L["q1"]["start"] - .1); put(sfx, pop(), L["pull"]["start"] - .1)
for w in L["soir"]["words"]:
    if w["w"].startswith("LUMI"):
        for k in range(4): put(sfx, pop(500 + k * 150), w["t"] + k * .18)
put(sfx, ding(990), L["intro"]["start"] + L["intro"]["dur"] * .8)
write("build/sfx.wav", sfx)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/voice.wav", "-i", "build/music.wav", "-i", "build/sfx.wav", "-filter_complex",
  "[1:a]volume=0.55[m];[0:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[md];"
  "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 0.8,alimiter=limit=0.95,loudnorm=I=-14:TP=-1[a]",
  "-map", "[a]", "-ar", "44100", "-ac", "2", "build/mix.wav"], check=True)
print("mix ok", T)
