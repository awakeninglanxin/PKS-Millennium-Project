#!/usr/bin/env python3
"""
Fractal Etalon Mapper — 七族映射路径完整框架
============================================================
将 NLS etalon 频率映射到 Mandelbrot / 逆 Mandelbrot 复平面，
检验是否落在螺旋中心或 bulb 节点上。

路径族：
  A: 对数/倒数族    B: 复指数/相角族    C: 黄金比例/斐波那契族
  D: M 集参数平面族  E: 双频/比率族       F: 分形维数族
  G: Farey/Bulb 中心族 (正 M + 逆 M 反演)

用法：
  python main_framework.py --mode all --etalon-csv organ_etalon_356.csv --map
"""
import argparse, numpy as np, json, csv, os, sys, time
from datetime import datetime
from pathlib import Path

PHI = (1 + 5**0.5) / 2  # 1.618033...
OUT = Path("04_output")

# ═══════════════════ 工具函数 ═══════════════════
def load_etalon(path):
    """加载 organ_etalon CSV (OrganRus, Val1~Val8, Samples)"""
    freqs, rows = [], []
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.reader(f):
            try:
                v = [float(x) for x in r[1:9]]
                if 0.1 < v[0] < 5.0:
                    freqs.append(v[0])
                    rows.append({"name": r[0], "vals": v})
            except: pass
    return np.array(freqs), rows

def norm(arr):
    return (arr - arr.min()) / (arr.max() - arr.min() + 1e-12)

# ═══════════════════ 七族映射路径 ═══════════════════
# 每个族返回 {method: (points_2d, score)}  点数=len(freqs)

def family_A(freqs):
    """A: 对数/倒数族"""
    pts = {}
    pts["A1_reciprocal"] = (np.column_stack([1/freqs, np.zeros_like(freqs)]), 0)
    pts["A2_inv_log"]     = (np.column_stack([1/np.log10(freqs), np.zeros_like(freqs)]), 0)
    pts["A3_log"]         = (np.column_stack([np.log10(freqs), np.zeros_like(freqs)]), 0)
    pts["A4_ln"]          = (np.column_stack([np.log(freqs/freqs[0]), np.zeros_like(freqs)]), 0)
    return pts

def family_B(freqs):
    """B: 复指数/相角族"""
    f_ref = np.median(freqs)
    theta = 2*np.pi*freqs/f_ref
    pts = {}
    pts["B1_phase"]        = (np.column_stack([np.cos(theta), np.sin(theta)]), 0)
    pts["B2_log_spiral"]   = (np.column_stack([np.log(freqs)*np.cos(theta), np.log(freqs)*np.sin(theta)]), 0)
    a, b = 0.1, 2*np.pi/f_ref
    pts["B3_decay_spiral"] = (np.column_stack([np.exp(-a*freqs)*np.cos(b*freqs), np.exp(-a*freqs)*np.sin(b*freqs)]), 0)
    return pts

def family_C(freqs):
    """C: 黄金比例/斐波那契族"""
    k = np.arange(len(freqs))
    pts = {}
    pts["C1_golden_decay"] = (np.column_stack([freqs * PHI**(-k/np.log(len(freqs)+1)), np.zeros_like(freqs)]), 0)
    pts["C2_golden_spiral"]= (np.column_stack([freqs*np.cos(2*np.pi*k/PHI**2), freqs*np.sin(2*np.pi*k/PHI**2)]), 0)
    return pts

def family_D(freqs, rows):
    """D: Mandelbrot 参数平面族"""
    vals = np.array([r["vals"] for r in rows])
    v1, v2 = vals[:,0], vals[:,1]
    pts = {}
    pts["D1_direct"]     = (np.column_stack([v1, v2]), 0)
    pts["D2_normalized"] = (np.column_stack([v1/v1.max(), v2/(np.abs(v2).max()+1e-12)]), 0)
    pts["D3_scaled"]     = (np.column_stack([2*v1/v1.max()-1, 2*v2/(np.abs(v2).max()+1e-12)-1]), 0)
    return pts

def family_E(freqs, rows):
    """E: 双频/比率族"""
    vals = np.array([r["vals"] for r in rows])
    v1, v2, v3, v4 = vals[:,0], vals[:,1], vals[:,2], vals[:,3]
    pts = {}
    pts["E1_ratio"] = (np.column_stack([v1/(v2+1e-12), v3/(v4+1e-12)]), 0)
    pts["E2_delta"] = (np.column_stack([(v2-v1)/(np.abs(v1)+1e-12), (v3-v2)/(np.abs(v2)+1e-12)]), 0)
    return pts

def family_F(freqs, rows):
    """F: 分形维数族（简化 box-counting + 小波近似）"""
    pts = {}
    f = norm(freqs)
    # F1: rolling window variance as wavelet proxy
    win = max(5, len(f)//50)
    w_std = np.array([np.std(f[i:i+win]) for i in range(len(f)-win+1)])
    w_full = np.zeros(len(f))
    w_full[:len(w_std)] = norm(w_std)
    pts["F1_wavelet"] = (np.column_stack([f, w_full]), 0)
    # F2: pointwise fractal dimension estimate
    eps = np.logspace(-3, -0.3, 20); counts = []
    for e in eps:
        bins = np.digitize(f, np.arange(0, 1.1+e, e))
        counts.append(len(set(bins)))
    D = -np.polyfit(np.log(eps), np.log(counts), 1)[0]
    pts["F2_box_count"] = (np.column_stack([f, np.full_like(f, D)]), 0)
    return pts

def family_G(freqs, rows):
    """G: Farey/Bulb 中心族 (Bulb解析解 + Newton法 + Moebius反演)"""
    pts = {}
    vals = np.array([r["vals"] for r in rows])
    v1 = vals[:, 0]
    
    # G1: 正M Bulb中心 — Douady-Hubbard 周期2 bulb c=-1 (最近似)
    bulb_c = complex(-1.0, 0.0)  # period-2 bulb center (exact)
    # Newton refine: zn+1 = zn - (zn^2+zn-P)/(2zn+1)
    dists_g1 = []
    for f in v1:
        c = complex(f/np.max(v1)*2 - 3, 0)  # 频率→复平面左边缘 [-3, -1]
        # 迭代逃逸检测
        z = 0+0j; esc = False
        for _ in range(100):
            z = z*z + c
            if abs(z) > 2: esc = True; break
        dists_g1.append(abs(c - bulb_c) if not esc else 999)
    pts["G1_bulb_center"] = (np.column_stack([v1/np.max(v1)*2-3, np.zeros_like(v1)]), 
                              np.mean(np.array(dists_g1) < 0.5))
    
    # G2: Moebius反演: w=1/c → 逆M坐标
    inv_cs = []
    for c_real in v1/np.max(v1)*2-3:
        if abs(c_real) > 0.001:
            w = 1.0 / complex(c_real, 0)
            inv_cs.append([w.real, w.imag])
        else:
            inv_cs.append([999, 0])
    inv_arr = np.array(inv_cs)
    pts["G2_inverse_bulb"] = (inv_arr, 
                               np.mean(np.abs(inv_arr[:,0]) < 1.0))
    return pts

# ═══════════════════ 命中率计算 ═══════════════════
def hit_rate(points_2d, method, threshold=0.3):
    """计算特征点落在M集内部区域的比例（简化：到bulb中心距离）"""
    centers = {"G1_bulb_center": (-1.0, 0.0), "G2_inverse_bulb": (-0.5, 0.0),
               "C2_golden_spiral": (-0.75, 0.0), "D3_scaled": (-0.75, 0.0)}
    cx, cy = centers.get(method, (-0.75, 0.0))
    dist = np.sqrt((points_2d[:,0] - cx)**2 + (points_2d[:,1] - cy)**2)
    return np.mean(dist < threshold)

# ═══════════════════ AutoDL 智能管理 ═══════════════════
class AutoDLManager:
    def __init__(self): self.t0 = time.time(); self.has_gpu = False
    def detect(self):
        try: import torch; self.has_gpu = torch.cuda.is_available()
        except: pass
        s = "🖥️ GPU" if self.has_gpu else "💻 CPU"
        print(f"\n{s}模式 | 计时开始 {datetime.now().strftime('%H:%M:%S')}")
    def pack(self, out_dir=OUT):
        import zipfile
        zipf = out_dir / "autodl_results.zip"
        with zipfile.ZipFile(zipf, 'w') as zf:
            for f in out_dir.glob("*"):
                if f.name != zipf.name: zf.write(f, f.name)
        print(f"📦 打包完成: {zipf}  ({zipf.stat().st_size/1024:.0f}KB)")
    def elapsed(self): return time.time() - self.t0

# ═══════════════════ 主入口 ═══════════════════
def main():
    ap = argparse.ArgumentParser(description="Fractal Etalon Mapper")
    ap.add_argument("--mode", default="all", choices=["all","fractal","map"])
    ap.add_argument("--etalon-csv", default="organ_etalon_356.csv")
    ap.add_argument("--map", action="store_true", help="运行七族映射")
    ap.add_argument("--map-method", default="", help="单条路径 (G1_bulb_center)")
    ap.add_argument("--resolution", type=int, default=4096)
    ap.add_argument("--timeout", type=int, default=60, help="超时(分钟)")
    ap.add_argument("--no-shutdown", action="store_true")
    args = ap.parse_args()

    auto = AutoDLManager()
    auto.detect()
    OUT.mkdir(exist_ok=True)

    freqs, rows = load_etalon(args.etalon_csv)
    print(f"✅ 加载 {len(freqs)} 器官频率  range={freqs.min():.3f}~{freqs.max():.3f} GHz\n")

    if not args.map: return

    # ──── 七族全跑 ────
    families = {
        "A": family_A(freqs), "B": family_B(freqs),
        "C": family_C(freqs), "D": family_D(freqs, rows),
        "E": family_E(freqs, rows), "F": family_F(freqs, rows),
        "G": family_G(freqs, rows),
    }

    all_methods = []
    for name, fam in families.items():
        for method, (pts, pscore) in fam.items():
            if args.map_method and method != args.map_method: continue
            score = hit_rate(pts, method) if pscore == 0 else pscore
            all_methods.append((method, score, pts))
            print(f"  {method:25s}  hit_rate={score*100:5.1f}%  pts={len(pts)}")

    all_methods.sort(key=lambda x: x[1], reverse=True)

    # ──── 排名 ────
    print("\n" + "="*60)
    print("📊 七族映射路径 命中率排名")
    print("="*60)
    rank = []
    for i, (method, score, pts) in enumerate(all_methods, 1):
        bar = "█"*int(score*50) + "░"*(50-int(score*50))
        print(f"  {i:2d}. {method:25s} {score*100:5.1f}% {bar[:50]}")
        rank.append({"rank": i, "method": method, "hit_rate": round(score*100, 1)})

    # ──── 保存 ────
    json.dump(rank, open(OUT/"hit_ranking.json", "w"), indent=2, ensure_ascii=False)
    np.savez(OUT/"all_points.npz", **{m: p for m, _, p in all_methods})

    # ──── 最佳路径详细 ────
    best_method, best_score, best_pts = all_methods[0]
    np.savetxt(OUT/f"best_{best_method}_points.csv", best_pts, delimiter=",",
               header="x,y", comments="")

    print(f"\n🏆 最佳路径: {best_method} ({best_score*100:.1f}%)")
    print(f"⏱️ 耗时: {auto.elapsed():.1f}s")

    # AutoDL 打包
    auto.pack(OUT)
    if not args.no_shutdown and auto.elapsed() > 2:
        remain = max(0, args.timeout*60 - auto.elapsed())
        print(f"\n⏳ 下载窗口 {remain/60:.0f}min，超时后自动退出")

if __name__ == "__main__":
    main()
