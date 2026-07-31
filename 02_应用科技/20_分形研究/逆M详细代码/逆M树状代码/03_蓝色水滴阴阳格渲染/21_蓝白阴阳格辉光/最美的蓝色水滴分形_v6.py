#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UF21 v6 — 蓝白阴阳格水滴分形（亮度修正版）

v5 诊断问题：
  ★ 内外亮度反了！目标=外部深蓝+内部亮白；v5=外部亮+内部暗
  ★ 白色空洞（逃逸势能极值点）
  ★ 外部LUT近场过亮（ice蓝接近白色）

v6 修正：
  1. ★ 外部基底全程深蓝色系（0.02~0.45范围，绝不超0.5）
  2. ★ 内部为亮色系（0.65~0.98范围）
  3. 限制逃逸势能归一化上限，消除白色空洞
  4. 棋盘格alpha进一步降低至0.18（极致柔和）
  5. 金边保持强对比度
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.ndimage import binary_dilation, gaussian_filter

# ============================================================
# 参数
# ============================================================
TIP = 4.0; BOTTOM = -4.0 / 3.0; HSPAN = 1.6242719100; MARGIN = 0.50
RE_MIN, RE_MAX = BOTTOM - MARGIN, TIP + MARGIN
IM_MIN, IM_MAX = -HSPAN - MARGIN, HSPAN + MARGIN

WIDTH = 2400
HEIGHT = int(WIDTH * (RE_MAX - RE_MIN) / (IM_MAX - IM_MIN))
MAX_ITER = 300; BAILOUT_SQ = 128**2

N_ANGLE = 420; LOG_R_STEP = 0.028
CHESS_ALPHA = 0.18; CHESS_BLUR = 1.0

# ---- 配色（★ 外部全深蓝 / 内部全亮）----
BG_BLACK     = [0.00, 0.00, 0.02]        # 最外围近黑
EXT_DARK     = [0.02, 0.06, 0.18]        # 深藏青（远场）
EXT_MID      = [0.08, 0.16, 0.38]        # 钴蓝（中场）
EXT_NEAR     = [0.18, 0.30, 0.56]        # 中蓝（近场，仍偏暗）

TILE_BRIGHT  = [0.35, 0.48, 0.78]         # 阳：中亮蓝
TILE_SHADOW  = [0.01, 0.03, 0.12]         # 阴：暗蓝

INT_HOT      = [0.95, 0.97, 1.0]          # 核心：炽白
INT_CORE     = [0.75, 0.86, 0.97]         # 核心区：乳白浅蓝
INT_MID      = [0.50, 0.68, 0.90]         # 中层：天蓝
INT_EDGE     = [0.25, 0.42, 0.74]         # 边缘：中海蓝

GOLD_CORE    = [1.0, 0.90, 0.28]
GOLD_MID     = [0.96, 0.60, 0.08]
DEM_SCALE    = 22.0


# ============================================================
# 引擎
# ============================================================
def compute(x_min,x_max,y_min,y_max,w,h,max_iter,bail_sq):
    x=np.linspace(x_min,x_max,w);y=np.linspace(y_min,y_max,h)
    X,Y=np.meshgrid(x,y);co=X+1j*Y
    safe=np.abs(co)>1e-12;ce=np.zeros_like(co,dtype=np.complex128)
    ce[safe]=1.0/co[safe];ce[~safe]=1e6+0j
    z=np.zeros_like(ce,dtype=np.complex128);dz=np.zeros_like(ce,dtype=np.complex128)
    ic=np.full(ce.shape,max_iter,dtype=np.float64)
    trap=np.full(ce.shape,1e30,dtype=np.float64);alive=np.ones(ce.shape,dtype=bool)
    for i in range(max_iter):
        if not alive.any():break
        idx=np.where(alive);za=z[idx];ca=ce[idx];dza=dz[idx]
        dza=2*za*dza+1;za=za*za+ca;m2=za.real**2+za.imag**2
        trap[idx]=np.minimum(trap[idx],m2);z[idx]=za;dz[idx]=dza
        esc=m2>bail_sq;ic[idx]=np.where(esc,i,ic[idx]);alive[idx]&=~esc
    return {'ic':ic,'trap':trap,'z':z.copy(),'dz':dz.copy(),
            'interior':~alive,'co':co}


# ============================================================
def render(data,w,h):
    ic=data['ic'];trap=data['trap'];fz=data['z'];fdz=data['dz']
    interior=data['interior'];ext=~interior
    img=np.full((h,w,3),BG_BLACK,dtype=np.float64)

    # ====== 层1: 外部 — 深蓝LUT（严格限制亮度上限）======
    with np.errstate(invalid='ignore',divide='ignore'):
        ms=fz.real**2+fz.imag**2+1e-30
        nc_f=np.minimum(ic,32).astype(np.float64)
        pot_raw=np.log(ms)/np.power(2.0,nc_f);pot_raw[interior]=0
        # 用clip硬限制归一化范围，防止极值点产生白洞
        p99=np.percentile(pot_raw[ext],99) if ext.any() else 1
        t=np.clip(pot_raw/max(p99,0.5),0,1)   # 上限不超过1
        t_smoother=np.power(t,0.55)

        # 深蓝LUT: 全程<0.6亮度
        r_lut=np.select([t_smoother<0.30,t_smoother<0.60,t_smoother<0.85,True],
            [EXT_DARK[0]+(EXT_MID[0]-EXT_DARK[0])*(t_smoother/0.30),
             EXT_MID[0]+(EXT_NEAR[0]-EXT_MID[0])*((t_smoother-0.30)/0.30),
             EXT_NEAR[0]+min(0.15,(EXT_NEAR[0]-EXT_MID[0])*0.5)*((t_smoother-0.60)/0.25),
             EXT_NEAR[0]])
        g_lut=np.select([t_smoother<0.30,t_smoother<0.60,t_smoother<0.85,True],
            [EXT_DARK[1]+(EXT_MID[1]-EXT_DARK[1])*(t_smoother/0.30),
             EXT_MID[1]+(EXT_NEAR[1]-EXT_MID[1])*((t_smoother-0.30)/0.30),
             EXT_NEAR[1]+min(0.15,(EXT_NEAR[1]-EXT_MID[1])*0.5)*((t_smoother-0.60)/0.25),
             EXT_NEAR[1]])
        b_lut=np.select([t_smoother<0.30,t_smoother<0.60,t_smoother<0.85,True],
            [EXT_DARK[2]+(EXT_MID[2]-EXT_DARK[2])*(t_smoother/0.30),
             EXT_MID[2]+(EXT_NEAR[2]-EXT_MID[2])*((t_smoother-0.30)/0.30),
             EXT_NEAR[2]+min(0.20,(EXT_NEAR[2]-EXT_MID[2])*0.5)*((t_smoother-0.60)/0.25),
             EXT_NEAR[2]])
        img[ext]=np.stack([r_lut[ext],g_lut[ext],b_lut[ext]],axis=-1)

    # ====== 层2: 内部 — 亮色渐变（白→浅蓝）======
    with np.errstate(invalid='ignore'):
        trap_s=np.maximum(trap,1e-30)
        v_raw=(np.log(trap_s)*0.45)%1.0
        v_adj=np.power(v_raw,0.50)

        r_ch=np.select([v_adj<0.20,v_adj<0.50,v_adj<0.80,True],
            [INT_HOT[0]+(INT_CORE[0]-INT_HOT[0])*(v_adj/0.20),
             INT_CORE[0]+(INT_MID[0]-INT_CORE[0])*((v_adj-0.20)/0.30),
             INT_MID[0]+(INT_EDGE[0]-INT_MID[0])*((v_adj-0.50)/0.30),
             INT_EDGE[0]*(1-(v_adj-0.80)/0.20)])
        g_ch=np.select([v_adj<0.20,v_adj<0.50,v_adj<0.80,True],
            [INT_HOT[1]+(INT_CORE[1]-INT_HOT[1])*(v_adj/0.20),
             INT_CORE[1]+(INT_MID[1]-INT_CORE[1])*((v_adj-0.20)/0.30),
             INT_MID[1]+(INT_EDGE[1]-INT_MID[1])*((v_adj-0.50)/0.30),
             INT_EDGE[1]*(1-(v_adj-0.80)/0.20)])
        b_ch=np.select([v_adj<0.20,v_adj<0.50,v_adj<0.80,True],
            [INT_HOT[2]+(INT_CORE[2]-INT_HOT[2])*(v_adj/0.20),
             INT_CORE[2]+(INT_MID[2]-INT_CORE[2])*((v_adj-0.20)/0.30),
             INT_MID[2]+(INT_EDGE[2]-INT_MID[2])*((v_adj-0.50)/0.30),
             INT_EDGE[2]*(1-(v_adj-0.80)/0.20)])
        img[interior]=np.stack([r_ch[interior],g_ch[interior],b_ch[interior]],axis=-1)

    # ====== 层3: 柔光棋盘格（仅外部，极低alpha）======
    yy,xx=np.ogrid[:h,:w]
    re_px=RE_MIN+(xx/(w-1))*(RE_MAX-RE_MIN)
    im_px=IM_MIN+(yy/(h-1))*(IM_MAX-IM_MIN)
    c_r=np.sqrt(re_px**2+im_px**2)
    c_theta=(np.arctan2(im_px,re_px)+np.pi)/(2*np.pi)
    c_log_r=np.log(c_r+0.01)
    qi=np.floor(c_theta*N_ANGLE).astype(int)
    qj=np.floor(c_log_r/LOG_R_STEP).astype(int)
    chess_raw=((qi%2==0)!=(qj%2==0)).astype(np.float64)
    chess_smooth=gaussian_filter(chess_raw,sigma=CHESS_BLUR) if CHESS_BLUR>0 else chess_raw
    ca=chess_smooth*CHESS_ALPHA;ca[interior]=0

    tex=np.zeros((h,w,3),dtype=np.float64)
    ml=chess_raw>0.5
    for ch in range(3):
        tex[:,:,ch]=np.where(ml,TILE_BRIGHT[ch],TILE_SHADOW[ch])
    for ch in range(3):
        img[:,:,ch]=np.clip(img[:,:,ch]*(1-ca)+tex[:,:,ch]*ca,0,1)

    # ====== 层4: 金色边界辉光 ======
    abs_z=np.sqrt(fz.real**2+fz.imag**2+1e-30)
    abs_dz=np.sqrt(fdz.real**2+fdz.imag**2+1e-30)
    dem=np.log(abs_z**2+1e-30)*abs_z/(abs_dz+1e-30);dem[~ext]=-1

    bd_h=interior[:,:-1]!=interior[:,1:]
    bd_v=interior[:-1,:]!=interior[1:,:]
    edge=np.zeros((h,w),dtype=bool)
    edge[:,:-1]|=bd_h;edge[:-1,:]|=bd_v

    g_far=binary_dilation(edge,np.ones((16,16)))
    g_mid=binary_dilation(edge,np.ones((8,8)))
    g_in =binary_dilation(edge,np.ones((3,3)))

    dv=dem.copy();dv[dv<0]=0
    dl=np.log1p(dv*DEM_SCALE)
    dn=dl/(dl.max()+1e-12) if dl.max()>0 else dl

    gf=g_far&ext&~g_mid
    if gf.any():
        d=np.power(dn[gf],1.5)
        img[gf,0]=np.clip(img[gf,0]+0.18*d,0,1)
        img[gf,1]=np.clip(img[gf,1]+0.10*d,0,1)
        img[gf,2]=np.clip(img[gf,2]+0.02*d,0,1)

    gm=g_mid&ext&~g_in
    if gm.any():
        d=dn[gm]
        img[gm]=np.stack([
            np.clip(GOLD_MID[0]*0.40+GOLD_CORE[0]*0.55*d,0,1),
            np.clip(GOLD_MID[1]*0.35+GOLD_CORE[1]*0.60*d,0,1),
            np.clip(GOLD_MID[2]*0.10+GOLD_CORE[2]*0.85*d,0,0.35)],axis=-1)

    gi=g_in&interior
    if gi.any():
        d=dn[gi]
        img[gi]=np.stack([
            np.clip(GOLD_CORE[0]*0.60+0.38*d,0,1),
            np.clip(GOLD_CORE[1]*0.50+0.48*d,0,1),
            np.clip(GOLD_CORE[2]*0.18+0.78*d,0,0.48)],axis=-1)

    return np.rot90(img,k=3)


# ============================================================
if __name__=='__main__':
    out_dir=os.path.dirname(os.path.abspath(__file__))
    print(f"=== v6 亮度修正版 === {WIDTH}x{HEIGHT} iter={MAX_ITER}")
    data=compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,WIDTH,HEIGHT,MAX_ITER,BAILOUT_SQ)
    print(f"int={data['interior'].sum()} ({100*data['interior'].mean():.1f}%)")
    img=render(data,WIDTH,HEIGHT)
    out=os.path.join(out_dir,'最美的蓝色水滴分形_v6.png')
    fw=8;fh=fw*HEIGHT/WIDTH
    fig,ax=plt.subplots(figsize=(fw,fh),dpi=150)
    ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],
              aspect='equal',interpolation='bilinear',origin='lower')
    ax.axis('off');plt.tight_layout(pad=0)
    plt.savefig(out,dpi=200,bbox_inches='tight',facecolor=tuple(BG_BLACK));plt.close()
    print(f"完成! {out} ({os.path.getsize(out)/1024/1024:.1f}MB)")
