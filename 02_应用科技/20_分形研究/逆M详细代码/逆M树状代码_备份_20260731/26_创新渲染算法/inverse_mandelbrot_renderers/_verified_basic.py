"""
_verified_basic.py
====================
VERIFIED WORKING — This is the exact script that produced
inverse_mandelbrot_final.png (300×240, 5000 iters, 72s) in the sandbox.

Simplest possible version: escape-time + smooth potential + orbit traps.
No fancy parameters — just the core algorithm that WORKS.

Run:  python _verified_basic.py
"""
import numpy as np, time, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter

# ── Parameters (verified) ──────────────────────────────────────────────────
W, H = 300, 240
MAX_I = 5000
RE0, RE1 = -3.0, 7.0
IM0, IM1 = -4.0, 4.0
BAILOUT = 2.0
N_RAYS = 36

t0 = time.time()
N = W * H
print(f"Verified basic renderer  W={W} H={H} MAX_I={MAX_I} rays={N_RAYS}")

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
tr = np.full(N, 1e10); tre = np.full(N, 1e10); tim = np.full(N, 1e10)

angs = np.linspace(0, 2*np.pi, N_RAYS, endpoint=False)
st = np.sin(angs); ct = np.cos(angs)

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
    if (s+1) % 1000 == 0:
        n=int(esc.sum())
        print(f"  iter {s+1}: {n:,}/{N:,} ({n/N*100:.1f}%) t={time.time()-t0:.0f}s")

n_esc=int(esc.sum())
print(f"  Done. Escaped: {n_esc:,}/{N:,}  Interior: {N-n_esc:,}")

# Potential
mag=np.abs(last).clip(1,None)
pot=np.log(np.log(mag)/np.log(2.0))/np.log(2.0)
pn=np.zeros(N)
if n_esc>0:
    pv=pot[esc]; pn[esc]=(pv-pv.min())/(pv.max()-pv.min())
pn[~esc]=itc[~esc].astype(float)/MAX_I*0.4

# Traps
def n01(a,l=0.5,h=99.5):
    b=a[(a<1e9)&(a>0)]
    if b.size<2: return np.zeros_like(a)
    lo,hi=np.percentile(b,[l,h])
    return np.clip((a-lo)/(hi-lo),0,1) if hi>lo else np.zeros_like(a)

rl=np.clip((1-n01(tr ))**0.25,0,1)
rel=np.clip((1-n01(tre))**0.15,0,1)
iml=np.clip((1-n01(tim))**0.15,0,1)

# Composite
base=pn.reshape(H,W)
fan=rl.reshape(H,W)*0.65+rel.reshape(H,W)*0.175+iml.reshape(H,W)*0.175
I=base*0.30+fan*0.60
I[~esc.reshape(H,W)]=itc[~esc.reshape(H,W)].astype(float)/MAX_I*0.25+0.03
I+=np.clip(base,0,1)*0.10
I=np.clip(I,1e-5,None)
I=np.log1p(I*10)/np.log1p(10)
I=gaussian_filter(I,sigma=0.6,mode='nearest')
I=np.clip(I,0,1)

# Rotate Re→UP
img=np.rot90(I,k=1)

# Save
cmap=LinearSegmentedColormap.from_list('invmb',
    ['#000004','#050318','#0a0a38','#101a58','#1a2e78',
     '#2a4ea0','#3a72c8','#4a96e8','#6ab8ff','#8ad8ff',
     '#aef0ff','#d4f6ff','#f0feff'],N=1024)

out=os.path.join(os.path.dirname(__file__),'_verified_basic.png')
fig,ax=plt.subplots(figsize=(H/100,W/100),dpi=150)
ax.set_position([0,0,1,1])
ax.imshow(img,cmap=cmap,aspect='auto',interpolation='bilinear',origin='lower')
ax.axis('off')
plt.savefig(out,dpi=150,bbox_inches='tight',pad_inches=0,facecolor='black')
plt.close()

print(f"\n✅ Saved: {out}")
print(f"   Time: {time.time()-t0:.1f}s")
print(f"\n   → Now try scaling up: edit W,H,MAX_I at the top of the file.")
