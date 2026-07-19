#!/usr/bin/env python3
"""SEG GCD对比GIF — 修复中文乱码"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.font_manager import FontProperties
import os

# 显式加载中文字体
fp=FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf',size=10)
fp_title=FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf',size=12)
fp_big=FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf',size=14)

MU0_4PI=1e-7; np.random.seed(42)

def dipole_force(m_s,m_t,r_vec):
    r=np.linalg.norm(r_vec)
    if r<1e-10:return np.zeros(3)
    rh=r_vec/r; m1r=np.dot(m_s,rh);m2r=np.dot(m_t,rh);m12=np.dot(m_s,m_t)
    return(3*MU0_4PI/r**4)*(m1r*m_t+m2r*m_s+m12*rh-5*m1r*m2r*rh)

def build_stator(N_p,R=1.0):
    a=2*np.pi*np.arange(N_p)/N_p
    p=np.column_stack([R*np.cos(a),R*np.sin(a),np.zeros(N_p)])
    pol=np.where(np.arange(N_p)%2==0,1.0,-1.0)
    m=np.column_stack([pol*np.cos(a),pol*np.sin(a),np.zeros(N_p)])
    return p,m

def build_roller(P_p,center,rr,asym,seed):
    rng=np.random.RandomState(seed)
    ba=2*np.pi*np.arange(P_p)/P_p
    pa=ba+asym*0.3*rng.randn(P_p)
    cx,cy=center[:2]
    px=cx+rr*np.cos(pa);py=cy+rr*np.sin(pa)
    pos=np.column_stack([px,py,np.zeros(P_p)])
    pol=np.where(np.arange(P_p)%2==0,1.0,-1.0).astype(float)
    pol*=1.0+asym*0.5*rng.randn(P_p)
    mom=np.column_stack([pol*np.cos(pa),pol*np.sin(pa),np.zeros(P_p)])
    return pos,mom

def compute_tangential(N_s,P_r,theta,asym):
    sp,sm=build_stator(N_s,1.0)
    center=np.array([0.65*np.cos(theta),0.65*np.sin(theta),0.0])
    rp,rm=build_roller(P_r,center,0.04,asym,int(theta*100+42))
    F=np.zeros((P_r,3))
    for j in range(P_r):
        for i in range(N_s):
            F[j]+=dipole_force(sm[i],rm[j],rp[j]-sp[i])
    tt=0
    for j in range(P_r):
        rh=(rp[j]-center)/(np.linalg.norm(rp[j]-center)+1e-10)
        tang=np.array([-rh[1],rh[0],0.0])
        tt+=np.dot(F[j],tang)
    return tt

N_STEPS=180
angles=np.linspace(0,2*np.pi,N_STEPS)

# gcd=1: N_s=122,P_r=9
t1=np.array([compute_tangential(122,9,a,0.3) for a in angles])
# gcd>1: N_s=120,P_r=8
t2=np.array([compute_tangential(120,8,a,0.3) for a in angles])
t1n=t1/(np.max(np.abs(t1))+1e-15)
t2n=t2/(np.max(np.abs(t2))+1e-15)

print(f"gcd=1: CV={np.std(t1)/np.mean(np.abs(t1)):.4f}")
print(f"gcd>1: CV={np.std(t2)/np.mean(np.abs(t2)):.4f}")

fig,axes=plt.subplots(2,2,figsize=(12,8),gridspec_kw={'width_ratios':[2,1]})

def animate(frame):
    for ax in axes.flat:ax.clear()
    theta=angles[frame]
    
    # 左上：gcd=1 扭矩
    ax=axes[0,0]
    ax.plot(angles*180/np.pi,t1n,'#1d9e75',linewidth=1.2)
    ax.axvline(theta*180/np.pi,color='#1d9e75',alpha=0.6,linewidth=2)
    ax.axhline(0,color='gray',linewidth=0.5)
    ax.set_xlim(0,360);ax.set_ylim(-1.2,1.2)
    ax.set_title('gcd=1 (磁静音) CV='+f'{np.std(t1)/np.mean(np.abs(t1)):.3f}',
                 fontproperties=fp_title,color='#1d9e75')
    ax.set_xlabel('轨道角度 (°)',fontproperties=fp)
    ax.set_ylabel('归一化切向力',fontproperties=fp)
    ax.grid(True,alpha=0.3)
    for label in ax.get_xticklabels()+ax.get_yticklabels():
        label.set_fontproperties(fp)
    
    # 右上：gcd>1 扭矩
    ax=axes[0,1]
    ax.plot(angles*180/np.pi,t2n,'#e24b4a',linewidth=1.2)
    ax.axvline(theta*180/np.pi,color='#e24b4a',alpha=0.6,linewidth=2)
    ax.axhline(0,color='gray',linewidth=0.5)
    ax.set_xlim(0,360);ax.set_ylim(-1.2,1.2)
    ax.set_title('gcd>1 (磁振动) CV='+f'{np.std(t2)/np.mean(np.abs(t2)):.3f}',
                 fontproperties=fp_title,color='#e24b4a')
    ax.set_xlabel('轨道角度 (°)',fontproperties=fp)
    ax.grid(True,alpha=0.3)
    for label in ax.get_xticklabels()+ax.get_yticklabels():
        label.set_fontproperties(fp)
    
    # 左下：频谱
    ax=axes[1,0]
    f1=np.abs(np.fft.rfft(t1-np.mean(t1)))
    f2=np.abs(np.fft.rfft(t2-np.mean(t2)))
    freqs=np.fft.rfftfreq(len(t1))
    ax.bar(freqs[:30],f1[:30]/np.max(f1),alpha=0.6,color='#1d9e75',label='gcd=1',width=0.003)
    ax.bar(freqs[:30]+0.003,f2[:30]/np.max(f2),alpha=0.6,color='#e24b4a',label='gcd>1',width=0.003)
    ax.set_title('力波动频谱',fontproperties=fp_title)
    ax.set_xlabel('频率',fontproperties=fp)
    ax.set_ylabel('归一化振幅',fontproperties=fp)
    ax.legend(prop=fp);ax.grid(True,alpha=0.3)
    ax.set_xlim(0,0.12)
    for label in ax.get_xticklabels()+ax.get_yticklabels():
        label.set_fontproperties(fp)
    
    # 右下：统计表
    ax=axes[1,1];ax.axis('off')
    cv1=f'{np.std(t1)/np.mean(np.abs(t1)):.4f}'
    cv2=f'{np.std(t2)/np.mean(np.abs(t2)):.4f}'
    rev1=f'{100*np.sum(t1[:-1]*t1[1:]<0)/len(t1):.1f}%'
    rev2=f'{100*np.sum(t2[:-1]*t2[1:]<0)/len(t2):.1f}%'
    stats=[
        ['指标','gcd=1','gcd>1'],
        ['变异系数CV',cv1,cv2],
        ['反转率',rev1,rev2],
        ['峰峰值',f'{np.max(t1)-np.min(t1):.4f}',f'{np.max(t2)-np.min(t2):.4f}'],
        ['均值|T|',f'{np.mean(np.abs(t1)):.4f}',f'{np.mean(np.abs(t2)):.4f}'],
        ['最强谐波比',f'{np.max(f1)/np.sum(f1):.3f}',f'{np.max(f2)/np.sum(f2):.3f}'],
    ]
    t=ax.table(cellText=stats,loc='center',cellLoc='center')
    t.auto_set_font_size(False);t.set_fontsize(9)
    t.scale(1.1,1.4)
    # 表格也用中文字体
    for key,cell in t.get_celld().items():
        cell.set_text_props(fontproperties=fp)
    ax.set_title(f'角度={theta*180/np.pi:.0f}°',fontproperties=fp_title,pad=20)
    
    plt.tight_layout(pad=2)
    return axes

anim=FuncAnimation(fig,animate,frames=N_STEPS,interval=40,blit=False)
out=os.path.join(os.path.dirname(__file__),'seg_gcd_comparison.gif')
anim.save(out,writer=PillowWriter(fps=15),dpi=100)
print(f"✓ GIF: {out} ({os.path.getsize(out)/1024/1024:.1f}MB)")
plt.close()
