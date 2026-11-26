#!/usr/bin/env bash
# =====================================================================
# KIT VIDÉO TIKTOK : tout le code dans un seul fichier
# 3D en blocs (three.js) + voix off française (Kokoro) + intonation réglée
# + contrôle de prononciation (Whisper) + musique et bruitages + MP4 1080x1920
#
# Pré-requis : python3 (3.10+), node (18+), ffmpeg (avec rubberband), curl
# Utilisation : bash kit_complet.sh
#   -> crée le dossier kit-video-tiktok/, installe tout, fabrique video_finale.mp4
# Pour seulement créer les fichiers, sans installer ni lancer : KIT_NO_RUN=1 bash kit_complet.sh
# =====================================================================
set -e
mkdir -p kit-video-tiktok/parts && cd kit-video-tiktok

# ---------------------------------------------------------------- package.json
cat > 'package.json' <<'__FIN_DU_FICHIER__'
{
  "name": "kit-video-tiktok",
  "private": true,
  "description": "Vid\u00e9o TikTok 3D en blocs : voix fran\u00e7aises, sous-titres mot par mot, HUSS rythm\u00e9s",
  "scripts": {
    "build": "bash build.sh"
  },
  "dependencies": {
    "three": "0.160.0",
    "playwright": "1.49.1",
    "@fontsource/baloo-2": "5.3.0",
    "@fontsource/nunito": "5.3.0"
  }
}
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- .gitignore
cat > '.gitignore' <<'__FIN_DU_FICHIER__'
node_modules
build/
models/
__pycache__/
index.html
*.mp4
!exemple_boulanville.mp4
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- voice_profile.json
cat > 'voice_profile.json' <<'__FIN_DU_FICHIER__'
{
 "_reference": "Voix mesurée sur la vidéo de référence : 164 Hz médian, 104 à 247 Hz, 5,8 demi-tons d'intonation, 8,7 syllabes/s, 5 % de silence",
 "start_s": 0.35,
 "gap_s": 0.05,
 "pad_scale": 0.3,
 "voices": {
  "N": {
   "name": "narrateur",
   "mix": {
    "ff_siwis": 0.55,
    "am_puck": 0.45
   },
   "speed": 1.12,
   "intonation": {
    "target_median": 164,
    "down": 1.55,
    "up": 1.65,
    "formant": 1.0
   }
  },
  "C": {
   "name": "coach",
   "mix": {
    "ff_siwis": 0.35,
    "bm_george": 0.35,
    "am_onyx": 0.3
   },
   "speed": 1.06,
   "intonation": null
  },
  "V": {
   "name": "voisin",
   "mix": {
    "ff_siwis": 0.4,
    "am_onyx": 0.6
   },
   "speed": 1.04,
   "intonation": null
  }
 },
 "moods": {
  "normal": 1.0,
  "excited": 1.04,
  "hype": 1.02,
  "sad": 0.93,
  "deadpan": 0.97,
  "suspense": 0.95
 },
 "huss": {
  "ipa": "hˈœs !",
  "offsets": [
   0.0,
   0.23,
   0.415
  ],
  "every": 0.97,
  "first_dur": 0.11,
  "other_dur": 0.08,
  "pitch_hz": 350,
  "hiss": 0.3
 },
 "ipa_fixes": [
  [
   "(en)kˈəʊtʃ(fr)",
   "kˈotʃ"
  ],
  [
   "(en)fˈʊt(fr)",
   "fˈut"
  ],
  [
   "(en)bˈɔɪŋ(fr)",
   "bwˈɛ̃ɡ"
  ],
  [
   "ɡˈeɪməz",
   "ɡˈɛmœʁ"
  ],
  [
   "nˈəʊʌ",
   "nˈoa"
  ],
  [
   "kjwˈi",
   "kiwˈi"
  ],
  [
   "ɡanjˈe",
   "ɡaɲˈe"
  ],
  [
   "ɡanj",
   "ɡaɲ"
  ],
  [
   "nyˈi",
   "nɥˈi"
  ],
  [
   "syˈi",
   "sɥˈi"
  ],
  [
   "pyˈi",
   "pɥˈi"
  ],
  [
   "pyˌi",
   "pɥˌi"
  ],
  [
   "lyˈi",
   "lɥˈi"
  ]
 ]
}
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- script.json
cat > 'script.json' <<'__FIN_DU_FICHIER__'
[
 {
  "id": "intro",
  "who": "N",
  "mood": "excited",
  "text": "À Boulanville, tout le monde adore le foot. Tout le monde... sauf *Timéo*.",
  "pad": 0.1
 },
 {
  "id": "saute",
  "who": "N",
  "mood": "excited",
  "text": "Timéo, lui, il *saute*. Partout. Tout le temps.",
  "pad": 0.0
 },
 {
  "id": "b1",
  "who": "N",
  "mood": "hype",
  "text": "*Huss ! Huss ! Huss !*",
  "pad": 0.3,
  "huss": true
 },
 {
  "id": "v1",
  "who": "V",
  "mood": "deadpan",
  "text": "Timéo ! Arrête de sauter sur ma voiture !",
  "pad": 0.2
 },
 {
  "id": "trampo",
  "who": "N",
  "mood": "normal",
  "text": "Il saute sur son trampoline, par-dessus la haie, jusqu'à l'école. Et tout le monde le trouve *bizarre*.",
  "pad": 0.3
 },
 {
  "id": "defi",
  "who": "N",
  "mood": "suspense",
  "text": "Un jour, un défi arrive de Grandeville, la ville d'à côté. Un match de foot. Et la ville qui perd... doit repeindre *sa mairie en rose*.",
  "pad": 0.4
 },
 {
  "id": "gardien",
  "who": "N",
  "mood": "sad",
  "text": "Gros problème : le gardien de Boulanville s'est cassé la jambe... en tombant du canapé.",
  "pad": 0.4
 },
 {
  "id": "coach",
  "who": "N",
  "mood": "normal",
  "text": "Le coach cherche un remplaçant. Personne ne veut. Sauf *un seul*.",
  "pad": 0.1
 },
 {
  "id": "b2",
  "who": "N",
  "mood": "hype",
  "text": "*Huss !*",
  "pad": 0.3,
  "huss": true
 },
 {
  "id": "rires",
  "who": "N",
  "mood": "suspense",
  "text": "Toute l'équipe se moque. Timéo, lui, mesure *un mètre vingt*.",
  "pad": 0.4
 },
 {
  "id": "match",
  "who": "N",
  "mood": "excited",
  "text": "Le jour du match, Grandeville tire. Une fois. Deux fois. *Dix fois*.",
  "pad": 0.1
 },
 {
  "id": "b3",
  "who": "N",
  "mood": "hype",
  "text": "*Huss ! Huss ! Huss !*",
  "pad": 0.2,
  "huss": true
 },
 {
  "id": "arret",
  "who": "N",
  "mood": "hype",
  "text": "Il arrête *absolument tout*. Zéro à zéro.",
  "pad": 0.4
 },
 {
  "id": "penalty",
  "who": "N",
  "mood": "suspense",
  "text": "Dernier tir au but. Le géant de Grandeville se prépare à tirer...",
  "pad": 0.3
 },
 {
  "id": "saut",
  "who": "N",
  "mood": "hype",
  "text": "Et là, Timéo saute *si haut*... qu'il attrape le ballon au-dessus de la barre.",
  "pad": 0.4
 },
 {
  "id": "gagne",
  "who": "N",
  "mood": "excited",
  "text": "Et c'est Boulanville qui *gagne le match* !",
  "pad": 0.1
 },
 {
  "id": "c1",
  "who": "C",
  "mood": "excited",
  "text": "Timéo, t'es le meilleur gardien de l'histoire !",
  "pad": 0.3
 },
 {
  "id": "fin",
  "who": "N",
  "mood": "excited",
  "text": "Depuis, à Grandeville, la mairie est *rose*. Et à Boulanville, sauter, c'est *obligatoire*.",
  "pad": 0.1
 },
 {
  "id": "b4",
  "who": "N",
  "mood": "hype",
  "text": "*Huss ! Huss ! Huss !*",
  "pad": 1.0,
  "huss": true
 }
]
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- tts.py
cat > 'tts.py' <<'__FIN_DU_FICHIER__'
#!/usr/bin/env python3
"""Generates the voices and the timeline of the video.

Input : script.json (the lines), voice_profile.json (voices, intonation, rhythm, HUSS)
Output: build/audio/<id>.wav and build/timeline.json (start, duration, word timings, lip-sync)
Usage : python3 tts.py [models/kokoro]

Script line format (script.json):
  {"id": "intro", "who": "N", "mood": "excited", "text": "À Boulanville, tout le monde *adore* le foot.", "pad": 0.2}
  - who   : a key of "voices" in voice_profile.json
  - mood  : a key of "moods" (speed multiplier)
  - *...* : emphasised words (yellow in the captions)
  - say   : optional text actually spoken (respelling to force a pronunciation), e.g. "bé-ère" for "BR"
  - at    : optional, the line never starts before this time (seconds)
  - huss  : true -> the line is "*Huss ! Huss !*": one burst of HUSS per "Huss" word
"""
import json, os, re, subprocess, sys, wave
import numpy as np
from kokoro_onnx import Kokoro

KD = sys.argv[1] if len(sys.argv) > 1 else "models/kokoro"
PROFILE = json.load(open("voice_profile.json"))
K = Kokoro(f"{KD}/kokoro-v1.0.onnx", f"{KD}/voices-v1.0.bin")
VOICES = {who: dict(cfg, vec=sum(w * K.voices[n] for n, w in cfg["mix"].items())) for who, cfg in PROFILE["voices"].items()}
MOODS, HUSS, FIXES = PROFILE["moods"], PROFILE["huss"], [tuple(x) for x in PROFILE["ipa_fixes"]]
OUT = "build/audio"; os.makedirs(OUT, exist_ok=True)
SR, FPS = 44100, 25


def ipa(text):
    """French phonemes (espeak-ng) + fixes for words espeak reads in English or gets wrong."""
    p = K.tokenizer.phonemize(text, "fr-fr")
    for a, b in FIXES:
        p = p.replace(a, b)
    return re.sub(r"\([a-z-]+\)", "", p)   # drop any remaining language-switch markers


def save(a, sr, path):
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def read(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def remap(x, sr, target_median, down=1.0, up=1.0, formant=1.0):
    """Intonation: sets the median pitch and widens the lows (down) and highs (up), in semitones (WORLD vocoder)."""
    import pyworld as pw
    x = x.astype(np.float64); fp = 5.0
    f0, t = pw.harvest(x, sr, f0_floor=60, f0_ceil=500, frame_period=fp)
    sp = pw.cheaptrick(x, f0, t, sr); ap = pw.d4c(x, f0, t, sr)
    v = f0 > 0; st = np.zeros_like(f0); st[v] = 12 * np.log2(f0[v] / np.median(f0[v]))
    idx = np.where(v)[0]
    for j, i in enumerate(idx):   # octave-error fix
        loc = np.median(st[idx[max(0, j - 40):j + 40]])
        while st[i] - loc > 8: st[i] -= 12
        while loc - st[i] > 8: st[i] += 12
    st = np.where(st < 0, st * down, st * up)
    f0n = np.where(v, target_median * 2 ** (st / 12), 0)
    if formant != 1.0:
        n = sp.shape[1]; src = np.clip(np.arange(n) / formant, 0, n - 1)
        sp = np.array([np.interp(src, np.arange(n), row) for row in sp])
    y = pw.synthesize(f0n, sp, ap, sr, fp)
    return (y / (np.abs(y).max() + 1e-6) * .9).astype(np.float32)


def huss_line(voice, bursts):
    """'HUSS' like the reference: the whole word squeezed (never cut), shouted high, with a crisp 's'.
    Hits at HUSS['offsets'] in every burst, one burst every HUSS['every'] seconds."""
    sr = 24000
    word, _ = K.create(HUSS["ipa"], voice=voice["vec"], speed=1.3, is_phonemes=True)
    nz = np.where(np.abs(word) > .03 * np.abs(word).max())[0]; word = word[nz[0]:nz[-1] + 1]
    import pyworld as pw
    f0, _ = pw.harvest(word.astype(np.float64), sr, f0_floor=60, f0_ceil=500, frame_period=5)
    f0m = float(np.median(f0[f0 > 0])) if (f0 > 0).any() else 150.

    def squeeze(dur, seed):
        tmp_in, tmp_out = f"{OUT}/_huss_in.wav", f"{OUT}/_huss_{dur}.wav"
        save(word / (np.abs(word).max() + 1e-6) * .9, sr, tmp_in)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp_in, "-af",
                        f"rubberband=tempo={len(word) / sr / dur:.3f}:pitch={HUSS['pitch_hz'] / f0m:.3f}:formant=preserved,highpass=f=150",
                        "-ar", str(sr), "-ac", "1", tmp_out], check=True)
        x = read(tmp_out)[: int(sr * dur)]
        env = np.ones(len(x)); env[:int(sr * .004)] = np.linspace(0, 1, int(sr * .004)); env[-int(sr * .015):] = np.linspace(1, 0, int(sr * .015))
        x = x * env / (np.abs(x).max() + 1e-6)
        noise = np.random.default_rng(seed).standard_normal(len(x))
        hiss = np.convolve(np.diff(noise, prepend=0), np.ones(6) / 6, "same")           # band-limited hiss for the final "s"
        u = np.linspace(0, 1, len(x)); shape = np.clip((u - .3) / .3, 0, 1) * np.clip((1 - u) / .15, 0, 1)
        x = x + hiss / (np.abs(hiss).max() + 1e-6) * shape * HUSS["hiss"]
        return x / (np.abs(x).max() + 1e-6)

    first, other = squeeze(HUSS["first_dur"], 1), squeeze(HUSS["other_dur"], 2)
    offs = HUSS["offsets"]; a = np.zeros(int(sr * (HUSS["every"] * (bursts - 1) + offs[-1] + .3)), np.float32)
    for j in range(bursts):
        for k, off in enumerate(offs):
            one = first if k == 0 else other; i0 = int(sr * (HUSS["every"] * j + off))
            a[i0:i0 + len(one)] += one * (1.0, .85, .9)[min(k, 2)]
    return a, sr


lines = json.load(open("script.json")); t = PROFILE["start_s"]; out = []
for ln in lines:
    if ln.get("at") is not None: t = max(t, ln["at"])
    who, mood = ln["who"], ln.get("mood", "normal"); V = VOICES[who]; text = ln["text"].replace("*", "")
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    if ln.get("huss"):
        a, sr = huss_line(VOICES["N"], text.lower().count("huss"))
    else:
        a, sr = K.create(ipa(ln.get("say", text)), voice=V["vec"], speed=V["speed"] * MOODS.get(mood, 1.0), is_phonemes=True)
        a = a / (np.abs(a).max() + 1e-6) * .9
        if V.get("intonation"): a = remap(a, sr, **V["intonation"])
    save(a, sr, raw)
    af = ("aresample=44100,highpass=f=70,equalizer=f=3200:t=q:w=1.2:g=1.5,deesser=i=0.3,"
          "acompressor=threshold=-20dB:ratio=2.5:attack=5:release=90:makeup=2,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "loudnorm=I=-16:TP=-1.5")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", fin], check=True)
    a = read(fin); dur = len(a) / SR; hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[i:i + hop] ** 2))) for i in range(0, len(a), hop)]; m = max(env) or 1
    env = [round(min(1, e / m * 1.4), 2) for e in env]
    raw_words = ln["text"].split(); emph = []; on = False
    for w in raw_words:
        on = on or w.startswith("*"); emph.append(on)
        if w.rstrip(".,!?:…").endswith("*"): on = False
    words = [w.replace("*", "") for w in raw_words]; w8 = [len(w.strip(".,?!:…")) + 2 for w in words]; tot = sum(w8); acc = 0; wt = []; hb = 0
    for w, kk, e in zip(words, w8, emph):
        s = w.strip(".,!:?…")
        if s and ln.get("huss"):
            for off in HUSS["offsets"]: wt.append({"w": s, "t": round(t + .01 + HUSS["every"] * hb + off, 3), "e": True})
            hb += 1
        elif s:
            wt.append({"w": s, "t": round(t + dur * acc / tot, 3), "e": e})
        acc += kk
    out.append({**ln, "text": text, "start": round(t, 3), "dur": round(dur, 3), "words": wt, "env": env})
    print(f"{ln['id']:10} {t:6.2f}s  {dur:5.2f}s  {text[:60]}")
    t += dur + PROFILE["gap_s"] + ln.get("pad", 0) * PROFILE["pad_scale"]
json.dump({"total": round(t + 0.8, 2), "lines": out}, open("build/timeline.json", "w"), ensure_ascii=False)
print("total", round(t + 0.8, 2), "s")
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- check_pronunciation.py
cat > 'check_pronunciation.py' <<'__FIN_DU_FICHIER__'
#!/usr/bin/env python3
"""Checks the pronunciation of every line with Whisper (speech recognition):
compares what Whisper hears with the text of script.json and prints the word error rate.
Usage: python3 check_pronunciation.py   (after tts.py)"""
import json, os, re, subprocess
import numpy as np
from faster_whisper import WhisperModel

asr = WhisperModel("small", device="cpu", compute_type="int8", download_root=os.environ.get("WHISPER_DIR", "models/whisper"))
norm = lambda s: re.sub(r"[^a-zàâçéèêëîïôûùüÿœ' ]", " ", s.lower().replace("-", " ").replace("é", "e")).split()

def wer(ref, hyp):
    r, h = norm(ref), norm(hyp); d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(1, len(r))

bad = 0
for l in json.load(open("build/timeline.json"))["lines"]:
    if l.get("huss"): continue
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f"build/audio/{l['id']}.wav", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    hyp = " ".join(s.text for s in asr.transcribe(a, language="fr", beam_size=5)[0]).strip(); w = wer(l["text"], hyp)
    flag = "  <-- to check" if w > .2 else ""; bad += w > .2
    print(f"{l['id']:10} error {w:4.0%} | heard: {hyp}{flag}")
print(f"\n{bad} line(s) to check. Digits ('6' instead of 'six') and the spelling of invented names are not pronunciation errors.")
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- mix.py
cat > 'mix.py' <<'__FIN_DU_FICHIER__'
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
G3 = lambda i: [w["t"] for k, w in enumerate(L[i]["words"]) if k % 3 == 0]
for t in [*G3("b1"), S("b2"), *G3("b3"), WT("saut", r"^si$"), *G3("b4")]: put(sfx, boing(.25), t)
for t in [w["t"] for i in ("b1", "b2", "b3", "b4") for w in L[i]["words"]]: put(sfx, thump(.18), t)
for k in range(8): put(sfx, boing(.12), S("saute") + k * .25)
for k in range(6): put(sfx, boing(.15), S("trampo") + k * .375)
for t in [S("match") + .4, S("match") + 1.4, S("match") + 2.4, *[t_ - .35 for t_ in G3("b3")], S("saut") + .25]: put(sfx, thump(), t)
put(sfx, whistle(), S("match") - .3); put(sfx, whistle(1.2), S("gagne") - .15)
put(sfx, crowd(1.6, .2), S("arret")); put(sfx, crowd(4, .35), S("gagne")); put(sfx, crowd(1.5, .15), S("rires"))
put(sfx, thud(), WT("gardien", r"^tombant") + .45)
write("build/sfx.wav", sfx)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/voice.wav", "-i", "build/music.wav", "-i", "build/sfx.wav", "-filter_complex",
  "[1:a]volume=0.4[m];[0:a]asplit[v][vk];[m][vk]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[md];"
  "[v][md][2:a]amix=inputs=3:normalize=0:weights=1 1 0.7,alimiter=limit=0.95,loudnorm=I=-14:TP=-1[a]", "-map", "[a]", "-ar", "44100", "-ac", "2", "build/mix.wav"], check=True)
print("mix ok", T)
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- render.js
cat > 'render.js' <<'__FIN_DU_FICHIER__'
// Serves the folder over HTTP (ES modules), renders index.html frame by frame (25 fps) to build/video.mp4,
// or stills: node render.js stills 3.2 10.5
const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path'); const { spawn } = require('child_process');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.json': 'application/json' };
const srv = http.createServer((q, r) => { const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0])); if (!f.startsWith(__dirname) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
(async () => {
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const port = srv.address().port;
  const tl = JSON.parse(fs.readFileSync(__dirname + '/build/timeline.json'));
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 720, height: 1280 } });
  p.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exit(1); });
  p.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await p.goto(`http://127.0.0.1:${port}/index.html`); await p.waitForFunction(() => window.ready === true);
  await p.evaluate(tl => window.init(tl), tl);
  const args = process.argv.slice(2);
  if (args[0] === 'stills') {
    for (const t of args.slice(1)) { const d = await p.evaluate(t => window.frame(+t, 'image/jpeg'), t); fs.writeFileSync(`${__dirname}/build/still_${t}.jpg`, Buffer.from(d.split(',')[1], 'base64')); }
    await b.close(); srv.close(); return;
  }
  const N = Math.round(tl.total * 25), t0 = Date.now();
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', '25', '-c:v', 'mjpeg', '-i', '-', '-vf', 'scale=1080:1920:flags=lanczos', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', __dirname + '/build/video.mp4'], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < N; i++) {
    const d = await p.evaluate(t => window.frame(t, 'image/jpeg'), i / 25);
    if (!ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 250 === 0) console.log(i, '/', N, Math.round((Date.now() - t0) / 1000) + 's');
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close(); srv.close(); console.log('done');
})();
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- parts/a_head.html
cat > 'parts/a_head.html' <<'__FIN_DU_FICHIER__'
<!doctype html>
<html><head><meta charset="utf-8">
<style>
@font-face{font-family:Baloo;font-weight:800;src:url(fonts/baloo-2-latin-800-normal.woff2)}
@font-face{font-family:Nun;font-weight:800;src:url(fonts/nunito-latin-800-normal.woff2)}
html,body{margin:0;background:#000}
</style>
<script type="importmap">{"imports":{"three":"./node_modules/three/build/three.module.js","three/addons/":"./node_modules/three/examples/jsm/"}}</script>
</head><body>
<canvas id="gl" width="720" height="1280"></canvas><canvas id="out" width="720" height="1280"></canvas>
<script type="module">
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const W = 720, H = 1280, FPS = 25;
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, k) => a + (b - a) * k;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const ease = x => x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
const back = x => { const c = 1.9; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
const rnd = i => { const s = Math.sin(i * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
let TL, L = {};
const S = id => L[id].start, E = id => L[id].start + L[id].dur;
const WT = (id, re) => { const w = L[id].words.find(w => re.test(w.w)); return w ? w.t : S(id); };
function talk(who, t) {
  for (const l of TL.lines) if (l.who === who && t >= l.start && t <= l.start + l.dur) return l.env[Math.floor((t - l.start) * FPS)] || 0;
  return 0;
}

// ---------- three setup ----------
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('gl'), antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 400);
const hemi = new THREE.HemisphereLight('#dff1ff', '#5d8a3a', 1.25); scene.add(hemi);
const sun = new THREE.DirectionalLight('#fff4e0', 2.2); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 80 }); sun.shadow.bias = -0.0005; sun.shadow.radius = 4;
scene.add(sun); scene.add(sun.target);
function skyTex(top, bottom) {
  const c = document.createElement('canvas'); c.width = 4; c.height = 256; const x = c.getContext('2d');
  const g = x.createLinearGradient(0, 0, 0, 256); g.addColorStop(0, top); g.addColorStop(1, bottom); x.fillStyle = g; x.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const SKY_DAY = skyTex('#3f8ff0', '#bfe4ff'), SKY_EVE = skyTex('#5a6fd8', '#ffb38a');
scene.fog = new THREE.Fog('#bfe4ff', 40, 110);

const geoCache = {}, matCache = {};
const RB = (w, h, d, r = .08) => geoCache[[w, h, d, r]] ||= new RoundedBoxGeometry(w, h, d, 3, Math.min(r, w / 2.1, h / 2.1, d / 2.1));
const M = c => matCache[c] ||= new THREE.MeshStandardMaterial({ color: c, roughness: .78 });
function box(w, h, d, color, x = 0, y = 0, z = 0, r = .08, parent = scene) {
  const m = new THREE.Mesh(RB(w, h, d, r), M(color)); m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; parent.add(m); return m;
}
function textTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  t.redraw = (...a) => { draw(c.getContext('2d'), ...a); t.needsUpdate = true; }; t.redraw(); return t;
}
function panel(w, h, tex, x, y, z, parent = scene, ry = 0) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: tex, roughness: .6 }));
  m.position.set(x, y, z); m.rotation.y = ry; parent.add(m); return m;
}
const FONT = (s, w = 800) => `${w} ${s}px Baloo`;

__FIN_DU_FICHIER__

# ---------------------------------------------------------------- parts/b_world.html
cat > 'parts/b_world.html' <<'__FIN_DU_FICHIER__'
// ---------- world ----------
scene.background = SKY_DAY;
const ground = new THREE.Mesh(new THREE.PlaneGeometry(700, 300), M('#63b84a')); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
const road = new THREE.Mesh(new THREE.PlaneGeometry(120, 4.5), M('#5b5f6b')); road.rotation.x = -Math.PI / 2; road.position.set(0, .01, 6.5); road.receiveShadow = true; scene.add(road);
for (let x = -58; x < 60; x += 4) { const d = new THREE.Mesh(new THREE.PlaneGeometry(1.8, .16), M('#f2f2f2')); d.rotation.x = -Math.PI / 2; d.position.set(x, .02, 6.5); scene.add(d); }
box(120, .12, 3.2, '#e3e0da', 0, .06, 2.9, .02);
const HOUSE_COLS = ['#f2b38a', '#9fd9b0', '#f4a6b8', '#f7d774', '#a9c7f5', '#c9a6f0'];
function house(x, z, i, s = 1) {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.scale.setScalar(s); scene.add(g);
  box(5, 3.4, 4, HOUSE_COLS[i % 6], 0, 1.7, 0, .1, g);
  const roof = new THREE.Mesh(new THREE.ConeGeometry(3.9, 2, 4), M(['#7a5cd6', '#e0533d', '#3fa35b', '#3b6fd8'][i % 4])); roof.rotation.y = Math.PI / 4; roof.position.y = 4.4; roof.castShadow = true; g.add(roof);
  for (const wx of [-1.4, 1.4]) { box(1.1, 1.1, .1, '#ffffff', wx, 2.1, 2.02, .03, g); box(.9, .9, .12, '#2f5fb0', wx, 2.1, 2.03, .02, g); }
  box(.95, 1.7, .1, '#7a4a2c', 0, .85, 2.02, .03, g); box(.12, .12, .12, '#f5c400', .3, .85, 2.1, .03, g);
  return g;
}
function tree(x, z, s = 1) { const g = new THREE.Group(); g.position.set(x, 0, z); g.scale.setScalar(s); scene.add(g); box(.4, 1.6, .4, '#7a5236', 0, .8, 0, .05, g); box(1.8, 1.4, 1.8, '#3fa35b', 0, 2.2, 0, .3, g); box(1.2, 1, 1.2, '#4fbf68', 0, 3.1, 0, .25, g); }
function sign(w, h, draw, x, y, z, ry = 0) { const t = textTex(512, Math.round(512 * h / w), draw); box(w + .15, h + .15, .12, '#ffffff', x, y, z - .07, .03).rotation.y = ry; return panel(w, h, t, x, y, z, scene, ry); }
// --- town (x ~ 0)
[-21, -14, -7, 7, 14, 21].forEach((x, i) => house(x, -6.5, i)); [-17.5, 3.5, 10.5, 24.5].forEach(x => tree(x, -2.6));
// Timéo's garden: trampoline + hedge
const tramp = new THREE.Group(); tramp.position.set(-9, 0, -1.4); scene.add(tramp);
const trampMat = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.4, .08, 32), M('#1e1a22')); trampMat.position.y = .62; tramp.add(trampMat);
const trampRim = new THREE.Mesh(new THREE.TorusGeometry(1.45, .09, 8, 40), M('#3b6fd8')); trampRim.rotation.x = Math.PI / 2; trampRim.position.y = .64; tramp.add(trampRim);
for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; box(.08, .62, .08, '#9aa3b5', Math.cos(a) * 1.35, .31, Math.sin(a) * 1.35, .02, tramp); }
box(.6, 1.1, 6, '#2f8a45', -6.2, .55, -1.2, .25);
// neighbour's car
const car = new THREE.Group(); car.position.set(3, 0, 5.2); scene.add(car);
box(3.6, .9, 1.7, '#e8473f', 0, .7, 0, .25, car); box(2, .8, 1.5, '#e8473f', -.2, 1.45, 0, .25, car); box(1.8, .62, 1.52, '#bfe4ff', -.2, 1.48, 0, .12, car);
for (const [wx, wz] of [[-1.2, .85], [1.2, .85], [-1.2, -.85], [1.2, -.85]]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(.36, .36, .3, 16), M('#222')); w.rotation.x = Math.PI / 2; w.position.set(wx, .36, wz); car.add(w); }
// school
const school = new THREE.Group(); school.position.set(36, 0, -5); scene.add(school);
box(12, 5, 5, '#e8693f', 0, 2.5, 0, .15, school); box(1.8, 2.6, .12, '#2a2033', 0, 1.3, 2.52, .02, school);
for (const wx of [-4, -2, 2, 4]) box(1.4, 1.2, .1, '#2f5fb0', wx, 3, 2.52, .02, school);
sign(4, 1, x => { x.fillStyle = '#fff'; x.fillRect(0, 0, 512, 128); x.fillStyle = '#2f5fb0'; x.font = FONT(96); x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('ÉCOLE', 256, 70); }, 36, 4.4, -2.42);
tree(29, -2.2); tree(43, -2.2);
// --- living room (x ~ -60)
box(10, .2, 8, '#c98a5a', -60, .1, 0, .02); box(10, 4.5, .3, '#f4d9a8', -60, 2.25, -3.9, .02); box(.3, 4.5, 8, '#f0c890', -64.9, 2.25, 0, .02);
box(4, .8, 1.4, '#c0392b', -60, .6, -2.6, .2); box(4, 1.1, .5, '#c0392b', -60, 1.3, -3.2, .2); box(.6, 1, 1.4, '#a93226', -62.1, .9, -2.6, .2); box(.6, 1, 1.4, '#a93226', -57.9, .9, -2.6, .2);
box(2.6, 1.5, .15, '#1e1a22', -60, 2.6, 3.6, .05); box(1.2, .5, .6, '#7a4a2c', -60, .45, 3.4, .05);
// --- training field (x ~ 60)
const pitchMat = (w, h) => { const t = textTex(512, Math.round(512 * h / w), x => { x.fillStyle = '#3fa548'; x.fillRect(0, 0, 512, 512); for (let i = 0; i < 10; i++) { x.fillStyle = i % 2 ? '#47b350' : '#3fa548'; x.fillRect(i * 51.2, 0, 51.2, 512); }
  x.strokeStyle = '#fff'; x.lineWidth = 5; x.strokeRect(6, 6, 500, x.canvas.height - 12); x.beginPath(); x.moveTo(256, 6); x.lineTo(256, x.canvas.height - 6); x.stroke(); x.beginPath(); x.arc(256, x.canvas.height / 2, 50, 0, 7); x.stroke(); }); return t; };
const field1 = new THREE.Mesh(new THREE.PlaneGeometry(26, 16), new THREE.MeshStandardMaterial({ map: pitchMat(26, 16), roughness: .9 })); field1.rotation.x = -Math.PI / 2; field1.position.set(60, .02, -2); field1.receiveShadow = true; scene.add(field1);
function goal(x, z, ry = 0) {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = ry; scene.add(g);
  box(.16, 2.4, .16, '#ffffff', -2.8, 1.2, 0, .04, g); box(.16, 2.4, .16, '#ffffff', 2.8, 1.2, 0, .04, g); box(5.76, .16, .16, '#ffffff', 0, 2.4, 0, .04, g);
  const net = textTex(256, 128, x => { x.clearRect(0, 0, 256, 128); x.strokeStyle = 'rgba(255,255,255,.7)'; x.lineWidth = 2; for (let i = 0; i <= 256; i += 12) { x.beginPath(); x.moveTo(i, 0); x.lineTo(i, 128); x.stroke(); } for (let j = 0; j <= 128; j += 12) { x.beginPath(); x.moveTo(0, j); x.lineTo(256, j); x.stroke(); } });
  const nm = new THREE.MeshBasicMaterial({ map: net, transparent: true, side: THREE.DoubleSide, depthWrite: false });
  const back = new THREE.Mesh(new THREE.PlaneGeometry(5.6, 2.4), nm); back.position.set(0, 1.2, -1.2); g.add(back);
  const top = new THREE.Mesh(new THREE.PlaneGeometry(5.6, 1.2), nm); top.rotation.x = Math.PI / 2; top.position.set(0, 2.4, -.6); g.add(top);
  return g;
}
goal(60, -9.8); house(52, -16, 2); house(68, -16, 4); tree(46, -12); tree(74, -12);
// --- stadium (x ~ 130)
const field2 = new THREE.Mesh(new THREE.PlaneGeometry(30, 44), new THREE.MeshStandardMaterial({ map: pitchMat(30, 44), roughness: .9 })); field2.rotation.x = -Math.PI / 2; field2.position.set(130, .02, -6); field2.receiveShadow = true; scene.add(field2);
const goal2 = goal(130, -26); goal(130, 14, Math.PI);
const CROWD_COLS = ['#e8473f', '#3b6fd8', '#f5c400', '#4fbf68', '#9a6be0', '#ff8a3d', '#5de0ff', '#ff7fb0', '#ffffff'];
const fans = new THREE.InstancedMesh(RB(.55, .9, .5, .12), new THREE.MeshStandardMaterial({ roughness: .8 }), 900);
const fanHeads = new THREE.InstancedMesh(RB(.45, .42, .42, .1), new THREE.MeshStandardMaterial({ roughness: .8 }), 900);
const FAN = []; { const m = new THREE.Matrix4(); let n = 0;
  for (const side of [-1, 1]) for (let row = 0; row < 7; row++) for (let i = 0; i < 64 && n < 900; i++) {
    const x = 130 + side * (17 + row * 1.1), z = -26 + i * .7, y = .9 + row * .8; FAN.push([x, y, z, side]);
    fans.setColorAt(n, new THREE.Color(CROWD_COLS[(i * 7 + row * 3) % 9])); fanHeads.setColorAt(n, new THREE.Color(['#f1c9a5', '#8d5a3b', '#c98a5a', '#6b3f28'][(i + row) % 4])); n++; }
  for (let row = 0; row < 7; row++) box(1.1, .2, 46, '#3a3f5c', 130 - 17 - row * 1.1, .4 + row * .8, -4, .02), box(1.1, .2, 46, '#3a3f5c', 130 + 17 + row * 1.1, .4 + row * .8, -4, .02);
  fans.count = fanHeads.count = FAN.length; scene.add(fans); scene.add(fanHeads); }
function updateFans(t, hype) {
  const m = new THREE.Matrix4();
  FAN.forEach(([x, y, z, side], i) => { const j = hype ? Math.abs(Math.sin(t * 9 + i * .7)) * .35 * hype : 0;
    m.makeRotationY(side > 0 ? -Math.PI / 2 : Math.PI / 2); m.setPosition(x, y + .45 + j, z); fans.setMatrixAt(i, m);
    m.setPosition(x, y + 1.15 + j, z); fanHeads.setMatrixAt(i, m); });
  fans.instanceMatrix.needsUpdate = true; fanHeads.instanceMatrix.needsUpdate = true;
}
const scoreTex = textTex(1024, 360, (x, a = 0, b = 0, msg = '') => {
  x.fillStyle = '#111428'; x.fillRect(0, 0, 1024, 360); x.strokeStyle = '#ffd23f'; x.lineWidth = 14; x.strokeRect(7, 7, 1010, 346);
  x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = '#5de0ff'; x.font = FONT(54); x.fillText('BOULANVILLE', 260, 70); x.fillStyle = '#c99bff'; x.fillText('GRANDEVILLE', 764, 70);
  x.fillStyle = '#fff'; x.font = FONT(170); x.fillText(String(a), 260, 220); x.fillText(String(b), 764, 220); x.fillText(':', 512, 210);
  if (msg) { x.fillStyle = '#ffd23f'; x.fillRect(120, 280, 784, 70); x.fillStyle = '#111428'; x.font = FONT(56); x.fillText(msg, 512, 318); }
});
for (const s of [-1, 1]) box(.4, 8, .4, '#2a2d44', 130 + s * 5, 4, -29.5, .05);
box(10.4, 3.8, .3, '#1c1d33', 130, 9, -29.6, .05); const score = panel(10, 3.5, scoreTex, 130, 9, -29.42);
// --- Grandeville town hall (x ~ 200)
const hallMat = new THREE.MeshStandardMaterial({ color: '#e8e0d0', roughness: .8 });
const hall = new THREE.Group(); hall.position.set(200, 0, -6); scene.add(hall);
const hallBody = new THREE.Mesh(RB(14, 7, 6, .15), hallMat); hallBody.position.y = 3.5; hallBody.castShadow = hallBody.receiveShadow = true; hall.add(hallBody);
const hallRoof = new THREE.Mesh(new THREE.ConeGeometry(8.5, 3, 4), hallMat); hallRoof.rotation.y = Math.PI / 4; hallRoof.scale.z = .5; hallRoof.position.y = 8.4; hall.add(hallRoof);
for (let i = -2; i <= 2; i++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(.35, .35, 5.6, 16), hallMat); c.position.set(i * 2.6, 2.8, 3.4); c.castShadow = true; hall.add(c); }
box(15, .4, 7.4, '#cfc6b4', 0, .2, .7, .05, hall);
sign(6, 1, x => { x.fillStyle = '#2b2f86'; x.fillRect(0, 0, 512, 86); x.fillStyle = '#fff'; x.font = FONT(54); x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('MAIRIE DE GRANDEVILLE', 256, 46); }, 200, 6.3, -2.85);
tree(190, -2); tree(210, -2); house(186, -8, 1); house(214, -8, 3);
// ball
const ballTex = textTex(256, 128, x => { x.fillStyle = '#fff'; x.fillRect(0, 0, 256, 128); x.fillStyle = '#1e1a22'; for (const [px, py] of [[32, 32], [96, 70], [160, 30], [224, 72], [64, 108], [192, 110], [128, 4]]) { x.beginPath(); for (let k = 0; k < 5; k++) x.lineTo(px + Math.cos(k * 1.2566) * 15, py + Math.sin(k * 1.2566) * 15); x.fill(); } });
const ball = new THREE.Mesh(new THREE.SphereGeometry(.24, 24, 16), new THREE.MeshStandardMaterial({ map: ballTex, roughness: .5 })); ball.castShadow = true; scene.add(ball);
const confetti = []; for (let i = 0; i < 70; i++) { const m = box(.14, .14, .02, ['#ff5d9e', '#ffd23f', '#5de0ff', '#7dff7a', '#ffffff'][i % 5], 0, 0, 0, .01); m.castShadow = false; confetti.push(m); }
const tramps = []; for (let i = 0; i < 5; i++) { const g = tramp.clone(); scene.add(g); tramps.push(g); }

__FIN_DU_FICHIER__

# ---------------------------------------------------------------- parts/c_chars.html
cat > 'parts/c_chars.html' <<'__FIN_DU_FICHIER__'
// ---------- characters ----------
const faceCache = {};
function faceTex(f) {
  const key = JSON.stringify(f); if (faceCache[key]) return faceCache[key];
  const c = document.createElement('canvas'); c.width = c.height = 256; const x = c.getContext('2d');
  const ink = '#1e1a22'; x.lineCap = 'round'; x.lineJoin = 'round';
  const ey = 108 - (f.mouth === 'open' ? 4 : 0);
  if (f.blush) { x.fillStyle = 'rgba(255,110,120,.45)'; for (const s of [-1, 1]) { x.beginPath(); x.ellipse(128 + s * 70, 150, 22, 12, 0, 0, 7); x.fill(); } }
  if (f.freckles) { x.fillStyle = 'rgba(150,80,40,.6)'; for (const s of [-1, 1]) for (let i = 0; i < 3; i++) { x.beginPath(); x.arc(128 + s * (58 + i * 9), 138 + (i % 2) * 8, 3.5, 0, 7); x.fill(); } }
  for (const s of [-1, 1]) {
    const ex = 128 + s * 46;
    if (f.eyes === 'happy') { x.strokeStyle = ink; x.lineWidth = 11; x.beginPath(); x.arc(ex, ey + 8, 17, Math.PI * 1.15, Math.PI * 1.85); x.stroke(); }
    else if (f.eyes === 'closed') { x.strokeStyle = ink; x.lineWidth = 10; x.beginPath(); x.arc(ex, ey - 6, 16, Math.PI * .2, Math.PI * .8); x.stroke(); }
    else {
      const big = f.eyes === 'wide' ? 1.35 : 1; x.fillStyle = ink; x.beginPath(); x.ellipse(ex, ey, 12 * big, 17 * big, 0, 0, 7); x.fill();
      x.fillStyle = '#fff'; x.beginPath(); x.arc(ex + 4, ey - 6, 4.5 * big, 0, 7); x.fill();
      if (f.eyes === 'wide') { x.strokeStyle = ink; x.lineWidth = 5; x.beginPath(); x.ellipse(ex, ey, 22, 27, 0, 0, 7); x.stroke(); }
    }
    // brows
    const b = f.brow || 0; x.strokeStyle = ink; x.lineWidth = 9; x.beginPath();
    x.moveTo(ex - s * 18, ey - 36 + b * 6); x.lineTo(ex + s * 18, ey - 36 - b * 8 + (f.eyes === 'wide' ? -8 : 0)); x.stroke();
  }
  if (f.shades) {
    x.fillStyle = '#121016'; for (const s of [-1, 1]) { x.beginPath(); x.roundRect(128 + s * 46 - 38, ey - 26, 76, 46, 10); x.fill(); }
    x.fillRect(110, ey - 22, 36, 9); x.fillStyle = 'rgba(255,255,255,.35)'; x.fillRect(68, ey - 18, 14, 7); x.fillRect(160, ey - 18, 14, 7);
  }
  if (f.round) { x.strokeStyle = '#8a6a2c'; x.lineWidth = 6; for (const s of [-1, 1]) { x.beginPath(); x.arc(128 + s * 46, ey, 28, 0, 7); x.stroke(); } x.beginPath(); x.moveTo(110, ey); x.lineTo(146, ey); x.stroke(); }
  if (f.tear) { x.fillStyle = '#4fb6ff'; x.beginPath(); x.moveTo(176, ey + 18); x.bezierCurveTo(190, ey + 44, 186, ey + 58, 176, ey + 58); x.bezierCurveTo(166, ey + 58, 162, ey + 44, 176, ey + 18); x.fill(); }
  if (f.mustache) { x.fillStyle = '#3a2618'; x.beginPath(); x.roundRect(88, 168, 80, 20, 9); x.fill(); }
  const my = 188, m = f.mouth || 'smile', o = f.open || 0;
  x.strokeStyle = ink; x.lineWidth = 10;
  if (o > .08 || m === 'open') {
    const h = 14 + Math.max(o, m === 'open' ? .7 : 0) * 34; x.fillStyle = '#5a1b26'; x.beginPath(); x.ellipse(128, my, 30, h / 2 + 4, 0, 0, 7); x.fill();
    x.save(); x.clip(); x.fillStyle = '#ff7b8f'; x.beginPath(); x.ellipse(128, my + h / 2, 22, 12, 0, 0, 7); x.fill(); x.fillStyle = '#fff'; x.fillRect(100, my - h / 2 - 6, 56, 8); x.restore();
  } else if (m === 'smile') { x.beginPath(); x.arc(128, my - 26, 34, Math.PI * .22, Math.PI * .78); x.stroke(); }
  else if (m === 'grin') { x.fillStyle = '#fff'; x.beginPath(); x.arc(128, my - 20, 36, Math.PI * .12, Math.PI * .88); x.closePath(); x.fill(); x.stroke(); }
  else if (m === 'sad') { x.beginPath(); x.arc(128, my + 26, 28, Math.PI * 1.22, Math.PI * 1.78); x.stroke(); }
  else if (m === 'o') { x.fillStyle = '#5a1b26'; x.beginPath(); x.ellipse(128, my, 13, 17, 0, 0, 7); x.fill(); }
  else if (m === 'wavy') { x.beginPath(); for (let i = 0; i <= 6; i++) x.lineTo(98 + i * 10, my + (i % 2 ? -6 : 6)); x.stroke(); }
  else { x.beginPath(); x.moveTo(104, my); x.lineTo(152, my); x.stroke(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; faceCache[key] = t; return t;
}
const CH = {};
function character(name, o) {
  const root = new THREE.Group(); scene.add(root);
  const body = new THREE.Group(); root.add(body);
  const legs = [], arms = [];
  for (const s of [-1, 1]) {
    const lg = new THREE.Group(); lg.position.set(s * .17, .72, 0); body.add(lg);
    box(.3, .62, .32, o.pants, 0, -.31, 0, .07, lg); box(.32, .14, .4, o.shoes || '#f2f2f2', 0, -.66, .03, .05, lg); legs.push(lg);
    const ar = new THREE.Group(); ar.position.set(s * .5, 1.38, 0); body.add(ar);
    box(.24, .56, .28, o.shirt, 0, -.26, 0, .08, ar); box(.22, .16, .24, o.skin, 0, -.6, 0, .06, ar); arms.push(ar);
  }
  box(.76, .72, .42, o.shirt, 0, 1.08, 0, .1, body);
  if (o.apron) box(.62, .62, .06, '#ffffff', 0, 1.02, .22, .03, body);
  if (o.bag) { box(.18, .5, .5, '#8a5a2c', -.47, 1.0, 0, .05, body); }
  const head = new THREE.Group(); head.position.set(0, 1.44, 0); body.add(head);
  box(.7, .64, .62, o.skin, 0, .32, 0, .12, head);
  const face = new THREE.Mesh(new THREE.PlaneGeometry(.62, .62), new THREE.MeshStandardMaterial({ transparent: true, roughness: .7 }));
  face.position.set(0, .32, .312); head.add(face);
  const hs = o.hair;
  if (hs === 'short') { box(.74, .18, .66, o.hairCol, 0, .66, -.01, .07, head); box(.74, .44, .14, o.hairCol, 0, .45, -.27, .05, head); }
  if (hs === 'spiky') { box(.74, .2, .66, o.hairCol, 0, .67, -.01, .07, head); for (let i = 0; i < 3; i++) box(.2, .2, .2, o.hairCol, -.22 + i * .22, .8, .05, .05, head); }
  if (hs === 'bun') { box(.74, .2, .66, o.hairCol, 0, .66, -.01, .07, head); box(.36, .3, .3, o.hairCol, 0, .82, -.18, .12, head); box(.74, .5, .14, o.hairCol, 0, .42, -.27, .05, head); }
  if (hs === 'pony') { box(.74, .2, .66, o.hairCol, 0, .66, -.01, .07, head); box(.22, .5, .22, o.hairCol, 0, .45, -.42, .08, head); }
  if (hs === 'cap') { box(.76, .22, .68, o.capCol, 0, .7, -.01, .1, head); box(.7, .05, .34, o.capCol, 0, .6, o.capBack ? -.46 : .46, .02, head); box(.74, .2, .12, o.hairCol, 0, .5, -.28, .04, head); }
  if (hs === 'pigtails') { box(.74, .2, .66, o.hairCol, 0, .66, -.01, .07, head); box(.74, .4, .14, o.hairCol, 0, .46, -.27, .05, head); for (const s2 of [-1, 1]) box(.18, .34, .18, o.hairCol, s2 * .46, .36, -.05, .07, head); }
  if (hs === 'hood') { box(.8, .3, .72, o.hoodCol, 0, .66, -.02, .12, head); box(.8, .62, .16, o.hoodCol, 0, .36, -.3, .06, head); }
  if (hs === 'bald') { for (const s2 of [-1, 1]) box(.08, .22, .4, o.hairCol, s2 * .36, .42, -.06, .03, head); }
  if (hs === 'chef') { box(.66, .5, .6, '#ffffff', 0, .86, 0, .18, head); box(.74, .12, .66, '#f0f0f0', 0, .64, 0, .04, head); }
  const c = { root, body, legs, arms, head, face, o, state: {} }; CH[name] = c; return c;
}
function pose(c, p) {
  const r = c.root; r.visible = p.visible !== false; if (!r.visible) return;
  r.position.set(p.x, p.y || 0, p.z); r.rotation.y = p.ry || 0; r.scale.setScalar(p.s || 1);
  const ph = p.walk || 0, amp = p.walkAmp ?? .6;
  c.legs[0].rotation.x = Math.sin(ph) * amp * (p.walk ? 1 : 0); c.legs[1].rotation.x = -Math.sin(ph) * amp * (p.walk ? 1 : 0);
  c.body.position.y = p.walk ? Math.abs(Math.sin(ph)) * .06 : (p.hop || 0);
  const a = p.arms || [0, 0];
  for (let i = 0; i < 2; i++) {
    const ar = c.arms[i], s = i ? 1 : -1; let v = a[i];
    if (p.walk && v === 0) { ar.rotation.x = -Math.sin(ph) * amp * (i ? -1 : 1) * .8; ar.rotation.z = 0; continue; }
    if (typeof v === 'number') { ar.rotation.z = s * v; ar.rotation.x = 0; } else { ar.rotation.z = s * v[0]; ar.rotation.x = v[1]; }
  }
  c.body.rotation.x = p.bend || 0;
  c.head.rotation.x = p.headX || 0; c.head.rotation.z = p.headZ || 0; c.head.rotation.y = p.headY || 0;
  const f = Object.assign({}, c.o.face, p.face || {}); if (p.talk > .08) f.open = Math.round(p.talk * 4) / 4;
  c.face.material.map = faceTex(f); c.face.material.needsUpdate = true;
}
const WAVE = t => [0, [2.6 + Math.sin(t * 12) * .35, 0]];
const CHEER = t => [[2.7 + Math.sin(t * 14) * .2, 0], [2.7 - Math.sin(t * 14) * .2, 0]];
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- parts/d_cast.html
cat > 'parts/d_cast.html' <<'__FIN_DU_FICHIER__'
// cast
const timeo = character('timeo', { skin: '#f1c9a5', shirt: '#ff8a3d', pants: '#2a3a6b', hair: 'spiky', hairCol: '#e8b23a', face: { eyes: 'n', mouth: 'grin', freckles: true, blush: true } });
const voisin = character('voisin', { skin: '#f0c39c', shirt: '#7d7d8c', pants: '#3a3a4a', shoes: '#222', hair: 'bald', hairCol: '#bbbbbb', face: { eyes: 'n', mouth: 'flat', mustache: true } });
const coachC = character('coach', { skin: '#c98a5a', shirt: '#c0392b', pants: '#2a2a3a', hair: 'cap', capCol: '#c0392b', hairCol: '#2a1c14', face: { eyes: 'n', mouth: 'smile', mustache: true } });
const gardien = character('gardien', { skin: '#8d5a3b', shirt: '#f5c400', pants: '#2a2a3a', hair: 'short', hairCol: '#1e1410', face: { eyes: 'n', mouth: 'flat' } });
const cast_ = box(.36, .7, .38, '#ffffff', 0, -.33, 0, .08, gardien.legs[1]);
const BLUE = ['#2f8ae0', '#2f8ae0', '#2f8ae0', '#2f8ae0', '#2f8ae0'];
const team = [0, 1, 2, 3, 4].map(i => character('team' + i, { skin: ['#f1c9a5', '#8d5a3b', '#c98a5a', '#f3cfb3', '#6b3f28'][i], shirt: BLUE[i], pants: '#ffffff',
  hair: ['short', 'pony', 'spiky', 'bun', 'cap'][i], hairCol: ['#2a1c14', '#1e1410', '#7a4a2c', '#e8b23a', '#2a1c14'][i], capCol: '#2f5fb0', face: { eyes: 'n', mouth: 'smile', blush: i % 2 === 0 } }));
const rivals = [0, 1, 2, 3].map(i => character('rival' + i, { skin: ['#c98a5a', '#f1c9a5', '#6b3f28', '#f3cfb3'][i], shirt: '#7a3cc0', pants: '#1e1a22',
  hair: ['short', 'spiky', 'short', 'pony'][i], hairCol: ['#1e1410', '#2a1c14', '#1e1410', '#7a4a2c'][i], face: { eyes: 'n', mouth: 'grin', brow: .6 } }));
const giant = character('giant', { skin: '#c98a5a', shirt: '#7a3cc0', pants: '#1e1a22', hair: 'short', hairCol: '#1e1410', shoes: '#ffd23f', face: { eyes: 'n', mouth: 'grin', brow: 1 } });
const maireG = character('maireG', { skin: '#f3cfb3', shirt: '#2b2f86', pants: '#2a2a3a', hair: 'bald', hairCol: '#999999', apron: false, face: { eyes: 'n', mouth: 'flat', round: true, mustache: true } });
box(.12, .8, .44, '#c0392b', 0, 1.1, .02, .02, maireG.body).rotation.z = .6;

__FIN_DU_FICHIER__

# ---------------------------------------------------------------- parts/e_overlay.html
cat > 'parts/e_overlay.html' <<'__FIN_DU_FICHIER__'
// ---------- 2D overlay ----------
const out = document.getElementById('out'), ctx = out.getContext('2d');
function text2(s, x, y, size, fill, { stroke = '#1e1a22', lw = 0, font = 'Baloo', align = 'center' } = {}) {
  ctx.font = `800 ${size}px ${font}`; ctx.textAlign = align; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  if (lw) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.strokeText(s, x, y); } ctx.fillStyle = fill; ctx.fillText(s, x, y);
}
const proj = v => { const p = v.clone().project(camera); return [(p.x + 1) / 2 * W, (1 - p.y) / 2 * H, p.z]; };
const headTop = (c, extra = .9) => { const v = new THREE.Vector3(); c.head.getWorldPosition(v); return v.add(new THREE.Vector3(0, extra * c.root.scale.y, 0)); };
function bubble(str, x, y, k, size = 26) {
  if (k <= 0) return; str = str.replace(/ ([!?:])/g, '\u00a0$1'); ctx.save(); ctx.translate(x, y); const s = back(clamp(k)); ctx.scale(s, s);
  ctx.font = `800 ${size}px Nun`; const words = str.split(' '), lines = []; let cur = '';
  for (const w of words) { const tr = cur ? cur + ' ' + w : w; if (ctx.measureText(tr).width > 360 && cur) { lines.push(cur); cur = w; } else cur = tr; } lines.push(cur);
  const lh = size * 1.2, bw = Math.max(...lines.map(l => ctx.measureText(l).width)) + 36, bh = lines.length * lh + 20;
  ctx.fillStyle = '#fff'; ctx.strokeStyle = '#1e1a22'; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.roundRect(-bw / 2, -bh, bw, bh, 18); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-12, -2); ctx.lineTo(0, 16); ctx.lineTo(12, -2); ctx.fill(); ctx.stroke(); ctx.fillRect(-14, -8, 28, 8);
  lines.forEach((l, i) => text2(l, 0, -bh + 10 + lh * (i + .5), size, '#1e1a22', { font: 'Nun' }));
  ctx.restore();
}
function bubbleOn(c, str, k, dy = 1.0) { if (k <= 0) return; const [x, y, z] = proj(headTop(c, dy)); if (z < 1) bubble(str, clamp(x, 190, W - 190), clamp(y, 140, H - 200), k); }
function label(c, str, col = '#fff', dy = 1.25, size = 44) { const [x, y, z] = proj(headTop(c, dy)); if (z < 1) text2(str, x, Math.max(80, y), size, col, { lw: 10 }); }
const POPS = [];
function pops(t) {
  for (const p of POPS) {
    const k = (t - p.t) / 1.1; if (k < 0 || k > 1) continue;
    const c = p.c; const v = !c.root ? (() => { const w = new THREE.Vector3(); c.getWorldPosition(w); return w.add(new THREE.Vector3(0, (p.dy || 1) * c.scale.y, 0)); })() : headTop(c, p.dy || 1);
    const [x, y, z] = proj(v); if (z > 1) continue;
    ctx.globalAlpha = 1 - Math.pow(k, 3); const s = back(clamp(k * 4)) * (p.size || 1);
    ctx.save(); ctx.translate(clamp(x + (p.ox || 0), 70, W - 70), Math.max(90, y - k * 110 + (p.oy || 0))); ctx.scale(s, s);
    text2(p.txt || '+1 cm', 0, 0, 40, p.col || '#7dff7a', { lw: 9 }); ctx.restore(); ctx.globalAlpha = 1;
  }
}
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- parts/f_direction.html
cat > 'parts/f_direction.html' <<'__FIN_DU_FICHIER__'
function caption(t) {
  let best = null;
  TL.lines.forEach(l => { if (t < l.start || t > l.start + l.dur + .15) return; l.words.forEach(w => { if (w.t <= t) best = w; }); });
  if (!best) return;
  const k = prog(t, best.t, best.t + .12), boing = /^huss/i.test(best.w), s = lerp(boing ? 1.8 : 1.28, 1, back(k));
  ctx.save(); ctx.translate(W / 2, H * .6); ctx.scale(s, s); if (boing) ctx.rotate(Math.sin(t * 30) * .05);
  text2(boing ? 'HUSS !' : best.w, 0, 0, boing ? 96 : 66, best.e ? '#ffd23f' : '#ffffff', { lw: boing ? 16 : 12 }); ctx.restore();
}

// ---------- direction ----------
const jumpY = (t, t0, d, h) => h * Math.sin(Math.PI * clamp((t - t0) / d));
const hop = (t, period, h) => h * Math.abs(Math.sin(Math.PI * t / period));
function shots() {
  return [
    [0, [0, 3.2, 15], [0, 3, 12.5], [0, 1.4, 2], [0, 1.4, 2], 50],
    [WT('intro', /^Timéo/) - .15, [-5, 1.1, 5.2], [-5, 1.05, 4.7], [-5, .9, 2.6], [-5, .9, 2.6], 42],
    [S('saute') - .1, [-4.6, 1.5, 7.8], [.4, 1.5, 7.8], [-4.4, 1.2, 2.6], [.6, 1.2, 2.6], 48],
    [S('b1') - .2, [7, 2, 11], [7, 2, 10.5], [2.6, 1.8, 4.8], [2.6, 1.8, 4.8], 48],
    [S('v1') - .1, [8.4, 2.6, 11], [8.1, 2.6, 10.5], [3.9, 2.2, 4.5], [3.9, 2.2, 4.5], 50],
    [S('trampo') - .1, [-5.6, 2.2, 6.6], [-6, 2.3, 6], [-9, 1.9, -1.4], [-9, 2.1, -1.4], 50],
    [WT('trampo', /^par-dessus/) - .1, [-2.5, 2.2, 8], [-3, 2.2, 7.6], [-6.2, 1.6, -1.2], [-6.2, 1.6, -1.2], 52],
    [WT('trampo', /^jusqu/) - .1, [41, 2.2, 9], [40.5, 2.2, 8.4], [38, 1.5, .5], [37.4, 1.5, .5], 52],
    [WT('trampo', /^bizarre/) - .25, [34, 1.5, 4.6], [34.2, 1.5, 4.2], [35.4, 1.3, .8], [35.4, 1.3, .8], 45],
    [S('defi') - .1, [0, 13, 24], [0, 12, 21], [0, 1, -3], [0, 1, -3], 50],
    [S('gardien') - .1, [-57.6, 1.9, 3.6], [-57.9, 1.85, 3.2], [-60, 1, -2.3], [-60, .9, -2.3], 48],
    [S('coach') - .1, [59.6, 1.9, 7.8], [59.6, 1.9, 7], [59.9, 1.2, -1.2], [59.9, 1.2, -1.2], 52],
    [S('b2') - .2, [61.6, .6, 4.6], [61.6, .6, 4.4], [61.2, 2, 0], [61.2, 2.2, 0], 58],
    [S('rires') - .1, [60.9, 1.5, 5.4], [60.9, 1.45, 4.9], [60.9, 1, .2], [60.9, 1, .2], 46],
    [S('match') - .2, [130, 6.5, -35], [130, 6, -34], [130, 1, -14], [130, 1, -14], 52],
    [S('b3') - .15, [130, 1.6, -18.5], [130, 1.6, -19.2], [130, 1.6, -25.4], [130, 1.6, -25.4], 55],
    [S('arret') - .1, [130, 8, -8.5], [130, 8.2, -9.5], [130, 8.8, -29.5], [130, 8.8, -29.5], 45],
    [WT('arret', /^Zéro/) - .1, [130, 4, -2], [130, 4.4, 0], [116, 3, -8], [114, 3.5, -8], 55],
    [S('penalty') - .1, [133.4, 2.6, -7.5], [133, 2.4, -8.5], [130, 1.4, -22], [130, 1.4, -22], 50],
    [S('saut') - .1, [130.6, .6, -20.8], [130.6, .6, -21.2], [130, 2.6, -25.6], [130, 3, -25.6], 62],
    [S('gagne') - .1, [130, 3, -13], [130, 3.4, -12], [130, 1.5, -24], [130, 1.8, -24], 55],
    [S('c1') - .1, [129.6, 1.6, -18.6], [129.6, 1.6, -19.1], [129.6, 1.3, -22.3], [129.6, 1.3, -22.3], 46],
    [S('fin') - .1, [200, 4, 17], [200, 4.5, 15], [200, 4, -6], [200, 4.2, -6], 52],
    [WT('fin', /^Et$/) - .1, [0, 2.6, 14], [0, 2.8, 12.5], [0, 2, 0], [0, 2.2, 0], 55],
  ];
}
let SH;
function applyCamera(t) {
  let i = 0; SH.forEach((s, j) => { if (t >= s[0]) i = j; });
  const s = SH[i], tEnd = i + 1 < SH.length ? SH[i + 1][0] : TL.total, k = ease(prog(t, s[0], tEnd));
  const pos = s[1].map((v, j) => lerp(v, s[2][j], k)), look = s[3].map((v, j) => lerp(v, s[4][j], k));
  camera.position.set(...pos); camera.lookAt(...look); camera.fov = s[5]; camera.updateProjectionMatrix();
  sun.position.set(look[0] + 8, 18, look[2] + 12); sun.target.position.set(look[0], 0, look[2]); sun.target.updateMatrixWorld();
}
const P = (c, p) => pose(c, Object.assign({ visible: true }, p));
const hideAll = () => { for (const c of Object.values(CH)) c.root.visible = false; ball.visible = false; confetti.forEach(m => m.visible = false); tramps.forEach(g => g.visible = false); cast_.visible = false; };
const BOINGS = [];   // [time, char] big "BOING" bursts above Timéo
let hallPink = 0;
function update(t) {
  hideAll(); updateFans(t, (t > S('arret') && t < S('penalty') - .2) ? 1 : (t > S('gagne') - .1 && t < S('fin') - .2 ? 1.6 : (t > S('match') && t < S('gagne') ? .15 : 0)));
  scoreTex.redrawKey = scoreTex.redrawKey || '';
  const sk = t > S('gagne') - .1 ? 'win' : 'zero'; if (scoreTex.redrawKey !== sk) { scoreTex.redraw(sk === 'win' ? 1 : 0, 0, sk === 'win' ? 'BOULANVILLE GAGNE !' : ''); scoreTex.redrawKey = sk; }
  // A-D: street
  if (t < S('trampo') - .1) {
    [0, 1, 2, 3].forEach(i => P(team[i], { x: .5 + i * 1.6, z: 3.2 + (i % 2) * 1.2, ry: i % 2 ? Math.PI * .8 : .3, s: .75, walk: t < S('saute') ? t * 6 + i : 0, arms: [0, 0], face: { eyes: t > S('v1') - .3 ? 'wide' : 'happy', mouth: t > S('v1') - .3 ? 'o' : 'grin' } }));
    if (t < S('saute')) { ball.visible = true; const ph = (t * .9) % 1, a = Math.floor(t * .9) % 3; ball.position.set(.5 + a * 1.6 + ph * 1.6, .24 + Math.abs(Math.sin(ph * Math.PI)) * .8, 3.8); ball.rotation.x = t * 8; }
    let x = -5, y = 0, z = 2.6, ry = 0, face = { eyes: 'happy', mouth: 'grin', freckles: true, blush: true }, arms = [[.4, 0], [.4, 0]];
    if (t > S('saute') - .1) { const k = prog(t, S('saute'), S('b1') - .1); x = lerp(-5, 1, k); y = hop(t - S('saute'), .5, .8); ry = Math.PI / 2; arms = [[2.4, 0], [2.4, 0]]; }
    if (t > S('b1') - .2) { const k = prog(t, S('b1') - .2, S('b1') + .45); x = lerp(1, 3, k); z = lerp(2.6, 5.2, k); y = lerp(0, 1.9, k) + Math.sin(Math.PI * k) * 2.2; arms = [[2.8, 0], [2.8, 0]]; ry = .6; }
    if (t > S('b1') + .45) { x = 3; z = 5.2; y = 1.9 + hop(t, .45, .5); ry = .4; face = { eyes: 'happy', mouth: 'open', freckles: true, blush: true }; }
    P(timeo, { x, y, z, ry, s: .62, arms, face });
    if (t > S('v1') - .3) P(voisin, { x: 5.6, z: 3, ry: -.9, s: 1, talk: talk('V', t), arms: [[2.5 + Math.sin(t * 16) * .2, -.3], [2.5 - Math.sin(t * 16) * .2, -.3]], headX: -.2, face: { eyes: 'n', mouth: 'flat', brow: 1, mustache: true } });
  }
  // E: trampoline, hedge, school
  else if (t < S('defi') - .1) {
    const tHedge = WT('trampo', /^par-dessus/), tSchool = WT('trampo', /^jusqu/);
    let x = -9, z = -1.4, y = .66 + hop(t - S('trampo'), .75, 2.4);
    if (t > tHedge - .1 && t < tSchool - .1) { const k = prog(t, tHedge, tSchool - .2); x = lerp(-9, -3, k); z = lerp(-1.4, -1, k); y = .66 * (1 - k) + Math.sin(Math.PI * k) * 3.2; }
    if (t >= tSchool - .1) { const k = prog(t, tSchool, WT('trampo', /^bizarre/)); x = lerp(41, 36.5, k); z = 1.2; y = hop(t, .5, 1); }
    P(timeo, { x, y, z, ry: t >= tSchool - .1 ? -Math.PI / 2 : (t > tHedge - .1 ? Math.PI / 2 : 0), s: .62, arms: [[2.6, 0], [2.6, 0]], face: { eyes: 'happy', mouth: 'open', freckles: true, blush: true } });
    if (t >= tSchool - .1) [0, 1, 2].forEach(i => P(team[i], { x: 33.6 + i * .9, z: .4 + (i % 2) * .5, ry: .5, s: .75, headY: .3, face: { eyes: 'n', mouth: 'flat', brow: -.6 } }));
  }
  // F: the challenge (town from above)
  else if (t < S('gardien') - .1) {
    [0, 1, 2, 3].forEach(i => P(team[i], { x: -2 + i * 1.5, z: 3.4, s: .75, face: { eyes: 'wide', mouth: 'o' } }));
  }
  // G: goalkeeper falls off the sofa
  else if (t < S('coach') - .1) {
    const fall = WT('gardien', /^tombant/) - .1, k = prog(t, fall, fall + .5), down = t > fall + .5;
    P(gardien, { x: -60, y: lerp(.44, .1, k), z: lerp(-2.4, -1.2, k), s: .78, ry: 0, sit: false, bend: lerp(0, 1.45, ease(k)),
      arms: k > 0 ? [[2.4 + Math.sin(t * 20) * .3, 0], [2.4 - Math.sin(t * 20) * .3, 0]] : [[.4, -1], [.4, -1]], face: { eyes: down ? 'closed' : (k > 0 ? 'wide' : 'n'), mouth: down ? 'wavy' : (k > 0 ? 'o' : 'flat') } });
    if (t < fall) { gardien.root.position.y = .44; gardien.legs.forEach(l => l.rotation.x = -1.4); }
    cast_.visible = t > WT('gardien', /^cassé/) - .2;
  }
  // H-J: training field
  else if (t < S('match') - .2) {
    const nobody = t > WT('coach', /^Personne/), laugh = t > S('rires') - .1;
    P(coachC, { x: 57.8, z: -.6, ry: .9, s: 1, arms: [0, [1.5, -.2]], face: { eyes: t > S('b2') ? 'wide' : 'n', mouth: laugh ? 'open' : 'smile', mustache: true } });
    team.forEach((c, i) => P(c, { x: 60 + i * 1.05, z: -2.2 + (i % 2) * .6 + (nobody && !laugh ? -.6 : 0), ry: -.4, s: .75, headY: nobody && !laugh && t < S('b2') ? Math.sin(t * 10 + i) * .4 : 0, hop: laugh ? Math.abs(Math.sin(t * 14 + i)) * .05 : 0,
      face: { eyes: laugh ? 'happy' : 'n', mouth: laugh ? 'open' : (nobody ? 'flat' : 'smile') } }));
    if (t > WT('coach', /^seul/) - .3) {
      const k = prog(t, S('b2') - .25, S('b2') + .4);
      P(timeo, { x: lerp(65, 61.2, prog(t, WT('coach', /^seul/) - .3, S('b2') - .25)), y: k > 0 && k < 1 ? Math.sin(Math.PI * k) * 2 : 0, z: .4, s: .62, ry: -.2,
        arms: k > 0 && k < 1 ? [[2.8, 0], [2.8, 0]] : [0, [2.6, 0]], face: { eyes: laugh ? 'n' : 'happy', mouth: laugh ? 'smile' : 'grin', freckles: true, blush: true } });
    }
  }
  // K-O: the match
  else if (t < S('fin') - .1) {
    const GL = -25.3;
    let tx = 130, ty = 0, arms = [[.6, 0], [.6, 0]], face = { eyes: 'n', mouth: 'grin', brow: .6, freckles: true, blush: true }, bend = .15;
    rivals.forEach((c, i) => P(c, { x: 126 + i * 2.6, z: -14 - (i % 2) * 1.5, ry: Math.PI, s: .8, walk: t < S('penalty') ? t * 7 + i : 0, face: { eyes: t > S('arret') ? 'wide' : 'n', mouth: t > S('arret') ? 'o' : 'grin', brow: .6 } }));
    team.slice(0, 4).forEach((c, i) => P(c, { x: 125 + i * 3.2, z: -18 + (i % 2) * 2, ry: 0, s: .75, arms: t > S('gagne') - .1 ? CHEER(t + i) : [0, 0], face: { eyes: t > S('gagne') - .1 ? 'happy' : 'n', mouth: t > S('gagne') - .1 ? 'open' : 'smile' } }));
    // shots during "match" + saves during "b3"
    const shotsT = [S('match') + .4, S('match') + 1.4, S('match') + 2.4, ...L.b3.words.filter((w, i) => i % 3 === 0).map(w => w.t - .35)];
    for (let j = 0; j < shotsT.length; j++) { const t0 = shotsT[j], k = prog(t, t0, t0 + .45); if (t > t0 && t < t0 + .9) {
      const side = (j % 2 ? 1 : -1) * 1.6; ball.visible = true; ball.position.set(lerp(126 + j % 4 * 2, 130 + side, k), .3 + Math.sin(Math.PI * k) * 1.3 + k * .6, lerp(-15, GL + .4, k)); ball.rotation.x = t * 12;
      tx = 130 + side * ease(prog(t, t0 + .1, t0 + .4)); ty = jumpY(t, t0 + .1, .6, 1.1); arms = [[2.7, 0], [2.7, 0]]; face = { eyes: 'wide', mouth: 'grin', freckles: true, blush: true };
      if (k >= 1) ball.position.set(tx, ty + 1.2, GL + .5); } }
    // penalty
    if (t > S('penalty') - .1 && t < S('gagne') - .1) {
      const run = prog(t, S('penalty') + .8, S('saut') + .25);
      P(giant, { x: 130, z: lerp(-14.5, -19.8, run), ry: Math.PI, s: 1.55, walk: run > 0 && run < 1 ? t * 9 : 0, face: { eyes: t > S('saut') + 1 ? 'wide' : 'n', mouth: t > S('saut') + 1 ? 'o' : 'grin', brow: 1 } });
      rivals.forEach(c => c.root.visible = false);
      const kick = S('saut') + .25, kb = prog(t, kick, kick + .9), catchT = kick + .75;
      ball.visible = true;
      if (t < kick) ball.position.set(130, .24, -20.5);
      else if (t < catchT) ball.position.set(lerp(130, 131.2, kb), .24 + kb * 3.4, lerp(-20.5, GL + .2, kb));
      bend = t < kick ? .35 : 0;
      if (t > kick - .1) { const j = jumpY(t, kick - .05, 1.6, 2.9); ty = j; tx = lerp(130, 131.1, prog(t, kick - .05, catchT)); arms = [[2.9, 0], [2.9, 0]]; face = { eyes: 'wide', mouth: 'open', freckles: true, blush: true }; }
      if (t >= catchT) ball.position.set(tx, ty + 1.25, GL + .45);
    }
    if (t > S('gagne') - .1) { ty = hop(t, .45, .9); arms = CHEER(t); face = { eyes: 'happy', mouth: 'open', freckles: true, blush: true }; ball.visible = false;
      confetti.forEach((m, i) => { m.visible = true; const ph = ((t - S('gagne')) * .35 + rnd(i)) % 1; m.position.set(124 + rnd(i + 3) * 12, 7 - ph * 7, -27 + rnd(i + 7) * 12); m.rotation.set(t * 3 + i, t * 2 + i, 0); }); }
    if (t > S('c1') - .15) { tx = 130.3; ty = 0; P(coachC, { x: 129.1, z: -22.2, ry: .5, s: 1, talk: talk('C', t), arms: [0, [2.2, -.6]], face: { eyes: 'happy', mouth: 'smile', mustache: true } }); arms = [[2.7, 0], [.4, 0]]; face = { eyes: 'happy', mouth: 'grin', freckles: true, blush: true }; }
    P(timeo, { x: tx, y: ty, z: t > S('c1') - .15 ? -22.3 : GL + .3, s: .62, ry: t > S('c1') - .15 ? -.4 : 0, bend: t > S('c1') - .15 ? 0 : bend, arms, face });
  }
  // P-Q: pink town hall, then jumping is mandatory
  else {
    const toEt = WT('fin', /^Et$/) - .1;
    if (t < toEt) {
      const k = back(prog(t, S('fin') + .4, S('fin') + .9)); hallMat.color.set('#e8e0d0').lerp(new THREE.Color('#ff7fb8'), clamp(k)); hall.scale.setScalar(1 + .04 * Math.sin(Math.PI * clamp(prog(t, S('fin') + .4, S('fin') + .9))));
      P(maireG, { x: 200, z: 1.8, s: 1, face: { eyes: 'n', mouth: 'sad', brow: -1, round: true, mustache: true, tear: t > S('fin') + 1 }, headX: .2 });
    } else {
      tramps.forEach((g, i) => { g.visible = true; g.position.set(-12 + i * 6, 0, 1.4); });
      const all = t > S('b4') - .2;
      [timeo, ...team.slice(0, 4)].forEach((c, i) => { const h = all ? jumpY(t, S('b4') - .2, .8, 3) : hop(t + i * .17, .7, 1.6);
        P(c, { x: -12 + i * 6, y: .66 + h, z: 1.4, s: c === timeo ? .62 : .75, arms: [[2.7, 0], [2.7, 0]], face: c === timeo ? { eyes: 'happy', mouth: 'open', freckles: true, blush: true } : { eyes: 'happy', mouth: 'open' } }); });
      P(voisin, { x: 3, z: 3.4, s: 1, ry: -.2, y: all ? jumpY(t, S('b4') - .2, .8, 1.2) : 0, arms: [[2.7, 0], [2.7, 0]], face: { eyes: 'happy', mouth: 'open', mustache: true } });
      if (all) confetti.forEach((m, i) => { m.visible = true; const ph = ((t - S('b4')) * .5 + rnd(i)) % 1; m.position.set(-8 + rnd(i + 3) * 16, 7 - ph * 7, -2 + rnd(i + 7) * 6); m.rotation.set(t * 3 + i, t * 2 + i, 0); });
    }
  }
}
function defiCard(t) {
  const a = S('defi'), b = S('gardien') - .1; if (t < a + .1 || t > b) return;
  const k = back(prog(t, a + .1, a + .45)); ctx.save(); ctx.translate(W / 2, H * .34); ctx.scale(k, k); ctx.rotate(-.03);
  ctx.fillStyle = '#fff8e6'; ctx.strokeStyle = '#1e1a22'; ctx.lineWidth = 6; ctx.beginPath(); ctx.roundRect(-290, -250, 580, 500, 18); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#e0533d'; ctx.fillRect(-290, -250, 580, 90); text2('DÉFI !', 0, -205, 64, '#ffffff', { lw: 0 });
  text2('De : Grandeville', 0, -120, 38, '#2b2f86');
  if (t > WT('defi', /^match/) - .1) text2('MATCH DE FOOT', 0, -40, 50, '#1e1a22');
  if (t > WT('defi', /^perd/) - .1) { text2('Le perdant repeint', 0, 50, 40, '#1e1a22'); text2('sa mairie', 0, 100, 40, '#1e1a22'); }
  if (t > WT('defi', /^rose/) - .15) { const g = back(prog(t, WT('defi', /^rose/) - .15, WT('defi', /^rose/) + .2)); ctx.save(); ctx.translate(0, 175); ctx.scale(g, g); ctx.rotate(-.08); text2('EN ROSE !', 0, 0, 66, '#ff5da8', { lw: 10 }); ctx.restore(); }
  ctx.restore();
}
function boingBurst(t) {
  const g3 = id => L[id].words.filter((w, i) => i % 3 === 0).map(w => w.t);
  const times = [...g3('b1'), S('b2'), ...g3('b3'), WT('saut', /^si$/), ...g3('b4')];
  for (const t0 of times) { const k = (t - t0) / .7; if (k < 0 || k > 1) continue;
    const [x, y] = proj(headTop(timeo, .6)); ctx.save(); ctx.translate(clamp(x, 160, W - 160), clamp(y - 40, 120, H * .45)); ctx.globalAlpha = 1 - k * k;
    for (let i = 0; i < 10; i++) { const a = i / 10 * 6.28; ctx.strokeStyle = '#ffd23f'; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(Math.cos(a) * 60 * (1 + k), Math.sin(a) * 60 * (1 + k)); ctx.lineTo(Math.cos(a) * 95 * (1 + k), Math.sin(a) * 95 * (1 + k)); ctx.stroke(); }
    ctx.restore(); ctx.globalAlpha = 1; }
}
function overlay(t) {
  bubbleOn(voisin, 'Timéo ! Arrête de sauter sur ma voiture !', t > S('v1') - .2 && t < E('v1') + .4 ? prog(t, S('v1') - .1, S('v1') + .1) : 0, 1.0);
  bubbleOn(coachC, 'Timéo, t’es le meilleur gardien de l’histoire !', t > S('c1') - .2 && t < E('c1') + .4 ? prog(t, S('c1') - .1, S('c1') + .1) : 0, 1.0);
  if (t > WT('rires', /^mesure/) && t < S('match') - .2) label(timeo, '1 m 20', '#ffffff', 1.0, 46);
  if (t > WT('trampo', /^bizarre/) - .2 && t < S('defi') - .1) team.slice(0, 3).forEach((c, i) => { const [x, y] = proj(headTop(c, .9)); text2('?', x, y - Math.sin(t * 6 + i) * 6, 54, '#ffd23f', { lw: 10 }); });
  defiCard(t); boingBurst(t); caption(t);
}
function render(t) {
  update(t); applyCamera(t); renderer.render(scene, camera);
  ctx.drawImage(renderer.domElement, 0, 0); overlay(t);
  const tl = TL.total; if (t > tl - .5) { ctx.fillStyle = `rgba(0,0,0,${prog(t, tl - .5, tl)})`; ctx.fillRect(0, 0, W, H); }
}
window.init = async tl => {
  TL = tl; L = {}; tl.lines.forEach(l => L[l.id] = l); SH = shots();
  await document.fonts.load('800 70px Baloo'); await document.fonts.load('800 30px Nun');
  scoreTex.redraw(0, 0, ''); render(0); return true;
};
window.frame = (t, type) => { render(t); return out.toDataURL(type, .9); };
window.ready = true;
</script></body></html>
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- setup.sh
cat > 'setup.sh' <<'__FIN_DU_FICHIER__'
#!/usr/bin/env bash
# One-time installation (Linux / macOS / WSL). Needs: python3 (3.10+), node (18+), ffmpeg with rubberband.
set -e
cd "$(dirname "$0")"
pip install "setuptools<81" numpy onnxruntime kokoro-onnx pyworld faster-whisper
npm install
mkdir -p fonts && cp node_modules/@fontsource/baloo-2/files/baloo-2-latin-800-normal.woff2 node_modules/@fontsource/nunito/files/nunito-latin-800-normal.woff2 fonts/
npx playwright install chromium
mkdir -p models/kokoro
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -f models/kokoro/$f ] || curl -L -o models/kokoro/$f https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f
done
echo "Install complete. Run: bash build.sh"
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- build.sh
cat > 'build.sh' <<'__FIN_DU_FICHIER__'
#!/usr/bin/env bash
# Builds the whole video: voices -> pronunciation check -> 3D render -> sound mix -> final MP4.
set -e
cd "$(dirname "$0")"
python3 tts.py models/kokoro                       # 1. voices + timeline (script.json + voice_profile.json)
python3 check_pronunciation.py || true             # 2. Whisper check (optional, does not block)
cat parts/a_head.html parts/b_world.html parts/c_chars.html parts/d_cast.html parts/e_overlay.html parts/f_direction.html > index.html
node render.js                                     # 3. 3D render, 25 fps, 1080x1920 -> build/video.mp4
python3 mix.py                                     # 4. voices + music + sound effects -> build/mix.wav
ffmpeg -loglevel error -y -i build/video.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart video_finale.mp4
echo "Done: video_finale.mp4"
__FIN_DU_FICHIER__

# ---------------------------------------------------------------- README.md
cat > 'README.md' <<'__FIN_DU_FICHIER__'
# Kit vidéo TikTok : 3D en blocs, voix off française, rafales « HUSS »

Ce kit fabrique une vidéo verticale 1080×1920 d'environ 60 s, entièrement par code et sans service payant :

1. Il génère les voix off françaises avec Kokoro, en local, puis applique l'intonation réglée dans `voice_profile.json`.
2. Il vérifie la prononciation avec Whisper.
3. Il fait le rendu 3D (three.js, personnages en blocs) image par image, à 25 images/s.
4. Il génère la musique et les bruitages, puis mixe le tout.
5. Il produit le fichier final `video_finale.mp4`.

L'histoire fournie en exemple, « Le gardien de Boulanville », est originale. Remplacez-la par la vôtre.

---

## 1. Installation (une seule fois)

Il faut au préalable :

- Python 3.10 ou plus récent ;
- Node 18 ou plus récent ;
- `ffmpeg`, compilé avec `rubberband`. Sous Ubuntu : `sudo apt install ffmpeg`. Sous macOS : `brew install ffmpeg`.

Ensuite :

```bash
bash setup.sh
```

Le script installe les paquets Python et Node, ainsi que Chromium pour le rendu. Il télécharge aussi le modèle de voix Kokoro, environ 340 Mo, dans `models/kokoro/`.

## 2. Fabriquer la vidéo

```bash
bash build.sh
```

| Étape | Fichier | Durée indicative (CPU) |
|---|---|---|
| Voix et timeline | `tts.py` → `build/audio/*.wav`, `build/timeline.json` | 1 à 2 min |
| Contrôle de prononciation | `check_pronunciation.py` | 1 min (le modèle Whisper, 480 Mo, est téléchargé au 1er lancement) |
| Rendu 3D | `render.js` → `build/video.mp4` | 5 à 10 min |
| Mixage audio | `mix.py` → `build/mix.wav` | 10 s |
| Montage final | `ffmpeg` → **`video_finale.mp4`** | 5 s |

Pour voir quelques images fixes sans lancer tout le rendu, par exemple aux secondes 3,2 et 10,5 :

```bash
python3 tts.py && cat parts/*.html > index.html && node render.js stills 3.2 10.5   # → build/still_3.2.jpg …
```

---

## 3. Écrire votre histoire : `script.json`

Le fichier contient une ligne par réplique, lues dans l'ordre :

```json
{"id": "intro", "who": "N", "mood": "excited", "text": "À Boulanville, tout le monde adore le foot. Tout le monde... sauf *Timéo*.", "pad": 0.1},
{"id": "b1", "who": "N", "huss": true, "text": "*Huss ! Huss !*", "pad": 0.3},
{"id": "v1", "who": "V", "mood": "excited", "text": "Timéo ! Arrête de sauter sur ma voiture !", "pad": 0.2}
```

| Champ | Rôle |
|---|---|
| `id` | Nom unique de la réplique. La mise en scène s'y réfère, voir §4. |
| `who` | Voix à utiliser : `N` narrateur, `C` coach, `V` voisin, ou une voix que vous ajoutez dans `voice_profile.json`. |
| `mood` | Change le débit : `normal`, `excited`, `hype`, `sad`, `deadpan`, `suspense`. |
| `text` | Texte du sous-titre. Les mots entre `*étoiles*` s'affichent en jaune et en gros. |
| `say` | Facultatif. Texte réellement prononcé, quand il doit différer du sous-titre. Exemple : `"say": "bé-ère"` pour un sigle. |
| `pad` | Silence ajouté après la réplique, en secondes, avant application de `pad_scale`. |
| `at` | Facultatif. Heure minimale de départ de la réplique, en secondes. |
| `huss` | `true` produit des rafales « HUSS », une par mot « Huss » du texte, au rythme réglé dans `voice_profile.json`. |

**Règles pour une prononciation sans faute :**

- Écrivez les nombres en lettres : « un mètre vingt » et non « 1 m 20 ».
- Lancez `python3 check_pronunciation.py` après `tts.py`. Une ligne marquée `<-- to check` doit être écoutée.
  - Un écart sur un prénom inventé (« Timéo » entendu « Timur ») ou sur des chiffres n'est pas une faute.
  - Un mot courant mal entendu est une faute. Changez le mot ou utilisez `say`. Exemple : « rigole » était lu « rigore » à chaque essai, il a été remplacé par « se moque ».
- Si un mot anglais est mal lu (foot, coach…), ajoutez une correction dans `ipa_fixes` de `voice_profile.json`, au format `[phonèmes produits, phonèmes voulus]`.
  - Pour voir les phonèmes produits : `python3 -c "from kokoro_onnx import Kokoro; K=Kokoro('models/kokoro/kokoro-v1.0.onnx','models/kokoro/voices-v1.0.bin'); print(K.tokenizer.phonemize('le coach', 'fr-fr'))"`

## 4. Mise en scène : `parts/*.html`

`build.sh` assemble les fichiers dans cet ordre pour former `index.html` :

| Fichier | Contenu |
|---|---|
| `a_head.html` | Scène three.js, lumières, helpers (`box`, `panel`, `textTex`, `lerp`, `ease`, `clamp`, `prog`). |
| `b_world.html` | Décors : maisons, arbres, panneaux, stade, buts, foule. |
| `c_chars.html` | Fabrique des personnages en blocs, visages dessinés et fonction `pose()`. |
| `d_cast.html` | La distribution : chaque personnage, avec ses couleurs, sa coiffure et son visage. |
| `e_overlay.html` | Calque 2D : bulles, étiquettes, textes qui « pop ». |
| `f_direction.html` | Sous-titres, plans caméra (`shots()`), animation (`update(t)`), rendu. |

**Plans caméra** (`shots()` dans `f_direction.html`). Chaque plan s'écrit :

```js
[heure_de_début, [caméra départ x,y,z], [caméra fin x,y,z], [regard départ x,y,z], [regard fin x,y,z], champ_de_vision]
```

L'heure se cale sur la voix avec `S('id')`, le début d'une réplique, ou `WT('id', /^mot/)`, l'instant où un mot est prononcé. Le décor suit donc automatiquement si vous changez le texte.

**Personnages** (`d_cast.html`) :

```js
const hero = character('hero', { skin: '#f1c9a5', shirt: '#ff8a3d', pants: '#2a3a6b', hair: 'spiky', hairCol: '#e8b23a',
                                 face: { eyes: 'n', mouth: 'grin', freckles: true, blush: true } });
```

- Coiffures (`hair`) : `short`, `spiky`, `pony`, `bun`, `cap`, `bald`, `pigtails`, `chef`, `hood`.
- Yeux (`eyes`) : `n`, `happy`, `wide`, `closed`.
- Bouche (`mouth`) : `smile`, `grin`, `flat`, `open`.

**Animation** (`update(t)` dans `f_direction.html`) : à chaque image, placez les personnages avec `P(perso, {...})`.

```js
P(hero, { x: 0, z: 0, ry: .3, walk: t * 9, hop: jumpY(t, S('saute'), .6, 1.2), arms: CHEER(t), talk: talk('V', t), face: { mouth: 'open' } });
```

| Paramètre | Effet |
|---|---|
| `x`, `y`, `z` | Position. |
| `ry` | Rotation (orientation du personnage). |
| `s` | Taille. |
| `walk` | Phase de marche. |
| `hop` | Saut. |
| `arms` | Bras. |
| `bend` | Penché. |
| `headX`, `headY`, `headZ` | Tête. |
| `talk` | Ouverture de la bouche. `talk('V', t)` la synchronise sur les répliques de la voix `V`. |
| `face` | Expression du moment. |

## 5. Régler la voix et l'intonation : `voice_profile.json`

| Clé | Effet |
|---|---|
| `mix` | Mélange de voix Kokoro, avec un poids pour chacune. Exemples : `ff_siwis` (française), `am_puck` (énergique), `am_onyx` (grave), `bm_george` (posée). |
| `speed` | Débit de base. 1,12 correspond à un débit TikTok rapide. |
| `intonation.target_median` | Hauteur moyenne de la voix, en Hz. |
| `intonation.down` / `intonation.up` | Amplifie les descentes et les montées de la mélodie. 1 = naturel, 1,5 = très expressif. Au-delà de 1,7, la voix sonne « robot » et Whisper comprend moins bien. |
| `intonation.formant` | Timbre. En dessous de 1, voix plus grosse. Au-dessus de 1, voix plus fine. |
| `huss.offsets` | Instants des 3 « HUSS » d'une rafale, en secondes. |
| `huss.every` | Intervalle entre deux rafales, en secondes. |
| `huss.first_dur` / `huss.other_dur` | Durée de chaque cri. |
| `huss.pitch_hz` | Hauteur des cris. |
| `huss.hiss` | Intensité du « s » final. |
| `gap_s` / `pad_scale` | Rythme général : silences entre les répliques. |

**Calage actuel du narrateur, mesuré sur la vidéo de référence et sur ce que le kit produit :**

| Mesure | Référence | Kit |
|---|---|---|
| Hauteur médiane | 164 Hz | 166 Hz |
| Bas de la voix (10 %) | 104 Hz | 111 Hz |
| Haut de la voix (90 %) | 247 Hz | 246 Hz |
| Amplitude d'intonation | 5,8 demi-tons | 5,4 demi-tons |
| Débit (pics d'énergie par seconde de parole, mix complet) | 8,7 | 8,0 |
| Part de silence | 5 % | 11 % |

Pour un débit plus serré, baissez `gap_s` et `pad_scale`, ou montez `speed` du narrateur à 1,2. Au-delà, contrôlez la prononciation avec `check_pronunciation.py`.

Pour mesurer votre propre réglage :

```bash
python3 - <<'EOF'
import json,wave,numpy as np,pyworld as pw
tl=json.load(open('build/timeline.json'))
def f0(p):
    w=wave.open(p);a=np.frombuffer(w.readframes(w.getnframes()),np.int16)/32768.
    f,_=pw.harvest(a,w.getframerate(),f0_floor=60,f0_ceil=500,frame_period=10);return f[f>0]
o=np.concatenate([f0(f"build/audio/{l['id']}.wav") for l in tl['lines'] if l['who']=='N' and not l.get('huss')])
print('médiane',round(np.median(o)),'Hz | p10',round(np.percentile(o,10)),'| p90',round(np.percentile(o,90)),'| demi-tons',round((12*np.log2(o/np.median(o))).std(),2))
EOF
```

---

## 6. Avant de publier

- Sur TikTok, cochez « contenu généré par IA » : la voix est synthétique.
- La musique et les bruitages sont générés par `mix.py`, il n'y a donc aucun droit musical à gérer. Si vous ajoutez une musique du catalogue TikTok, faites-le dans l'application.
- N'utilisez pas la voix d'une personne réelle sans son accord.
__FIN_DU_FICHIER__

chmod +x setup.sh build.sh
echo "Fichiers créés dans $(pwd)"
if [ -z "$KIT_NO_RUN" ]; then
  bash setup.sh
  bash build.sh
fi
