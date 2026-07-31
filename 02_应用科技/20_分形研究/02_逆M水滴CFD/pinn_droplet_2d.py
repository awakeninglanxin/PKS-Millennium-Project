#!/usr/bin/env python3
"""逆M水滴 PINN (Physics-Informed Neural Networks) — 2D 稳态 Hybrid"""
import numpy as np, os, torch, torch.nn as nn, math, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Device: {device}')

# ═══════ 加载 LBM 参考数据 ═══════
this_dir = os.path.dirname(os.path.abspath(__file__))
data = np.load(os.path.join(this_dir, 'cfd_Greedy_BaseToTip', 'cfd_data.npz'))
vort_lbm = data['vort']; vel_lbm = data['vel']; mask = data['mask']
NX, NY = vel_lbm.shape
print(f'LBM ref: {NX}x{NY}')

# 物理域: 水滴 x∈[-1.33,4], y∈[-1.62,1.62]
# 计算域映射
scale = 150.0 / 5.333; cx0 = int(NX*0.4); cy0 = NY//2
def grid_to_phys(i, j):
    return (i - cx0)/scale, (j - cy0)/scale

# ═══════ PINN 网络 ═══════
class PINN(nn.Module):
    def __init__(self, layers=[2, 64, 64, 64, 64, 3]):
        super().__init__()
        self.net = nn.ModuleList()
        for i in range(len(layers)-1):
            self.net.append(nn.Linear(layers[i], layers[i+1]))
            if i < len(layers)-2:
                self.net.append(nn.Tanh())

    def forward(self, x):
        for layer in self.net:
            x = layer(x)
        # x[:,0]=u, x[:,1]=v, x[:,2]=p
        return x[:,0:1], x[:,1:2], x[:,2:3]

model = PINN().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=500, factor=0.5)

# ═══════ 采样点 ═══════
# 物理域采样: 避开障碍物
n_pde = 3000  # PDE 残差点
n_bc_wall = 1000  # 壁面无滑移
n_bc_inlet = 200  # 入口
n_data = 2000  # LBM 监督点

# 生成水滴轮廓用于壁面采样
def load_greedy_contour():
    pts = np.loadtxt(os.path.join(this_dir, 'droplet_invM_analytic.csv'), delimiter=',', skiprows=1)
    N_half = len(pts)//2; ux, uy = pts[:N_half,0], pts[:N_half,1]
    def coprime(a,b): return math.gcd(a,b)==1
    def inv_cardioid(th):
        return 1.0/(0.5*np.exp(1j*th)-0.25*np.exp(2j*th))
    ancs=set()
    for q in range(2,8):
        for p in range(1,q):
            if coprime(p,q):
                th=2*np.pi*p/q; ci=inv_cardioid(th)
                if 0<th<np.pi and ci.imag<=0:
                    ancs.add(int(np.argmin(np.hypot(ux-ci.real,uy+ci.imag))))
    ancs.add(0); ancs.add(N_half-1)
    def seg_dev(a,b):
        md,mi=0.0,a; ax,ay=ux[a],uy[a]; bx,by=ux[b],uy[b]
        abx,aby=bx-ax,by-ay; ab2=abx**2+aby**2
        if ab2<1e-20: return 0.0,a
        for i in range(a,b+1):
            t=max(0,min(1,((ux[i]-ax)*abx+(uy[i]-ay)*aby)/ab2))
            d=np.hypot(ux[i]-(ax+t*abx),uy[i]-(ay+t*aby))
            if d>md: md,mi=d,i
        return md,mi
    k4=list(ancs)
    while True:
        ki=sorted(k4); wd,ws=0,0
        for s in range(len(ki)-1):
            d,_=seg_dev(ki[s],ki[s+1])
            if d>wd: wd,ws=d,s
        if wd<0.002: break
        a,b=ki[ws],ki[ws+1]; _,wi=seg_dev(a,b); k4.append(wi)
    k4=sorted(set(k4))
    gx=ux[k4]; gy=uy[k4]
    return np.concatenate([gx,gx[::-1],[gx[0]]]), np.concatenate([gy,-gy[::-1],[gy[0]]])

bx, by = load_greedy_contour()

# 采样函数
def sample_wall(n):
    """在壁面上均匀采样"""
    n_seg = len(bx)-1
    # 沿轮廓弧长采样
    seg_lens = np.hypot(np.diff(bx), np.diff(by))
    cum = np.concatenate([[0], np.cumsum(seg_lens)])
    t = np.random.uniform(0, cum[-1], n)
    idx = np.searchsorted(cum, t, side='right') - 1
    idx = np.clip(idx, 0, n_seg-1)
    frac = (t - cum[idx]) / (seg_lens[idx] + 1e-10)
    x = bx[idx] + frac * (bx[idx+1] - bx[idx])
    y = by[idx] + frac * (by[idx+1] - by[idx])
    return x, y

def sample_domain(n, x_range=(-2, 4.5), y_range=(-2, 2)):
    """在计算域均匀采样（避开壁面）"""
    x = np.random.uniform(*x_range, n)
    y = np.random.uniform(*y_range, n)
    # 简单排除: 水滴内部点 (用包围盒近似)
    x_c = np.clip(x, -1.33, 4.0)
    y_abs = np.abs(y)
    # 水滴近似: y^2 < droplet_height(x)
    h = np.interp(x_c, bx[:len(bx)//2], by[:len(by)//2])
    inside = y_abs < h
    # 重采样内部的点
    n_inside = inside.sum()
    if n_inside > 0:
        x[inside] = np.random.uniform(*x_range, n_inside)
        y[inside] = np.random.uniform(*y_range, n_inside)
    return x, y

def sample_inlet(n):
    """入口（左边界 x≈-2，或右边界 x≈4.5）"""
    side = np.random.choice([-2, 4.5], n)
    y = np.random.uniform(-2, 2, n)
    u = np.where(side < 0, 0.05, 0.0)  # 左入口 u=0.05
    return side, y, u, np.zeros(n)

# ═══════ 准备训练张量 ═══════
wall_x, wall_y = sample_wall(n_bc_wall)
wall_pts = torch.tensor(np.column_stack([wall_x, wall_y]), dtype=torch.float32).to(device)

dom_x, dom_y = sample_domain(n_pde)
dom_pts = torch.tensor(np.column_stack([dom_x, dom_y]), dtype=torch.float32).to(device)

# LBM 数据点: 从网格采样
data_ij = np.random.choice(NX*NY, n_data, replace=False)
data_i, data_j = data_ij // NY, data_ij % NY
data_x = np.array([(i - cx0)/scale for i in data_i])
data_y = np.array([(j - cy0)/scale for j in data_j])
data_pts = torch.tensor(np.column_stack([data_x, data_y]), dtype=torch.float32).to(device)
data_u = torch.tensor(vel_lbm[data_i, data_j] * 0.8, dtype=torch.float32).to(device)  # 速度大小参考

# ═══════ 训练 ═══════
print(f'Training PINN: {n_pde} PDE + {n_bc_wall} wall + {n_data} data pts')
losses = []
for epoch in range(5000):
    optimizer.zero_grad()

    # ── PDE loss: NS 残差 (简化 2D 稳态不可压) ──
    dom_pts.requires_grad_(True)
    u, v, p = model(dom_pts)
    # 连续性: ∂u/∂x + ∂v/∂y = 0
    u_x = torch.autograd.grad(u.sum(), dom_pts, create_graph=True)[0][:,0]
    v_y = torch.autograd.grad(v.sum(), dom_pts, create_graph=True)[0][:,1]
    loss_cont = torch.mean((u_x + v_y)**2)

    # 动量 (简化: 仅对流项主导)
    u_y = torch.autograd.grad(u.sum(), dom_pts, create_graph=True)[0][:,1]
    v_x = torch.autograd.grad(v.sum(), dom_pts, create_graph=True)[0][:,0]
    loss_mom = torch.mean(u_y**2 + v_x**2) * 0.01

    loss_pde = loss_cont + loss_mom

    # ── BC loss: 壁面无滑移 ──
    u_w, v_w, _ = model(wall_pts)
    loss_wall = torch.mean(u_w**2 + v_w**2)

    # ── Data loss: LBM 参考 ──
    u_d, v_d, _ = model(data_pts)
    vel_pred = torch.sqrt(u_d**2 + v_d**2).squeeze()
    loss_data = torch.mean((vel_pred - data_u)**2)

    # ── 总损失 ──
    loss = loss_pde + 10*loss_wall + 5*loss_data
    loss.backward()
    optimizer.step()
    scheduler.step(loss)

    if epoch % 500 == 0:
        lr = optimizer.param_groups[0]['lr']
        print(f'  epoch {epoch:>5d} | loss={loss.item():.2e} pde={loss_pde.item():.2e} wall={loss_wall.item():.2e} data={loss_data.item():.2e} lr={lr:.1e}')
    losses.append(loss.item())

# ═══════ 预测 + 可视化 ═══════
print('Predicting flow field...')
res = 200
xs = np.linspace(-2, 4.5, res); ys = np.linspace(-2, 2, res)
X, Y = np.meshgrid(xs, ys)
pts = torch.tensor(np.column_stack([X.ravel(), Y.ravel()]), dtype=torch.float32).to(device)
with torch.no_grad():
    U, V, P = model(pts)
U = U.cpu().numpy().reshape(res, res); V = V.cpu().numpy().reshape(res, res)

# 涡量
uy = np.gradient(U, ys, axis=0)
vx = np.gradient(V, xs, axis=1)
vort_pinn = vx - uy
speed = np.sqrt(U**2 + V**2)

fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

ax = axes[0]
vm = abs(vort_pinn).max() * 0.4
ax.imshow(vort_pinn, cmap='RdBu_r', extent=[-2, 4.5, -2, 2], origin='lower', vmin=-vm, vmax=vm)
ax.plot(bx, by, 'k-', lw=1.5)
ax.set_title('PINN Vorticity (2D steady hybrid)'); ax.set_aspect('equal')

ax = axes[1]
sk = 12; xi = np.arange(0, res, sk); yi = np.arange(0, res, sk)
ax.quiver(X[yi[:,None],xi], Y[yi[:,None],xi],
          U[yi[:,None],xi], V[yi[:,None],xi], scale=1.5, alpha=0.7)
ax.plot(bx, by, 'k-', lw=1.5)
ax.set_title('PINN Velocity Field'); ax.set_aspect('equal'); ax.set_xlim(-2, 4.5)

ax = axes[2]
im = ax.imshow(speed, cmap='hot', extent=[-2, 4.5, -2, 2], origin='lower')
ax.plot(bx, by, 'c-', lw=1.2)
ax.set_title('PINN Speed Magnitude'); ax.set_aspect('equal')
plt.colorbar(im, ax=ax, shrink=0.8)

fig.suptitle('Inverse-M Droplet: PINN 2D Steady Hybrid (LBM-supervised)', fontsize=13, fontweight='bold')
plt.tight_layout()
out = os.path.join(this_dir, 'droplet_pinn_2d_hybrid.png')
fig.savefig(out, dpi=180, bbox_inches='tight'); plt.close(fig)

# 损失曲线
fig2, ax2 = plt.subplots(figsize=(10, 4))
ax2.semilogy(losses)
ax2.set_xlabel('Epoch'); ax2.set_ylabel('Loss')
ax2.set_title('PINN Training Loss'); ax2.grid(True, alpha=0.3)
loss_png = os.path.join(this_dir, 'droplet_pinn_loss.png')
fig2.savefig(loss_png, dpi=120, bbox_inches='tight'); plt.close(fig2)

print(f'✅ {out}')
print(f'✅ {loss_png}')
torch.save(model.state_dict(), os.path.join(this_dir, 'pinn_model.pt'))
print('✅ pinn_model.pt saved')
