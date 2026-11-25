# Soundtrack: voice + upbeat procedural score + SFX (spring "boing", kicks, whistle, crowd).
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
sad = (S("gardien") - .2, S("coach") - .2); tense = (S("penalty") - .1, S("saut") + 1.2)
t0 = 0; n = 0
while t0 < T - .8:
    b = n // 8; ch = chords[b % 4]
    if not (sad[0] < t0 < sad[1]):
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
def boing(g=.45):
    t = np.arange(int(.55 * SR)) / SR; f = 180 + 260 * np.exp(-t * 6) * (1 + .35 * np.sin(2 * np.pi * 14 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * g
def thump(g=.5):
    t = np.arange(int(.15 * SR)) / SR; return (np.sin(2 * np.pi * 120 * t) + rng.standard_normal(len(t)) * .3 * np.exp(-t * 80)) * np.exp(-t * 30) * g
def whistle(d=.7):
    t = np.arange(int(d * SR)) / SR; f = 2900 + 120 * np.sign(np.sin(2 * np.pi * 28 * t)); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, (d - t) * 8) * np.minimum(1, t * 30) * .12
def crowd(d=3, g=.3):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); a = 0.0
    for i in range(n): a += .09 * (x[i] - a); y[i] = a
    tt = np.arange(n) / SR; return y * np.minimum(1, tt * 3) * np.minimum(1, (d - tt) * 1.5) * g * 4
def thud(): 
    t = np.arange(int(.4 * SR)) / SR; return np.sin(2 * np.pi * 70 * t) * np.exp(-t * 10) * .7
for t in [S("b1"), S("b2"), *[w["t"] for w in L["b3"]["words"]], WT("saut", r"^si$"), S("b4")]: put(sfx, boing(), t)
for k in range(8): put(sfx, boing(.12), S("saute") + k * .25)
for k in range(6): put(sfx, boing(.15), S("trampo") + k * .375)
for t in [S("match") + .4, S("match") + 1.4, S("match") + 2.4, *[w["t"] - .35 for w in L["b3"]["words"]], S("saut") + .25]: put(sfx, thump(), t)
put(sfx, whistle(), S("match") - .3); put(sfx, whistle(1.2), S("gagne") - .15)
put(sfx, crowd(1.6, .2), S("arret")); put(sfx, crowd(4, .35), S("gagne")); put(sfx, crowd(1.5, .15), S("rires"))
put(sfx, thud(), WT("gardien", r"^tombant") + .45)
write("build/sfx.wav", sfx)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/voice.wav", "-i", "build/music.wav", "-i", "build/sfx.wav", "-filter_complex",
  "[1:a]volume=0.4[m];[0:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[md];"
  "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 0.7,alimiter=limit=0.95,loudnorm=I=-14:TP=-1[a]", "-map", "[a]", "-ar", "44100", "-ac", "2", "build/mix.wav"], check=True)
print("mix ok", T)
