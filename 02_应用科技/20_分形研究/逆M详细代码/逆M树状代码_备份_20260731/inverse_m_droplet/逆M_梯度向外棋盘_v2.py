#!/usr/bin/env python3
"""逆M_梯度向外棋盘_v2
参数按老师调整: R2=1024, LUT=3段, 视窗[-4,4]×[-2.5,5.5], nu简化"""
import numpy as np,os,sys,math,time
from PIL import Image

OUT_DIR=os.path.dirname(os.path.abspath(__file__))
RES=1200;MAX_ITER=400;R2=1024;ALPHA=-1.0

# LUT: 3段渐变 — 深蓝→白→金 (4个色标)
stops=[[5,10,50],[220,230,245],[255,180,60],[120,55,8]]
LUT=np.zeros((256,3),dtype=np.uint8);sn=len(stops)-1  # sn=3
for i in range(256):
    t=i/255*sn;k=min(int(t),sn-1);f=t-k
    for c in range(3):LUT[i,c]=int(stops[k][c]*(1-f)+stops[k+1][c]*f)

print(f"[1/3] 逆M迭代 {RES}x{RES}  R2={R2}")
t0=time.time()
xs=np.linspace(-4.0,4.0,RES,dtype=np.float64)
ys=np.linspace(-2.5,5.5,RES,dtype=np.float64)
X,Y=np.meshgrid(xs,ys);C=Y+1j*X
rC=np.abs(C);rC=np.maximum(rC,1e-13);thC=np.angle(C)
rp=np.power(rC,ALPHA);aa=ALPHA*thC;cr=rp*np.cos(aa);ci=rp*np.sin(aa)
Zr=np.zeros_like(cr);Zi=np.zeros_like(ci)
ic=np.full(C.shape,MAX_ITER,dtype=np.int32)
trap=np.full(C.shape,1e30,dtype=np.float64);al=np.ones(C.shape,dtype=bool)
for n in range(MAX_ITER):
    if not al.any():break
    zr=Zr[al];zi=Zi[al];er=cr[al];ei=ci[al]
    nzr=zr*zr-zi*zi+er;nzi=2*zr*zi+ei
    Zr[al]=nzr;Zi[al]=nzi
    m2=nzr*nzr+nzi*nzi
    trap[al]=np.minimum(trap[al],m2)
    esc=m2>R2;ic[al]=np.where(esc,n,ic[al]);al[al]=~esc
print(f"  iter:[{ic.min()},{ic.max()}]  {time.time()-t0:.1f}s")

# 梯度
print("[2/3] 梯度+着色...")
t0=time.time()
ic_float=ic.astype(np.float64)
gy,gx=np.gradient(ic_float)

interior=ic>=MAX_ITER;exterior=~interior

# 内部: orbit trap
v_arr=np.zeros(C.shape,dtype=np.float64)
with np.errstate(invalid='ignore',divide='ignore'):
    v_int=4.0*np.log(trap[interior]+1e-9)
    v_arr[interior]=0.3+0.7*v_int

# 外部: 简化 nu + v_smooth
Zr_e=Zr[exterior];Zi_e=Zi[exterior];ic_e=ic[exterior]
m2=Zr_e*Zr_e+Zi_e*Zi_e
nu=1.0/np.sqrt(np.maximum(m2,1e-30))  # 1/|z|          # 简化: ln(|z|²)/2
v_smooth=(ic_e+1-nu)*0.1                    # 不再乘系数

# 纯平滑着色 (取消棋盘)
v_arr[exterior]=v_smooth

# ── 生成两张图: spring 和 rainbow ──
for cmap_name in ['spring','rainbow']:
    if cmap_name == 'spring':
        t=np.clip(v_arr,0,1)
        rgb=np.stack([np.ones_like(t), t, 1-t],-1)  # (1,t,1-t)
    else:
        h6=(v_arr%1.0)*6;sv=1.0  # S=1, V=1
        c=sv;x=c*(1-np.abs(h6%2-1));m=0
        hi=h6.astype(int)%6
        r=np.where(hi==0,c,np.where(hi==1,x,np.where(hi==2,0,np.where(hi==3,0,np.where(hi==4,x,c)))))
        g=np.where(hi==0,x,np.where(hi==1,c,np.where(hi==2,c,np.where(hi==3,x,np.where(hi==4,0,0)))))
        b=np.where(hi==0,0,np.where(hi==1,0,np.where(hi==2,x,np.where(hi==3,c,np.where(hi==4,c,x)))))
        rgb=np.stack([r+m,g+m,b+m],-1)
    img=(np.clip(rgb,0,1)*255).astype(np.uint8)[::-1,:,:]
    out=os.path.join(OUT_DIR,f"逆M_{cmap_name}.png")
    Image.fromarray(img,'RGB').save(out)
    print(f"  → {out}")
print(f"  {time.time()-t0:.1f}s")
print("Done!")
