# Expressive prosody with the WORLD vocoder: widened pitch range, French sentence intonation,
# per-line mood (register shift, range, energy), and emphasised words (pitch accent + lengthening + louder).
import numpy as np, pyworld as pw
ST = np.log(2) / 12
MOODS = {"normal": (0, 1.0, 1.0), "excited": (2.0, 1.15, 1.25), "hype": (3.5, 1.25, 1.4),
         "sad": (-2.5, .75, .8), "deadpan": (-1.5, .6, .7), "suspense": (-1.0, .85, .9)}

def expressive(x, sr, clauses, pitch=1.0, formant=1.0, k=2.0, energy=1.0, emph=(), mood="normal"):
    shift, km, em = MOODS.get(mood, MOODS["normal"]); k *= km; energy *= em
    x = x.astype(np.float64); fp = 5.0
    f0, t = pw.harvest(x, sr, f0_floor=60, f0_ceil=420, frame_period=fp)
    sp = pw.cheaptrick(x, f0, t, sr); ap = pw.d4c(x, f0, t, sr)
    v = f0 > 0; lf = np.zeros_like(f0); lf[v] = np.log(f0[v]); m = np.median(lf[v])
    out = lf.copy(); out[v] = m + (lf[v] - m) * k + shift * ST
    fr = lambda s: int(s / sr * 1000 / fp)
    for (s, e, term) in clauses:
        a, b = fr(s), min(len(f0), fr(e))
        if b - a < 4: continue
        u = np.linspace(0, 1, b - a)
        if term == "?": c = 1.0 * ST - 1.5 * ST * u + 7 * ST * np.clip((u - .65) / .35, 0, 1) ** 1.5
        elif term in (",", ":"): c = 1.5 * ST * (1 - u) + 3 * ST * np.clip((u - .72) / .28, 0, 1)
        elif term == "!": c = 4 * ST * np.exp(-((u - .25) / .2) ** 2) * energy + 1.5 * ST * (1 - u) - 2 * ST * np.clip((u - .75) / .25, 0, 1)
        else: c = 3 * ST * (1 - u) * energy - 3.5 * ST * np.clip((u - .7) / .3, 0, 1) + 1.5 * ST * np.exp(-((u - .15) / .1) ** 2) * energy
        seg = slice(a, b); out[seg] = np.where(v[seg], out[seg] + c, 0)
    gain = np.ones(len(f0)); stretch = np.ones(len(f0))
    for (s, e) in emph:
        a, b = fr(s), min(len(f0), fr(e))
        if b - a < 3: continue
        u = np.linspace(0, 1, b - a); bell = np.sin(np.pi * u) ** .7
        out[a:b] = np.where(v[a:b], out[a:b] + 4.5 * ST * bell * max(.6, energy), 0)
        gain[a:b] *= 1 + .45 * bell; stretch[a:b] = 1.18
    f0n = np.where(v, np.clip(np.exp(out) * pitch, 60, 480), 0)
    if formant != 1.0:
        n = sp.shape[1]; src = np.clip(np.arange(n) / formant, 0, n - 1)
        sp = np.array([np.interp(src, np.arange(n), row) for row in sp])
    sp = sp * (gain[:, None] ** 2)
    # time-stretch emphasised regions by resampling frame indices
    pos = np.concatenate([[0], np.cumsum(stretch)]); total = int(pos[-1]); idx = np.interp(np.arange(total), pos[:-1], np.arange(len(f0)))
    i0 = np.floor(idx).astype(int); i1 = np.minimum(i0 + 1, len(f0) - 1); w = (idx - i0)[:, None]
    f0s = np.where((f0n[i0] > 0) & (f0n[i1] > 0), f0n[i0] * (1 - w[:, 0]) + f0n[i1] * w[:, 0], f0n[i0])
    sps = sp[i0] * (1 - w) + sp[i1] * w; aps = ap[i0] * (1 - w) + ap[i1] * w
    y = pw.synthesize(np.ascontiguousarray(f0s), np.ascontiguousarray(sps), np.ascontiguousarray(aps), sr, fp)
    return (y / (np.abs(y).max() + 1e-6) * .9).astype(np.float32)
