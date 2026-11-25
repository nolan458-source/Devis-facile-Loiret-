# Re-map a voice's pitch to target statistics with the WORLD vocoder: set the median, scale the excursions
# below and above it separately (in semitones), and optionally warp formants (vocal-tract length).
import numpy as np, pyworld as pw
def remap(x, sr, target_median, down=1.0, up=1.0, formant=1.0):
    x = x.astype(np.float64); fp = 5.0
    f0, t = pw.harvest(x, sr, f0_floor=60, f0_ceil=500, frame_period=fp)
    sp = pw.cheaptrick(x, f0, t, sr); ap = pw.d4c(x, f0, t, sr)
    v = f0 > 0; st = np.zeros_like(f0); med = np.median(f0[v]); st[v] = 12 * np.log2(f0[v] / med)
    # octave-error correction: pull frames that jump about an octave away from their neighbourhood back
    idx = np.where(v)[0]
    for j, i in enumerate(idx):
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
