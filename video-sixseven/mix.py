# Soundtrack: voices + comic beat (cut during the silences, big drop on the teacher's "SIX SEVEN") + SFX (bass boom on every chant, slam, door, crowd).
import json, wave, numpy as np, subprocess
SR = 44100; tl = json.load(open("build/timeline.json")); T = tl["total"]; N = int(T * SR)
L = {l["id"]: l for l in tl["lines"]}; S = lambda i: L[i]["start"]; E = lambda i: L[i]["start"] + L[i]["dur"]
def read(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
def write(p, a):
    with wave.open(p, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
def put(buf, sig, t, g=1.0):
    i = int(t * SR); n = min(len(sig), len(buf) - i)
    if n > 0 and i >= 0: buf[i:i + n] += sig[:n] * g
rng = np.random.default_rng(6); midi = lambda m: 440 * 2 ** ((m - 69) / 12)
voice = np.zeros(N, np.float32)
for l in tl["lines"]: put(voice, read(f"build/audio/{l['id']}.wav"), l["start"])
write("build/voice.wav", voice)
def pluck(f, d=.25, g=.12):
    t = np.arange(int(d * SR)) / SR; return sum(np.sin(2 * np.pi * f * h * t) / h ** 1.3 * np.exp(-t * (14 + 6 * h)) for h in range(1, 6)) * np.minimum(1, t * 400) * g
def kick(g=.6):
    t = np.arange(int(.22 * SR)) / SR; return np.sin(2 * np.pi * (48 + 110 * np.exp(-t * 28)) * t) * np.exp(-t * 13) * g
def snare():
    t = np.arange(int(.16 * SR)) / SR; return (rng.standard_normal(len(t)) * .6 + np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 22) * .2
def hat():
    t = np.arange(int(.04 * SR)) / SR; return np.diff(rng.standard_normal(len(t)), prepend=0) * np.exp(-t * 100) * .05
music = np.zeros(N, np.float32); beat = 60 / 116
quiet = [(S("n4") - .1, S("d4") - .1), (S("r2") - .1, S("d6") - .05)]
drop = S("d6"); chords = [[62, 65, 69], [60, 64, 67], [58, 62, 65], [60, 64, 67]]; roots = [38, 36, 34, 36]
t0 = 0; n = 0
while t0 < T - .8:
    if not any(a < t0 < b for a, b in quiet):
        big = t0 > drop; ch = chords[(n // 8) % 4]
        put(music, pluck(midi(ch[[0, 2, 1, 2, 0, 1, 2, 1][n % 8]] + 12), .25, .1 if not big else .14), t0)
        if n % 2 == 0: put(music, pluck(midi(roots[(n // 8) % 4]), .4, .22), t0)
        if n % 4 == 0: put(music, kick(.55 if not big else .8), t0)
        if n % 4 == 2: put(music, snare(), t0)
        put(music, hat(), t0)
    t0 += beat / 2; n += 1
fade = np.ones(N); fi = int((T - 1.2) * SR); fade[fi:] = np.linspace(1, 0, N - fi); music *= fade
write("build/music.wav", music)
sfx = np.zeros(N, np.float32)
def boom():
    t = np.arange(int(.7 * SR)) / SR; return np.sin(2 * np.pi * (40 + 60 * np.exp(-t * 10)) * t) * np.exp(-t * 4) * .9
def slam():
    t = np.arange(int(.3 * SR)) / SR; return (np.sin(2 * np.pi * 90 * t) + rng.standard_normal(len(t)) * .5 * np.exp(-t * 60)) * np.exp(-t * 18) * .8
def creak():
    t = np.arange(int(.6 * SR)) / SR; return np.sin(2 * np.pi * np.cumsum(300 + 120 * np.sin(t * 20)) / SR) * np.exp(-t * 3) * .08
def crowd(d=2, g=.25):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); a = 0.0
    for i in range(n): a += .1 * (x[i] - a); y[i] = a
    tt = np.arange(n) / SR; return y * np.minimum(1, tt * 6) * np.minimum(1, (d - tt) * 2) * g * 4
def tick():
    t = np.arange(int(.05 * SR)) / SR; return np.sin(2 * np.pi * 2000 * t) * np.exp(-t * 80) * .12
def whoosh(d=.3):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); a = 0.0; cut = np.linspace(.02, .3, n)
    for i in range(n): a += cut[i] * (x[i] - a); y[i] = a
    return y * np.sin(np.linspace(0, np.pi, n)) * .3
for c in ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "d6"]: put(sfx, boom(), S(c)); put(sfx, crowd(1.1, .18), S(c))
put(sfx, crowd(3.5, .35), S("c7")); put(sfx, slam(), S("d2") + .12); put(sfx, creak(), S("n7") + .1)
for k in range(8): put(sfx, tick(), S("n8") + k * .5)
for i in ["n2", "d1", "n4", "n5", "n7", "n9"]: put(sfx, whoosh(), S(i) - .25)
write("build/sfx.wav", sfx)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/voice.wav", "-i", "build/music.wav", "-i", "build/sfx.wav", "-filter_complex",
  "[1:a]volume=0.4[m];[0:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[md];"
  "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 0.75,alimiter=limit=0.95,loudnorm=I=-14:TP=-1[a]", "-map", "[a]", "-ar", "44100", "-ac", "2", "build/mix.wav"], check=True)
print("mix ok", T)
