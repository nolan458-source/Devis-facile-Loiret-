# Soundtrack: voice + procedural score (festive -> mysterious -> warm) + SFX (whooshes, bell dings, owl hoot, cheers).
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
rng = np.random.default_rng(5); midi = lambda m: 440 * 2 ** ((m - 69) / 12)
voice = np.zeros(N, np.float32)
for l in tl["lines"]: put(voice, read(f"build/audio/{l['id']}.wav"), l["start"])
write("build/voice.wav", voice)
def pluck(f, d=.4, g=.14):
    t = np.arange(int(d * SR)) / SR; s = sum(np.sin(2 * np.pi * f * h * t) / h ** 1.4 * np.exp(-t * (10 + 5 * h)) for h in range(1, 6)); return s * np.minimum(1, t * 400) * g
def pad(f, d, g=.05):
    t = np.arange(int(d * SR)) / SR; s = sum(np.sin(2 * np.pi * f * k * t + k) for k in (1, 1.003, .997, 2.001)) / 4
    return s * np.minimum(1, t / .8) * np.minimum(1, (d - t) / .8) * g
def bell(f=1568, g=.2):
    t = np.arange(int(1.2 * SR)) / SR; return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * 2.76 * f * t) + .25 * np.sin(2 * np.pi * 5.4 * f * t)) * np.exp(-t * 4) * g
def kick():
    t = np.arange(int(.2 * SR)) / SR; return np.sin(2 * np.pi * (50 + 100 * np.exp(-t * 28)) * t) * np.exp(-t * 14) * .5
music = np.zeros(N, np.float32)
# festive part (0 -> bizarre) and finale (village -> end): 104 bpm, C F G Am
fest = [(0, S("bizarre") - .2), (S("village") - .2, T - .5)]
beat = 60 / 104
chords = [[60, 64, 67], [65, 69, 72], [67, 71, 74], [57, 60, 64]]
for a, b in fest:
    n = 0; t0 = a
    while t0 < b:
        ch = chords[(n // 8) % 4]; put(music, pluck(midi(ch[[0, 1, 2, 1, 0, 2, 1, 2][n % 8]] + 12), .35), t0)
        if n % 2 == 0: put(music, pluck(midi(ch[0] - 12), .5, .2), t0); put(music, kick(), t0, .6)
        t0 += beat / 2; n += 1
# mysterious part: slow minor pads + sparse plucks (bizarre -> village)
a, b = S("bizarre") - .2, S("village") - .2
prog = [[57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 56, 59]]; d = 2.6; t0 = a; k = 0
while t0 < b:
    for m in prog[k % 4]: put(music, pad(midi(m), min(d + .8, b - t0 + .4)), t0)
    put(music, pluck(midi(prog[k % 4][2] + 12), .9, .08), t0 + d * .5)
    t0 += d; k += 1
fade = np.ones(N); fi = int((T - 1.5) * SR); fade[fi:] = np.linspace(1, 0, N - fi); music *= fade
write("build/music.wav", music)
sfx = np.zeros(N, np.float32)
def whoosh(d=.4):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); acc = 0.0; cut = np.linspace(.02, .3, n)
    for i in range(n): acc += cut[i] * (x[i] - acc); y[i] = acc
    return y * np.sin(np.linspace(0, np.pi, n)) * .3
def hoot():
    t = np.arange(int(.9 * SR)) / SR; f = 330 + 40 * np.sin(t * 9)
    env = np.exp(-((t - .2) / .12) ** 2) + .8 * np.exp(-((t - .6) / .14) ** 2); return np.sin(2 * np.pi * np.cumsum(f) / SR) * env * .4
def cheer(d=3, g=.3):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); acc = 0.0
    for i in range(n): acc += .08 * (x[i] - acc); y[i] = acc
    t = np.arange(n) / SR; return y * np.minimum(1, t * 3) * np.minimum(1, (d - t) * 1.5) * g * 4
put(sfx, bell(), WT("plan", r"clochette"))
for k in range(6): put(sfx, bell(1568, .08 + k * .03), S("foret") + k * .55)
put(sfx, bell(1568, .3), S("chene") + .3)
for i in range(5): put(sfx, bell(1760 + i * 90, .05), S("nuit") + 1 + i * .5)
put(sfx, hoot(), S("hibou") + .25); put(sfx, cheer(3.2), WT("fin", r"Cette")); put(sfx, cheer(2, .15), WT("regle", r"lâche"))
for i in ["bizarre", "lendemain", "lina", "nuit", "foret", "village", "fin"]: put(sfx, whoosh(), S(i) - .35)
write("build/sfx.wav", sfx)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/voice.wav", "-i", "build/music.wav", "-i", "build/sfx.wav", "-filter_complex",
  "[1:a]volume=0.4[m];[0:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[md];"
  "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 0.7,alimiter=limit=0.95,loudnorm=I=-14:TP=-1[a]", "-map", "[a]", "-ar", "44100", "-ac", "2", "build/mix.wav"], check=True)
print("mix ok", T)
