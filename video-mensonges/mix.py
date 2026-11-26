# Soundtrack: voice + upbeat procedural score + SFX (house going up / down, HUSS thumps, crickets, landing).
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
tense = (S("regle") - .1, E("regle"))
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
WTn = lambda i, rx, n: [w["t"] for w in L[i]["words"] if re.match(rx, w["w"])][n]
def sweep(f0, f1, d, g=.3, noise=0.0):
    t = np.arange(int(d * SR)) / SR; f = f0 * (f1 / f0) ** (t / d); s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    if noise: s = s * (1 - noise) + rng.standard_normal(len(t)) * noise * .5
    return s * np.minimum(1, t * 60) * np.minimum(1, (d - t) * 12) * g
def thump(g=.5):
    t = np.arange(int(.15 * SR)) / SR; return (np.sin(2 * np.pi * 120 * t) + rng.standard_normal(len(t)) * .3 * np.exp(-t * 80)) * np.exp(-t * 30) * g
def thud():
    t = np.arange(int(.6 * SR)) / SR; return (np.sin(2 * np.pi * 55 * t) * .9 + rng.standard_normal(len(t)) * .25 * np.exp(-t * 12)) * np.exp(-t * 7) * .8
def swish(d=.18, g=.16):
    n = int(d * SR); x = np.diff(rng.standard_normal(n), prepend=0); t = np.arange(n) / SR; return x * np.sin(np.pi * t / d) * g
def cricket(d=1.4, g=.07):
    t = np.arange(int(d * SR)) / SR; chirp = (np.sin(2 * np.pi * 30 * t) > .6) * ((t * 2.2) % 1 < .45)
    return np.sin(2 * np.pi * 4300 * t) * chirp * g
def blip(f, g=.08):
    t = np.arange(int(.07 * SR)) / SR; return np.sin(2 * np.pi * f * t) * np.exp(-t * 40) * g
# lies: the house goes up (rising "bloop"), truths: it goes down
for t in [E("oui"), E("chat"), WTn("engrenage", r"^autre", 0), WTn("engrenage", r"^autre", 1), *G3("b2"), E("brocolis") - .05, S("qeu") + .05]: put(sfx, sweep(220, 660, .35, .22), t)
for t, d in [(WT("engrenage", r"^dix"), 1.0), (S("nuages") - .35, 1.0), (S("voisin") - .5, .6)]: put(sfx, sweep(160, 900, d, .2, .35), t)
a = S("verites") + .5; d = E("verites") - a
for k in range(32): put(sfx, blip(900 - k * 14), a + d * k / 32)
for t in hits("b3")[:8]: put(sfx, sweep(500, 260, .12, .12), t)
put(sfx, thud(), hits("b3")[7] + .05); put(sfx, sweep(660, 220, .4, .2), S("moins") + .05)
for i in ("b1", "b2", "b3", "b4"):
    for t in hits(i): put(sfx, thump(.18), t)
    for t in G3(i): put(sfx, swish(), t - .05)
put(sfx, cricket(), S("pasdechat") + .2)
tl = WT("pizza", r"^lancer"); put(sfx, sweep(300, 1200, 1.0, .1, .6), tl); put(sfx, thump(.4), tl + 1.1)
write("build/sfx.wav", sfx)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/voice.wav", "-i", "build/music.wav", "-i", "build/sfx.wav", "-filter_complex",
  "[1:a]volume=0.4[m];[0:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[md];"
  "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 0.7,alimiter=limit=0.95,loudnorm=I=-14:TP=-1[a]", "-map", "[a]", "-ar", "44100", "-ac", "2", "build/mix.wav"], check=True)
print("mix ok", T)
