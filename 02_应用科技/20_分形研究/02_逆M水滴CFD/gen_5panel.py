#!/usr/bin/env python3
"""逆M水滴 5子图: Full | x-heur | 2^n+φ(n) | Farey+Sharkovsky | Greedy108"""
import numpy as np, math, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif']=['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus']=False

this_dir=r'D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M水滴CFD流体实验'
pts=np.loadtxt(os.path.join(this_dir,'droplet_invM_analytic.csv'),delimiter=',',skiprows=1)
N_half=len(pts)//2;ux,uy=pts[:N_half,0],pts[:N_half,1]
D=np.ptp(ux)  # 5.333

def coprime(a,b):return math.gcd(a,b)==1
phi=lambda n:sum(1 for k in range(1,n) if coprime(k,n))
def inv_cardioid(th):
    return 1.0/(0.5*np.exp(1j*th)-0.25*np.exp(2j*th))
def seg_dev(a,b):
    md,mi=0.0,a;ax,ay=ux[a],uy[a];bx,by=ux[b],uy[b]
    abx,aby=bx-ax,by-ay;ab2=abx**2+aby**2
    if ab2<1e-20:return 0.0,a
    for i in range(a,b+1):
        t=max(0,min(1,((ux[i]-ax)*abx+(uy[i]-ay)*aby)/ab2))
        d=np.hypot(ux[i]-(ax+t*abx),uy[i]-(ay+t*aby))
        if d>md:md,mi=d,i
    return md,mi
def rot90(x,y):return -y,x
def closed(x,y):
    return rot90(np.concatenate([x,x[::-1]]),np.concatenate([y,-y[::-1]]))
def poly_area(x,y):
    return 0.5*abs(np.dot(x[:-1],y[1:])-np.dot(x[1:],y[:-1]))

# 主锚点
ancs_info=[];anchors=set()
for q in range(2,8):
    for p in range(1,q):
        if coprime(p,q):
            th=2*np.pi*p/q;ci=inv_cardioid(th)
            if 0<th<np.pi and ci.imag<=0:
                idx=int(np.argmin(np.hypot(ux-ci.real,uy+ci.imag)))
                ancs_info.append((q,p,idx));anchors.add(idx)
ancs_info.append((1,0,0));ancs_info.append((1,0,N_half-1))
ancs_info.sort(key=lambda x:x[2])
anchors.add(0);anchors.add(N_half-1)
sharkovsky_rank={3:1,5:2,7:3,6:4,4:5,2:6,1:7}
sharkovsky_colors={1:'#e74c3c',2:'#e67e22',3:'#f1c40f',4:'#2ecc71',5:'#9b59b6',6:'#3498db',7:'#95a5a6'}

# ═══ 算法1: Full ═══
k1=np.ones(N_half,bool)

# ═══ 算法2: x-heuristic ═══
k2=np.zeros(N_half,bool)
for i in range(N_half):
    x=ux[i]
    if x>3.5:r=1.0
    elif x>2.0:r=1/3
    elif x>0.0:r=1/5
    elif x>-0.8:r=1/3
    else:r=1/2
    k2[i]=(i%max(1,int(1/r))==0)
k2[0]=k2[-1]=True

# ═══ 算法3: 2^n+φ(n) decomposed ═══
weights={n:2**n+phi(n) for n in range(1,9)}
k3=set(anchors);phi_sub=set();p2_sub=set()
for k in range(len(ancs_info)-1):
    q1,_,i1=ancs_info[k];q2,_,i2=ancs_info[k+1]
    max_q=max(q1,q2)
    w=weights.get(max_q,2**max_q+max_q)
    n_sub=min(w//8,(i2-i1)//2)
    if n_sub>0 and i2>i1+1:
        p2v=2**max_q;phiv=phi(max_q)
        n_phi=max(1,round(n_sub*phiv/(p2v+phiv))) if phiv>0 else 0
        steps=np.linspace(i1+1,i2-1,n_sub+2,dtype=int)[1:-1]
        for j,si in enumerate(steps):
            k3.add(int(si))
            (phi_sub if j<n_phi else p2_sub).add(int(si))
k3a=np.zeros(N_half,bool)
for i in k3:k3a[i]=True

# ═══ 算法4: Farey+Sharkovsky anchors ═══
# 收集所有Farey分数对应的锚点并按Sharkovsky序着色
farey_anchors={}  # {idx: (period, sharkovsky_rank)}
for q in range(2,8):
    for p in range(1,q):
        if coprime(p,q):
            th=2*np.pi*p/q;ci=inv_cardioid(th)
            if 0<th<np.pi and ci.imag<=0:
                idx=int(np.argmin(np.hypot(ux-ci.real,uy+ci.imag)))
                sr=sharkovsky_rank.get(q,99)
                farey_anchors[idx]=(q,sr)
farey_anchors[0]=(1,7);farey_anchors[N_half-1]=(1,7)

# ═══ 算法5: Greedy 108 ═══
k=list(anchors)
while len(k)*2<108:
    ki=sorted(k);wd,ws=0,0
    for s in range(len(ki)-1):
        d,_=seg_dev(ki[s],ki[s+1])
        if d>wd:wd,ws=d,s
    a,b=ki[ws],ki[ws+1];_,wi=seg_dev(a,b);k.append(wi)
k5=sorted(set(k))
k5a=np.zeros(N_half,bool)
for i in k5:k5a[i]=True
k5_dev=max(seg_dev(k5[s],k5[s+1])[0] for s in range(len(k5)-1) if k5[s+1]>k5[s])

# ═══ 背景轮廓 ═══
bfx,bfy=closed(ux,uy)
full_area=poly_area(np.append(np.concatenate([ux,ux[::-1]]),ux[0]),
                    np.append(np.concatenate([uy,-uy[::-1]]),uy[0]))

def get_closed(keep):
    rx=ux[keep];ry=uy[keep]
    return np.append(np.concatenate([rx,rx[::-1]]),rx[0]),np.append(np.concatenate([ry,-ry[::-1]]),ry[0])

# ═══ 5子图 ═══
fig,axes=plt.subplots(1,5,figsize=(30,7))

panels=[
    (k1,'#27ae60',f'Full baseline\n{N_half*2} pts (100%)','plain',2),
    (k2,'#e74c3c',f'x-heuristic\n{np.sum(k2)*2} pts ({np.sum(k2)/N_half*100:.0f}%)','plain',9),
    (k3a,'#2980b9',f'2^n+phi(n) DECOMPOSED\n{np.sum(k3a)*2} pts ({np.sum(k3a)/N_half*100:.0f}%)','split',9),
    (k1,'#555',f'Farey+Sharkovsky\n{len(farey_anchors)} anchors (period 1-7)','farey',2),
    (k5a,'#8e44ad',f'Greedy 108 pts\n{np.sum(k5a)*2} pts ({np.sum(k5a)/N_half*100:.0f}%)','plain',10),
]

for ax,(keep,color,title,mode,ms) in zip(axes,panels):
    bx,by=closed(ux[keep],uy[keep])
    ax.fill(bfx,bfy,color='#4ecdc4',alpha=0.18,edgecolor='none')
    ax.plot(bfx,bfy,'lightblue',lw=0.3,alpha=0.3)
    ax.plot(bx,by,'-',color=color,lw=1.1,alpha=0.85)

    if mode=='split':
        ax.plot(bx,by,'--',color=color,lw=0.4,alpha=0.3)
        ax.scatter([-uy[i] for i in anchors],[ux[i] for i in anchors],
                   marker='D',c='#FFD700',s=90,ec='#B8860B',lw=1.5,zorder=8)
        ax.scatter([-uy[i] for i in p2_sub],[ux[i] for i in p2_sub],
                   marker='o',c='#3498db',s=26,ec='#1a5276',lw=0.5,alpha=0.9,zorder=7)
        ax.scatter([-uy[i] for i in phi_sub],[ux[i] for i in phi_sub],
                   marker='^',c='#e74c3c',s=48,ec='#922b21',lw=0.8,alpha=0.95,zorder=7)
        leg=[
            Line2D([0],[0],marker='D',color='w',markerfacecolor='#FFD700',markersize=9,label='phi(n) 10'),
            Line2D([0],[0],marker='o',color='w',markerfacecolor='#3498db',markersize=7,label='2^n'),
            Line2D([0],[0],marker='^',color='w',markerfacecolor='#e74c3c',markersize=7,label='phi sub'),
        ]
        ax.legend(handles=leg,loc='lower right',fontsize=6,framealpha=0.8)

    elif mode=='farey':
        # 按Sharkovsky序着色锚点
        # 先画轮廓
        ax.plot(bx,by,'-',color=color,lw=0.8,alpha=0.5)
        legend_handles=[]
        for sr in sorted(set(sr for _,sr in farey_anchors.values())):
            pts_sr=[idx for idx,(q,sr2) in farey_anchors.items() if sr2==sr]
            if not pts_sr:continue
            c=sharkovsky_colors[sr]
            label_map={1:'Per 3',2:'Per 5',3:'Per 7',4:'Per 6(2*3)',5:'Per 4',6:'Per 2',7:'Per 1'}
            lb=f'{label_map[sr]} ({len(pts_sr)})'
            ax.scatter([-uy[i] for i in pts_sr],[ux[i] for i in pts_sr],
                       marker='D',c=c,s=80,ec='white',lw=0.8,zorder=7)
            legend_handles.append(Line2D([0],[0],marker='D',color='w',markerfacecolor=c,markersize=8,label=lb))
        ax.legend(handles=legend_handles,loc='lower right',fontsize=5.5,framealpha=0.85,title='Sharkovsky order')
        ax.plot(bx,by,'--',color='#555',lw=0.5,alpha=0.3)
    else:
        ax.scatter(bx,by,c=color,s=ms**2,ec='white',lw=0.3,zorder=5)

    # 形变/面积标注
    if mode in ('plain','greedy') and np.sum(keep)!=N_half:
        kk=np.zeros(N_half,bool)
        if isinstance(keep,np.ndarray):kk=keep
        else:
            for i in keep:kk[i]=True
        rx,ry=get_closed(kk)
        a=poly_area(rx,ry)
        da=abs(a-full_area)/full_area*100
        ki=sorted(np.where(kk)[0] if isinstance(kk,np.ndarray) else list(kk))
        d=max(seg_dev(ki[s],ki[s+1])[0] for s in range(len(ki)-1) if ki[s+1]>ki[s])
        ax.text(0.98,0.05,f'Δarea={da:.3f}%  Δshape={d/D*100:.3f}%',
                transform=ax.transAxes,fontsize=7,ha='right',color='#888')

    ax.set_aspect('equal')
    ax.set_title(title,fontsize=10,fontweight='bold',color=color)
    ax.grid(True,alpha=0.08)
    ax.set_xticks([]);ax.set_yticks([])

fig.suptitle('Inverse-M Droplet: 5 Sampling Strategies (90 CCW) — Sharkovsky Ordinal Color-Coding',
             fontsize=13,fontweight='bold',y=0.99)
fig.tight_layout(rect=[0,0,1,0.94])
out=os.path.join(this_dir,'droplet_5way_compare.png')
fig.savefig(out,dpi=180,bbox_inches='tight');plt.close(fig)

for nm,k in [('Full',k1),('x-heur',k2),('2^n+phi',k3a),('Farey',np.ones(N_half)),('108pt',k5a)]:
    if isinstance(k,np.ndarray):
        print(f'{nm}: {np.sum(k)*2} pts')
    else:
        print(f'{nm}: {len(k)*2} pts (estimated)')
print(f'108pt shape dev: {k5_dev:.6f} ({k5_dev/D*100:.4f}%)')
print(f'✅ {out}')
