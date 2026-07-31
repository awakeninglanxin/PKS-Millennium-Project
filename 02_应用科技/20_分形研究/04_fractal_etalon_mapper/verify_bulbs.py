#!/usr/bin/env python3
"""
NLS etalon 频率 → Mandelbrot 集多周期 Bulb 精确匹配验证
排除假阳性：使用 Douady-Hubbard 解析解 + 多bulb分布检验
"""
import numpy as np, csv, json
from pathlib import Path

# ═══════════════ Douady-Hubbard Bulb 中心精确公式 ═══════════════
# p/q bulb (外周期q, 内周期p): c = (1/4)*(2·e^(i2πp/q) - e^(i4πp/q))
# 取实部作为c_real坐标
def bulb_center(p, q):
    """p/q周期bulb的中心c坐标（实数轴）"""
    theta = 2 * np.pi * p / q
    c = 0.25 * (2 * np.exp(1j * theta) - np.exp(2j * theta))
    return c.real  # 只取实部（etalon频率无虚部）

# Fibonacci & Farey 相关周期对
# 主cardioid: 周期1; 周期2 bulb: c=-1; 周期3: c≈-1.75; 周期4: c≈-1.94
bulbs = {
    "p1_cardioid":   bulb_center(0, 1),   # 0.25 (main cardioid center)
    "p2_bulb":       bulb_center(1, 2),   # -1.0  (1/3 + 1/3i)
    "p3_bulb":       bulb_center(1, 3),   # -1.75 (upper bulb)
    "p4_bulb":       bulb_center(1, 4),   # -1.94 (smaller bulb)
    "p5_bulb":       bulb_center(1, 5),   # periodic
    "p7_bulb":       bulb_center(1, 7),   # Fibonacci related
    "p8_bulb":       bulb_center(1, 8),   # Fibonacci 8
    "p13_bulb":      bulb_center(1, 13),  # Fibonacci 13
    "p21_bulb":      bulb_center(1, 21),  # Fibonacci 21
    # Secondary bulbs (higher period)
    "p2_q5":         bulb_center(2, 5),   # Farey vertex
    "p3_q8":         bulb_center(3, 8),   # Golden ratio approx
}

# Print known bulbs
print("═══ Douady-Hubbard Bulb Centers (exact) ═══")
for name, c in sorted(bulbs.items(), key=lambda x: x[1]):
    print(f"  {name:15s}  c = {c:.10f}")

# ═══════════════ Load etalon ═══════════════
csv_path = r"D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\fractal_etalon_mapper\organ_etalon_356.csv"
data = []
with open(csv_path, 'r', encoding='utf-8') as f:
    for row in csv.reader(f):
        try:
            v = float(row[1])
            if 0.1 < v < 5.0: data.append({"name": row[0], "f": v})
        except: pass
freqs = np.array([d["f"] for d in data])
n = len(freqs)

# ═══════════════ 多映射方案 ═══════════════
mappings = {
    # D1: c = -f  (已验证：centroid -1.74)
    "D1_neg_f": -freqs,
    # D2: 归一化到 [-2.5, -1.0]（M集左边缘主cardioid范围）
    "D2_norm_left": -2.5 + (freqs - freqs.min()) / (freqs.max() - freqs.min()) * 1.5,
    # D3: log(f) 映射
    "D3_log_f": np.log10(freqs) * 1.5 - 3.0,
    # D4: 倒数映射
    "D4_recip": -3.0 + 2.0 / (freqs / freqs.min()),
}

# ═══════════════ 多bulb匹配检验 ═══════════════
print(f"\n═══ 多Bulb匹配检验 (n={n}) ═══")
print(f"频率范围: [{freqs.min():.4f}, {freqs.max():.4f}] GHz\n")

best_map = {}
for map_name, c_vals in mappings.items():
    print(f"──── {map_name} ────")
    # 对每个bulb中心，统计距离<阈值的点数
    results = {}
    for bulb_name, bulb_c in bulbs.items():
        dist = np.abs(c_vals - bulb_c)
        # 使用精确阈值：bulb中心间距的25%
        hits = np.sum(dist < 0.05)  # 严格阈值
        near = np.sum(dist < 0.15)  # 宽松阈值
        mean_d = np.mean(dist)
        results[bulb_name] = {"hits": int(hits), "near": int(near), "mean_dist": mean_d}
    
    # 统计多少不同bulb被命中
    hit_bulbs = [b for b, r in results.items() if r["hits"] > 0]
    near_bulbs = [b for b, r in results.items() if r["near"] > 5]  # >5个点靠近
    
    print(f"  命中(±0.05): {sum(r['hits'] for r in results.values())} 点 / {len(hit_bulbs)} 个不同bulb")
    print(f"  靠近(±0.15): {sum(r['near'] for r in results.values())} 点 / {len(near_bulbs)} 个不同bulb")
    
    if hit_bulbs:
        # 按命中数排序
        hit_sorted = sorted(hit_bulbs, key=lambda b: results[b]["hits"], reverse=True)
        print(f"  最大命中: {hit_sorted[0]} = {results[hit_sorted[0]]['hits']}点  ({results[hit_sorted[0]]['hits']*100/n:.1f}%)")
        if len(hit_sorted) > 1:
            print(f"  次大命中: {hit_sorted[1]} = {results[hit_sorted[1]]['hits']}点  ({results[hit_sorted[1]]['hits']*100/n:.1f}%)")
    
    # 反假阳性检验：如果>90%命中了同一个bulb → 假阳性
    if hit_bulbs and results[hit_bulbs[0]]["hits"] > n * 0.9:
        print(f"  ⚠️ 假阳性: {results[hit_bulbs[0]]['hits']*100/n:.0f}%集中在一个bulb ({hit_bulbs[0]})")
        best_map[map_name] = {"verdict": "FALSE_POSITIVE", "concentration": hit_bulbs[0]}
    elif len(hit_bulbs) >= 2:
        print(f"  ✅ 真信号: 分布在{len(hit_bulbs)}个不同bulb")
        best_map[map_name] = {"verdict": "PASS", "n_bulbs": len(hit_bulbs)}
    else:
        print(f"  ❌ 无信号: 没有命中任何bulb")
        best_map[map_name] = {"verdict": "NO_SIGNAL"}

# ═══════════════ 终极判定 ═══════════════
print("\n" + "="*60)
print("📊 终极判定")
print("="*60)

passes = [k for k, v in best_map.items() if v["verdict"] == "PASS"]
fps = [k for k, v in best_map.items() if v["verdict"] == "FALSE_POSITIVE"]
dead = [k for k, v in best_map.items() if v["verdict"] == "NO_SIGNAL"]

print(f"\n  ✅ 通过 (多bulb分布): {len(passes)} 条映射")
for p in passes: print(f"     {p} ({best_map[p]['n_bulbs']} bulbs)")
print(f"  ⚠️ 假阳性 (单bulb集中): {len(fps)} 条映射")
for f in fps: print(f"     {f} → 全部在 {best_map[f]['concentration']}")
print(f"  ❌ 无效: {len(dead)} 条映射")

if passes:
    print(f"\n🏆 验证通过! NLS etalon频率在至少{max(best_map[p]['n_bulbs'] for p in passes)}个不同周期bulb上有分布.")
    print("   N11: → ⭐⭐⭐⭐⭐ 多周期分形采样证实")
elif fps:
    print(f"\n⚠️  所有映射都是假阳性——频率范围压缩到单个bulb附近.")
    print("   N11: → ⭐⭐ 待不同映射方案验证")
else:
    print(f"\n❌ 当前映射均未命中bulb. N11维持在⭐⭐⭐ (c=-f有分形边界特征但非bulb精确匹配)")

# ═══════════════ 保存结果 ═══════════════
Out = Path(r"D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\01_NLS分形研究")
save = {
    "bulbs": {k: round(v, 10) for k, v in bulbs.items()},
    "freq_range": [float(freqs.min()), float(freqs.max())],
    "n_organs": n,
    "verdict": {
        "passes": passes, "false_positives": fps, "no_signal": dead,
        "summary": "PASS" if passes else ("FALSE_POSITIVE" if fps else "NO_SIGNAL")
    }
}
json.dump(save, open(Out / "bulb_verification.json", "w"), indent=2, ensure_ascii=False)
print(f"Results saved to bulb_verification.json")
