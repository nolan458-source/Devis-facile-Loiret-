# Narration with Kokoro (82M, ONNX): fluid French voice "ff_siwis", whole sentences synthesised at once from
# corrected IPA (gn -> ɲ, ui -> ɥi), speed per mood for rhythm. The mayor keeps the male Piper "tom" voice.
import json, re, subprocess, sys, wave, os, numpy as np
from kokoro_onnx import Kokoro
KD, PD = sys.argv[1], sys.argv[2]
K = Kokoro(f"{KD}/kokoro-v1.0.onnx", f"{KD}/voices-v1.0.bin")
sys.path.insert(0, "."); from voice2 import PiperFR
from pitchmap import remap
MAP = {}
TOM = PiperFR(f"{PD}/fr_FR-tom-medium.onnx"); PIERRE = PiperFR(f"{PD}/fr_FR-upmc-medium.onnx", "pierre")
PIPER = {"C": TOM, "V": PIERRE}
OUT = "build/audio"; os.makedirs(OUT, exist_ok=True)
SPEED = {"normal": 1.08, "excited": 1.12, "hype": 1.1, "sad": 1.0, "deadpan": 1.04, "suspense": 1.02}
FIXES = [("ɡˈeɪməz", "ɡˈɛmœʁ"), ("(en)kˈəʊtʃ(fr)", "kˈotʃ"), ("(en)fˈʊt(fr)", "fˈut"), ("(en)bˈɔɪŋ(fr)", "bwˈɛ̃ɡ"), ("ɡanjˈe", "ɡaɲˈe"), ("ɡanj", "ɡaɲ"), ("nyˈi", "nɥˈi"), ("syˈi", "sɥˈi"), ("pyˈi", "pɥˈi"), ("pyˌi", "pɥˌi"), ("lyˈi", "lɥˈi")]
FPS = 25; SR = 44100; GAP = 0.05
# voices = Kokoro style blends (French ff_siwis + male voices), chosen by an audition scored with Whisper
_V = K.voices
VOICE = {"N": (.5 * _V["ff_siwis"] + .5 * _V["am_puck"], 1.0),     # Kenzo (narrator, young boy)
         "E": (_V["ff_siwis"], 1.0),                                  # laughing kid
         "G": (.5 * _V["ff_siwis"] + .5 * _V["bm_lewis"], 1.0)}       # exhausted gamer
HUSS_VOICE = VOICE["N"][0]
HUSS_IPA, HUSS_EVERY, HUSS_HITS, HUSS_GAP = "hˈœs", 0.96, 3, 0.2   # measured on the reference: bursts of 3 "huss" 0.2 s apart, a burst every 0.96 s
PRE = json.load(open("voice_pre.json")) if os.path.exists("voice_pre.json") else {}  # per-voice pitch chain (calibrated)
def ipa(text):
    p = K.tokenizer.phonemize(text, "fr-fr")
    for a, b in FIXES: p = p.replace(a, b)
    return re.sub(r"\([a-z-]+\)", "", p)  # drop any remaining language-switch markers
def save(a, sr, path):
    with wave.open(path, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
lines = json.load(open("script.json")); t = 0.35; out = []; log = []
lines_at = {l["id"]: l.get("at") for l in lines}
for ln in lines:
    text = ln["text"].replace("*", ""); who = ln["who"]; mood = ln.get("mood", "normal")
    if ln.get("at") is not None: t = max(t, ln["at"])
    raw, fin = f"{OUT}/{ln['id']}_raw.wav", f"{OUT}/{ln['id']}.wav"
    if False:
        pass
    elif ln.get("huss"):
        one, sr = K.create(HUSS_IPA, voice=HUSS_VOICE, speed=1.5, is_phonemes=True)
        nz = np.where(np.abs(one) > .02 * np.abs(one).max())[0]; one = one[nz[0]:nz[-1]][: int(sr * .17)]
        one = one * np.concatenate([np.ones(len(one) - int(sr * .03)), np.linspace(1, 0, int(sr * .03))]); one /= np.abs(one).max() + 1e-6
        nh = text.lower().count("huss"); a = np.zeros(int(sr * (HUSS_EVERY * (nh - 1) + HUSS_GAP * (HUSS_HITS - 1) + .3)), np.float32)
        for j in range(nh):
            for k_ in range(HUSS_HITS): i0 = int(sr * (HUSS_EVERY * j + HUSS_GAP * k_)); a[i0:i0 + len(one)] += one * (1.0, .8, .9)[k_]
        log.append(f"{ln['id']}: {nh} bursts x {HUSS_HITS} '{HUSS_IPA}' ({HUSS_GAP}s apart), a burst every {HUSS_EVERY}s")
        save(a * .9, sr, raw); pre = (f"rubberband=pitch={VOICE[who][1]}:formant=preserved:pitchq=quality," if VOICE[who][1] != 1.0 else "")
    else:
        ph = ipa(text); log.append(f"{ln['id']}: {ph}")
        a, sr = K.create(ph, voice=VOICE[who][0], speed=SPEED[mood] * {"E": 1.12, "G": .92}.get(who, 1.0), is_phonemes=True)
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
            for k_ in range(HUSS_HITS): wt.append({"w": s, "t": round(t + .02 + HUSS_EVERY * hi + HUSS_GAP * k_, 3), "e": True})
            hi += 1
        elif s: wt.append({"w": s, "t": round(t + dur * acc / tot, 3), "e": e})
        acc += kk
    out.append({**ln, "text": text, "start": round(t, 3), "dur": round(dur, 3), "words": wt, "env": env})
    t += dur + GAP + ln.get("pad", 0) * .3
json.dump({"total": round(t + 0.8, 2), "lines": out}, open("build/timeline.json", "w"), ensure_ascii=False)
open("build/ipa.txt", "w").write("\n".join(log)); print("total", round(t + 0.8, 2))
