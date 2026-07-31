"""
01_escape_time_basic.py
========================
SCRIPT 1 of 5 — Start here.

Renders the Inverse Mandelbrot using the simplest possible method:
standard ESCAPE-TIME algorithm with smooth coloring.

Formula:  z_{n+1} = z_n^2 + 1/c,   z_0 = 0
Viewport: Re(c) ∈ [-3, 7], Im(c) ∈ [-4, 4]
Output:   real axis pointing UP (rotated 90°)

This script establishes the BASELINE.  It will give you the teardrop
shape but WITHOUT the rich radial fan texture.  That's intentional —
run this first to confirm the formula works, then move to scripts 2-5
which progressively add the texture.

Run:  python 01_escape_time_basic.py

Dependencies: numpy, matplotlib
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import time, os

# ── Parameters ──────────────────────────────────────────────────────────────
W, H = 800, 640
RE0, RE1 = -3.0, 7.0
IM0, IM1 = -4.0, 4.0
MAX_ITER = 5000
BAILOUT = 2.0

t0 = time.time()
N = W * H
print(f"[01] Escape-time baseline  W={W} H={H} max_iter={MAX_ITER}")

# c-grid
re = np.linspace(RE0, RE1, W, dtype=np.float64)
im = np.linspace(IM0, IM1, H, dtype=np.float64)
R, I = np.meshgrid(re, im)
c = R + 1j * I
inv = 1.0 / np.where(np.abs(c) < 1e-15, 1e-15 + 0j, c)

invf = inv.ravel()
z = np.zeros(N, dtype=np.complex128)
esc = np.zeros(N, dtype=bool)
itc = np.zeros(N, dtype=np.int32)
last = np.zeros(N, dtype=np.complex128)

# Iterate
print("Iterating...")
for s in range(MAX_ITER):
    act = ~esc
    if not act.any(): break
    z[act] = z[act]**2 + invf[act]
    m2 = z.real[act]**2 + z.imag[act]**2
    ne = m2 > BAILOUT**2
    idx = np.where(act)[0][ne]
    itc[idx] = s + 1
    last[idx] = z[idx]
    esc[idx] = True
    z[esc] = 0
    if (s+1) % 1000 == 0:
        n = int(esc.sum())
        print(f"  iter {s+1}: {n:,}/{N:,} escaped ({n/N*100:.1f}%)")

n_esc = int(esc.sum())
print(f"  Done. Escaped: {n_esc:,}/{N:,}")

# Smooth continuous potential (Hubbard-Douady)
mag = np.abs(last).clip(1, None)
pot = np.log(np.log(mag) / np.log(2.0)) / np.log(2.0)
pn = np.zeros(N)
if n_esc > 0:
    pv = pot[esc]
    pn[esc] = (pv - pv.min()) / (pv.max() - pv.min())

# Interior
pn[~esc] = itc[~esc].astype(float) / MAX_ITER * 0.5

# Rotate Re-axis → UP
img = np.rot90(pn.reshape(H, W), k=1)

# Colormap
cmap = LinearSegmentedColormap.from_list('invmb',
    ['#000006','#0a0a48','#1a2e88','#3a72c8','#6ab8ff','#aef0ff','#f0feff'], N=512)

out = os.path.join(os.path.dirname(__file__), '01_escape_time_basic.png')
fig, ax = plt.subplots(figsize=(H/100, W/100), dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img, cmap=cmap, aspect='auto', interpolation='bilinear', origin='lower')
ax.axis('off')
plt.savefig(out, dpi=100, bbox_inches='tight', pad_inches=0, facecolor='black')
plt.close()

print(f"\n✅ Saved: {out}")
print(f"   Time: {time.time()-t0:.1f}s")
print(f"   Note: This is the BARE teardrop — no fan texture yet.")
print(f"         Run 02_orbittrap_rays.py next to add the radial fans.")
