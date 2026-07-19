"""9种特殊M水滴拐点对比图"""
import numpy as np, math, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif']=['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus']=False

this_dir=r'D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M水滴CFD流体实验'
pts=np.loadtxt(os.path.join(this_dir,'droplet_invM_analytic.csv'),delimiter=',',skiprows=1)
N_half=len(pts)//2;ux,uy=pts[:N_half,0],pts[:N_half,1];D=np.ptp(ux)

def coprime(a,b):return math.gcd(a,b)==1
def inv_cardioid(th):
    return 1.0/(0.5*np.exp(1j*th)-0.25*np.exp(2j*th))
def seg_dev(a,b):
    if a>=b:return 0.0,a
    md,mi=0.0,a;ax,ay=ux[a],uy[a];bx,by=ux[b],uy[b]
    abx,aby=bx-ax,by-ay;ab2=abx**2+aby**2
    if ab2<1e-20:return 0.0,a
    for i in range(a,b+1):
        t=max(0,min(1,((ux[i]-ax)*abx+(uy[i]-ay)*aby)/ab2))
        d=np.hypot(ux[i]-(ax+t*abx),uy[i]-(ay+t*aby))
        if d>md:md,mi=d,i
    return md,mi

def rot90(x,y):return -y,x
def closed_f(ki):
    sx=ux[ki];sy=uy[ki]
    return rot90(np.concatenate([sx,sx[::-1]]),np.concatenate([sy,-sy[::-1]]))

def compute_greedy_inflections(max_period, max_pts=800):
    anc=[0]
    for q in range(2,max_period+1):
        for p in range(1,q):
            if coprime(p,q):
                th=2*np.pi*p/q;ci=inv_cardioid(th)
                if 0<th<np.pi and ci.imag<=0:
                    anc.append(int(np.argmin(np.hypot(ux-ci.real,uy+ci.imag))))
    anc.append(N_half-1);anc=sorted(set(anc))
    M=len(anc)
    
    k=list(anc);history=[]
    while len(k)*2<max_pts and len(k)*2<N_half:
        ki=sorted(k);wd,ws,worst_mi=0,0,0
        for s in range(len(ki)-1):
            d,mi=seg_dev(ki[s],ki[s+1])
            if d>wd:wd,ws,worst_mi=d,s,mi
        history.append((len(k)*2,wd))
        if wd<5e-5:break
        k.append(worst_mi)
    
    # 拐点
    inflections=[]
    for i in range(5,len(history)-5):
        b5,b0,b_p5=history[i-5][1],history[i][1],history[i+5][1]
        sb,sa=(b5-b0)/5,(b0-b_p5)/5
        ratio=abs(sb/sa) if sa>0 else 999
        if ratio>3:inflections.append(history[i][0])
    
    major_inf=[]
    if inflections:
        major_inf=[inflections[0]]
        for i in range(1,len(inflections)):
            if inflections[i]-inflections[i-1]>2:
                major_inf.append(inflections[i])
    
    return M,anc,major_inf,history

# 9个特殊M → 对应period
# M→period映射 (from data)
M_to_period={2:2,4:4,7:6,10:7,12:8,15:9,30:13,71:21,101:25}

cases=[
    (M_to_period[2],  'M=2 极简种子\n2 anchors, 13拐'),
    (M_to_period[4],  'M=4 最少拐点\n4 anchors, 11拐, 最长尾140pt'),
    (M_to_period[7],  'M=7 素数\n7 anchors, 16拐'),
    (M_to_period[10], 'M=10 最多拐点\n10 anchors, 20拐, 最早收敛542pt'),
    (M_to_period[12], 'M=12 基准序列\n12 anchors, 19拐, OEIS候选'),
    (M_to_period[15], 'M=15 效率冠军\n15 anchors, 17拐, 尾段仅24pt'),
    (M_to_period[30], 'M=30 末拐最早\n30 anchors, 15拐, 末拐470'),
    (M_to_period[71], 'M=71 绝对最少\n71 anchors, 10拐, 素数'),
    (M_to_period[101],'M=101 最大首拐\n101 anchors, 11拐, 素数'),
]

# 背景轮廓
bfx,bfy=closed_f(range(N_half))

fig,axes=plt.subplots(3,3,figsize=(24,18))
axes=axes.flatten()

for idx,(max_period,title) in enumerate(cases):
    ax=axes[idx]
    M,anc_idx,major_inf,hist=compute_greedy_inflections(max_period)
    
    # 背景
    ax.fill(bfx,bfy,color='#4ecdc4',alpha=0.12,edgecolor='none')
    
    # Farey锚点: 金色菱形
    anchor_rot_x=[-uy[i] for i in anc_idx]
    anchor_rot_y=[ux[i] for i in anc_idx]
    ax.scatter(anchor_rot_x,anchor_rot_y,marker='D',c='#FFD700',s=45,
               edgecolors='#B8860B',linewidths=0.8,zorder=8,alpha=0.9)
    
    # 拐点: 红圈
    if major_inf:
        # 从拐点序列回推顶点索引
        # major_inf是顶点总数, 需要映射回上半平面索引
        # 顶点总数=M*2+greedy, 每条拐点=顶点总数/2-M 就是greedy索引
        # 但更难的是回推贪心插入路径
        # 简化: 标明拐点位置——拐点对应history中的特定idx
        # 拐点顶点数/2 是上半平面的点序
        inf_upper=[n//2-M for n in major_inf if n//2>=M]
        # 实际上我们需要插入路径。让我直接从贪婪路径取
        # 重建贪婪到最大拐点
        k=list(anc_idx)
        greedy_added=[]
        while len(k)*2<max(major_inf) and len(k)*2<N_half:
            ki=sorted(k);wd,ws,worst_mi=0,0,0
            for s in range(len(ki)-1):
                d,mi=seg_dev(ki[s],ki[s+1])
                if d>wd:wd,ws,worst_mi=d,s,mi
            if wd<5e-5:break
            k.append(worst_mi)
            greedy_added.append(worst_mi)
        
        # 拐点对应的插入时刻 (顶点数)
        inf_times=set(major_inf)
        inf_pts=set()
        cur_pts=M*2
        for gi in greedy_added:
            cur_pts+=2
            if cur_pts in inf_times:
                inf_pts.add(gi)
        
        inf_rx=[-uy[i] for i in inf_pts]
        inf_ry=[ux[i] for i in inf_pts]
        ax.scatter(inf_rx,inf_ry,marker='o',c='#e74c3c',s=30,
                   edgecolors='#922b21',linewidths=0.6,zorder=7,alpha=0.85)
    
    # 轮廓线
    bk=sorted(set(list(anc_idx)))
    bx,by=closed_f(bk)
    ax.plot(bx,by,'-',color='#2980b9',lw=0.8,alpha=0.5)
    ax.plot(bfx,bfy,'lightblue',lw=0.2,alpha=0.25)
    
    ax.set_aspect('equal')
    ax.set_title(title,fontsize=10,fontweight='bold')
    ax.grid(True,alpha=0.06)
    ax.set_xticks([]);ax.set_yticks([])

fig.suptitle('逆M水滴 9种特殊M：Farey锚点(金◆) + 贪婪拐点(红●)',fontsize=14,fontweight='bold',y=0.995)
plt.tight_layout(rect=[0,0,1,0.97])

out=os.path.join(this_dir,'droplet_9special_compare.png')
fig.savefig(out,dpi=150,bbox_inches='tight')
plt.close(fig)
print(f'✅ {out}')
for mp,title in cases:
    M,anc,major_inf,hist=compute_greedy_inflections(mp)
    print(f'M={M:>3d} (1-{mp:>2d}): {len(major_inf)}拐点 末拐={major_inf[-1] if major_inf else 0}')
