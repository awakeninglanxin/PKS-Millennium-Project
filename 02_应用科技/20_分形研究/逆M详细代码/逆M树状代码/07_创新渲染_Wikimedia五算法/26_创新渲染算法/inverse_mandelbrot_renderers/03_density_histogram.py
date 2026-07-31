"""
03_density_histogram.py
========================
SCRIPT 3 of 5 — Density/Histogram method.

Instead of coloring by escape iteration count, this script records the
FULL TRAJECTORY of each orbit (every z_n point) into a 2D histogram.
The histogram is then log-scaled and rendered.

This produces a different aesthetic: smooth, cloud-like density with
the geometric structure emerging from the statistical accumulation.
Notable for revealing the "flow lines" of the dynamics.

NOTE: This renders the trajectory space (z-plane), not the parameter
space (c-plane). The teardrop will appear rotated/transformed because
it's the image of the inverse mapping, not the set itself.

Run:  python 03_density_histogram.py

Dependencies: numpy, matplotlib, scipy
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter
import time, os

# ── Parameters ──────────────────────────────────────────────────────────────
N_SAMPLES = 300_000      # random c samples
MAX_ITER = 5000
BAILOUT = 4.0
GW, GH = 1600, 1280      # histogram grid resolution
W, H = 800, 640          # output image size

t0 = time.time()
print(f"[03] Density histogram  samples={N_SAMPLES} max_iter={MAX_ITER}")

# ── Sample c in viewport ────────────────────────────────────────────────────
rng = np.random.default_rng(42)
re_c = rng.uniform(-3.0, 7.0, N_SAMPLES)
im_c = rng.uniform(-4.0, 4.0, N_SAMPLES)
c = re_c + 1j * im_c
inv_c = 1.0 / c
N = N_SAMPLES

# ── Pilot run to find z-bounds ──────────────────────────────────────────────
print("Pilot run (200 iters) to find trajectory bounds...")
z = np.zeros(N, dtype=np.complex128)
for _ in range(200):
    z = z**2 + inv_c
    z[np.abs(z) > BAILOUT] = 0

finite = z[np.isfinite(z.real) & (np.abs(z) < 1e6)]
m = 0.5
zr0, zr1 = finite.real.min() - m, finite.real.max() + m
zi0, zi1 = finite.imag.min() - m, finite.imag.max() + m
print(f"  z-window: Re[{zr0:.2f}, {zr1:.2f}], Im[{zi0:.2f}, {zi1:.2f}]")

# ── Main accumulation ───────────────────────────────────────────────────────
print("Accumulating orbit points into histogram...")
z = np.zeros(N, dtype=np.complex128)
esc = np.zeros(N, dtype=bool)
hist = np.zeros((GH, GW), dtype=np.float64)

def accum(za):
    gx = ((za.real - zr0) / (zr1 - zr0) * GW).astype(np.int64)
    gy = ((za.imag - zi0) / (zi1 - zi0) * GH).astype(np.int64)
    ok = (gx >= 0) & (gx < GW) & (gy >= 0) & (gy < GH)
    np.add.at(hist, (gy[ok], gx[ok]), 1.0)

hits = 0
for s in range(MAX_ITER):
    act = ~esc
    z[act] = z[act]**2 + inv_c[act]
    m2 = z.real[act]**2 + z.imag[act]**2
    ne = m2 > BAILOUT**2
    idx_ne = np.where(act)[0][ne]
    esc[idx_ne] = True

    still = ~esc
    if still.any():
        accum(z[still])
        hits += still.sum()

    z[esc] = 0
    if (s+1) % 1000 == 0:
        n=int(esc.sum())
        print(f"  iter {s+1}: esc {n:,}/{N:,} hits={hits:,} t={time.time()-t0:.0f}s")
    if esc.all(): break

print(f"  Total hits: {hits:,}")

# ── Log tone map ────────────────────────────────────────────────────────────
print("Log tone mapping...")
h = hist.copy()
h[h == 0] = 1.0
logh = np.log(h)
lo, hi = logh.min(), logh.max()
img = np.clip((logh - lo) / (hi - lo), 0, 1)

# Light blur
img = gaussian_filter(img, sigma=1.0, mode='nearest')

# ── Save ────────────────────────────────────────────────────────────────────
cmap = LinearSegmentedColormap.from_list('invmb',
    ['#000006','#0a0a48','#1a2e88','#3a72c8','#6ab8ff','#aef0ff','#f0feff'], N=512)

out = os.path.join(os.path.dirname(__file__), '03_density_histogram.png')
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img, extent=[zr0, zr1, zi0, zi1],
          cmap=cmap, aspect='auto', interpolation='bilinear', origin='lower')
ax.axis('off')
plt.savefig(out, dpi=100, bbox_inches='tight', pad_inches=0, facecolor='black')
plt.close()

print(f"\n✅ Saved: {out}")
print(f"   Time: {time.time()-t0:.1f}s")
print(f"   Note: This shows z-space (trajectory density), not c-space.")
print(f"         The structure is the 'shadow' of the inverse map.")
