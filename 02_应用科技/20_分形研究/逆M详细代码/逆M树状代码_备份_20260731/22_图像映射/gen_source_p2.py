#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速生成 p=2 六向帕斯卡源图"""
import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, os, time
from matplotlib.colors import hsv_to_rgb as h2r

od = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\22_图像映射'
P, N_ROWS, SRC, DPI = 2, 1680, 1200, 150
SR3 = np.sqrt(3)
off = SRC//2; src_s = N_ROWS/(off*0.85)
ANGLES = np.array([m*np.pi/3-np.pi/6 for m in range(6)])
RC, RS = np.cos(-ANGLES), np.sin(-ANGLES)

t0 = time.time()
# Pascal
p = np.zeros((N_ROWS,N_ROWS), dtype=np.int8); p[0,0]=1%P
for n in range(1,N_ROWS):
    p[n,0]=p[n,n]=1%P
    for k in range(1,n): p[n,k]=(p[n-1,k]+p[n-1,k-1])%P
print(f'Pascal mod {P}: fill={(p>0).mean()*100:.1f}% ({time.time()-t0:.1f}s)')

# Grid
SX,SY = np.meshgrid(np.arange(SRC), np.arange(SRC))
szr = ((SX-off)/src_s).ravel(); szi = ((SY-off)/src_s).ravel()
N = len(szr)

# 6-way query
bf = np.zeros(N); bn = np.full(N,-1,dtype=np.int64); bp = np.full(N,N_ROWS,dtype=np.float64)
for m in range(6):
    zr=szr*RC[m]-szi*RS[m]; zi=szr*RS[m]+szi*RC[m]
    nr=np.round(zr+zi/SR3).astype(np.int64); kr=np.round(2*zi/SR3).astype(np.int64)
    v=(kr>=0)&(kr<=nr)&(nr>=0)&(nr<N_ROWS)
    if v.any():
        vi=np.where(v)[0]
        nz=(p[nr[vi],kr[vi]]>0)
        if nz.any():
            ui=vi[nz]; pr=nr[ui].astype(np.float64)
            bt=pr<bp[ui]
            if bt.any():
                bi=ui[bt]; bf[bi]=1; bn[bi]=nr[bi]; bp[bi]=pr[bt]

bf_img=bf.reshape(SRC,SRC); bn_img=bn.reshape(SRC,SRC)
fill_pct=bf.mean()*100
print(f'fill={fill_pct:.1f}% ({time.time()-t0:.1f}s)')

# n-rainbow
rgb = np.ones((SRC,SRC,3))
mask = bf_img>0
if mask.any():
    nv = bn_img[mask].astype(np.float64)
    hue = 0.12 - (nv/N_ROWS)*0.65; hue[hue<0] += 1.0
    sat = 0.7 + 0.3*(nv/N_ROWS)
    val = 0.5 + 0.5*(1-nv/N_ROWS)
    hsv_arr = np.stack([hue,sat,val],axis=-1)
    rgb[mask] = h2r(hsv_arr)

out = os.path.join(od, 'UF22_六向帕斯卡源图_p2_v10.png')
fig,ax = plt.subplots(figsize=(SRC/DPI,SRC/DPI), dpi=DPI)
ax.imshow(rgb, interpolation='bilinear')
ax.set_aspect('equal')
ax.set_title(f'6-Way Pascal p={P} N_ROWS={N_ROWS} fill={fill_pct:.1f}%', fontsize=13)
ax.axis('off'); fig.tight_layout()
fig.savefig(out, dpi=DPI, facecolor='white'); plt.close()
print(f'Done: {out} ({os.path.getsize(out)//1024}KB)')
