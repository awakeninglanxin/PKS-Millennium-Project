"""LBM v8 — EQ-reset inlet (skip collision on inlet), gravity everywhere, Z↑ render"""
import cupy as cp, numpy as np, time, math, pickle, os

cx_np = np.array([0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0], np.int32)
cy_np = np.array([0, 0, 0, 1,-1, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1], np.int32)
cz_np = np.array([0, 0, 0, 0, 0, 1,-1, 0, 0, 0, 0, 1, 1,-1,-1, 1, 1,-1,-1], np.int32)
w_np  = np.array([1/3] + [1/18]*6 + [1/36]*12, np.float64)
opp   = [0,2,1,4,3,6,5,8,7,10,9,12,11,14,13,16,15,18,17]

cx = cp.array(cx_np, cp.int32); cy = cp.array(cy_np, cp.int32); cz = cp.array(cz_np, cp.int32)
w  = cp.array(w_np, cp.float64)

NX, NY, NZ = 128, 128, 192
tau = 0.56; omega = 1.0/tau
u_down = 0.06; u_tan = 0.10; g_grav = 8e-5
STEPS = 10000; SNAP_EVERY = 400

Re_est = max(u_down,u_tan)*(NX//3)/((tau-0.5)/3)
print(f"LBM v8: {NX}x{NY}x{NZ}, Re~{Re_est:.0f}, EQ-reset inlet, g={g_grav}")
t0 = time.time()

# ── Geometry ──
xg,yg,zg = np.meshgrid(np.arange(NX),np.arange(NY),np.arange(NZ),indexing='ij')
cx0,cy0 = NX//2,NY//2
r_grid = np.sqrt((xg-cx0)**2+(yg-cy0)**2)
z_rel = zg/(NZ-1)
throat_r = 4.0
top_r = throat_r + (NX//3 - throat_r)*z_rel**1.5
wall_r = top_r + 2.0

mask_np = (r_grid >= top_r) & (r_grid < wall_r) & (z_rel > 0.02)
mask_np |= (r_grid < throat_r+1) & (z_rel <= 0.02) & (r_grid >= throat_r-1)
mask = cp.asarray(mask_np)
print(f"  Wall: {int(mask.sum())}")

# ── Inlet (top 20%) ──
inlet_np = (z_rel > 0.80) & (r_grid < top_r) & (~mask_np)
print(f"  Inlet: {int(inlet_np.sum())}")

dx_np = (xg-cx0).astype(np.float64); dy_np = (yg-cy0).astype(np.float64)
rr_np = np.maximum(np.sqrt(dx_np**2+dy_np**2),1e-6)
scale = np.clip(r_grid/np.maximum(top_r,1e-6),0.0,1.0)

ux_in_np = np.where(inlet_np, -u_tan*(dy_np/rr_np)*scale*scale, 0.0)
uy_in_np = np.where(inlet_np,  u_tan*(dx_np/rr_np)*scale*scale, 0.0)
uz_in_np = np.where(inlet_np, -u_down*scale, 0.0)

ux_in = cp.asarray(ux_in_np.astype(np.float64))
uy_in = cp.asarray(uy_in_np.astype(np.float64))
uz_in = cp.asarray(uz_in_np.astype(np.float64))
inlet_mask = cp.asarray(inlet_np)
collide_zone = (~mask) & (~inlet_mask)  # collide everywhere except wall+inlet

# ── Init ──
f = cp.zeros((NX,NY,NZ,19), dtype=cp.float64)
for k in range(19): f[:,:,:,k] = w[k]

snap3d = []
u2_in = ux_in*ux_in + uy_in*uy_in + uz_in*uz_in  # precompute for inlet

for t_step in range(STEPS):
    # 1. Macroscopic
    rho = f.sum(axis=3); de = rho+1e-10
    ux = (f[:,:,:,1]+f[:,:,:,7]+f[:,:,:,9]+f[:,:,:,11]+f[:,:,:,13]
         -f[:,:,:,2]-f[:,:,:,8]-f[:,:,:,10]-f[:,:,:,12]-f[:,:,:,14])/de
    uy = (f[:,:,:,3]+f[:,:,:,7]+f[:,:,:,8]+f[:,:,:,15]+f[:,:,:,17]
         -f[:,:,:,4]-f[:,:,:,9]-f[:,:,:,10]-f[:,:,:,16]-f[:,:,:,18])/de
    uz = (f[:,:,:,5]+f[:,:,:,11]+f[:,:,:,12]+f[:,:,:,15]+f[:,:,:,16]
         -f[:,:,:,6]-f[:,:,:,13]-f[:,:,:,14]-f[:,:,:,17]-f[:,:,:,18])/de
    ux[mask]=0; uy[mask]=0; uz[mask]=0

    # 2. EQ-reset inlet (BEFORE collision)
    for k in range(19):
        cu = 3.0*(float(cx_np[k])*ux_in + float(cy_np[k])*uy_in + float(cz_np[k])*uz_in)
        feq = w[k]*(1.0 + cu + 0.5*cu*cu - 1.5*u2_in)
        f[inlet_mask, k] = feq[inlet_mask]

    # 3. Collision (skip inlet)
    u2 = ux*ux + uy*uy + uz*uz
    for k in range(19):
        cu = 3.0*(float(cx_np[k])*ux + float(cy_np[k])*uy + float(cz_np[k])*uz)
        feq = w[k]*rho*(1.0 + cu + 0.5*cu*cu - 1.5*u2)
        f[collide_zone, k] -= omega*(f[collide_zone, k]-feq[collide_zone])

    # 4. Gravity (everywhere in fluid)
    for k in range(19):
        if cz_np[k]:
            f[~mask, k] += 3.0*float(w_np[k])*float(-cz_np[k])*g_grav

    # 5. Streaming + bounce-back
    for k in range(19):
        if cx_np[k]: f[:,:,:,k] = cp.roll(f[:,:,:,k], -int(cx_np[k]), axis=0)
        if cy_np[k]: f[:,:,:,k] = cp.roll(f[:,:,:,k], -int(cy_np[k]), axis=1)
        if cz_np[k]: f[:,:,:,k] = cp.roll(f[:,:,:,k], -int(cz_np[k]), axis=2)
    fb = f.copy()
    for k in range(19): f[mask,k] = fb[mask,opp[k]]

    # 6. Snapshot
    if t_step % SNAP_EVERY == 0 or t_step == STEPS-1:
        duz_dy=(cp.roll(uz,-1,1)-cp.roll(uz,1,1))/2; duy_dz=(cp.roll(uy,-1,2)-cp.roll(uy,1,2))/2
        dux_dz=(cp.roll(ux,-1,2)-cp.roll(ux,1,2))/2; duz_dx=(cp.roll(uz,-1,0)-cp.roll(uz,1,0))/2
        duy_dx=(cp.roll(uy,-1,0)-cp.roll(uy,1,0))/2; dux_dy=(cp.roll(ux,-1,1)-cp.roll(ux,1,1))/2
        w_mag = cp.sqrt((duz_dy-duy_dz)**2+(dux_dz-duz_dx)**2+(duy_dx-dux_dy)**2)
        w_mag[mask]=0
        v_max = float(cp.sqrt(ux*ux+uy*uy+uz*uz).max())
        w_max = float(w_mag.max())
        ok = not np.isnan(w_max)
        ds = cp.asnumpy(w_mag[::2,::2,::2]).astype(np.float32) if ok else np.zeros((64,64,96),dtype=np.float32)
        snap3d.append((t_step, ds))
        print(f"  {t_step:5d}: |w|max={w_max:.4e} |v|max={v_max:.4e} {'✓' if ok else '💥'}")

total_t = time.time()-t0
print(f"Done: {total_t:.0f}s, {len(snap3d)} snaps")

# ── Save ──
with open('/root/lbm_v8.pkl','wb') as f:
    pickle.dump({'snaps':snap3d,'mask':mask_np[::2,::2,::2],'NX':64,'NY':64,'NZ':96,'Re':Re_est},f)

# ── Render Z↑ isometric GIF ──
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

mask_ds = mask_np[::2,::2,::2]
mz,my,mx = np.where(mask_ds.transpose(2,1,0))
if len(mz)>25000:
    idx=np.random.choice(len(mz),25000,replace=False); mz,my,mx=mz[idx],my[idx],mx[idx]

valid=[(s,w) for s,w in snap3d if w.max()>1e-6 and not np.isnan(w.max())]
wref=np.percentile(np.concatenate([w.ravel() for _,w in valid]),99) if valid else 0.01
print(f"  wref(99%): {wref:.4f}")

fig=plt.figure(figsize=(13,11)); ax=fig.add_subplot(111,projection='3d')
from matplotlib import animation as ani

def render(i):
    ax.clear()
    step,w_ds=snap3d[i]
    if w_ds.max()<1e-8: return []
    if len(mz)>0: ax.scatter(mx,my,mz,c='white',s=0.06,alpha=0.11,rasterized=True)
    zz,yy,xx=np.where(w_ds>max(wref*0.02,1e-6))
    if len(zz)>60000:
        idx=np.random.choice(len(zz),60000,replace=False); zz,yy,xx=zz[idx],yy[idx],xx[idx]
    if len(zz)>0:
        vals=w_ds[xx,yy,zz]; nv=np.clip(vals/max(wref,0.001),0,1)
        colors=np.zeros((len(vals),4))
        for j in range(len(vals)):
            v=nv[j]
            if v<0.2: colors[j]=[0,0,0.3+3*v,0.5]
            elif v<0.4: colors[j]=[0,3*(v-0.2),0.7,0.7]
            elif v<0.6: colors[j]=[4*(v-0.4),0.8,0,0.8]
            elif v<0.8: colors[j]=[0.9,max(0.6-4*(v-0.6),0),0,0.85]
            else: colors[j]=[1,0.2,0,0.9]
        ax.scatter(xx,yy,zz,c=colors,s=0.5,alpha=0.4,rasterized=True)
    rng=32; ax.set_xlim(32-rng,32+rng); ax.set_ylim(32-rng,32+rng); ax.set_zlim(0,96)
    ax.view_init(elev=22,azim=-55)
    ax.set_title(f'PKS Cone Spiral | Z↑ flow↓ | Re~{Re_est:.0f}',color='lightgray',fontsize=12)
    ax.set_xlabel('X',color='gray'); ax.set_ylabel('Y',color='gray'); ax.set_zlabel('Z↑',color='gray')
    ax.tick_params(colors='gray',labelsize=5); ax.grid(True,alpha=0.03,color='white')
    ax.set_facecolor('#050510'); fig.patch.set_facecolor('#050510')
    return []

anim=ani.FuncAnimation(fig,render,frames=len(snap3d),interval=150,blit=False)
anim.save('/root/lbm_v8.gif',dpi=100,fps=7,savefig_kwargs={'facecolor':'#050510','bbox_inches':'tight'})
plt.close()
print(f"  GIF: {os.path.getsize('/root/lbm_v8.gif')/1024:.0f}KB")

import csv
with open('/root/lbm_v8.csv','w',newline='') as f:
    wr=csv.writer(f); wr.writerow(['step','w_max'])
    for s,w in snap3d: wr.writerow([s,float(w.max()) if not np.isnan(w.max()) else 0])
print("Saved: lbm_v8.csv + pkl + gif")
