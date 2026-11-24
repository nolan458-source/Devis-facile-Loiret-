# Male French voice "tom" (Mimic 3, VITS ONNX) driven by espeak-ng phonemes from piper-tts.
import re, unicodedata, numpy as np, onnxruntime as ort
from piper import espeakbridge as eb
import piper.phonemize_espeak as pe

FIX = {"pull": "pule", "EDF": "eu-dé-èf", "GPS": "jé-pé-èss", "Euh,": "Euh…"}
MAP = {"ɐ": "a", "ɑ": "a", "ɜ": "ə", "ɪ": "i", "ʊ": "u", "r": "ʁ", "g": "ɡ", "ɒ": "ɔ", "ʌ": "œ", "æ": "a", "ɚ": "ə", "ɾ": "ʁ", "x": "ʁ"}

class Tom:
    def __init__(self, voice_dir):
        self.sess = ort.InferenceSession(f"{voice_dir}/generator.onnx")
        self.ids = {}
        for line in open(f"{voice_dir}/phonemes.txt", encoding="utf-8"):
            i, s = line.rstrip("\n").split(" ", 1); self.ids[s] = int(i)
        eb.initialize(str(pe.ESPEAK_DATA_DIR)); eb.set_voice("fr")

    def tokens(self, ipa):
        ipa = unicodedata.normalize("NFD", re.sub(r"\([^)]+\)", "", ipa))
        words = []
        for w in ipa.split():
            raw = []
            for ch in w:
                if ch == "\u0303" and raw: raw[-1] += ch
                else: raw.append(ch)
            NAS = {"a": "ɑ̃", "ɑ": "ɑ̃", "e": "ɛ̃", "ɛ": "ɛ̃", "o": "ɔ̃", "ɔ": "ɔ̃", "œ": "œ̃", "ø": "œ̃"}
            toks = []
            for r in raw:
                if r.endswith("\u0303"): r = NAS.get(r[0], r[0])
                elif r not in self.ids: r = MAP.get(r, r)
                if r in self.ids and r not in ("ˈ", "ˌ"): toks.append(r)
            if toks: words.append(toks)
        return words

    def clause(self, ipa, length=1.0, noise=0.667, noise_w=0.8):
        I = self.ids; seq = [I["^"], I["_"]]
        for k, w in enumerate(self.tokens(ipa)):
            if k: seq += [I["#"], I["_"]]
            for t in w: seq += [I[t], I["_"]]
        seq.append(I["$"])
        audio = self.sess.run(None, {"input": np.array([seq], np.int64), "input_lengths": np.array([len(seq)], np.int64),
                                     "scales": np.array([noise, length, noise_w], np.float32)})[0]
        return audio.squeeze().astype(np.float32)

    def say(self, text, length=1.0):
        for a, b in FIX.items(): text = text.replace(a, b)
        sr = 22050; out = []
        for ipa, term, end in eb.get_phonemes(text):
            out.append(self.clause(ipa, length))
            out.append(np.zeros(int(sr * (0.32 if end else 0.14)), np.float32))
        a = np.concatenate(out); return a / (np.abs(a).max() + 1e-6) * 0.9, sr
