"""
02_orbittrap_rays.py
=====================
SCRIPT 2 of 5 — Adds RADIAL FAN TEXTURE via Orbit Traps.

This is the KEY script for reproducing the "triangular fan" appearance.
While iterating z_{n+1} = z_n^2 + 1/c, we simultaneously measure the
minimum distance from each orbit point z_n to a set of radial lines
passing through the origin.  Points that come close to a radial line
get brightened → this produces the spoke/fan pattern.

The "non-sticky" look comes from:
  1. High iteration count (orbits have time to settle into patterns)
  2. Logarithmic density scaling (compresses bright cores, reveals faint fans)
  3. The orbit trap minimum (captures the geometric skeleton, not noise)

Run:  python 02_orbittrap_rays.py

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
W, H = 800, 640
RE0, RE1 = -3.0, 7.0
IM0, IM1 = -4.0, 4.0
MAX_ITER = 8000         # ★ increase to 20000 for finer fans
BAILOUT = 2.0
N_RAYS = 36             # ★ increase to 72 for sharper spokes

t0 = time.time()
N = W * H
print(f"[02] Orbit-trap rays  W={W} H={H} max_iter={MAX_ITER} rays={N_RAYS}")

# c-grid
re = np.linspace(RE0, RE1, W, dtype=np.float64)
im = np.linspace(IM0, IM1, H, dtype=np.float64)
Rg, Ig = np.meshgrid(re, im)
c = Rg + 1j * Ig
inv = 1.0 / np.where(np.abs(c) < 1e-15, 1e-15 + 0j, c)
invf = inv.ravel()

# State
z = np.zeros(N, dtype=np.complex128)
esc = np.zeros(N, dtype=bool)
itc = np.zeros(N, dtype=np.int32)
last = np.zeros(N, dtype=np.complex128)

# Orbit traps
trap_ray = np.full(N, 1e10, dtype=np.float64)
trap_re  = np.full(N, 1e10, dtype=np.float64)
trap_im  = np.full(N, 1e10, dtype=np.float64)

# Ray angle tables
angs = np.linspace(0, 2*np.pi, N_RAYS, endpoint=False)
st = np.sin(angs)
ct = np.cos(angs)

# ── Iterate ────────────────────────────────────────────────────────────────
print("Iterating with orbit traps...")
for s in range(MAX_ITER):
    act = ~esc
    if not act.any(): break
    z[act] = z[act]**2 + invf[act]

    m2 = z.real[act]**2 + z.imag[act]**2
    ne = m2 > BAILOUT**2
    idx_ne = np.where(act)[0][ne]
    itc[idx_ne] = s + 1
    last[idx_ne] = z[idx_ne]
    esc[idx_ne] = True

    # Traps on still-active
    still = ~esc
    if still.any():
        idx = np.where(still)[0]
        zr = z.real[idx]
        zi = z.imag[idx]
        # Dist to Re axis = |Im(z)|
        trap_re[idx] = np.minimum(trap_re[idx], np.abs(zi))
        # Dist to Im axis = |Re(z)|
        trap_im[idx] = np.minimum(trap_im[idx], np.abs(zr))
        # Dist to radial lines: |re*sin(θ) - im*cos(θ)|, min over θ
        d = np.abs(zr[:,None]*st[None,:] - zi[:,None]*ct[None,:])
        trap_ray[idx] = np.minimum(trap_ray[idx], d.min(axis=1))

    z[esc] = 0
    if (s+1) % 2000 == 0:
        n = int(esc.sum())
        print(f"  iter {s+1}: {n:,}/{N:,} ({n/N*100:.1f}%) t={time.time()-t0:.0f}s")

n_esc = int(esc.sum())
print(f"  Done. Escaped: {n_esc:,}/{N:,}  Interior: {N-n_esc:,}")

# ── Potential ───────────────────────────────────────────────────────────────
mag = np.abs(last).clip(1, None)
pot = np.log(np.log(mag)/np.log(2.0)) / np.log(2.0)
pn = np.zeros(N)
if n_esc > 0:
    pv = pot[esc]
    pn[esc] = (pv - pv.min()) / (pv.max() - pv.min())
pn[~esc] = itc[~esc].astype(float) / MAX_ITER * 0.4

# ── Normalize traps ─────────────────────────────────────────────────────────
def n01(a, l=0.5, h=99.5):
    b = a[(a < 1e9) & (a > 0)]
    if b.size < 2: return np.zeros_like(a)
    lo, hi = np.percentile(b, [l, h])
    return np.clip((a - lo) / (hi - lo), 0, 1) if hi > lo else np.zeros_like(a)

ray_lines = 1.0 - n01(trap_ray)
re_lines  = 1.0 - n01(trap_re)
im_lines  = 1.0 - n01(trap_im)

# Gamma sharpen — lower power = thinner, sharper lines
ray_lines = np.clip(ray_lines**0.2, 0, 1)
re_lines  = np.clip(re_lines**0.15, 0, 1)
im_lines  = np.clip(im_lines**0.15, 0, 1)

# ── Composite ───────────────────────────────────────────────────────────────
base = pn.reshape(H, W)
# The fan = radial rays (dominant) + axis crosses (subtle)
fan = ray_lines.reshape(H,W)*0.7 + re_lines.reshape(H,W)*0.15 + im_lines.reshape(H,W)*0.15

I = base*0.3 + fan*0.6
I[~esc.reshape(H,W)] = itc[~esc.reshape(H,W)].astype(float)/MAX_ITER*0.25 + 0.03
I += np.clip(base,0,1)*0.08

# Log scaling → "non-sticky" ethereal look
I = np.clip(I, 1e-5, None)
I = np.log1p(I * 10) / np.log1p(10)

# Anti-alias
I = gaussian_filter(I, sigma=0.6, mode='nearest')
I = np.clip(I, 0, 1)

# Rotate Re-axis → UP
img = np.rot90(I, k=1)

# Save
cmap = LinearSegmentedColormap.from_list('invmb',
    ['#000004','#050318','#0a0a38','#101a58','#1a2e78',
     '#2a4ea0','#3a72c8','#4a96e8','#6ab8ff','#8ad8ff',
     '#aef0ff','#d4f6ff','#f0feff'], N=1024)

out = os.path.join(os.path.dirname(__file__), '02_orbittrap_rays.png')
fig, ax = plt.subplots(figsize=(H/100, W/100), dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img, cmap=cmap, aspect='auto', interpolation='bilinear', origin='lower')
ax.axis('off')
plt.savefig(out, dpi=100, bbox_inches='tight', pad_inches=0, facecolor='black')
plt.close()

# Also save grayscale for comparison
outg = out.replace('.png', '_gray.png')
fig, ax = plt.subplots(figsize=(H/100, W/100), dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img, cmap='gray_r', aspect='auto', interpolation='bilinear', origin='lower')
ax.axis('off')
plt.savefig(outg, dpi=100, bbox_inches='tight', pad_inches=0, facecolor='black')
plt.close()

print(f"\n✅ Saved: {out}")
print(f"✅ Saved: {outg}")
print(f"   Time: {time.time()-t0:.1f}s")
print(f"\n   ★ Tuning tips:")
print(f"     - Thinner/sharper fans:  lower the **0.2 power (try 0.1)")
print(f"     - More spokes:           increase N_RAYS (try 72)")
print(f"     - Finer detail:          increase MAX_ITER (try 20000)")
print(f"     - Brighter fans:         increase fan multiplier (0.6→0.8)")
