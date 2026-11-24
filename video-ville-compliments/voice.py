# French voice (Piper "siwis" medium) driven clause by clause with espeak-ng phonemes.
# Words wrapped in *stars* are returned as emphasis spans (sample ranges) for prosody.py.
import json, re, unicodedata, numpy as np, onnxruntime as ort
from piper import espeakbridge as eb
import piper.phonemize_espeak as pe

FIX = {"Noé": "No-é", "toise": "touaze"}
PUNCT = r"[,.;:!?…]"

class Voice:
    def __init__(self, onnx):
        self.sess = ort.InferenceSession(onnx)
        self.map = json.load(open(onnx + ".json"))["phoneme_id_map"]
        eb.initialize(str(pe.ESPEAK_DATA_DIR)); eb.set_voice("fr")

    def clause(self, ipa, length):
        M = self.map; ipa = unicodedata.normalize("NFD", re.sub(r"\([^)]+\)", "", ipa))
        seq = M["^"] + M["_"]
        for ch in ipa:
            if ch in M: seq += M[ch] + M["_"]
        seq += M["$"]
        a = self.sess.run(None, {"input": np.array([seq], np.int64), "input_lengths": np.array([len(seq)], np.int64),
                                 "scales": np.array([0.667, length, 0.8], np.float32)})[0]
        return a.squeeze().astype(np.float32)

    def say(self, text, length=1.0):
        # clause texts with emphasis flags per character
        plain, flags, on = "", [], False
        for ch in text:
            if ch == "*": on = not on; continue
            plain += ch; flags.append(on)
        spoken = plain
        for a, b in FIX.items(): spoken = spoken.replace(a, b)
        chunks = [(m.start(), m.end()) for m in re.finditer(r"[^,.;:!?…]+" + PUNCT + "*", plain) if m.group().strip(" .…")]
        sr = 22050; out = []; self.clauses = []; self.emph = []; pos = 0
        res = list(eb.get_phonemes(spoken))
        for ci, (ipa, term, end) in enumerate(res):
            c = self.clause(ipa + term, length); n = len(c)
            if len(res) == len(chunks):  # map emphasised characters proportionally into this clause's audio
                s0, s1 = chunks[ci]; seg = flags[s0:s1]; L = max(1, len(seg))
                i = 0
                while i < len(seg):
                    if seg[i]:
                        j = i
                        while j < len(seg) and seg[j]: j += 1
                        self.emph.append((pos + int(n * (i / L) * .92), pos + int(n * min(1, (j / L) * 1.02))))
                        i = j
                    else: i += 1
            out.append(c); self.clauses.append((pos, pos + n, term)); pos += n
            gap = np.zeros(int(sr * (0.12 if end else 0.05)), np.float32); out.append(gap); pos += len(gap)
        a = np.concatenate(out); return a / (np.abs(a).max() + 1e-6) * 0.9, sr
