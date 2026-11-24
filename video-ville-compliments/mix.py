# Soundtrack: voice lines at their timeline positions + procedural music bed + SFX (+1 cm blips, bonk, cheers).
import json, wave, re, numpy as np, subprocess
SR = 44100; tl = json.load(open("build/timeline.json")); T = tl["total"]; N = int(T * SR)
L = {l["id"]: l for l in tl["lines"]}
S = lambda i: L[i]["start"]; E = lambda i: L[i]["start"] + L[i]["dur"]
def WT(i, rx):
    for w in L[i]["words"]:
        if re.match(rx, w["w"]): return w["t"]
    return S(i)
def read(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
def write(p, a):
    with wave.open(p, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
def put(buf, sig, t, g=1.0):
    i = int(t * SR); n = min(len(sig), len(buf) - i)
    if n > 0 and i >= 0: buf[i:i + n] += sig[:n] * g
rng = np.random.default_rng(3)
voice = np.zeros(N, np.float32)
for l in tl["lines"]: put(voice, read(f"build/audio/{l['id']}.wav"), l["start"])
write("build/voice.wav", voice)
# music: 118 bpm, F C Dm Bb, marimba-like plucks + soft bass + light drums; drops out during the "silence" beat
bpm = 97; beat = 60 / bpm; bar = 4 * beat
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
chords = [[65, 69, 72], [60, 64, 67], [62, 65, 69], [58, 62, 65]]; roots = [41, 36, 38, 34]
music = np.zeros(N, np.float32)
def mar(f, d=.35, g=.15):  # pizzicato-like pluck
    t = np.arange(int(d * SR)) / SR; s = sum(np.sin(2 * np.pi * f * h * t) / h ** 1.3 * np.exp(-t * (14 + 6 * h)) for h in range(1, 6))
    return s * np.minimum(1, t * 400) * g
def bass(f, d):
    t = np.arange(int(d * SR)) / SR; s = np.sin(2 * np.pi * f * t) * np.minimum(1, t * 60) * np.exp(-t * 2); s[-150:] *= np.linspace(1, 0, 150); return s * .32
def kick():
    t = np.arange(int(.22 * SR)) / SR; return np.sin(2 * np.pi * (48 + 100 * np.exp(-t * 28)) * t) * np.exp(-t * 14) * .6
def hat(g=.05):
    t = np.arange(int(.04 * SR)) / SR; return np.diff(rng.standard_normal(len(t)), prepend=0) * np.exp(-t * 100) * g
quiet = (WT("tour", r"silence") - .2, S("foule") + .6)
for b in range(int(T / bar) + 1):
    t0 = b * bar; ci = b % 4
    for i in range(8):
        tt = t0 + i * beat / 2
        if quiet[0] < tt < quiet[1] or tt > T - 1: continue
        note = chords[ci][[0, 2, 1, 2, 0, 2, 1, 2][i]] + (12 if i in (2, 6) else 0)
        put(music, mar(midi(note)), tt)
    for i in range(4):
        tt = t0 + i * beat
        if quiet[0] < tt < quiet[1] or tt > T - 1: continue
        put(music, bass(midi(roots[ci]), beat * .9), tt)
        if tt > 1: put(music, kick(), tt, .8 if i % 2 == 0 else .4); put(music, hat(), tt + beat / 2)
fade = np.ones(N); fi = int((T - 1.2) * SR); fade[fi:] = np.linspace(1, 0, N - fi); music *= fade
write("build/music.wav", music)
sfx = np.zeros(N, np.float32)
def blip(f=1200, g=.25):
    t = np.arange(int(.18 * SR)) / SR; return (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * 1.5 * f * t) * .5) * np.exp(-t * 22) * g
def sad(g=.25):
    t = np.arange(int(.45 * SR)) / SR; return np.sin(2 * np.pi * (300 - 140 * t / .45) * t) * np.exp(-t * 5) * g
def bonk():
    t = np.arange(int(.35 * SR)) / SR; return np.sin(2 * np.pi * (220 * np.exp(-t * 4)) * t) * np.exp(-t * 10) * .7
def cheer(d=2.5, g=.25):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); a = 0.0
    for i in range(n): a += .08 * (x[i] - a); y[i] = a
    t = np.arange(n) / SR; return y * np.minimum(1, t * 4) * np.minimum(1, (d - t) * 2) * g * 4
def whoosh(d=.3):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); a = 0.0; cut = np.linspace(.02, .3, n)
    for i in range(n): a += cut[i] * (x[i] - a); y[i] = a
    return y * np.sin(np.linspace(0, np.pi, n)) * .35
plus = [WT("hook", r"grandir"), WT("hook", r"centimètre"), S("hook") + 3.6, S("c1") + .4, S("chien") + .1, S("c2") + .5, E("o1") - .4, E("o2") - .3,
        S("tous") + .4, S("tous") + .85, S("tous") + 1.3, WT("tous", r"pigeons") + .2, S("b1") + .5, S("p1") + .2, S("x1") + .8]
for k, t in enumerate(plus): put(sfx, blip(1100 + (k % 3) * 120), t)
for i in range(40): put(sfx, blip(900 + (i % 7) * 90 + i * 12, .16), S("cpt") + .3 + i * .09)
for t in [WT("noe", r"personne") + .1, WT("tous", r"Sauf") + .2]: put(sfx, sad(), t)
put(sfx, bonk(), S("ecole") + L["ecole"]["dur"] * .7)
put(sfx, cheer(2.6), S("max") + .8); put(sfx, cheer(1.5, .18), S("c2")); put(sfx, cheer(4, .3), S("cpt") + .3)
for i in ["noe", "ecole", "idee", "toise", "fin"]: put(sfx, whoosh(), S(i) - .3)
write("build/sfx.wav", sfx)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/voice.wav", "-i", "build/music.wav", "-i", "build/sfx.wav", "-filter_complex",
  "[1:a]volume=0.32[m];[0:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[md];"
  "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 0.7,alimiter=limit=0.95,loudnorm=I=-14:TP=-1[a]", "-map", "[a]", "-ar", "44100", "-ac", "2", "build/mix.wav"], check=True)
print("mix ok", T)
