# Soundtrack: voice + upbeat procedural score + SFX (flies, shower, machine, thunder and rain, HUSS thumps).
import json, wave, re, numpy as np, subprocess
SR = 44100; tl = json.load(open("build/timeline.json")); T = tl["total"]; N = int(T * SR)
L = {l["id"]: l for l in tl["lines"]}; S = lambda i: L[i]["start"]; E = lambda i: L[i]["start"] + L[i]["dur"]
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
rng = np.random.default_rng(9); midi = lambda m: 440 * 2 ** ((m - 69) / 12)
voice = np.zeros(N, np.float32)
for l in tl["lines"]: put(voice, read(f"build/audio/{l['id']}.wav"), l["start"])
write("build/voice.wav", voice)
def pluck(f, d=.3, g=.13):
    t = np.arange(int(d * SR)) / SR; s = sum(np.sin(2 * np.pi * f * h * t) / h ** 1.3 * np.exp(-t * (12 + 6 * h)) for h in range(1, 6)); return s * np.minimum(1, t * 400) * g
def bass(f, d):
    t = np.arange(int(d * SR)) / SR; s = np.tanh(2 * np.sin(2 * np.pi * f * t)) * np.minimum(1, t * 60) * np.exp(-t * 3); s[-150:] *= np.linspace(1, 0, 150); return s * .28
def kick():
    t = np.arange(int(.2 * SR)) / SR; return np.sin(2 * np.pi * (50 + 110 * np.exp(-t * 28)) * t) * np.exp(-t * 14) * .6
def snare():
    t = np.arange(int(.18 * SR)) / SR; return (rng.standard_normal(len(t)) * .6 + np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 22) * .22
def hat():
    t = np.arange(int(.04 * SR)) / SR; return np.diff(rng.standard_normal(len(t)), prepend=0) * np.exp(-t * 100) * .05
music = np.zeros(N, np.float32); beat = 60 / 120
chords = [[60, 64, 67], [67, 71, 74], [69, 72, 76], [65, 69, 72]]; roots = [36, 43, 45, 41]
tense = (S("rien") - .1, S("b3"))
t0 = 0; n = 0
while t0 < T - .8:
    b = n // 8; ch = chords[b % 4]
    if True:
        put(music, pluck(midi(ch[[0, 2, 1, 2, 0, 2, 1, 2][n % 8]] + 12)), t0)
        if n % 2 == 0: put(music, bass(midi(roots[b % 4]), beat * .9), t0)
        if not (tense[0] < t0 < tense[1]):
            if n % 4 == 0: put(music, kick(), t0)
            if n % 4 == 2: put(music, snare(), t0)
            put(music, hat(), t0)
        elif n % 2 == 0: put(music, kick(), t0, .5)
    elif n % 4 == 0: put(music, pluck(midi([57, 53, 55, 52][b % 4]), .9, .1), t0)
    t0 += beat / 2; n += 1
fade = np.ones(N); fi = int((T - 1.2) * SR); fade[fi:] = np.linspace(1, 0, N - fi); music *= fade
write("build/music.wav", music)
sfx = np.zeros(N, np.float32)
hits = lambda i: [w["t"] for w in L[i]["words"]]
G3 = lambda i: hits(i)[::3]
def env(n, a=.02, r=.1):
    e = np.ones(n); ia, ir = int(a * SR), int(r * SR); e[:ia] = np.linspace(0, 1, ia); e[-ir:] = np.linspace(1, 0, ir); return e
def lowpass(x, k):
    y = np.zeros_like(x); a = 0.0
    for i in range(len(x)): a += k * (x[i] - a); y[i] = a
    return y
def noise(d): return rng.standard_normal(int(d * SR))
def buzz(d, g):
    t = np.arange(int(d * SR)) / SR; f = 210 + 25 * np.sin(2 * np.pi * 3.1 * t) + 12 * np.sin(2 * np.pi * 7.3 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .5 + np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * .3
    return s * (.6 + .4 * np.sin(2 * np.pi * 1.3 * t)) * env(len(t), .2, .3) * g
def water(d, g): x = np.diff(noise(d), prepend=0); return x * env(len(x), .2, .3) * g
def clank(g=.3):
    t = np.arange(int(.35 * SR)) / SR; return (np.sin(2 * np.pi * 820 * t) * .6 + np.sin(2 * np.pi * 1310 * t) * .4 + rng.standard_normal(len(t)) * np.exp(-t * 60) * .8) * np.exp(-t * 14) * g
def thump(g=.5):
    t = np.arange(int(.15 * SR)) / SR; return (np.sin(2 * np.pi * 120 * t) + rng.standard_normal(len(t)) * .3 * np.exp(-t * 80)) * np.exp(-t * 30) * g
def swish(d=.18, g=.16):
    n = int(d * SR); x = np.diff(rng.standard_normal(n), prepend=0); t = np.arange(n) / SR; return x * np.sin(np.pi * t / d) * g
def hum(d, g):
    t = np.arange(int(d * SR)) / SR; s = ((t * 58) % 1 - .5) * .8 + np.sin(2 * np.pi * 116 * t) * .3; return s * env(len(t), .3, .4) * g
def whoosh(d, g): x = lowpass(noise(d), .08); t = np.arange(len(x)) / SR; return x * np.sin(np.pi * t / d) ** 2 * g * 3
def thunder(g=.6): x = lowpass(noise(2.2), .02); t = np.arange(len(x)) / SR; return x * np.exp(-t * 1.6) * np.minimum(1, t * 30) * g * 8
def chime(f0=1320, g=.12):
    t = np.arange(int(.6 * SR)) / SR; return sum(np.sin(2 * np.pi * f0 * m * t) / m for m in (1, 2.01, 3.02)) * np.exp(-t * 6) * g
def cricket(d=1.2, g=.07):
    t = np.arange(int(d * SR)) / SR; return np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 30 * t) > .6) * ((t * 2.2) % 1 < .45) * g
def blip(f=880, g=.1): t = np.arange(int(.09 * SR)) / SR; return np.sin(2 * np.pi * f * t) * np.exp(-t * 30) * g
tA = WT("jourj", r"allume")
put(sfx, buzz(S("mousse") - S("sale"), .035), S("sale")); put(sfx, buzz(E("mouches") - S("mouches") + .3, .07), S("mouches") - .1)
put(sfx, water(E("vanille") - S("douche") + .3, .05), S("douche") + .1); put(sfx, water(E("fin") - S("fin") + .4, .04), S("fin") + .2)
put(sfx, chime(1568), WT("mousse", r"^madame")); put(sfx, chime(1760, .08), WT("mousse", r"^madame") + .12)
put(sfx, blip(990), WT("moi", r"^dix"))
for t in hits("b2"): put(sfx, clank(.22), t)
put(sfx, blip(300, .2), tA); put(sfx, hum(S("pluie") - tA, .05), tA + .05)
put(sfx, cricket(), S("rien") + .1)
put(sfx, whoosh(S("pluie") - S("puis"), .06), S("puis"))
put(sfx, thunder(), S("pluie") - .2); put(sfx, water(S("fin") - S("pluie"), .06), S("pluie"))
for i in ("b1", "b2", "b3", "b4"):
    for t in hits(i): put(sfx, thump(.18), t)
    for t in G3(i): put(sfx, swish(), t - .05)
put(sfx, chime(1046, .14), WT("twist", r"^million") if any(w["w"].startswith("million") for w in L["twist"]["words"]) else E("twist") - 1); put(sfx, chime(1568, .1), E("twist") - .9)
write("build/sfx.wav", sfx)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/voice.wav", "-i", "build/music.wav", "-i", "build/sfx.wav", "-filter_complex",
  "[1:a]volume=0.4[m];[0:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[md];"
  "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 0.7,alimiter=limit=0.95,loudnorm=I=-14:TP=-1[a]", "-map", "[a]", "-ar", "44100", "-ac", "2", "build/mix.wav"], check=True)
print("mix ok", T)
