# Piper "medium" French voices (tom, upmc jessica/pierre) driven clause by clause from espeak-ng phonemes,
# exactly as they were trained, so names and liaisons come out as the model learned them.
import json, re, unicodedata, numpy as np, onnxruntime as ort
from piper import espeakbridge as eb
import piper.phonemize_espeak as pe
eb.initialize(str(pe.ESPEAK_DATA_DIR))

class PiperFR:
    def __init__(self, onnx, speaker=None):
        self.sess = ort.InferenceSession(onnx); cfg = json.load(open(onnx + ".json"))
        self.map = cfg["phoneme_id_map"]; self.sr = cfg["audio"]["sample_rate"]
        self.sid = None if speaker is None else cfg["speaker_id_map"][speaker]

    def ids(self, ipa):
        M = self.map; seq = list(M["^"]) + list(M["_"])
        for ch in unicodedata.normalize("NFD", ipa):
            if ch in M: seq += M[ch] + M["_"]
        return seq + list(M["$"])

    def synth(self, ipa, length=1.0, noise=0.667, noise_w=0.85):
        seq = self.ids(ipa)
        feed = {"input": np.array([seq], np.int64), "input_lengths": np.array([len(seq)], np.int64),
                "scales": np.array([noise, length, noise_w], np.float32)}
        if self.sid is not None: feed["sid"] = np.array([self.sid], np.int64)
        return self.sess.run(None, feed)[0].squeeze().astype(np.float32)

    def clauses(self, text):
        """[(ipa_with_punct, terminator, end_of_sentence, emphasised)] for text whose *starred* words are emphasised."""
        plain, flags, on = "", [], False
        for ch in text:
            if ch == "*": on = not on; continue
            plain += ch; flags.append(on)
        eb.set_voice("fr")
        res = list(eb.get_phonemes(plain))
        chunks = [(m.start(), m.end()) for m in re.finditer(r"[^,.;:!?…]+[,.;:!?…]*", plain) if m.group().strip(" .…")]
        out = []
        for i, (ipa, term, end) in enumerate(res):
            emph = any(flags[chunks[i][0]:chunks[i][1]]) if len(res) == len(chunks) else False
            out.append((re.sub(r"\([^)]+\)", "", ipa) + term, term, end, emph))
        return out
