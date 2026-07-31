"""
05_explore_params.py
=====================
SCRIPT 5 of 5 — Interactive parameter explorer.

This script lets you quickly try different parameter combinations from
the command line.  It's the same algorithm as 04_hires_combined.py but
exposes all key parameters as CLI arguments.

Usage examples:
  python 05_explore_params.py                      # defaults
  python 05_explore_params.py 600 480 5000 36     # W H MAX_ITER N_RAYS
  python 05_explore_params.py 1200 960 20000 72   # high quality
  python 05_explore_params.py 400 320 3000 24      # quick preview

Output files are named with the parameters so you can compare:
  explore_W600_H480_I5000_R36.png

Dependencies: numpy, matplotlib, scipy
"""
import sys, time, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter

# ── CLI args with defaults ──────────────────────────────────────────────────
W     = int(sys.argv[1]) if len(sys.argv) > 1 else 600
H     = int(sys.argv[2]) if len(sys.argv) > 2 else 480
MAX_I = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
N_RAY = int(sys.argv[4]) if len(sys.argv) > 4 else 36
RE0,RE1 = -3.0, 7.0
IM0,IM1 = -4.0, 4.0
BAILOUT = 2.0

t0 = time.time()
N = W * H
tag = f"W{W}_H{H}_I{MAX_I}_R{N_RAY}"
print(f"[05] Explore: {tag}  ({N:,} pixels)")

# c-grid
re = np.linspace(RE0, RE1, W, dtype=np.float64)
im = np.linspace(IM0, IM1, H, dtype=np.float64)
Rg, Ig = np.meshgrid(re, im)
c = Rg + 1j * Ig
inv = 1.0 / np.where(np.abs(c) < 1e-15, 1e-15 + 0j, c)
invf = inv.ravel()

z = np.zeros(N, dtype=np.complex128)
esc = np.zeros(N, dtype=bool)
itc = np.zeros(N, dtype=np.int32)
last = np.zeros(N, dtype=np.complex128)
tr = np.full(N, 1e10, dtype=np.float64)
tre = np.full(N, 1e10, dtype=np.float64)
tim = np.full(N, 1e10, dtype=np.float64)

angs = np.linspace(0, 2*np.pi, N_RAYS, endpoint=False)
st = np.sin(angs)
ct = np.cos(angs)

# Iterate
print("Iterating...")
for s in range(MAX_I):
    act = ~esc
    if not act.any(): break
    z[act] = z[act]**2 + invf[act]
    m2 = z.real[act]**2 + z.imag[act]**2
    ne = m2 > BAILOUT**2
    idx = np.where(act)[0][ne]
    itc[idx] = s+1; last[idx] = z[idx]; esc[idx] = True

    still = ~esc
    if still.any():
        idx2 = np.where(still)[0]
        zr = z.real[idx2]; zi = z.imag[idx2]
        tre[idx2] = np.minimum(tre[idx2], np.abs(zi))
        tim[idx2] = np.minimum(tim[idx2], np.abs(zr))
        d = np.abs(zr[:,None]*st[None,:] - zi[:,None]*ct[None,:])
        tr[idx2] = np.minimum(tr[idx2], d.min(axis=1))
    z[esc] = 0
    if (s+1) % 2000 == 0:
        n=int(esc.sum())
        print(f"  iter {s+1}: {n:,}/{N:,} ({n/N*100:.1f}%) t={time.time()-t0:.0f}s")

n_esc=int(esc.sum())
print(f"  Done. Escaped: {n_esc:,}/{N:,}")

# Potential
mag=np.abs(last).clip(1,None)
pot=np.log(np.log(mag)/np.log(2.0))/np.log(2.0)
pn=np.zeros(N)
if n_esc>0:
    pv=pot[esc]; pn[esc]=(pv-pv.min())/(pv.max()-pv.min())
pn[~esc]=itc[~esc].astype(float)/MAX_I*0.35

# Traps
def n01(a,l=0.5,h=99.5):
    b=a[(a<1e9)&(a>0)]
    if b.size<2: return np.zeros_like(a)
    lo,hi=np.percentile(b,[l,h])
    return np.clip((a-lo)/(hi-lo),0,1) if hi>lo else np.zeros_like(a)

rl =np.clip((1-n01(tr ))**0.2, 0,1)
rel=np.clip((1-n01(tre))**0.15,0,1)
iml=np.clip((1-n01(tim))**0.15,0,1)

# Composite
base=pn.reshape(H,W)
fan =rl.reshape(H,W)*0.6+rel.reshape(H,W)*0.2+iml.reshape(H,W)*0.2
I=base*0.25+fan*0.65
I[~esc.reshape(H,W)]=itc[~esc.reshape(H,W)].astype(float)/MAX_I*0.2+0.02
I+=np.clip(base,0,1)*0.08
I=np.clip(I,1e-5,None)
I=np.log1p(I*12)/np.log1p(12)
I=gaussian_filter(I,sigma=0.6,mode='nearest')
I=np.clip(I,0,1)

# Rotate Re→UP
img=np.rot90(I,k=1)

# Save
cmap=LinearSegmentedColormap.from_list('invmb',
    ['#000004','#050318','#0a0a38','#101a58','#1a2e78',
     '#2a4ea0','#3a72c8','#4a96e8','#5ab0ff','#7ac8ff',
     '#9adfff','#bcefff','#defbff','#f0feff'],N=1024)

out=os.path.join(os.path.dirname(__file__),f'explore_{tag}.png')
fig,ax=plt.subplots(figsize=(H/100,W/100),dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img,cmap=cmap,aspect='auto',interpolation='bilinear',origin='lower')
ax.axis('off')
plt.savefig(out,dpi=100,bbox_inches='tight',pad_inches=0,facecolor='black')
plt.close()

# Gray
outg=out.replace('.png','_gray.png')
fig,ax=plt.subplots(figsize=(H/100,W/100),dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img,cmap='gray_r',aspect='auto',interpolation='bilinear',origin='lower')
ax.axis('off')
plt.savefig(outg,dpi=100,bbox_inches='tight',pad_inches=0,facecolor='black')
plt.close()

print(f"\n✅ Saved: {out}")
print(f"✅ Saved: {outg}")
print(f"   Time: {time.time()-t0:.1f}s")
print(f"\n   Try these combos:")
print(f"   python 05_explore_params.py 400  320  3000  24   ← fast preview")
print(f"   python 05_explore_params.py 800  640  8000  36   ← balanced")
print(f"   python 05_explore_params.py 1200 960  15000 48   ← high quality")
print(f"   python 05_explore_params.py 1600 1280 30000 72   ← max quality")
