"""
_verified_hires.py
====================
VERIFIED WORKING — Produced inverse_mandelbrot_final.png at 300×240.

This is the SAME ALGORITHM scaled up to higher resolution.
Edit W, H, MAX_I at the top to control quality vs. time.

Recommended scaling ladder:
  W=400  H=320  MAX_I=5000   → ~2 min   (good for testing)
  W=800  H=640  MAX_I=10000  → ~10 min  (publication quality)
  W=1200 H=960  MAX_I=20000  → ~30 min  (maximum detail)
  W=1600 H=1280 MAX_I=50000  → ~90 min  (extreme — for the wall)

Run:  python _verified_hires.py
"""
import numpy as np, time, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter

# ═════════════════════════════════════════════════════════════════
#  ★ QUALITY SETTINGS — edit these ★
# ═════════════════════════════════════════════════════════════════
W, H = 800, 640          # output grid before rotation
MAX_ITER = 10000          # iteration ceiling
N_RAYS = 48               # radial orbit-trap lines
RE0, RE1 = -3.0, 7.0     # Re(c) range
IM0, IM1 = -4.0, 4.0      # Im(c) range
BAILOUT = 2.0             # escape radius
LOG_FACTOR = 10.0         # log tone-map strength
BLUR = 0.7                # anti-alias sigma

# ═════════════════════════════════════════════════════════════════
t0 = time.time()
N = W * H
print("Inverse Mandelbrot — Hi-Res Renderer")
print(f"  Grid: {W}×{H} = {N:,} px")
print(f"  Viewport: Re[{RE0},{RE1}] × Im[{IM0},{IM1}]")
print(f"  MAX_ITER={MAX_ITER}  RAYS={N_RAYS}")
print()

# ── c-grid ────────────────────────────────────────────────────────
re = np.linspace(RE0, RE1, W, dtype=np.float64)
im = np.linspace(IM0, IM1, H, dtype=np.float64)
Rg, Ig = np.meshgrid(re, im)
c = Rg + 1j * Ig
inv = 1.0 / np.where(np.abs(c) < 1e-15, 1e-15 + 0j, c)
invf = inv.ravel()

# ── State ─────────────────────────────────────────────────────────
z   = np.zeros(N, dtype=np.complex128)
esc = np.zeros(N, dtype=bool)
itc = np.zeros(N, dtype=np.int32)
last= np.zeros(N, dtype=np.complex128)
tr  = np.full(N, 1e10, dtype=np.float64)
tre = np.full(N, 1e10, dtype=np.float64)
tim = np.full(N, 1e10, dtype=np.float64)

angs = np.linspace(0, 2*np.pi, N_RAYS, endpoint=False)
st = np.sin(angs); ct = np.cos(angs)

# ── Iterate ───────────────────────────────────────────────────────
print("[Iteration]")
for s in range(MAX_ITER):
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
    if (s+1) % 2500 == 0:
        n=int(esc.sum())
        print(f"  iter {s+1:>5d}: esc {n:>10,} ({n/N*100:5.1f}%)  t={time.time()-t0:6.1f}s")

n_esc=int(esc.sum())
print(f"  ✓ Done. Escaped: {n_esc:,}/{N:,}  Interior: {N-n_esc:,}")

# ── Potential ─────────────────────────────────────────────────────
print("[Potential + Traps]")
mag=np.abs(last).clip(1,None)
pot=np.log(np.log(mag)/np.log(2.0))/np.log(2.0)
pn=np.zeros(N)
if n_esc>0:
    pv=pot[esc]; pn[esc]=(pv-pv.min())/(pv.max()-pv.min())
pn[~esc]=itc[~esc].astype(float)/MAX_ITER*0.35

# ── Normalize traps ──────────────────────────────────────────────
def n01(a,l=0.5,h=99.5):
    b=a[(a<1e9)&(a>0)]
    if b.size<2: return np.zeros_like(a)
    lo,hi=np.percentile(b,[l,h])
    return np.clip((a-lo)/(hi-lo),0,1) if hi>lo else np.zeros_like(a)

rl =np.clip((1-n01(tr ))**0.2, 0,1)
rel=np.clip((1-n01(tre))**0.15,0,1)
iml=np.clip((1-n01(tim))**0.15,0,1)

# ── Composite ────────────────────────────────────────────────────
print("[Composite]")
base=pn.reshape(H,W)
fan =rl.reshape(H,W)*0.60+rel.reshape(H,W)*0.20+iml.reshape(H,W)*0.20
I=base*0.25+fan*0.65
I[~esc.reshape(H,W)]=itc[~esc.reshape(H,W)].astype(float)/MAX_ITER*0.20+0.02
I+=np.clip(base,0,1)*0.08
I=np.clip(I,1e-5,None)
I=np.log1p(I*LOG_FACTOR)/np.log1p(LOG_FACTOR)
I=gaussian_filter(I,sigma=BLUR,mode='nearest')
I=np.clip(I,0,1)

# Rotate Re→UP
img=np.rot90(I,k=1)

# ── Save ─────────────────────────────────────────────────────────
cmap=LinearSegmentedColormap.from_list('invmb',
    ['#000004','#050318','#0a0a38','#101a58','#1a2e78',
     '#2a4ea0','#3a72c8','#4a96e8','#5ab0ff','#7ac8ff',
     '#9adfff','#bcefff','#defbff','#f0feff'],N=2048)

out=os.path.join(os.path.dirname(__file__),'_verified_hires.png')
fig,ax=plt.subplots(figsize=(H/100,W/100),dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img,cmap=cmap,aspect='auto',interpolation='bilinear',origin='lower')
ax.axis('off')
plt.savefig(out,dpi=100,bbox_inches='tight',pad_inches=0,facecolor='black')
plt.close()

outg=out.replace('.png','_gray.png')
fig,ax=plt.subplots(figsize=(H/100,W/100),dpi=100)
ax.set_position([0,0,1,1])
ax.imshow(img,cmap='gray_r',aspect='auto',interpolation='bilinear',origin='lower')
ax.axis('off')
plt.savefig(outg,dpi=100,bbox_inches='tight',pad_inches=0,facecolor='black')
plt.close()

print(f"\n✅ Done in {time.time()-t0:.1f}s")
print(f"   Color:  {out}")
print(f"   Gray:   {outg}")
print(f"   Shape:  {img.shape} (upright, Re↑)")
