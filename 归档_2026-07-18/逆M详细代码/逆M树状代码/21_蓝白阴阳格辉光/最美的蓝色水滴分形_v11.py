#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v11 - 修复v10的PNG保存方式：用 PIL 直接保存精确像素，绕过 matplotlib resampling
改动：
  1. 用 PIL.Image.fromarray() 替代 plt.savefig() → 保留 SSAA 下采样后的精确像素
     原来 matplotlib 按 figure dpi=200 重采样 → 2400px 变 ~1600px，SSAA 优势丢失
  2. 其余算法完全等同 v10 (SSAA RGB积分 + 逆心形解析描边 + 5层金边 + 棋盘格)
"""
import numpy as np, matplotlib.pyplot as plt, os, sys
from scipy.ndimage import binary_dilation, gaussian_filter
from PIL import Image

TIP=4.0;BOTTOM=-4.0/3.0;HSPAN=1.6242719100;MARGIN=0.50
RE_MIN,RE_MAX=BOTTOM-MARGIN,TIP+MARGIN
IM_MIN,IM_MAX=-HSPAN-MARGIN,HSPAN+MARGIN
WIDTH=int(sys.argv[1]) if len(sys.argv)>1 else 2400
SSAA=int(sys.argv[2]) if len(sys.argv)>2 else 2
HEIGHT=int(WIDTH*(RE_MAX-RE_MIN)/(IM_MAX-IM_MIN))
MAX_ITER=320;BAILOUT_SQ=128**2
N_ANGLE=480;LOG_R_STEP=0.022;CHESS_ALPHA=0.17;CHESS_BLUR=1.4
BG_BLACK=[0.00,0.00,0.02]
EXT_FAR=[0.03,0.08,0.22];EXT_MID=[0.10,0.18,0.42];EXT_NEAR=[0.20,0.33,0.60]
TILE_BRIGHT=[0.38,0.52,0.82];TILE_SHADOW=[0.01,0.04,0.14]
INT_HOT=[0.94,0.97,1.0];INT_CORE=[0.76,0.87,0.98];INT_MID=[0.52,0.70,0.92];INT_EDGE=[0.28,0.46,0.78]
GOLD_WHITE=[1.0,1.0,0.70];GOLD_HOT=[1.0,0.88,0.25];GOLD_WARM=[0.95,0.55,0.06];GOLD_EMBER=[0.75,0.28,0.02]
DEM_SCALE=26.0

def compute(x_min,x_max,y_min,y_max,w,h,max_iter,bail_sq):
    x=np.linspace(x_min,x_max,w);y=np.linspace(y_min,y_max,h);X,Y=np.meshgrid(x,y);co=X+1j*Y
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
    return {'ic':ic,'trap':trap,'z':z.copy(),'dz':dz.copy(),'interior':~alive,'co':co}

def generate_outline(n_pts=9000):
    t=np.linspace(1e-4,2*np.pi-1e-4,n_pts)
    c=0.5*np.exp(1j*t)-0.25*np.exp(2j*t)
    inv=1.0/c
    return inv.real, inv.imag

def render(data,w,h):
    ic=data['ic'];trap=data['trap'];fz=data['z'];fdz=data['dz']
    interior=data['interior'];ext=~interior;img=np.full((h,w,3),BG_BLACK,dtype=np.float64)
    with np.errstate(invalid='ignore',divide='ignore'):
        ms=fz.real**2+fz.imag**2+1e-30;nc_f=np.minimum(ic,32).astype(np.float64)
        pot_raw=np.log(ms)/np.power(2.0,nc_f);pot_raw[interior]=0
        p99=np.percentile(pot_raw[ext],99) if ext.any() else 1
        t=np.clip(pot_raw/max(p99,0.5),0,1);ts=np.power(t,0.52)
        def lut(v,r0,g0,b0,r1,g1,b1,r2,g2,b2,rl,gl,bl):
            r=np.select([v<0.25,v<0.55,v<0.82,True],[r0+(r1-r0)*(v/0.25),r1+(r2-r1)*((v-0.25)/0.30),r2+(rl-r2)*((v-0.55)/0.27),rl])
            g=np.select([v<0.25,v<0.55,v<0.82,True],[g0+(g1-g0)*(v/0.25),g1+(g2-g1)*((v-0.25)/0.30),g2+(gl-g2)*((v-0.55)/0.27),gl])
            b=np.select([v<0.25,v<0.55,v<0.82,True],[b0+(b1-b0)*(v/0.25),b1+(b2-b1)*((v-0.25)/0.30),b2+(bl-b2)*((v-0.55)/0.27),bl])
            return np.stack([r,g,b],axis=-1)
        ext_rgb=lut(ts,EXT_FAR[0],EXT_FAR[1],EXT_FAR[2],EXT_MID[0],EXT_MID[1],EXT_MID[2],
                     EXT_NEAR[0],EXT_NEAR[1],EXT_NEAR[2],
                     min(EXT_NEAR[0]+0.08,0.35),min(EXT_NEAR[1]+0.08,0.45),min(EXT_NEAR[2]+0.06,0.70))
        img[ext]=ext_rgb[ext]
    with np.errstate(invalid='ignore'):
        trap_s=np.maximum(trap,1e-30);v_raw=(np.log(trap_s)*0.43)%1.0;v_adj=np.power(v_raw,0.48)
        r_i=np.select([v_adj<0.12,v_adj<0.30,v_adj<0.55,v_adj<0.80,True],
            [INT_HOT[0]+(INT_CORE[0]-INT_HOT[0])*(v_adj/0.12),INT_CORE[0]+(INT_MID[0]-INT_CORE[0])*((v_adj-0.12)/0.18),
             INT_MID[0]+(INT_EDGE[0]-INT_MID[0])*((v_adj-0.30)/0.25),INT_EDGE[0]+(INT_EDGE[0]*0.65-INT_EDGE[0])*((v_adj-0.55)/0.25),
             INT_EDGE[0]*0.65*(1-(v_adj-0.80)/0.20)])
        g_i=np.select([v_adj<0.12,v_adj<0.30,v_adj<0.55,v_adj<0.80,True],
            [INT_HOT[1]+(INT_CORE[1]-INT_HOT[1])*(v_adj/0.12),INT_CORE[1]+(INT_MID[1]-INT_CORE[1])*((v_adj-0.12)/0.18),
             INT_MID[1]+(INT_EDGE[1]-INT_MID[1])*((v_adj-0.30)/0.25),INT_EDGE[1]+(INT_EDGE[1]*0.68-INT_EDGE[1])*((v_adj-0.55)/0.25),
             INT_EDGE[1]*0.68*(1-(v_adj-0.80)/0.20)])
        b_i=np.select([v_adj<0.12,v_adj<0.30,v_adj<0.55,v_adj<0.80,True],
            [INT_HOT[2]+(INT_CORE[2]-INT_HOT[2])*(v_adj/0.12),INT_CORE[2]+(INT_MID[2]-INT_CORE[2])*((v_adj-0.12)/0.18),
             INT_MID[2]+(INT_EDGE[2]-INT_MID[2])*((v_adj-0.30)/0.25),INT_EDGE[2]+(INT_EDGE[2]*0.75-INT_EDGE[2])*((v_adj-0.55)/0.25),
             INT_EDGE[2]*0.75*(1-(v_adj-0.80)/0.20)])
        img[interior]=np.stack([r_i[interior],g_i[interior],b_i[interior]],axis=-1)
    yy,xx=np.ogrid[:h,:w];re_px=RE_MIN+(xx/(w-1))*(RE_MAX-RE_MIN);im_px=IM_MIN+(yy/(h-1))*(IM_MAX-IM_MIN)
    c_r=np.sqrt(re_px**2+im_px**2);c_theta=(np.arctan2(im_px,re_px)+np.pi)/(2*np.pi);c_log_r=np.log(c_r+0.01)
    qi=np.floor(c_theta*N_ANGLE).astype(int);qj=np.floor(c_log_r/LOG_R_STEP).astype(int)
    chess_raw=((qi%2==0)!=(qj%2==0)).astype(np.float64)
    cs=gaussian_filter(chess_raw,sigma=CHESS_BLUR) if CHESS_BLUR>0 else chess_raw
    ca=cs*CHESS_ALPHA;ca[interior]=0
    tex=np.zeros((h,w,3),dtype=np.float64);ml=chess_raw>0.5
    for ch in range(3): tex[:,:,ch]=np.where(ml,TILE_BRIGHT[ch],TILE_SHADOW[ch])
    for ch in range(3): img[:,:,ch]=np.clip(img[:,:,ch]*(1-ca)+tex[:,:,ch]*ca,0,1)
    abs_z=np.sqrt(fz.real**2+fz.imag**2+1e-30);abs_dz=np.sqrt(fdz.real**2+fdz.imag**2+1e-30)
    dem=np.log(abs_z**2+1e-30)*abs_z/(abs_dz+1e-30);dem[~ext]=-1
    bd_h=interior[:,:-1]!=interior[:,1:];bd_v=interior[:-1,:]!=interior[1:,:]
    edge=np.zeros((h,w),dtype=bool);edge[:,:-1]|=bd_h;edge[:-1,:]|=bd_v
    g_ember=binary_dilation(edge,np.ones((28,28)));g_warm=binary_dilation(edge,np.ones((18,18)))
    g_gold=binary_dilation(edge,np.ones((10,10)));g_hot=binary_dilation(edge,np.ones((5,5)));g_core=binary_dilation(edge,np.ones((2,2)))
    dv=dem.copy();dv[dv<0]=0;dl=np.log1p(dv*DEM_SCALE);dn=dl/(dl.max()+1e-12) if dl.max()>0 else dl
    ge=g_ember&ext&~g_warm
    if ge.any():
        d=np.power(dn[ge],2.0);img[ge,0]=np.clip(img[ge,0]+0.10*d,0,1);img[ge,1]=np.clip(img[ge,1]+0.05*d,0,1);img[ge,2]=np.clip(img[ge,2]+0.01*d,0,1)
    gw=g_warm&ext&~g_gold
    if gw.any():
        d=dn[gw];img[gw]=np.stack([np.clip(GOLD_EMBER[0]*0.35+GOLD_WARM[0]*0.60*d,0,1),np.clip(GOLD_EMBER[1]*0.25+GOLD_WARM[1]*0.68*d,0,1),np.clip(GOLD_EMBER[2]*0.08+GOLD_WARM[2]*0.85*d,0,0.32)],axis=-1)
    gg=g_gold&ext&~g_hot
    if gg.any():
        d=dn[gg];img[gg]=np.stack([np.clip(GOLD_WARM[0]*0.40+GOLD_HOT[0]*0.56*d,0,1),np.clip(GOLD_WARM[1]*0.32+GOLD_HOT[1]*0.64*d,0,1),np.clip(GOLD_WARM[2]*0.12+GOLD_HOT[2]*0.82*d,0,0.40)],axis=-1)
    gh=g_hot&ext&~g_core
    if gh.any():
        d=dn[gh];img[gh]=np.stack([np.clip(GOLD_HOT[0]*0.55+GOLD_WHITE[0]*0.42*d,0,1),np.clip(GOLD_HOT[1]*0.48+GOLD_WHITE[1]*0.48*d,0,1),np.clip(GOLD_HOT[2]*0.18+GOLD_WHITE[2]*0.75*d,0,0.50)],axis=-1)
    gc=g_core&interior
    if gc.any():
        d=dn[gc];img[gc]=np.stack([np.clip(GOLD_WHITE[0]*0.62+0.36*d,0,1),np.clip(GOLD_WHITE[1]*0.58+0.39*d,0,1),np.clip(GOLD_WHITE[2]*0.35+0.60*d,0,0.58)],axis=-1)
    a,b=generate_outline(n_pts=9000)
    col=np.round((a-RE_MIN)/(RE_MAX-RE_MIN)*(w-1)).astype(int);row=np.round((b-IM_MIN)/(IM_MAX-IM_MIN)*(h-1)).astype(int)
    ok=(row>=1)&(row<h-1)&(col>=1)&(col<w-1);row,col=row[ok],col[ok]
    line=np.zeros((h,w),dtype=bool);line[row,col]=True;line=binary_dilation(line,np.ones((2,2)))
    if line.any():
        img[line,0]=np.clip(img[line,0]*0.20+GOLD_WHITE[0]*0.80,0,1)
        img[line,1]=np.clip(img[line,1]*0.20+GOLD_WHITE[1]*0.80,0,1)
        img[line,2]=np.clip(img[line,2]*0.20+GOLD_WHITE[2]*0.80,0,1)
    return np.rot90(img,k=3)

def downsample(raw, ssaa):
    h,w,_=raw.shape;H,W=h//ssaa,w//ssaa;out=np.zeros((H,W,3),dtype=np.float64)
    for j in range(ssaa):
        for i in range(ssaa): out+=raw[j::ssaa, i::ssaa, :]
    out/=(ssaa*ssaa);return np.clip(out,0,1)

if __name__=='__main__':
    out_dir=os.path.dirname(os.path.abspath(__file__))
    rw,rh=WIDTH*SSAA,HEIGHT*SSAA
    print(f"=== v11 SSAA版 (PIL精确保存) === target={WIDTH}x{HEIGHT} SSAA={SSAA} raw={rw}x{rh} iter={MAX_ITER}")
    data=compute(RE_MIN,RE_MAX,IM_MIN,IM_MAX,rw,rh,MAX_ITER,BAILOUT_SQ)
    print(f"int={data['interior'].sum()} ({100*data['interior'].mean():.1f}%)")
    raw=render(data,rw,rh)
    print(f"raw渲染完成 {raw.shape}, 下采样 SSAA={SSAA}...")
    img=downsample(raw,SSAA)
    print(f"img shape={img.shape}, dtype={img.dtype}, range=[{img.min():.3f},{img.max():.3f}]")
    out=os.path.join(out_dir,f'最美的蓝色水滴分形_v11.png')
    # ★ 关键修复: 用 PIL 保存精确像素, 绕过 matplotlib 重采样
    img_uint8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img_uint8, mode='RGB').save(out, compress_level=1)
    print(f"完成! {out} ({os.path.getsize(out)/1024/1024:.1f}MB) 精确像素 {img.shape[1]}x{img.shape[0]}")
