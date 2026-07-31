"""LBM v5 — 3D isometric rendering version
Re-runs LBM v4 (proven params) + saves 3D vorticity snapshots + renders isometric GIF
"""
import cupy as cp, numpy as np, time, csv, math, pickle

cx = cp.array([0, 1,-1, 0, 0, 0, 0, 1,-1, 1,-1, 1,-1, 1,-1, 0, 0, 0, 0], cp.int32)
cy = cp.array([0, 0, 0, 1,-1, 0, 0, 1, 1,-1,-1, 0, 0, 0, 0, 1,-1, 1,-1], cp.int32)
cz = cp.array([0, 0, 0, 0, 0, 1,-1, 0, 0, 0, 0, 1, 1,-1,-1, 1, 1,-1,-1], cp.int32)
w  = cp.array([1/3] + [1/18]*6 + [1/36]*12, cp.float64)
opp = [0,2,1,4,3,6,5,8,7,10,9,12,11,14,13,16,15,18,17]
cx_h = cp.asnumpy(cx); cy_h = cp.asnumpy(cy); cz_h = cp.asnumpy(cz)

NX, NY, NZ = 128, 128, 192
u0 = 0.06; tau = 0.56; omega = 1.0/tau
STEPS = 8000; SNAP_EVERY = 320  # 25 3D snapshots
Re_est = u0*(NX//3)/((tau-0.5)/3)

print(f"LBM v5 3D-iso: {NX}x{NY}x{NZ}, Re~{Re_est:.0f}")
t0 = time.time()

xg, yg, zg = np.meshgrid(np.arange(NX), np.arange(NY), np.arange(NZ), indexing='ij')
cx0, cy0 = NX//2, NY//2
r_grid = np.sqrt((xg-cx0)**2 + (yg-cy0)**2)
z_rel = zg/(NZ-1)
throat_r = 4.0
top_r = throat_r + (NX//3 - throat_r)*z_rel**1.5
wall_r = top_r + 2.0
mask_np = (r_grid >= top_r) & (r_grid < wall_r) & (z_rel > 0.02)
mask_np |= (r_grid < throat_r+1) & (z_rel <= 0.02) & (r_grid >= throat_r-1)
mask = cp.asarray(mask_np)
print(f"  Wall: {int(mask.sum())}")

f = cp.zeros((NX,NY,NZ,19), dtype=cp.float64)
for k in range(19): f[:,:,:,k] = w[k]

snap3d = []  # (step, w_mag downsampled 2x)

for t_step in range(STEPS):
    rho = f.sum(axis=3); de = rho+1e-10
    ux = (f[:,:,:,1]+f[:,:,:,7]+f[:,:,:,9]+f[:,:,:,11]+f[:,:,:,13]
         -f[:,:,:,2]-f[:,:,:,8]-f[:,:,:,10]-f[:,:,:,12]-f[:,:,:,14])/de
    uy = (f[:,:,:,3]+f[:,:,:,7]+f[:,:,:,8]+f[:,:,:,15]+f[:,:,:,17]
         -f[:,:,:,4]-f[:,:,:,9]-f[:,:,:,10]-f[:,:,:,16]-f[:,:,:,18])/de
    uz = (f[:,:,:,5]+f[:,:,:,11]+f[:,:,:,12]+f[:,:,:,15]+f[:,:,:,16]
         -f[:,:,:,6]-f[:,:,:,13]-f[:,:,:,14]-f[:,:,:,17]-f[:,:,:,18])/de
    ux[mask]=0; uy[mask]=0; uz[mask]=0
    
    u2 = ux*ux+uy*uy+uz*uz
    for k in range(19):
        cu = 3.0*(int(cx_h[k])*ux+int(cy_h[k])*uy+int(cz_h[k])*uz)
        feq = w[k]*rho*(1.0+cu+0.5*cu*cu-1.5*u2)
        f[:,:,:,k] -= omega*(f[:,:,:,k]-feq)
    
    for k in range(19):
        if cx_h[k]: f[:,:,:,k] = cp.roll(f[:,:,:,k], -int(cx_h[k]), axis=0)
        if cy_h[k]: f[:,:,:,k] = cp.roll(f[:,:,:,k], -int(cy_h[k]), axis=1)
        if cz_h[k]: f[:,:,:,k] = cp.roll(f[:,:,:,k], -int(cz_h[k]), axis=2)
    
    fb = f.copy()
    for k in range(19): f[mask,k] = fb[mask,opp[k]]
    
    g_force = 1e-5
    for k in range(19):
        if cz_h[k]: f[:,:,:,k] += 3.0*float(w[k])*int(-cz_h[k])*g_force  # -Z: top→down
    
    if t_step % SNAP_EVERY == 0 or t_step == STEPS-1:
        duz_dy=(cp.roll(uz,-1,1)-cp.roll(uz,1,1))/2; duy_dz=(cp.roll(uy,-1,2)-cp.roll(uy,1,2))/2
        dux_dz=(cp.roll(ux,-1,2)-cp.roll(ux,1,2))/2; duz_dx=(cp.roll(uz,-1,0)-cp.roll(uz,1,0))/2
        duy_dx=(cp.roll(uy,-1,0)-cp.roll(uy,1,0))/2; dux_dy=(cp.roll(ux,-1,1)-cp.roll(ux,1,1))/2
        wxv=duz_dy-duy_dz; wyv=dux_dz-duz_dx; wzv=duy_dx-dux_dy
        w_mag = cp.sqrt(wxv*wxv+wyv*wyv+wzv*wzv); w_mag[mask]=0
        # Downsample 2x for storage
        w_ds = cp.asnumpy(w_mag[::2,::2,::2]).astype(np.float32)
        snap3d.append((t_step, w_ds))
        print(f"  step {t_step:5d}: |w|max={float(w_mag.max()):.4f}")

total_t = time.time()-t0
print(f"LBM done: {total_t:.0f}s, {len(snap3d)} 3D snapshots")

mask_ds = mask_np[::2,::2,::2]
with open('/root/lbm_3d_snaps.pkl','wb') as pf:
    pickle.dump({'snaps':snap3d,'mask':mask_ds,'NX':NX//2,'NY':NY//2,'NZ':NZ//2,'Re':Re_est}, pf)
print("Saved: lbm_3d_snaps.pkl")

# ═══ Render isometric 3D GIF ═══
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

nx2, ny2, nz2 = NX//2, NY//2, NZ//2
# Wall surface points (downsampled)
wz_i, wy_i, wx_i = np.where(mask_ds.transpose(2,1,0))  # z,y,x order

all_w = np.concatenate([s[1].ravel() for s in snap3d[5:]])
wmax_ref = np.percentile(all_w[all_w>1e-6], 99.5) if (all_w>1e-6).sum() else 0.01

fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')

def anim(i):
    ax.clear()
    ax.set_facecolor('#050510'); fig.patch.set_facecolor('#050510')
    ax.view_init(elev=28, azim=48)  # isometric view
    step, wd = snap3d[i]
    
    # Cone wall: white translucent scatter
    if len(wx_i) > 0:
        idx = np.random.choice(len(wx_i), min(8000, len(wx_i)), replace=False)
        ax.scatter(wx_i[idx], wz_i[idx], wy_i[idx], c='white', s=0.3, alpha=0.12)
    
    # Vorticity: blue→red colormap
    zz, yy, xx = np.where(wd.transpose(2,1,0) > wmax_ref*0.05)
    if len(zz) > 0:
        if len(zz) > 60000:
            idx = np.random.choice(len(zz), 60000, replace=False)
            zz, yy, xx = zz[idx], yy[idx], xx[idx]
        vals = wd.transpose(2,1,0)[zz, yy, xx]
        nv = np.clip(vals/wmax_ref, 0, 1)
        colors = np.zeros((len(vals), 4))
        for j in range(len(vals)):
            v = nv[j]
            if v < 0.25: colors[j] = [0, 0.2+v*2, 0.9, 0.35+v]
            elif v < 0.5: colors[j] = [0, 0.85, 0.9-1.5*(v-0.25), 0.6]
            elif v < 0.75: colors[j] = [3.2*(v-0.5), 0.85, 0, 0.75]
            else: colors[j] = [1, 0.85-3*(v-0.75), 0, 0.9]
        colors = np.clip(colors, 0, 1)
        ax.scatter(xx, zz, yy, c=colors, s=0.8, alpha=0.6, rasterized=True)
    
    ax.set_xlim(0, nx2); ax.set_ylim(0, nz2); ax.set_zlim(0, ny2)
    ax.set_title(f'LBM D3Q19 PKS Cone | Isometric | Re~{Re_est:.0f} | step={step}\n'
                 f'blue=low vorticity, red=high | flow: bottom->top',
                 color='white', fontsize=12)
    for a in [ax.xaxis, ax.yaxis, ax.zaxis]:
        a.label.set_color('gray')
    ax.tick_params(colors='gray', labelsize=6)
    ax.grid(True, alpha=0.05)

ani = animation.FuncAnimation(fig, anim, frames=len(snap3d), interval=200)
ani.save('/root/lbm_3d_iso.gif', writer='pillow', fps=5, dpi=75)
plt.close(fig)
print("Saved: lbm_3d_iso.gif")
