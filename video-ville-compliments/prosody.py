# Makes the flat TTS more expressive with the WORLD vocoder: widens the pitch range, adds
# French sentence intonation (statements fall, questions rise), and shifts pitch/formants per character.
import numpy as np, pyworld as pw
ST = np.log(2) / 12  # one semitone in log-F0

def expressive(x, sr, clauses, pitch=1.0, formant=1.0, k=2.0, energy=1.0):
    x = x.astype(np.float64); fp = 5.0
    f0, t = pw.harvest(x, sr, f0_floor=60, f0_ceil=400, frame_period=fp)
    sp = pw.cheaptrick(x, f0, t, sr); ap = pw.d4c(x, f0, t, sr)
    v = f0 > 0; lf = np.zeros_like(f0); lf[v] = np.log(f0[v]); m = np.median(lf[v])
    out = lf.copy(); out[v] = m + (lf[v] - m) * k
    for (s, e, term) in clauses:
        a, b = int(s / sr * 1000 / fp), min(len(f0), int(e / sr * 1000 / fp))
        if b - a < 4: continue
        u = np.linspace(0, 1, b - a)
        if term == "?": c = 1.0 * ST - 1.5 * ST * u + 7 * ST * np.clip((u - .65) / .35, 0, 1) ** 1.5
        elif term == ",": c = 1.5 * ST * (1 - u) + 2.5 * ST * np.clip((u - .75) / .25, 0, 1)   # continuation rise
        else: c = 3 * ST * (1 - u) * energy - 3 * ST * np.clip((u - .7) / .3, 0, 1) + 1.5 * ST * np.exp(-((u - .15) / .1) ** 2) * energy
        seg = slice(a, b); out[seg] = np.where(v[seg], out[seg] + c, 0)
    f0n = np.where(v, np.clip(np.exp(out) * pitch, 60, 420), 0)
    if formant != 1.0:
        n = sp.shape[1]; src = np.clip(np.arange(n) / formant, 0, n - 1)
        sp = np.array([np.interp(src, np.arange(n), row) for row in sp])
    y = pw.synthesize(f0n, sp, ap, sr, fp)
    return (y / (np.abs(y).max() + 1e-6) * .9).astype(np.float32)
