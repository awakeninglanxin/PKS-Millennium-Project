#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UF21 v5 — 蓝白阴阳格水滴分形（宝石蓝辉光版）

v4→v5 核心改进：
  1. ★ 外部使用基于逃逸速度的蓝色LUT渐变（非纯色基底）→ 宝石般层次感
  2. ★ 棋盘格加高斯模糊抗锯齿 → 瓷砖边缘柔和自然
  3. ★ 金边增加 Bloom 辉光溢出（模拟镜头光晕）
  4. 内部亮点缩小为小核心（幂指数0.35→更集中）
  5. 整体色温偏冷：深靛蓝底+钴蓝中调+冰蓝高光
  6. 棋盘alpha降至0.25（极度柔和）
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

MAX_ITER = 300
BAILOUT_SQ = 128 ** 2

# ---- 极坐标棋盘 ----
N_ANGLE = 420
LOG_R_STEP = 0.028
CHESS_ALPHA = 0.25          # 更低的混合透明度
CHESS_BLUR_SIGMA = 1.2      # 棋盘边缘高斯模糊sigma(像素)

# ---- 冷蓝配色方案 ----
BG_MIDNIGHT   = [0.005, 0.018, 0.08]      # 午夜藏青（最远场）
BLUE_DEEP     = [0.02, 0.08, 0.24]         # 深靛蓝（远场）
BLUE_COBALT   = [0.10, 0.22, 0.52]         # 钴蓝（中场）
BLUE_SKY      = [0.28, 0.46, 0.78]         # 天蓝（近场）
BLUE_ICE      = [0.60, 0.78, 0.96]         # 冰蓝（高光）

TILE_BRIGHT   = [0.55, 0.68, 0.92]         # 阳（混合后极淡）
TILE_SHADOW   = [0.00, 0.03, 0.14]         # 阴（混合后极淡）

INT_HOT       = [0.88, 0.94, 1.0]          # 内核炽白点（很小区域）
INT_CORE      = [0.55, 0.72, 0.93]         # 核心区亮蓝
INT_MID       = [0.30, 0.50, 0.80]         # 中层天蓝
INT_EDGE      = [0.12, 0.26, 0.58]         # 边缘海蓝

GOLD_CORE     = [1.0, 0.92, 0.30]          # 金核峰值
GOLD_MID      = [0.98, 0.65, 0.08]         # 金橙过渡
GOLD_OUTER    = [0.70, 0.35, 0.02]         # 暗红褐外沿（bloom用）
DEM_SCALE     = 24.0
BLOOM_STRENGTH = 0.30                      # 辉光溢出强度


# ============================================================
# 引擎
# ============================================================
def compute(x_min, x_max, y_min, y_max, w, h, max_iter, bail_sq):
    x = np.linspace(x_min, x_max, w)
    y = np.linspace(y_min, y_max, h)
    X, Y = np.meshgrid(x, y)
    co = X + 1j * Y
    safe = np.abs(co) > 1e-12
    ce = np.zeros_like(co, dtype=np.complex128)
    ce[safe] = 1.0 / co[safe]; ce[~safe] = 1e6+0j
    z = np.zeros_like(ce, dtype=np.complex128)
    dz = np.zeros_like(ce, dtype=np.complex128)
    ic = np.full(ce.shape, max_iter, dtype=np.float64)
    trap = np.full(ce.shape, 1e30, dtype=np.float64)
    alive = np.ones(ce.shape, dtype=bool)

    for i in range(max_iter):
        if not alive.any(): break
        idx = np.where(alive)
        za=z[idx]; ca=ce[idx]; dza=dz[idx]
        dza=2*za*dza+1; za=za*za+ca; m2=za.real**2+za.imag**2
        trap[idx]=np.minimum(trap[idx],m2); z[idx]=za; dz[idx]=dza
        esc=m2>bail_sq; ic[idx]=np.where(esc,i,ic[idx]); alive[idx]&=~esc

    return {'ic':ic,'trap':trap,'z':z.copy(),'dz':dz.copy(),
            'interior':~alive,'co':co}


# ============================================================
# 渲染器 v5 — 宝石蓝LUT + Bloom
# ============================================================
def render(data, w, h):
    ic=data['ic']; trap=data['trap']
    fz=data['z']; fdz=data['dz']
    interior=data['interior']; ext=~interior
    img=np.full((h,w,3), BG_MIDNIGHT, dtype=np.float64)

    # ====== 层1: 外部 — 连续势能蓝色LUT ======
    with np.errstate(invalid='ignore',divide='ignore'):
        ms=fz.real**2+fz.imag**2+1e-30
        nc_f=np.minimum(ic,32).astype(np.float64)
        pot_raw=np.log(ms)/np.power(2.0,nc_f)
        pot_raw[interior]=0
        # 归一化：远场=0, 近场=1
        p95=np.percentile(pot_raw[ext],97) if ext.any() else 1
        t=np.clip(pot_raw/p95, 0, 1)
        t_smoother=np.power(t, 0.45)  # 让近场更亮

        # 4段蓝色LUT: midnight→deep→cobalt→sky→ice
        def lut(v):
            r=np.select(
                [v<0.20, v<0.45, v<0.75, True],
                [BLUE_DEEP[0]+(BLUE_COBALT[0]-BLUE_DEEP[0])*(v/0.20),
                 BLUE_COBALT[0]+(BLUE_SKY[0]-BLUE_COBALT[0])*((v-0.20)/0.25),
                 BLUE_SKY[0]+(BLUE_ICE[0]-BLUE_SKY[0])*((v-0.45)/0.30),
                 BLUE_ICE[0]+(1-BLUE_ICE[0])*((v-0.75)/0.25)])
            g=np.select(
                [v<0.20, v<0.45, v<0.75, True],
                [BLUE_DEEP[1]+(BLUE_COBALT[1]-BLUE_DEEP[1])*(v/0.20),
                 BLUE_COBALT[1]+(BLUE_SKY[1]-BLUE_COBALT[1])*((v-0.20)/0.25),
                 BLUE_SKY[1]+(BLUE_ICE[1]-BLUE_SKY[1])*((v-0.45)/0.30),
                 BLUE_ICE[1]+(1-BLUE_ICE[1])*((v-0.75)/0.25)])
            b=np.select(
                [v<0.20, v<0.45, v<0.75, True],
                [BLUE_DEEP[2]+(BLUE_COBALT[2]-BLUE_DEEP[2])*(v/0.20),
                 BLUE_COBALT[2]+(BLUE_SKY[2]-BLUE_COBALT[2])*((v-0.20)/0.25),
                 BLUE_SKY[2]+(BLUE_ICE[2]-BLUE_SKY[2])*((v-0.45)/0.30),
                 BLUE_ICE[2]+(1-BLUE_ICE[2])*((v-0.75)/0.25)])
            return np.stack([r,g,b],axis=-1)

        ext_rgb=lut(t_smoother)
        img[ext]=ext_rgb[ext]

    # ====== 层2: 内部 — 浓缩亮点渐变 ======
    with np.errstate(invalid='ignore'):
        trap_s=np.maximum(trap,1e-30)
        v_raw=(np.log(trap_s)*0.42)%1.0
        # 强压缩：仅中心10%区域是亮的
        v_adj=np.power(v_raw, 0.35)

        r_ch=np.select([v_adj<0.15, v_adj<0.40, v_adj<0.70, True],
            [INT_HOT[0]+(INT_CORE[0]-INT_HOT[0])*(v_adj/0.15),
             INT_CORE[0]+(INT_MID[0]-INT_CORE[0])*((v_adj-0.15)/0.25),
             INT_MID[0]+(INT_EDGE[0]-INT_MID[0])*((v_adj-0.40)/0.30),
             INT_EDGE[0]*(1-(v_adj-0.70)/0.30)])
        g_ch=np.select([v_adj<0.15, v_adj<0.40, v_adj<0.70, True],
            [INT_HOT[1]+(INT_CORE[1]-INT_HOT[1])*(v_adj/0.15),
             INT_CORE[1]+(INT_MID[1]-INT_CORE[1])*((v_adj-0.15)/0.25),
             INT_MID[1]+(INT_EDGE[1]-INT_MID[1])*((v_adj-0.40)/0.30),
             INT_EDGE[1]*(1-(v_adj-0.70)/0.30)])
        b_ch=np.select([v_adj<0.15, v_adj<0.40, v_adj<0.70, True],
            [INT_HOT[2]+(INT_CORE[2]-INT_HOT[2])*(v_adj/0.15),
             INT_CORE[2]+(INT_MID[2]-INT_CORE[2])*((v_adj-0.15)/0.25),
             INT_MID[2]+(INT_EDGE[2]-INT_MID[2])*((v_adj-0.40)/0.30),
             INT_EDGE[2]*(1-(v_adj-0.70)/0.30)])
        img[interior]=np.stack([r_ch[interior],g_ch[interior],b_ch[interior]],axis=-1)

    # ====== 层3: 高斯模糊棋盘格纹理（极低alpha）======
    yy,xx=np.ogrid[:h,:w]
    re_px=RE_MIN+(xx/(w-1))*(RE_MAX-RE_MIN)
    im_px=IM_MIN+(yy/(h-1))*(IM_MAX-IM_MIN)
    c_r=np.sqrt(re_px**2+im_px**2)
    c_theta=(np.arctan2(im_px,re_px)+np.pi)/(2*np.pi)
    c_log_r=np.log(c_r+0.01)

    qi=np.floor(c_theta*N_ANGLE).astype(int)
    qj=np.floor(c_log_r/LOG_R_STEP).astype(int)
    chess_raw=((qi%2==0)!=(qj%2==0)).astype(np.float64)

    # 高斯模糊棋盘掩码
    if CHESS_BLUR_SIGMA > 0:
        chess_smooth=gaussian_filter(chess_raw, sigma=CHESS_BLUR_SIGMA)
    else:
        chess_smooth=chess_raw

    # 仅在外部区域以低alpha混合
    chess_alpha_mask=chess_smooth*CHESS_ALPHA
    chess_alpha_mask[interior]=0  # 内部不叠加棋盘

    # 构建棋盘纹理RGB（3通道）
    tex_chess = np.zeros((h, w, 3), dtype=np.float64)
    mask_light = chess_raw > 0.5
    for ch in range(3):
        tex_chess[:, :, ch] = np.where(mask_light, TILE_BRIGHT[ch], TILE_SHADOW[ch])

    for ch in range(3):
        blended=img[:,:,ch]*(1-chess_alpha_mask)+tex_chess[:,:,ch]*chess_alpha_mask
        img[:,:,ch]=np.clip(blended,0,1)

    # ====== 层4: 多层金边+Bloom辉光溢出 ======
    abs_z=np.sqrt(fz.real**2+fz.imag**2+1e-30)
    abs_dz=np.sqrt(fdz.real**2+fdz.imag**2+1e-30)
    dem=np.log(abs_z**2+1e-30)*abs_z/(abs_dz+1e-30)
    dem[~ext]=-1

    bd_h=interior[:,:-1]!=interior[:,1:]
    bd_v=interior[:-1,:]!=interior[1:,:]
    edge=np.zeros((h,w),dtype=bool)
    edge[:,:-1]|=bd_h; edge[:-1,:]|=bd_v

    # 4层辉光结构
    g_bloom=binary_dilation(edge,structure=np.ones((24,24)))  # 最外层bloom
    g_outer=binary_dilation(edge,structure=np.ones((14,14)))  # 外层暖色
    g_mid  =binary_dilation(edge,structure=np.ones((7,7)))   # 中层金橙
    g_inner=binary_dilation(edge,structure=np.ones((3,3)))   # 内层炽白

    dv=dem.copy();dv[dv<0]=0
    dl=np.log1p(dv*DEM_SCALE)
    dn=dl/(dl.max()+1e-12) if dl.max()>0 else dl

    # Bloom层（远端微弱金色散射）
    gb=g_bloom&ext&~g_outer
    if gb.any():
        d=np.power(dn[gb],1.8)  # 极快衰减
        img[gb,0]=np.clip(img[gb,0]+0.12*d,0,1)
        img[gb,1]=np.clip(img[gb,1]+0.06*d,0,1)
        img[gb,2]=np.clip(img[gb,2]+0.01*d,0,1)

    # 外层暖色过渡
    go=g_outer&ext&~g_mid
    if go.any():
        d=dn[go]
        img[go]=np.stack([
            np.clip(GOLD_OUTER[0]*0.40+GOLD_MID[0]*0.55*d,0,1),
            np.clip(GOLD_OUTER[1]*0.30+GOLD_MID[1]*0.65*d,0,1),
            np.clip(GOLD_OUTER[2]*0.10+GOLD_MID[2]*0.85*d,0,0.35),
        ],axis=-1)

    # 中层金橙
    gm=g_mid&ext&~g_inner
    if gm.any():
        d=dn[gm]
        img[gm]=np.stack([
            np.clip(GOLD_MID[0]*0.50+GOLD_CORE[0]*0.50*d,0,1),
            np.clip(GOLD_MID[1]*0.40+GOLD_CORE[1]*0.60*d,0,1),
            np.clip(GOLD_MID[2]*0.15+GOLD_CORE[2]*0.85*d,0,0.40),
        ],axis=-1)

    # 内侧炽白金
    gi=g_inner&interior
    if gi.any():
        d=dn[gi]
        img[gi]=np.stack([
            np.clip(GOLD_CORE[0]*0.65+0.35*d,0,1),
            np.clip(GOLD_CORE[1]*0.55+0.45*d,0,1),
            np.clip(GOLD_CORE[2]*0.20+0.80*d,0,0.50),
        ],axis=-1)

    return np.rot90(img,k=3)


# ============================================================
if __name__=='__main__':
    out_dir=os.path.dirname(os.path.abspath(__file__))
    print(f"=== v5 宝石蓝辉光版 ===")
    print(f"{WIDTH}x{HEIGHT} | iter={MAX_ITER} | chess_alpha={CHESS_ALPHA}")

    data=compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,WIDTH,HEIGHT,MAX_ITER,BAILOUT_SQ)
    print(f"int={data['interior'].sum()} ({100*data['interior'].mean():.1f}%)")

    img=render(data,WIDTH,HEIGHT)
    out=os.path.join(out_dir,'最美的蓝色水滴分形_v5.png')
    fw=8;fh=fw*HEIGHT/WIDTH
    fig,ax=plt.subplots(figsize=(fw,fh),dpi=150)
    ax.imshow(img,extent=[IM_MIN,IM_MAX,RE_MIN,RE_MAX],
              aspect='equal',interpolation='bilinear',origin='lower')
    ax.axis('off');plt.tight_layout(pad=0)
    plt.savefig(out,dpi=200,bbox_inches='tight',facecolor=tuple(BG_MIDNIGHT))
    plt.close()
    print(f"完成! {out} ({os.path.getsize(out)/1024/1024:.1f}MB)")
