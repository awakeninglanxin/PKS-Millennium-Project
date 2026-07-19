"""
三合一 M集渲染 — 完整全图版
全范围、不缩放、高迭代
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time, os

OUT = "D:/AAA我的文件/PKS_千禧难题_GitHub版/02_应用科技/AI审美分析"
os.makedirs(OUT, exist_ok=True)

W, H = 1600, 1000  # 大尺寸
MAX_ITER = 2000

# ═══════════════════════════════════════
#  1. Peitgen DEM/M — 完整 M 集
# ═══════════════════════════════════════
def dem_full(w, h, max_iter):
    x_min, x_max = -2.5, 1.0
    y_min, y_max = -1.25, 1.25
    dem = np.zeros((h,w), dtype=np.float64)
    iters = np.zeros((h,w), dtype=np.int32)
    dx = 3.5/w; dy = 2.5/h
    for py in range(h):
        ci = y_max - py*dy
        for px in range(w):
            cr = x_min + px*dx
            zr, zi = 0.0, 0.0
            dzr, dzi = 0.0, 0.0
            for n in range(max_iter):
                zr2=zr*zr; zi2=zi*zi
                if zr2+zi2 > 4.0:
                    mod_z = np.sqrt(zr2+zi2)
                    mod_dz = np.sqrt(dzr*dzr+dzi*dzi)
                    if mod_dz>0:
                        dem[py,px] = np.log(mod_z*mod_z)*mod_z/mod_dz
                    iters[py,px] = n
                    break
                dzi_new = 2.0*(zr*dzi+zi*dzr)
                dzr_new = 2.0*(zr*dzr-zi*dzi)+1.0
                zi = 2.0*zr*zi+ci
                zr = zr2-zi2+cr
                dzr, dzi = dzr_new, dzi_new
            else:
                dem[py,px]=0.0; iters[py,px]=max_iter
    return dem, iters

def dem_color(dem, iters, max_iter):
    h,w=dem.shape; rgb=np.zeros((h,w,3))
    for py in range(h):
        for px in range(w):
            d=dem[py,px]; it=iters[py,px]
            if it>=max_iter:
                rgb[py,px]=[0,0,0.02]
            else:
                ci=max(0.0,1.0-25.0*np.log(1.0+d))
                hh=0.06+0.18*ci; ss=0.85; vv=0.10+0.90*ci
                c=vv*ss; x=c*(1-abs((hh*6)%2-1)); m=vv-c
                if hh<1/6: r,g,b=c,x,0
                elif hh<2/6: r,g,b=x,c,0
                elif hh<3/6: r,g,b=0,c,x
                elif hh<4/6: r,g,b=0,x,c
                elif hh<5/6: r,g,b=x,0,c
                else: r,g,b=c,0,x
                rgb[py,px]=[r+m,g+m,b+m]
    return np.clip(rgb,0,1)

print("[1/3] DEM/M 完整M集...")
t0=time.time()
dem,it=dem_full(W,H,MAX_ITER)
rgb=dem_color(dem,it,MAX_ITER)
fig,ax=plt.subplots(figsize=(16,10))
ax.imshow(rgb,extent=[-2.5,1.0,-1.25,1.25])
ax.set_title("Peitgen DEM/M — Full Mandelbrot Set",fontsize=16)
ax.axis('off'); plt.tight_layout(pad=0)
plt.savefig(f'{OUT}/01_DEM_Full_Mandelbrot.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print(f"   Done {time.time()-t0:.0f}s")


# ═══════════════════════════════════════
#  2. Angel Wings — 完整 M 集着色
# ═══════════════════════════════════════
def angel_wings_full(w,h,max_iter):
    x_min,x_max=-2.5,1.0; y_min,y_max=-1.25,1.25
    wings=np.zeros((h,w),dtype=np.int32)
    iters=np.zeros((h,w),dtype=np.int32)
    dx=3.5/w; dy=2.5/h
    for py in range(h):
        ci=y_max-py*dy
        for px in range(w):
            cr=x_min+px*dx
            zr,zi=0.0,0.0
            prev_mag=0.0; streak=0; max_streak=0
            for n in range(max_iter):
                zr2=zr*zr; zi2=zi*zi
                if zr2+zi2>4.0:
                    iters[py,px]=n; break
                zi=2.0*zr*zi+ci; zr=zr2-zi2+cr
                cur_mag=zr2+zi2
                if n>0 and cur_mag<prev_mag:
                    streak+=1
                    if streak>max_streak: max_streak=streak
                else: streak=0
                prev_mag=cur_mag
            else:
                iters[py,px]=max_iter
            wings[py,px]=max_streak
    return wings, iters

def wings_color(wings,iters,max_iter):
    h,w=wings.shape; rgb=np.zeros((h,w,3))
    for py in range(h):
        for px in range(w):
            s=wings[py,px]; it=iters[py,px]
            if it>=max_iter:
                rgb[py,px]=[0.02,0,0.05]
            elif s>=3:
                t=min(1.0,s/15.0)
                rgb[py,px]=[0.95,0.55+0.3*t,0.08+0.3*t]
            elif s>=1:
                rgb[py,px]=[0.6,0.25,0.5]
            else:
                t=min(1.0,it/max_iter)
                rgb[py,px]=[0.08,0.15+0.6*t,0.3+0.65*t]
    return np.clip(rgb,0,1)

print("[2/3] Angel Wings 完整M集...")
t0=time.time()
wings,it=angel_wings_full(W,H,MAX_ITER)
rgb=wings_color(wings,it,MAX_ITER)
fig,ax=plt.subplots(figsize=(16,10))
ax.imshow(rgb,extent=[-2.5,1.0,-1.25,1.25])
ax.set_title("Angel Wings (Klaus Messner) — Full Mandelbrot Set",fontsize=16)
ax.axis('off'); plt.tight_layout(pad=0)
plt.savefig(f'{OUT}/02_Angel_Wings_Full.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print(f"   Done {time.time()-t0:.0f}s")


# ═══════════════════════════════════════
#  3. 逆M集 DEM — 完整逆M集 (z²+1/c)
# ═══════════════════════════════════════
def inverse_dem_full(w,h,max_iter):
    # 逆M集(z²+1/c)中，1/c把外区反演到内部
    # 完整可见区: c∈[-4,4]×[-3,3] 足以看到水滴全貌
    x_min,x_max=-3.0,3.0; y_min,y_max=-2.0,2.0
    dem=np.zeros((h,w),dtype=np.float64)
    iters=np.zeros((h,w),dtype=np.int32)
    dx=(x_max-x_min)/w; dy=(y_max-y_min)/h
    for py in range(h):
        ci=y_max-py*dy
        for px in range(w):
            cr=x_min+px*dx
            if abs(cr)<1e-10 and abs(ci)<1e-10: cr=1e-10
            c_inv_r=cr/(cr*cr+ci*ci)
            c_inv_i=-ci/(cr*cr+ci*ci)
            zr,zi=c_inv_r,c_inv_i
            dzr,dzi=1.0,0.0
            for n in range(max_iter):
                zr2=zr*zr; zi2=zi*zi
                if zr2+zi2>1e8:
                    mod_z=np.sqrt(zr2+zi2)
                    mod_dz=np.sqrt(dzr*dzr+dzi*dzi)
                    if mod_dz>0:
                        dem[py,px]=np.log(mod_z)*mod_z/mod_dz
                    iters[py,px]=n; break
                # 逆M迭代 z→z²+1/c, f'(z)=2z, 导数更新(no +1)
                dzi_new=2.0*(zr*dzi+zi*dzr)
                dzr_new=2.0*(zr*dzr-zi*dzi)
                zi=2.0*zr*zi+c_inv_i
                zr=zr2-zi2+c_inv_r
                dzr, dzi = dzr_new, dzi_new
            else:
                dem[py,px]=0; iters[py,px]=max_iter
    return dem, iters

print("[3/3] 逆M集 DEM 完整版...")
t0=time.time()
dem,it=inverse_dem_full(W,H,MAX_ITER)
rgb=dem_color(dem,it,MAX_ITER)  # reuse dem_color for now
fig,ax=plt.subplots(figsize=(16,10))
ax.imshow(rgb,extent=[-3,3,-2,2])
ax.set_title("Inverse Mandelbrot DEM — z²+1/c Full View",fontsize=16)
ax.axis('off'); plt.tight_layout(pad=0)
plt.savefig(f'{OUT}/03_InverseM_DEM_Full.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print(f"   Done {time.time()-t0:.0f}s")

print(f"\n全部完成! {OUT}/")
