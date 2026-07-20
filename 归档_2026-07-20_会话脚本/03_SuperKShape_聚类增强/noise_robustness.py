#!/usr/bin/env python3
"""Sharkovsky-DP & Farey: 噪声鲁棒性验证 (真实场景模拟)
命题: 合成数据上无增益的两个增强 → 噪声/不规则数据上是否能超越 baseline?
"""
import numpy as np, time, os, json, sys
sys.path.insert(0, '/root/super_kshape_work')
from super_kshape import (SuperKShape, generate_synthetic_data, evaluate_clustering,
                          detect_inflections, sharkovsky_rank, sbd)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = '/root/noise_results'
os.makedirs(OUT, exist_ok=True)

def generate_dataset(name, n_series=200, length=128):
    """Generate datasets matching previous GPU experiment types"""
    np.random.seed(hash(name) % 2**32)
    data, labels = [], []
    if name == 'sine_phases':
        templates = [
            lambda t: np.sin(2*np.pi*t*3/length),
            lambda t: 1.5*np.sin(2*np.pi*t*5/length + np.pi/4),
            lambda t: 0.8*np.sin(2*np.pi*t*2/length + np.pi/2),
        ]
    elif name == 'trend_mix':
        templates = [
            lambda t: 0.5*t + np.sin(2*np.pi*t/20),
            lambda t: 3.0 - 0.3*t + np.cos(2*np.pi*t/10),
            lambda t: 2.0 + 1.5*np.sin(2*np.pi*t/8) + 0.1*t,
        ]
    else:  # step_noise
        templates = [
            lambda t: np.where(t < length//2, 1, 3) + np.sin(2*np.pi*t/15)*0.5,
            lambda t: np.where(t < length//3, 2, np.where(t<2*length//3, 0, 4)),
            lambda t: np.where(t < length//4, 0, 5) + np.cos(2*np.pi*t/12),
        ]
    for ci, tmpl in enumerate(templates):
        for _ in range(n_series // 3):
            ts = tmpl(np.arange(length)) + np.random.randn(length)*0.3
            shift = np.random.randint(0, length//6)
            ts = np.roll(ts, shift)
            data.append(ts); labels.append(ci)
    return data, np.array(labels)

# ============================================================
# 噪声策略
# ============================================================
def add_noise(X, sigma):
    """加高斯噪声"""
    return [ts + np.random.randn(len(ts)) * sigma for ts in X]

def add_irregular(X, drop_rate=0.2):
    """随机删除 20% 观测点, 线性插值补回 (模拟不规则采样)"""
    result = []
    for ts in X:
        n = len(ts)
        mask = np.random.random(n) > drop_rate
        if mask.sum() < 3:
            result.append(ts)
            continue
        idx_keep = np.where(mask)[0]
        vals_keep = ts[idx_keep]
        ts_new = np.interp(np.arange(n), idx_keep, vals_keep)
        result.append(ts_new)
    return result

def add_phase_jitter(X, max_shift=5):
    """随机局部拉伸/压缩 (模拟真实传感器时钟漂移)"""
    result = []
    for ts in X:
        n = len(ts)
        t_orig = np.arange(n, dtype=float)
        t_warped = t_orig + np.cumsum(np.random.randn(n) * 0.3)
        t_warped = np.clip(t_warped, 0, n-1)
        ts_new = np.interp(t_orig, t_warped, ts)
        result.append(ts_new)
    return result

# ============================================================
# 实验运行
# ============================================================
NOISE_LEVELS = [
    ("clean", lambda X: X),
    ("noise_0.5", lambda X: add_noise(X, 0.5)),
    ("noise_1.0", lambda X: add_noise(X, 1.0)),
    ("noise_2.0", lambda X: add_noise(X, 2.0)),
    ("irregular", lambda X: add_irregular(X)),
    ("phase_jitter", lambda X: add_phase_jitter(X)),
]

CONFIGS = [
    ("k-Shape baseline", False, False),
    ("+Sharkovsky init", True, False),
    ("+Farey distance", False, True),
]

DATASETS = ['sine_phases', 'trend_mix', 'step_noise']

all_results = {}

print("=" * 60)
print("NOISE ROBUSTNESS: Sharkovsky-DP & Farey vs Baseline")
print("=" * 60)

for ds_name in DATASETS:
    print(f"\n{'='*60}")
    print(f"DATASET: {ds_name}")
    print(f"{'='*60}")
    
    X_clean, y_true = generate_dataset(ds_name, n_series=200, length=128)
    
    for noise_name, noise_fn in NOISE_LEVELS:
        X = noise_fn(X_clean)
        key = f"{ds_name}_{noise_name}"
        
        for cfg_name, use_shark, use_farey in CONFIGS:
            lf = 0.3 if use_farey else 0.0
            model = SuperKShape(k=3, lambda_farey=lf, lambda_anti=0.0,
                               use_magic_decomp=False, use_sharkovsky_init=use_shark,
                               max_iter=30)
            t0 = time.time()
            model.fit(X)
            metrics = evaluate_clustering(y_true, model.labels_)
            elapsed = time.time() - t0
            
            all_results.setdefault(key, {})[cfg_name] = {
                'ARI': metrics['ARI'], 'NMI': metrics['NMI'], 'time': elapsed
            }
            
            delta = "" if cfg_name == "k-Shape baseline" else \
                f" vs baseline ARI={all_results[key]['k-Shape baseline']['ARI']:.3f}"
            print(f"  {noise_name:>15s} {cfg_name:>20s}: ARI={metrics['ARI']:.4f} NMI={metrics['NMI']:.4f} {elapsed:.1f}s{delta}")

# 保存
with open(f'{OUT}/noise_results.json', 'w') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

# ============================================================
# 生成 4 张看板图
# ============================================================
print(f"\n{'='*60}")
print("GENERATING FIGURES")
print(f"{'='*60}")

plt.rcParams.update({'font.size': 9, 'axes.titlesize': 11, 'figure.dpi': 150, 'savefig.dpi': 200})

colors = {'k-Shape baseline': '#888', '+Sharkovsky init': '#2a9d8f', '+Farey distance': '#e9c46a'}

# ---------- Fig 1: 噪声递增曲线 ----------
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for ds_idx, ds_name in enumerate(DATASETS):
    ax = axes[ds_idx]
    clean_configs = ['clean', 'noise_0.5', 'noise_1.0', 'noise_2.0']
    for cfg_name, color in colors.items():
        aris = [all_results[f'{ds_name}_{nc}'][cfg_name]['ARI'] for nc in clean_configs]
        ax.plot(range(4), aris, 'o-', color=color, label=cfg_name, linewidth=2, markersize=7)
    ax.set_xticks(range(4))
    ax.set_xticklabels(['Clean','Sigma=0.5','Sigma=1.0','Sigma=2.0'], fontsize=8)
    ax.set_ylabel('ARI'); ax.set_ylim(0, 1.05)
    ax.set_title(ds_name, fontweight='bold')
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
fig.suptitle('Noise Robustness: ARI vs Gaussian Noise Level\nSharkovsky-DP & Farey vs k-Shape Baseline',
             fontsize=14, fontweight='bold')
plt.tight_layout()
fig.savefig(f'{OUT}/fig1_noise_curves.png', facecolor='white')
plt.close()
print("  fig1: noise curves")

# ---------- Fig 2: 非标准数据 (irregular + jitter) ----------
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for ds_idx, ds_name in enumerate(DATASETS):
    ax = axes[ds_idx]
    scenarios = ['clean', 'irregular', 'phase_jitter']
    x = np.arange(len(scenarios))
    w = 0.25
    for i, (cfg_name, color) in enumerate(colors.items()):
        aris = [all_results[f'{ds_name}_{sc}'][cfg_name]['ARI'] for sc in scenarios]
        ax.bar(x + (i-1)*w, aris, w, color=color, label=cfg_name, edgecolor='white')
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=8)
    ax.set_ylabel('ARI'); ax.set_ylim(0, 1.05)
    ax.set_title(ds_name, fontweight='bold')
    ax.legend(fontsize=7)
fig.suptitle('Non-Standard Data: Irregular Sampling & Phase Jitter\nReal-world simulation (missing data, clock drift)',
             fontsize=14, fontweight='bold')
plt.tight_layout()
fig.savefig(f'{OUT}/fig2_irregular_jitter.png', facecolor='white')
plt.close()
print("  fig2: irregular + jitter")

# ---------- Fig 3: 改善幅度热图 ----------
fig, ax = plt.subplots(figsize=(14, 6))
matrix = np.zeros((len(CONFIGS)-1, 0))
row_labels = [c[0] for c in CONFIGS[1:]]
col_labels = []

for ds_name in DATASETS:
    for noise_name, _ in NOISE_LEVELS:
        key = f"{ds_name}_{noise_name}"
        if key not in all_results: continue
        base_ari = all_results[key]['k-Shape baseline']['ARI']
        col_data = []
        for cfg_name, _, _ in CONFIGS[1:]:
            delta = all_results[key][cfg_name]['ARI'] - base_ari
            col_data.append(delta)
        if matrix.shape[1] == 0:
            matrix = np.array([col_data])
        else:
            matrix = np.vstack([matrix, col_data])
        col_labels.append(f'{ds_name[:5]}\n{noise_name}')

matrix = matrix.T  # rows=enhancements, cols=scenarios

im = ax.imshow(matrix, cmap='RdYlGn', vmin=-0.3, vmax=0.3, aspect='auto')
ax.set_xticks(range(len(col_labels)))
ax.set_xticklabels(col_labels, rotation=45, ha='right', fontsize=6)
ax.set_yticks(range(2))
ax.set_yticklabels(row_labels, fontsize=9)
plt.colorbar(im, ax=ax, label='Delta ARI vs Baseline')
for i in range(2):
    for j in range(len(col_labels)):
        v = matrix[i, j]
        ax.text(j, i, f'{v:+.3f}', ha='center', va='center', fontsize=7,
                fontweight='bold', color='white' if abs(v) > 0.15 else 'black')
ax.set_title('Sharkovsky-DP & Farey: Delta ARI vs Baseline\nGreen=improvement, Red=degradation, White=no change',
             fontweight='bold')
plt.tight_layout()
fig.savefig(f'{OUT}/fig3_delta_heatmap.png', facecolor='white')
plt.close()
print("  fig3: delta heatmap")

# ---------- Fig 4: 综合仪表板 ----------
fig = plt.figure(figsize=(16, 11))
gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)

# Top-left: Best-case gains
ax0 = fig.add_subplot(gs[0, 0])
best_shark = 0; best_farey = 0
best_shark_label = ''; best_farey_label = ''
all_deltas_shark = []; all_deltas_farey = []
for key, configs in all_results.items():
    base = configs['k-Shape baseline']['ARI']
    ds = all_results[key]['+Sharkovsky init']['ARI'] - base
    df = all_results[key]['+Farey distance']['ARI'] - base
    all_deltas_shark.append(ds); all_deltas_farey.append(df)
    if ds > best_shark: best_shark = ds; best_shark_label = key
    if df > best_farey: best_farey = df; best_farey_label = key

ax0.barh([0,1], [best_shark, best_farey], color=['#2a9d8f','#e9c46a'])
ax0.set_yticks([0,1]); ax0.set_yticklabels(['Sharkovsky-DP','Farey Distance'])
ax0.set_xlabel('Max ARI Gain vs Baseline')
ax0.set_title(f'Best-Case Win\nShark: {best_shark:+.3f} ({best_shark_label})\nFarey: {best_farey:+.3f} ({best_farey_label})',
              fontweight='bold', fontsize=9)
for i, (v, label) in enumerate([(best_shark,best_shark_label),(best_farey,best_farey_label)]):
    ax0.text(v+0.01, i, f'{v:+.3f}', va='center', fontweight='bold')

# Top-right: Distribution of deltas
ax1 = fig.add_subplot(gs[0, 1])
ax1.hist(all_deltas_shark, bins=15, alpha=0.7, label='Sharkovsky-DP', color='#2a9d8f')
ax1.hist(all_deltas_farey, bins=15, alpha=0.7, label='Farey Distance', color='#e9c46a')
ax1.axvline(x=0, color='black', linewidth=0.5)
ax1.set_xlabel('ARI Delta vs Baseline')
ax1.set_ylabel('Frequency')
ax1.set_title('Distribution of ARI Gains\n(18 scenarios × 2 enhancements)', fontweight='bold', fontsize=9)
ax1.legend(fontsize=8)

# Bottom: Mean delta by noise type
ax2 = fig.add_subplot(gs[1, :])
noise_types = ['clean','noise_0.5','noise_1.0','noise_2.0','irregular','phase_jitter']
shark_means = []; farey_means = []
for nt in noise_types:
    d1 = [all_results[f'{ds}_{nt}']['+Sharkovsky init']['ARI'] - all_results[f'{ds}_{nt}']['k-Shape baseline']['ARI'] for ds in DATASETS if f'{ds}_{nt}' in all_results]
    d2 = [all_results[f'{ds}_{nt}']['+Farey distance']['ARI'] - all_results[f'{ds}_{nt}']['k-Shape baseline']['ARI'] for ds in DATASETS if f'{ds}_{nt}' in all_results]
    shark_means.append(np.mean(d1) if d1 else 0)
    farey_means.append(np.mean(d2) if d2 else 0)
x = np.arange(len(noise_types)); w = 0.35
ax2.bar(x-w/2, shark_means, w, label='Sharkovsky-DP', color='#2a9d8f', edgecolor='white')
ax2.bar(x+w/2, farey_means, w, label='Farey Distance', color='#e9c46a', edgecolor='white')
ax2.set_xticks(x); ax2.set_xticklabels(noise_types, fontsize=8)
ax2.set_ylabel('Mean ARI Delta vs Baseline')
ax2.axhline(y=0, color='black', linewidth=0.5)
ax2.set_title('Mean ARI Gain by Noise Type (averaged across 3 datasets)', fontweight='bold')
ax2.legend(fontsize=8)
ax2.grid(axis='y', alpha=0.3)

fig.suptitle('Sharkovsky-DP & Farey: Noise Robustness Dashboard\n18 scenarios (3 datasets x 6 noise types) on RTX 4090',
             fontsize=14, fontweight='bold', y=1.01)
fig.savefig(f'{OUT}/fig4_summary_dashboard.png', facecolor='white', dpi=200)
plt.close()
print("  fig4: dashboard")

# ============================================================
# 总结
# ============================================================
print(f"\n{'='*60}")
print("NOISE ROBUSTNESS SUMMARY")
print(f"{'='*60}")

shark_wins = sum(1 for d in all_deltas_shark if d > 0.01)
shark_losses = sum(1 for d in all_deltas_shark if d < -0.01)
farey_wins = sum(1 for d in all_deltas_farey if d > 0.01)
farey_losses = sum(1 for d in all_deltas_farey if d < -0.01)

print(f"  Sharkovsky-DP: {shark_wins} wins (>+0.01), {shark_losses} losses (<-0.01), "
      f"mean delta={np.mean(all_deltas_shark):+.4f}")
print(f"  Farey Distance: {farey_wins} wins (>+0.01), {farey_losses} losses (<-0.01), "
      f"mean delta={np.mean(all_deltas_farey):+.4f}")

# 找出 Sharkovsky 在哪个场景赢了
if best_shark > 0.01:
    print(f"\n  🏆 Sharkovsky-DP WINS on: {best_shark_label} (ΔARI={best_shark:+.4f})")
    print(f"     → 噪声/不规则场景下, 拐点检测的拓扑不变性可能比全序列NCC更鲁棒")
else:
    print(f"\n  ❌ Sharkovsky-DP: no significant wins across 18 scenarios")

if best_farey > 0.01:
    print(f"  🏆 Farey Distance WINS on: {best_farey_label} (ΔARI={best_farey:+.4f})")
else:
    print(f"  ❌ Farey Distance: no significant wins across 18 scenarios")

print(f"\n  Output: {len(os.listdir(OUT))} files in {OUT}/")
for f in sorted(os.listdir(OUT)):
    if f.endswith(('.png','.json')):
        print(f"    {f}")

print(f"\n{'='*60}")
print("DONE")
print(f"{'='*60}")
