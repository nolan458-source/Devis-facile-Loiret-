# Narration with Kokoro (82M, ONNX): fluid French voice "ff_siwis", whole sentences synthesised at once from
# corrected IPA (gn -> ɲ, ui -> ɥi), speed per mood for rhythm. The mayor keeps the male Piper "tom" voice.
import json, re, subprocess, sys, wave, os, numpy as np
from kokoro_onnx import Kokoro
KD, PD = sys.argv[1], sys.argv[2]
K = Kokoro(f"{KD}/kokoro-v1.0.onnx", f"{KD}/voices-v1.0.bin")
sys.path.insert(0, "."); from voice2 import PiperFR
from pitchmap import remap
MAP = json.load(open("voice_map.json"))  # target pitch statistics per voice (from the "Logique de papa" table)
TOM = PiperFR(f"{PD}/fr_FR-tom-medium.onnx"); PIERRE = PiperFR(f"{PD}/fr_FR-upmc-medium.onnx", "pierre")
PIPER = {"C": TOM, "V": PIERRE}
OUT = "build/audio"; os.makedirs(OUT, exist_ok=True)
SPEED = {"normal": 1.08, "excited": 1.12, "hype": 1.1, "sad": 1.0, "deadpan": 1.04, "suspense": 1.02}
FIXES = [("(en)kˈəʊtʃ(fr)", "kˈotʃ"), ("(en)fˈʊt(fr)", "fˈut"), ("(en)bˈɔɪŋ(fr)", "bwˈɛ̃ɡ"), ("ɡanjˈe", "ɡaɲˈe"), ("ɡanj", "ɡaɲ"), ("nyˈi", "nɥˈi"), ("syˈi", "sɥˈi"), ("pyˈi", "pɥˈi"), ("pyˌi", "pɥˌi"), ("lyˈi", "lɥˈi")]
FPS = 25; SR = 44100; GAP = 0.05
# voices = Kokoro style blends (French ff_siwis + male voices), chosen by an audition scored with Whisper
_V = K.voices
VOICE = {"N": (.4 * _V["ff_siwis"] + .35 * _V["bm_george"] + .25 * _V["am_onyx"], 1.0),   # narrator: naturally deep blend, no pitch processing
         "C": (.35 * _V["ff_siwis"] + .35 * _V["bm_george"] + .3 * _V["am_onyx"], 1.0),   # coach
         "V": (.4 * _V["ff_siwis"] + .6 * _V["am_onyx"], 1.0)}               # neighbour
HUSS_VOICE = VOICE["N"][0]
HUSS_IPA, HUSS_EVERY, HUSS_HITS, HUSS_GAP = "hˈœs", 0.97, 3, 0.2   # measured on the reference video
HUSS_OFFS, HUSS_F0, HUSS_S = (0.0, 0.23, 0.415), 350.0, 0.3
PRE = json.load(open("voice_pre.json")) if os.path.exists("voice_pre.json") else {}  # per-voice pitch chain (calibrated)
def ipa(text):
    p = K.tokenizer.phonemize(text, "fr-fr")
    for a, b in FIXES: p = p.replace(a, b)
    return re.sub(r"\([a-z-]+\)", "", p)  # drop any remaining language-switch markers
def save(a, sr, path):
    with wave.open(path, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
lines = json.load(open("script.json")); t = 0.35; out = []; log = []
for ln in lines:
    text = ln["text"].replace("*", ""); who = ln["who"]; mood = ln.get("mood", "normal")
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    if False:
        pass
    elif ln.get("huss"):
        # "HUSS" as on the reference: the whole word "heuss" (never cut), squeezed to 0.11 s (1st hit) / 0.08 s (others),
        # shouted high (~350 Hz), placed at the measured offsets 0 / 0.23 / 0.415 s, bursts every 0.97 s
        sr = 24000; word, _ = K.create("hˈœs !", voice=HUSS_VOICE, speed=1.3, is_phonemes=True)
        nz = np.where(np.abs(word) > .03 * np.abs(word).max())[0]; word = word[nz[0]:nz[-1] + 1]
        import pyworld as _pw
        f0w, _t = _pw.harvest(word.astype(np.float64), sr, f0_floor=60, f0_ceil=500, frame_period=5); f0m = float(np.median(f0w[f0w > 0])) if (f0w > 0).any() else 150.
        def squeeze(dur):
            tmp_in, tmp_out = f"{OUT}/_huss_in.wav", f"{OUT}/_huss_{dur}.wav"; save(word / (np.abs(word).max() + 1e-6) * .9, sr, tmp_in)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp_in, "-af", f"rubberband=tempo={len(word) / sr / dur:.3f}:pitch={HUSS_F0 / f0m:.3f}:formant=preserved,highpass=f=150",
                            "-ar", str(sr), "-ac", "1", tmp_out], check=True)
            with wave.open(tmp_out) as w_: x = np.frombuffer(w_.readframes(w_.getnframes()), np.int16).astype(np.float32) / 32768
            x = x[: int(sr * dur)]; f = np.ones(len(x)); f[:int(sr * .004)] = np.linspace(0, 1, int(sr * .004)); f[-int(sr * .015):] = np.linspace(1, 0, int(sr * .015))
            x = x * f / (np.abs(x).max() + 1e-6)
            nse = np.random.default_rng(int(dur * 1000)).standard_normal(len(x)); nse = np.convolve(np.diff(nse, prepend=0), np.ones(6) / 6, "same")   # band-limited hiss (~2-6 kHz) for the final "s"
            u = np.linspace(0, 1, len(x)); env = np.clip((u - .3) / .3, 0, 1) * np.clip((1 - u) / .15, 0, 1)
            x = x + nse / (np.abs(nse).max() + 1e-6) * env * HUSS_S
            return x / (np.abs(x).max() + 1e-6)
        long_, short_ = squeeze(.11), squeeze(.08)
        nh = text.lower().count("huss"); a = np.zeros(int(sr * (HUSS_EVERY * (nh - 1) + HUSS_OFFS[-1] + .3)), np.float32)
        for j in range(nh):
            for k_, off in enumerate(HUSS_OFFS):
                one = long_ if k_ == 0 else short_; i0 = int(sr * (HUSS_EVERY * j + off)); a[i0:i0 + len(one)] += one * (1.0, .85, .9)[k_]
        log.append(f"{ln['id']}: {nh} bursts, hits at {HUSS_OFFS} s, every {HUSS_EVERY} s, word squeezed to 0.11/0.08 s at {HUSS_F0} Hz (from {f0m:.0f} Hz)")
        save(a * .9, sr, raw); pre = (f"rubberband=pitch={VOICE[who][1]}:formant=preserved:pitchq=quality," if VOICE[who][1] != 1.0 else "")
    else:
        ph = ipa(text); log.append(f"{ln['id']}: {ph}")
        a, sr = K.create(ph, voice=VOICE[who][0], speed=SPEED[mood], is_phonemes=True)
        save(a / (np.abs(a).max() + 1e-6) * .9, sr, raw)
        pre = (f"rubberband=pitch={VOICE[who][1]}:formant=preserved:pitchq=quality," if VOICE[who][1] != 1.0 else "")
    af = (f"aresample={SR},{pre}highpass=f=70,equalizer=f=3200:t=q:w=1.2:g=1.5,deesser=i=0.3,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=90:makeup=2,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", fin], check=True)
    with wave.open(fin) as w: a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    dur = len(a) / SR; hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[i:i+hop]**2))) for i in range(0, len(a), hop)]; m = max(env) or 1; env = [round(min(1, e / m * 1.4), 2) for e in env]
    raw_words = ln["text"].split(); emph = []; on = False
    for w_ in raw_words:
        on = on or w_.startswith("*"); emph.append(on)
        if w_.rstrip(".,!?:…").endswith("*"): on = False
    words = [w_.replace("*", "") for w_ in raw_words]; w8 = [len(w_.strip(".,?!:…")) + 2 for w_ in words]; tot = sum(w8); acc = 0; wt = []
    hi = 0
    for w_, kk, e in zip(words, w8, emph):
        s = w_.strip(".,!:?…")
        if s and ln.get("huss"):
            for off in HUSS_OFFS: wt.append({"w": s, "t": round(t + .01 + HUSS_EVERY * hi + off, 3), "e": True})
            hi += 1
        elif s: wt.append({"w": s, "t": round(t + dur * acc / tot, 3), "e": e})
        acc += kk
    out.append({**ln, "text": text, "start": round(t, 3), "dur": round(dur, 3), "words": wt, "env": env})
    t += dur + GAP + ln.get("pad", 0) * .3
json.dump({"total": round(t + 0.8, 2), "lines": out}, open("build/timeline.json", "w"), ensure_ascii=False)
open("build/ipa.txt", "w").write("\n".join(log)); print("total", round(t + 0.8, 2))
