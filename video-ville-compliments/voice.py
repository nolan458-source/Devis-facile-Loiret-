# French voice (Piper "siwis" medium, female) driven clause by clause with espeak-ng phonemes,
# so that prosody.py can reshape each clause's intonation.
import json, re, unicodedata, numpy as np, onnxruntime as ort
from piper import espeakbridge as eb
import piper.phonemize_espeak as pe

FIX = {"Noé": "No-é", "toise": "touaze"}

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
        for a, b in FIX.items(): text = text.replace(a, b)
        sr = 22050; out = []; self.clauses = []; pos = 0
        for ipa, term, end in eb.get_phonemes(text):
            c = self.clause(ipa + term, length); out.append(c); self.clauses.append((pos, pos + len(c), term)); pos += len(c)
            gap = np.zeros(int(sr * (0.18 if end else 0.07)), np.float32); out.append(gap); pos += len(gap)
        a = np.concatenate(out); return a / (np.abs(a).max() + 1e-6) * 0.9, sr
