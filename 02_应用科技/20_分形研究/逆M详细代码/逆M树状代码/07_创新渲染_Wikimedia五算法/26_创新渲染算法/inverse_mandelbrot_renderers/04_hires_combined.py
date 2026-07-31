"""
04_hires_combined.py
=====================
SCRIPT 4 of 5 — HIGH-RESOLUTION COMBINED RENDERER.

This is the recommended "best quality" script. It combines:
  ✓ Smooth escape potential (Hubbard-Douady) → base relief
  ✓ Orbit trap: 48 radial lines              → fan/spoke texture
  ✓ Orbit trap: Re/Im axes                   → cross structure
  ✓ Logarithmic tone mapping                 → "non-sticky" ethereal look
  ✓ Gaussian anti-aliasing                   → smooth edges
  ✓ High iteration (10000)                   → crisp boundary detail
  ✓ 48 radial rays                          → sharp triangular sectors

Output: 1200×960 grid → rotated to 960×1200 upright teardrop.

For MAXIMUM quality on a powerful machine, change the parameters to:
  W, H = 2400, 1920
  MAX_ITER = 50000
  N_RAYS = 72

Run:  python 04_hires_combined.py

Dependencies: numpy, matplotlib, scipy
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter
import time, os

# ═════════════════════════════════════════════════════════════════════════
#  ★ EDIT THESE PARAMETERS ★
# ═════════════════════════════════════════════════════════════════════════
W, H = 1200, 960        # c-plane grid (after rotation: 960×1200 upright)
RE0, RE1 = -3.0, 7.0   # Re(c)
IM0, IM1 = -4.0, 4.0    # Im(c)
MAX_ITER = 10000        # ★★ increase to 50000 for publication quality
BAILOUT = 2.0
N_RAYS = 48             # ★★ increase to 72 for more spokes

# Texture weights (must sum to ~1.0)
W_POTENTIAL = 0.25       # smooth relief from escape potential
W_RADIAL    = 0.60       # radial fan lines (THE key texture)
W_AXES      = 0.15       # Re/Im axis crosses
LOG_FACTOR  = 12.0       # log scaling strength (higher = more ethereal)
BLUR_SIGMA  = 0.8        # anti-alias (0.5=sharp, 1.5=soft)

# ═════════════════════════════════════════════════════════════════════════
t0 = time.time()
N = W * H
print("╔════════════════════════════════════════════════╗")
print("║  Inverse Mandelbrot — Hi-Res Combined Render  ║")
print("╚════════════════════════════════════════════════╝")
print(f"  Grid: {W}×{H} = {N:,} pixels")
print(f"  Viewport: Re∈[{RE0},{RE1}], Im∈[{IM0},{IM1}]")
print(f"  max_iter={MAX_ITER}  bailout={BAILOUT}  rays={N_RAYS}")

# ── 1. c-grid ──────────────────────────────────────────────────────────────
re = np.linspace(RE0, RE1, W, dtype=np.float64)
im = np.linspace(IM0, IM1, H, dtype=np.float64)
Rg, Ig = np.meshgrid(re, im)
c = Rg + 1j * Ig
inv = 1.0 / np.where(np.abs(c) < 1e-15, 1e-15 + 0j, c)
invf = inv.ravel()

# ── 2. State arrays ────────────────────────────────────────────────────────
z = np.zeros(N, dtype=np.complex128)
esc = np.zeros(N, dtype=bool)
itc = np.zeros(N, dtype=np.int32)
last = np.zeros(N, dtype=np.complex128)

trap_ray = np.full(N, 1e10, dtype=np.float64)
trap_re  = np.full(N, 1e10, dtype=np.float64)
trap_im  = np.full(N, 1e10, dtype=np.float64)

angs = np.linspace(0, 2*np.pi, N_RAYS, endpoint=False)
st = np.sin(angs)
ct = np.cos(angs)

# ── 3. Iteration loop ──────────────────────────────────────────────────────
print("\n[Iteration]")
for s in range(MAX_ITER):
    act = ~esc
    if not act.any():
        print(f"  ✓ All escaped at iter {s}"); break

    z[act] = z[act]**2 + invf[act]

    m2 = z.real[act]**2 + z.imag[act]**2
    ne = m2 > BAILOUT**2
    idx_ne = np.where(act)[0][ne]
    itc[idx_ne] = s + 1
    last[idx_ne] = z[idx_ne]
    esc[idx_ne] = True

    still = ~esc
    if still.any():
        idx = np.where(still)[0]
        zr = z.real[idx]
        zi = z.imag[idx]
        trap_re[idx]  = np.minimum(trap_re[idx],  np.abs(zi))
        trap_im[idx]  = np.minimum(trap_im[idx],  np.abs(zr))
        d = np.abs(zr[:,None]*st[None,:] - zi[:,None]*ct[None,:])
        trap_ray[idx] = np.minimum(trap_ray[idx], d.min(axis=1))

    z[esc] = 0

    if (s+1) % 2500 == 0:
        n = int(esc.sum())
        print(f"  iter {s+1:>5d}: active={N-n:>10,}  "
              f"esc={n:>10,} ({n/N*100:5.1f}%)  t={time.time()-t0:6.1f}s")

n_esc = int(esc.sum())
print(f"\n  ✓ Done. Escaped: {n_esc:,}/{N:,} ({n_esc/N*100:.1f}%)")
print(f"    Interior: {N-n_esc:,}")

# ── 4. Potential ───────────────────────────────────────────────────────────
print("[Potential + Traps]")
mag = np.abs(last).clip(1, None)
pot = np.log(np.log(mag)/np.log(2.0)) / np.log(2.0)
pn = np.zeros(N)
if n_esc > 0:
    pv = pot[esc]
    pn[esc] = (pv - pv.min()) / (pv.max() - pv.min())
pn[~esc] = itc[~esc].astype(float) / MAX_ITER * 0.35

# ── 5. Normalize traps ─────────────────────────────────────────────────────
def n01(a, l=0.5, h=99.5):
    b = a[(a < 1e9) & (a > 0)]
    if b.size < 2: return np.zeros_like(a)
    lo, hi = np.percentile(b, [l, h])
    return np.clip((a - lo) / (hi - lo), 0, 1) if hi > lo else np.zeros_like(a)

rl  = np.clip((1.0 - n01(trap_ray))**0.2,  0, 1)
rel = np.clip((1.0 - n01(trap_re ))**0.15, 0, 1)
iml = np.clip((1.0 - n01(trap_im ))**0.15, 0, 1)

# ── 6. Composite ──────────────────────────────────────────────────────────
print("[Composite]")
base = pn.reshape(H, W)
fan  = rl.reshape(H,W)*W_RADIAL + rel.reshape(H,W)*W_AXES*0.5 + iml.reshape(H,W)*W_AXES*0.5

I = base*W_POTENTIAL + fan*(1.0 - W_POTENTIAL)
I[~esc.reshape(H,W)] = itc[~esc.reshape(H,W)].astype(float)/MAX_ITER*0.2 + 0.02
I += np.clip(base, 0, 1) * 0.08

# Log scaling
I = np.clip(I, 1e-5, None)
I = np.log1p(I * LOG_FACTOR) / np.log1p(LOG_FACTOR)

# Anti-alias
I = gaussian_filter(I, sigma=BLUR_SIGMA, mode='nearest')
I = np.clip(I, 0, 1)

# Rotate Re-axis → UP
img = np.rot90(I, k=1)

# ── 7. Save ───────────────────────────────────────────────────────────────
cmap = LinearSegmentedColormap.from_list('invmb',
    ['#000004','#050318','#0a0a38','#101a58','#1a2e78',
     '#2a4ea0','#3a72c8','#4a96e8','#5ab0ff','#7ac8ff',
     '#9adfff','#bcefff','#defbff','#f0feff'], N=2048)

out = os.path.join(os.path.dirname(__file__), '04_hires_combined.png')
fig, ax = plt.subplots(figsize=(H/100, W/100), dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img, cmap=cmap, aspect='auto', interpolation='bilinear', origin='lower')
ax.axis('off')
plt.savefig(out, dpi=100, bbox_inches='tight', pad_inches=0, facecolor='black')
plt.close()

# Grayscale version
outg = out.replace('.png', '_gray.png')
fig, ax = plt.subplots(figsize=(H/100, W/100), dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img, cmap='gray_r', aspect='auto', interpolation='bilinear', origin='lower')
ax.axis('off')
plt.savefig(outg, dpi=100, bbox_inches='tight', pad_inches=0, facecolor='black')
plt.close()

elapsed = time.time() - t0
print(f"\n✅ Complete in {elapsed:.1f}s")
print(f"   Color:  {out}")
print(f"   Gray:   {outg}")
print(f"   Shape:  {img.shape} (upright, Re axis ↑)")
print(f"\n   ★ To match the reference image:")
print(f"     1. If fans are too thick:    lower the **0.2 to **0.1")
print(f"     2. If fans are too faint:    raise W_RADIAL to 0.75")
print(f"     3. If interior is too dark:  raise the +0.02 offset")
print(f"     4. For max quality:          W=2400 H=1920 MAX_ITER=50000")
