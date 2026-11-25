# Soundtrack: voices + procedural score (playful bakery -> tense contest -> triumphant) + SFX.
import json, wave, re, numpy as np, subprocess
SR = 44100; tl = json.load(open("build/timeline.json")); T = tl["total"]; N = int(T * SR)
L = {l["id"]: l for l in tl["lines"]}; S = lambda i: L[i]["start"]; E = lambda i: L[i]["start"] + L[i]["dur"]
def read(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
def write(p, a):
    with wave.open(p, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
def put(buf, sig, t, g=1.0):
    i = int(t * SR); n = min(len(sig), len(buf) - i)
    if n > 0 and i >= 0: buf[i:i + n] += sig[:n] * g
rng = np.random.default_rng(4); midi = lambda m: 440 * 2 ** ((m - 69) / 12)
voice = np.zeros(N, np.float32)
for l in tl["lines"]: put(voice, read(f"build/audio/{l['id']}.wav"), l["start"])
write("build/voice.wav", voice)
def pluck(f, d=.3, g=.12):
    t = np.arange(int(d * SR)) / SR; return sum(np.sin(2 * np.pi * f * h * t) / h ** 1.3 * np.exp(-t * (12 + 6 * h)) for h in range(1, 6)) * np.minimum(1, t * 400) * g
def pad(f, d, g=.04):
    t = np.arange(int(d * SR)) / SR; return sum(np.sin(2 * np.pi * f * k * t + k) for k in (1, 1.004, .996)) / 3 * np.minimum(1, t / .5) * np.minimum(1, (d - t) / .5) * g
def kick():
    t = np.arange(int(.2 * SR)) / SR; return np.sin(2 * np.pi * (50 + 100 * np.exp(-t * 28)) * t) * np.exp(-t * 14) * .5
music = np.zeros(N, np.float32)
sec = [(0, S("nuit") - .1, "play"), (S("nuit") - .1, S("concours") - .1, "night"), (S("concours") - .1, S("k3") - .1, "tense"), (S("k3") - .1, T - .5, "win")]
for a, b, kind in sec:
    beat = 60 / (112 if kind in ("play", "win") else 80); t0 = a; n = 0
    prog_ = {"play": [[62, 66, 69], [67, 71, 74], [64, 67, 71], [69, 73, 76]], "night": [[57, 60, 64], [53, 57, 60]], "tense": [[57, 60, 63], [56, 59, 62]], "win": [[60, 64, 67], [65, 69, 72], [67, 71, 74], [60, 64, 67]]}[kind]
    while t0 < b:
        ch = prog_[(n // 8) % len(prog_)]
        if kind in ("play", "win"):
            put(music, pluck(midi(ch[[0, 2, 1, 2, 0, 1, 2, 1][n % 8]] + 12)), t0)
            if n % 2 == 0: put(music, pluck(midi(ch[0] - 12), .4, .18), t0)
            if kind == "win" and n % 4 == 0: put(music, kick(), t0)
        else:
            if n % 8 == 0: [put(music, pad(midi(m), min(beat * 8, b - t0 + .3)), t0) for m in ch]
            if kind == "tense" and n % 2 == 0: put(music, pluck(midi(ch[0] - 12), .25, .14), t0)
            if kind == "night" and n % 4 == 2: put(music, pluck(midi(ch[2] + 12), .9, .07), t0)
        t0 += beat / 2; n += 1
fade = np.ones(N); fi = int((T - 1.2) * SR); fade[fi:] = np.linspace(1, 0, N - fi); music *= fade
write("build/music.wav", music)
sfx = np.zeros(N, np.float32)
def whoosh(d=.35):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); acc = 0.0; cut = np.linspace(.02, .3, n)
    for i in range(n): acc += cut[i] * (x[i] - acc); y[i] = acc
    return y * np.sin(np.linspace(0, np.pi, n)) * .3
def ding(f=1568, g=.22):
    t = np.arange(int(1 * SR)) / SR; return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * 2.76 * f * t)) * np.exp(-t * 4) * g
def buzzer():
    t = np.arange(int(.6 * SR)) / SR; return np.sign(np.sin(2 * np.pi * 110 * t)) * .12 * np.minimum(1, (.6 - t) * 10)
def cheer(d=3, g=.3):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); acc = 0.0
    for i in range(n): acc += .09 * (x[i] - acc); y[i] = acc
    tt = np.arange(n) / SR; return y * np.minimum(1, tt * 3) * np.minimum(1, (d - tt) * 1.5) * g * 4
def coin():
    t = np.arange(int(.35 * SR)) / SR; f = np.where(t < .08, 988, 1319); return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 8) * .08
for i in ["journee", "nuit", "decouvre", "concours", "voix"]: put(sfx, whoosh(), S(i) - .3)
put(sfx, ding(2093, .15), S("journee") + 1.4)
for w in L["journee"]["words"]:
    if w["w"].lower().startswith("trois"): put(sfx, coin(), w["t"])
put(sfx, buzzer(), S("k2")); put(sfx, ding(), S("k3")); put(sfx, cheer(4, .35), S("k3") + .4); put(sfx, cheer(1.2, .12), S("c3") + .1)
write("build/sfx.wav", sfx)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/voice.wav", "-i", "build/music.wav", "-i", "build/sfx.wav", "-filter_complex",
  "[1:a]volume=0.4[m];[0:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[md];"
  "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 0.7,alimiter=limit=0.95,loudnorm=I=-14:TP=-1[a]", "-map", "[a]", "-ar", "44100", "-ac", "2", "build/mix.wav"], check=True)
print("mix ok", T)
