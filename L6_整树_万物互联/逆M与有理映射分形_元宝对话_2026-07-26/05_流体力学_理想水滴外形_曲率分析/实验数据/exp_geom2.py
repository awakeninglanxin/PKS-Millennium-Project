"""
逆 M 主边界 vs 经典水滴形 — 几何定量对比 (clean)
==================================================
提取逆 M 主边界 (标准 M cardioid 经 1/c 映射)
对比: von Karman / Joukowski / Natural Droplet / Tuna
指标: Hausdorff / 厚度分布 / 曲率 / 解析拟合
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial.distance import directed_hausdorff
from scipy.interpolate import splprep, splev, interp1d
from scipy.optimize import least_squares
import json, warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
print("=" * 65)
print("  逆 M Boundary vs Classical Droplet Shapes")
print("=" * 65)

# ============================================================
# 1. 逆 M 主边界 (解析法)
# ============================================================
print("\n[1] 逆 M 主边界: c_inv = 1/(0.5*exp(iθ) - 0.25*exp(2iθ))")
theta = np.linspace(0, 2*np.pi, 20000, endpoint=False)
c_std = 0.5*np.exp(1j*theta) - 0.25*np.exp(2j*theta)
c_inv = 1.0 / c_std

# 包围盒
x_min, x_max = c_inv.real.min(), c_inv.real.max()
y_min, y_max = c_inv.imag.min(), c_inv.imag.max()
print(f"    包围盒: x=[{x_min:.3f},{x_max:.3f}], y=[{y_min:.3f},{y_max:.3f}]")

# 归一化: x→[0,1], y 中心化后按比例
inv_x = (c_inv.real - x_min) / (x_max - x_min)
inv_y = (c_inv.imag - (y_min+y_max)/2) / ((y_max-y_min)/2)
inv_curve = np.column_stack([inv_x, inv_y])

# 弧长参数化
arc = np.zeros(len(inv_curve))
for i in range(1,len(inv_curve)):
    arc[i] = arc[i-1]+np.linalg.norm(inv_curve[i]-inv_curve[i-1])
arc/=arc[-1]

# ============================================================
# 2. 经典水滴形
# ============================================================
print("\n[2] 生成经典水滴形...")

def align(curve):
    """最左点→(0,0), 长轴→x轴, x归一化[0,1], y保持aspect"""
    # 找最左点
    idx=np.argmin(curve[:,0])
    # 旋转使最左点附近切线水平
    half=8
    idxs=np.arange(max(0,idx-half),min(len(curve),idx+half+1))
    dx=curve[idxs,0].mean()-curve[idx,0]
    dy=curve[idxs,1].mean()-curve[idx,1]
    ang=np.arctan2(dy,dx)
    R=np.array([[np.cos(-ang),-np.sin(-ang)],[np.sin(-ang),np.cos(-ang)]])
    c=curve@R.T
    c[:,0]-=c[:,0].min()
    c[:,0]/=c[:,0].max()
    y_rng=c[:,1].max()-c[:,1].min()
    if y_rng>0: c[:,1]/=(y_rng/2)
    return c

# --- von Karman ---
# 用参数化: x = L*cos(θ), r = R*sin(θ)*(1+a*cos(θ))
L_vk,R_vk,a_vk=0.8,0.5,0.15
th_vk=np.linspace(0,np.pi,5000)
x_vk=L_vk*np.cos(th_vk)
r_vk=R_vk*np.sin(th_vk)*(1+a_vk*np.cos(th_vk))
# 加尾部
tail_mask=x_vk>L_vk*0.85
r_vk[tail_mask]*=np.linspace(1,0.3,sum(tail_mask))
upper_vk=np.column_stack([x_vk,r_vk])
lower_vk=np.column_stack([x_vk[::-1],-r_vk[::-1]])
vk_full=np.vstack([upper_vk,lower_vk[1:]])
# 归一化
vk_full[:,0]=(vk_full[:,0]-vk_full[:,0].min())/(vk_full[:,0].max()-vk_full[:,0].min())
vk_full[:,1]*=0.8
vk_curve=align(vk_full)
print(f"    von Karman: L={L_vk}, R={R_vk}, a={a_vk}")

# --- Joukowski 对称 (椭圆) ---
a_jk=2.0
th_jk=np.linspace(0,2*np.pi,5000)
x_jk=0.5*(a_jk+1.0/a_jk)*np.cos(th_jk)
y_jk=0.5*(a_jk-1.0/a_jk)*np.sin(th_jk)
jk_full=np.column_stack([x_jk,y_jk])
jk_full[:,0]=(jk_full[:,0]-jk_full[:,0].min())/(jk_full[:,0].max()-jk_full[:,0].min())
jk_full[:,1]*=0.6
jk_curve=align(jk_full)
print(f"    Joukowski:  a={a_jk} (椭圆)")

# --- Natural Droplet (Worthington/Grace-Mari) ---
x_nd=np.linspace(0,1.0,5000)
r_nd=np.zeros(5000)
# 前端圆弧
mask_f=x_nd<=0.5
r_nd[mask_f]=0.18*np.sqrt(np.maximum(1-((x_nd[mask_f]-0.30)/0.20)**2,0))
# 尾部指数
mask_b=x_nd>0.5
r_nd[mask_b]=0.16*np.exp(-3.0*(x_nd[mask_b]-0.5)/0.5)
upper_nd=np.column_stack([x_nd,r_nd])
lower_nd=np.column_stack([x_nd[::-1],-r_nd[::-1]])
nd_full=np.vstack([upper_nd,lower_nd[1:]])
nd_full[:,0]=(nd_full[:,0]-nd_full[:,0].min())/(nd_full[:,0].max()-nd_full[:,0].min())
nd_full[:,1]*=0.9
nd_curve=align(nd_full)
print(f"    Natural Droplet: 前端R=0.18, 尾exp衰减")

# --- Tuna (鱼形) ---
x_tu=np.linspace(0,1.0,5000)
r_tu=np.zeros(5000)
mask_t1=x_tu<=0.35
r_tu[mask_t1]=0.18*np.sqrt(np.maximum(1-((x_tu[mask_t1]-0.15)/0.25)**2,0))
mask_t2=x_tu>0.35
r_tu[mask_t2]=0.18*np.exp(-4.0*(x_tu[mask_t2]-0.35)/0.65)
r_tu+=0.02*np.exp(-0.5*((x_tu-0.40)/0.15)**2)
upper_tu=np.column_stack([x_tu,r_tu])
lower_tu=np.column_stack([x_tu[::-1],-r_tu[::-1]])
tu_full=np.vstack([upper_tu,lower_tu[1:]])
tu_full[:,0]=(tu_full[:,0]-tu_full[:,0].min())/(tu_full[:,0].max()-tu_full[:,0].min())
tu_full[:,1]*=0.85
tu_curve=align(tu_full)
print(f"    Tuna: 经验公式 (fish hydrodynamics)")

# ============================================================
# 3. 对齐 + 统一
# ============================================================
print("\n[3] 对齐 + 量化...")

curves={
    'Inverse M':inv_curve,
    'von Karman':vk_curve,
    'Joukowski':jk_curve,
    'Natural':nd_curve,
    'Tuna':tu_curve,
}

def hausdorff(a,b):
    return max(directed_hausdorff(a,b)[0],directed_hausdorff(b,a)[0])

names=list(curves.keys())
N=len(names)

# Hausdorff 矩阵
H=np.zeros((N,N))
for i in range(N):
    for j in range(N):
        H[i,j]=hausdorff(curves[names[i]],curves[names[j]])

print(f"\n    Hausdorff 距离矩阵:")
fmt=f"    {'':<14s}"+''.join(f'{n[:10]:>10s}' for n in names)
print(fmt)
for i,n1 in enumerate(names):
    row=f"    {n1:<14s}"
    for j in range(N):
        row+=f'{H[i,j]:>10.4f}'
    print(row)

# 逆 M vs 其他
print(f"\n    逆 M 相似度排名:")
sim=[(n,H[0,i]) for i,n in enumerate(names) if i>0]
sim.sort(key=lambda x:x[1])
for n,d in sim:
    print(f"      {n:<14s}: {d:.4f}")

# ============================================================
# 4. 几何指标
# ============================================================
print("\n[4] 几何指标...")

def curvature(curve):
    dx=np.gradient(curve[:,0]);dy=np.gradient(curve[:,1])
    ddx=np.gradient(dx);ddy=np.gradient(dy)
    k=(dx*ddy-dy*ddx)/(dx**2+dy**2+1e-12)**1.5
    from scipy.ndimage import uniform_filter1d
    return uniform_filter1d(np.nan_to_num(k,0),size=20,mode='wrap')

def thickness_dist(curve,n_bins=50):
    x=curve[:,0];y=np.abs(curve[:,1])
    bins=np.linspace(0,1,n_bins+1)
    centers=(bins[:-1]+bins[1:])/2
    r=[]
    for i in range(n_bins):
        m=(x>=bins[i])&(x<bins[i+1])
        r.append(y[m].max() if m.any() else 0)
    return centers,np.array(r)

def aspect(c): 
    return (c[:,0].max()-c[:,0].min())/max(c[:,1].max()-c[:,1].min(),1e-9)

metrics={}
for n,c in curves.items():
    k=curvature(c)
    # 前端曲率 (最左点附近)
    idx=np.argmin(c[:,0])
    front_k=np.abs(k[idx])
    # 最大厚度位置
    max_y=np.argmax(np.abs(c[:,1]))
    thick_x=c[max_y,0]
    thick_max=np.abs(c[:,1]).max()
    # 面积 (鞋带公式)
    area=0.5*abs(sum(c[i,0]*c[(i+1)%len(c),1]-c[(i+1)%len(c),0]*c[i,1] for i in range(len(c))))
    # 周长
    perim=sum(np.linalg.norm(c[(i+1)%len(c)]-c[i]) for i in range(len(c)))
    metrics[n]={
        'aspect_ratio':float(aspect(c)),
        'front_curvature':float(front_k),
        'max_thickness_x':float(thick_x),
        'max_thickness':float(thick_max),
        'perimeter':float(perim),
        'area':float(area),
    }

print(f"\n    {'形状':<14s} {'长宽比':>8s} {'前端曲率':>10s} {'厚x':>8s} {'厚max':>8s} {'周长':>8s} {'面积':>8s}")
print(f"    {'-'*70}")
for n in names:
    m=metrics[n]
    print(f"    {n:<14s} {m['aspect_ratio']:>8.2f} {m['front_curvature']:>10.3f} {m['max_thickness_x']:>8.3f} {m['max_thickness']:>8.3f} {m['perimeter']:>8.3f} {m['area']:>8.3f}")

# 厚度分布
thicknesses={}
for n,c in curves.items():
    xc,r=thickness_dist(c)
    thicknesses[n]=(xc,r)

# ============================================================
# 5. 解析拟合 (逆 M → 参数曲线)
# ============================================================
print("\n[5] 逆 M 边界 → 参数拟合...")

inv_upper=inv_curve[inv_curve[:,1]>=0]
# 参数形式: x=a*cos(t)+d, y=b*sin(t)*(1+c*cos(t))+e
t_param=np.linspace(0,np.pi,len(inv_upper))

def param_curve(t,a,b,c,d,e):
    return np.column_stack([a*np.cos(t)+d,b*np.sin(t)*(1+c*np.cos(t))+e])

def residuals(params):
    fit=param_curve(t_param,*params)
    return np.sqrt((fit[:,0]-inv_upper[:,0])**2+(fit[:,1]-inv_upper[:,1])**2)

res_fit=least_squares(residuals,[0.5,0.3,0.2,0.0,0.0],max_nfev=20000)
a_f,b_f,c_f,d_f,e_f=res_fit.x
fit_curve=param_curve(t_param,*res_fit.x)
err=np.sqrt((fit_curve[:,0]-inv_upper[:,0])**2+(fit_curve[:,1]-inv_upper[:,1])**2)
rms=err.mean();mx=err.max()
print(f"    拟合公式: x={a_f:.4f}*cos(t)+{d_f:.4f}")
print(f"              y={b_f:.4f}*sin(t)*(1+{c_f:.4f}*cos(t))+{e_f:.4f}")
print(f"    RMS 误差: {rms:.6f}")
print(f"    最大误差: {mx:.6f}")

# ============================================================
# 6. 可视化
# ============================================================
print("\n[6] 绘图...")
palette={'Inverse M':'#FF5722','von Karman':'#2196F3','Joukowski':'#4CAF50',
          'Natural':'#FFC107','Tuna':'#9C27B0'}

# 图1: 五条曲线叠加
fig1,ax1=plt.subplots(figsize=(14,9),facecolor='black')
for n,c in curves.items():
    ax1.plot(c[:,0],c[:,1],color=palette[n],lw=2.5,label=n)
    ax1.plot(c[:,0],-c[:,1],color=palette[n],lw=1.2,alpha=0.4)
ax1.set_xlabel('Normalized x (front→tail)',fontsize=13)
ax1.set_ylabel('Normalized y (half-thickness)',fontsize=13)
ax1.set_title('Aligned Droplet Shapes — Overlay\nAll: front at x=0, unit length, aspect preserved',
              fontsize=14,color='white')
ax1.legend(fontsize=12,facecolor='black',edgecolor='white',labelcolor='white',loc='upper right')
ax1.tick_params(colors='white');ax1.set_facecolor('#080808')
ax1.grid(True,alpha=0.1,color='white');ax1.set_aspect('equal')
plt.tight_layout()
plt.savefig('/data/workspace/shapes_overlay.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ shapes_overlay.png")

# 图2: 厚度分布
fig2,ax2=plt.subplots(figsize=(12,8),facecolor='black')
for n,(xc,r) in thicknesses.items():
    ax2.plot(xc,r,color=palette[n],lw=2.5,label=n)
ax2.set_xlabel('Normalized x',fontsize=13);ax2.set_ylabel('Half-thickness r(x)',fontsize=13)
ax2.set_title('Thickness Distribution r(x) — Key for drag prediction',
              fontsize=14,color='white')
ax2.legend(fontsize=12,facecolor='black',edgecolor='white',labelcolor='white')
ax2.tick_params(colors='white');ax2.set_facecolor('#080808')
ax2.grid(True,alpha=0.1,color='white')
plt.tight_layout()
plt.savefig('/data/workspace/thickness_dist.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ thickness_dist.png")

# 图3: Hausdorff 热图
fig3,ax3=plt.subplots(figsize=(10,8),facecolor='black')
im=ax3.imshow(H,cmap='YlOrRd',origin='lower')
ax3.set_xticks(range(N));ax3.set_yticks(range(N))
ax3.set_xticklabels([n[:10] for n in names],rotation=35,ha='right',fontsize=11)
ax3.set_yticklabels([n[:14] for n in names],fontsize=11)
for i in range(N):
    for j in range(N):
        c='black' if H[i,j]<np.mean(H) else 'white'
        ax3.text(j,i,f'{H[i,j]:.3f}',ha='center',va='center',color=c,fontsize=9)
ax3.set_title('Hausdorff Distance Matrix\nLower = More Similar',fontsize=14,color='white')
plt.colorbar(im,ax=ax3,shrink=0.8)
ax3.tick_params(colors='white');ax3.set_facecolor('black')
plt.tight_layout()
plt.savefig('/data/workspace/hausdorff_hm.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ hausdorff_hm.png")

# 图4: 曲率
fig4,ax4=plt.subplots(figsize=(12,8),facecolor='black')
for n,c in curves.items():
    k=curvature(c);arclen=np.linspace(0,1,len(k))
    mask=k!=0
    ax4.semilogy(arclen[mask],np.abs(k[mask])+1e-10,color=palette[n],lw=1.5,label=n,alpha=0.8)
ax4.set_xlabel('Arc length',fontsize=13);ax4.set_ylabel('|Curvature| (log)',fontsize=13)
ax4.set_title('Curvature Distribution — Nose sharpness & tail convergence',
              fontsize=14,color='white')
ax4.legend(fontsize=11,facecolor='black',edgecolor='white',labelcolor='white')
ax4.tick_params(colors='white');ax4.set_facecolor('#080808')
ax4.grid(True,alpha=0.1,color='white')
plt.tight_layout()
plt.savefig('/data/workspace/curvature.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ curvature.png")

# 图5: 解析拟合
fig5,ax5=plt.subplots(figsize=(10,8),facecolor='black')
ax5.plot(inv_upper[:,0],inv_upper[:,1],'o',color='#FF5722',ms=2,label='Inverse M (data)',alpha=0.5)
ax5.plot(fit_curve[:,0],fit_curve[:,1],'-',color='cyan',lw=2.5,label='Parametric fit')
ax5.set_xlabel('x');ax5.set_ylabel('y')
ax5.set_title(f'Inverse M → Parametric Fit\nRMS={rms:.6f}  Max={mx:.6f}',
              fontsize=13,color='white')
ax5.legend(fontsize=12,facecolor='black',edgecolor='white',labelcolor='white')
ax5.tick_params(colors='white');ax5.set_facecolor('#080808')
ax5.grid(True,alpha=0.1,color='white');ax5.set_aspect('equal')
plt.tight_layout()
plt.savefig('/data/workspace/parametric_fit.png',dpi=150,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ parametric_fit.png")

# 图6: 综合海报
fig6,axes6=plt.subplots(2,3,figsize=(24,15),facecolor='black')
ax=axes6[0][0]
for n,c in curves.items():ax.plot(c[:,0],c[:,1],color=palette[n],lw=2,label=n)
ax.set_title('Overlay');ax.legend(fontsize=9);ax.tick_params(colors='white');ax.set_facecolor('#080808');ax.set_aspect('equal')

ax=axes6[0][1]
for n,(xc,r) in thicknesses.items():ax.plot(xc,r,color=palette[n],lw=2,label=n)
ax.set_title('Thickness r(x)');ax.legend(fontsize=9);ax.tick_params(colors='white');ax.set_facecolor('#080808')

ax=axes6[0][2]
im=ax.imshow(H,cmap='YlOrRd',origin='lower')
ax.set_xticks(range(N));ax.set_yticks(range(N))
ax.set_xticklabels([n[:8] for n in names],rotation=35,ha='right',fontsize=9)
ax.set_yticklabels([n[:10] for n in names],fontsize=9)
ax.set_title('Hausdorff');ax.tick_params(colors='white');ax.set_facecolor('black')

ax=axes6[1][0]
for n,c in curves.items():
    k=curvature(c);al=np.linspace(0,1,len(k))
    ax.semilogy(al[k!=0],np.abs(k[k!=0])+1e-10,color=palette[n],lw=1.5,label=n)
ax.set_title('Curvature');ax.legend(fontsize=9);ax.tick_params(colors='white');ax.set_facecolor('#080808')

ax=axes6[1][1];ax.axis('off')
lines=[f"{'Shape':<14s}|{'AR':>6s}|{'FrK':>7s}|{'ThX':>6s}|{'ThM':>6s}"]
lines.append('-'*55)
for n in names:
    m=metrics[n]
    lines.append(f"{n:<14s}|{m['aspect_ratio']:>6.2f}|{m['front_curvature']:>7.3f}|{m['max_thickness_x']:>6.3f}|{m['max_thickness']:>6.3f}")
ax.text(0.02,0.98,'\n'.join(lines),transform=ax.transAxes,color='white',fontsize=11,
         verticalalignment='top',family='monospace',bbox=dict(boxstyle='round',fc='#111',ec='white',alpha=0.9))
ax.set_title('Key Metrics',color='white')

ax=axes6[1][2];ax.axis('off')
lines2=["Verdict:",""]
for n,d in sim:
    lines2.append(f"  {n:<14s}: Hausdorff={d:.4f}")
lines2.append("")
closest=sim[0];farthest=sim[-1]
lines2.append(f"Closest:  {closest[0]} ({closest[1]:.4f})")
lines2.append(f"Farthest: {farthest[0]} ({farthest[1]:.4f})")
lines2.append("")
if closest[1]<0.05:
    lines2.append("✅ GEOMETRICALLY CLOSE (<0.05)")
    lines2.append("  → Strong candidate for hydrodynamic testing")
elif closest[1]<0.10:
    lines2.append("⚠️ Moderate similarity (0.05-0.10)")
    lines2.append("  → Worth CFD validation")
else:
    lines2.append("❌ Limited similarity (>0.10)")
    lines2.append("  → Inverse M may be a NEW shape class")
lines2.append("")
lines2.append(f"Parametric fit: RMS={rms:.6f}")
if rms<0.01:lines2.append("✅ High-precision fit → engineering-ready")
else:lines2.append("⚠️ Moderate fit → refine parametrization")
ax.text(0.02,0.98,'\n'.join(lines2),transform=ax.transAxes,color='white',fontsize=11,
         verticalalignment='top',family='monospace',bbox=dict(boxstyle='round',fc='#111',ec='lime',alpha=0.9))
ax.set_title('Verdict + Next Steps',color='white')

fig6.suptitle('Inverse Mandelbrot Boundary vs Classical Droplet Shapes\nGeometric Comparison for Hydrodynamic Applications',
              fontsize=17,color='white',y=1.005)
plt.tight_layout(rect=[0,0,1,0.97])
plt.savefig('/data/workspace/geometry_poster.png',dpi=130,bbox_inches='tight',facecolor='black')
plt.close()
print("  ✓ geometry_poster.png")

# ============================================================
# 7. 保存
# ============================================================
results={
    'hausdorff_matrix':{names[i]:{names[j]:float(H[i,j]) for j in range(N)} for i in range(N)},
    'metrics':{n:metrics[n] for n in names},
    'similarity_ranking':[{'shape':n,'hausdorff':float(d)} for n,d in sim],
    'parametric_fit':{
        'formula':'x=a*cos(t)+d, y=b*sin(t)*(1+c*cos(t))+e',
        'a':float(a_f),'b':float(b_f),'c':float(c_f),'d':float(d_f),'e':float(e_f),
        'rms_error':float(rms),'max_error':float(mx),
    },
    'verdict':{
        'closest_shape':closest[0],
        'closest_hausdorff':float(closest[1]),
        'farthest_shape':farthest[0],
        'farthest_hausdorff':float(farthest[1]),
        'geometric_close':bool(closest[1]<0.05),
        'moderate_similarity':bool(0.05<=closest[1]<0.10),
        'new_shape_class':bool(closest[1]>=0.10),
        'fit_engineering_ready':bool(rms<0.01),
    },
}
with open('/data/workspace/geometry_results.json','w') as f:json.dump(results,f,indent=2)

import subprocess
subprocess.run(['zip','-j','/data/workspace/geometry_exp.zip',
                '/data/workspace/shapes_overlay.png',
                '/data/workspace/thickness_dist.png',
                '/data/workspace/hausdorff_hm.png',
                '/data/workspace/curvature.png',
                '/data/workspace/parametric_fit.png',
                '/data/workspace/geometry_poster.png',
                '/data/workspace/geometry_results.json',
                '/data/workspace/exp_geom2.py'],check=True)

print(f"\n{'='*65}")
print("  FINAL RESULTS")
print(f"{'='*65}")

print(f"\n  逆 M Hausdorff 排名:")
for n,d in sim:
    flag=" ◀ 最近" if n==closest[0] else ""
    print(f"    {n:<14s}: {d:.4f}{flag}")

v=results['verdict']
print(f"\n  判定:")
if v['geometric_close']:
    print(f"    ✅ 逆 M 与 {closest[0]} 几何接近 (H={closest[1]:.4f} < 0.05)")
    print(f"    → 强烈建议进入 CFD 验证阶段")
elif v['moderate_similarity']:
    print(f"    ⚠️ 中等相似度 (H={closest[1]:.4f}), 值得 CFD 验证")
else:
    print(f"    ❌ 与已知形状差异较大 (H={closest[1]:.4f})")
    print(f"    → 逆 M 可能是一个全新的外形类别!")

print(f"\n  解析拟合 RMS: {rms:.6f}", "✅" if rms<0.01 else "⚠️")

print(f"\n  文件: geometry_exp.zip")
print("  ALL DONE!")
