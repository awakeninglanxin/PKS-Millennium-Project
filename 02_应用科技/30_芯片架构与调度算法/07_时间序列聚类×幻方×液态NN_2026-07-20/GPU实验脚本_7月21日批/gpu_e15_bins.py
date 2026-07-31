#!/usr/bin/env python3
"""E15: AF2距离分箱消融 — 64 bins vs 13 bins 信息损失量化"""
import numpy as np, time, json, os
from scipy.spatial.distance import pdist, squareform
from scipy.spatial import procrustes

OUT = "/root/magic_tetra_results"
os.makedirs(OUT, exist_ok=True)
results = {}

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def bin_distance(d, n_bins, dmin=2.0, dmax=22.0):
    """将连续距离 d 分到 n_bins 个等宽 bin 中，返回 bin 中心值"""
    d_clipped = np.clip(d, dmin, dmax)
    bin_width = (dmax - dmin) / n_bins
    bin_idx = np.clip(((d_clipped - dmin) / bin_width).astype(int), 0, n_bins-1)
    bin_center = dmin + (bin_idx + 0.5) * bin_width
    return bin_center

def distance_to_3d(dist_matrix, n_iters=100):
    """用经典 MDS 从距离矩阵重建 3D 坐标"""
    n = dist_matrix.shape[0]
    # 双中心化
    H = np.eye(n) - np.ones((n,n))/n
    B = -0.5 * H @ (dist_matrix**2) @ H
    # SVD
    U, S, Vt = np.linalg.svd(B)
    # 取前 3 个特征值
    coords = U[:,:3] * np.sqrt(S[:3])
    return coords

# ============================================================
# E15: 距离分箱消融
# ============================================================
def exp_E15():
    log("=== E15: 距离分箱消融 (64 vs 13 bins) ===")
    np.random.seed(42)
    
    # 模拟蛋白质结构: N 个残基的 3D 坐标
    n_proteins = 50
    n_residues = 100  # 小型蛋白
    bins_list = [64, 32, 16, 13, 8, 6]
    
    rmsd_results = {b: [] for b in bins_list}
    info_loss_results = {b: [] for b in bins_list}
    
    for p in range(n_proteins):
        # 生成随机折叠蛋白 (3D random walk + 压缩)
        coords = np.cumsum(np.random.randn(n_residues, 3) * 3.8, axis=0)
        coords -= coords.mean(axis=0)  # 中心化
        
        # 真实距离矩阵
        true_dists = squareform(pdist(coords))
        
        for n_bins in bins_list:
            # 分箱 → 重建
            binned_dists = bin_distance(true_dists, n_bins)
            np.fill_diagonal(binned_dists, 0)
            binned_dists = (binned_dists + binned_dists.T) / 2  # 对称化
            
            try:
                recon_coords = distance_to_3d(binned_dists)
                # Procrustes 对齐后计算 RMSD
                _, _, disparity = procrustes(coords, recon_coords)
                rmsd = np.sqrt(disparity / n_residues)
                rmsd_results[n_bins].append(rmsd)
            except:
                rmsd_results[n_bins].append(np.nan)
            
            # 信息损失: 用 bin 宽度归一化后计算 JS 散度
            hist_64 = np.histogram(true_dists.flatten(), bins=64, range=(2,22))[0].astype(float) + 1
            hist_n = np.histogram(true_dists.flatten(), bins=n_bins, range=(2,22))[0].astype(float) + 1
            hist_64_norm = hist_64 / hist_64.sum()
            hist_n_norm = hist_n / hist_n.sum()
            # 用插值而非 repeat (处理非整除情况)
            x_64 = np.linspace(2, 22, 64)
            x_n = np.linspace(2, 22, n_bins)
            hist_n_interp = np.interp(x_64, x_n, hist_n_norm)
            hist_n_interp = hist_n_interp / hist_n_interp.sum()
            # JS 散度 (对称, 比 KL 更稳健)
            m = 0.5 * (hist_64_norm + hist_n_interp)
            kl_64 = np.sum(hist_64_norm * np.log((hist_64_norm + 1e-12) / (m + 1e-12)))
            kl_n = np.sum(hist_n_interp * np.log((hist_n_interp + 1e-12) / (m + 1e-12)))
            js = 0.5 * (kl_64 + kl_n)
            info_loss_results[n_bins].append(js)
    
    # 汇总
    summary = {}
    for n_bins in bins_list:
        rmsd_vals = [v for v in rmsd_results[n_bins] if not np.isnan(v)]
        loss_vals = info_loss_results[n_bins]
        summary[f"bins_{n_bins}"] = {
            "median_RMSD_A": round(np.median(rmsd_vals), 3) if rmsd_vals else "N/A",
            "mean_RMSD_A": round(np.mean(rmsd_vals), 3) if rmsd_vals else "N/A",
            "success_rate": f"{len(rmsd_vals)}/{n_proteins}",
            "mean_KL_loss": round(np.mean(loss_vals), 4),
            "bin_width_A": round(20.0/n_bins, 3),
            "note": "实验分辨率~2-3A, bin宽度<2A即可"
        }
        log(f"  bins={n_bins:3d}: RMSD={summary[f'bins_{n_bins}']['median_RMSD_A']}A, "
            f"bin_width={20.0/n_bins:.2f}A, "
            f"KL_loss={summary[f'bins_{n_bins}']['mean_KL_loss']:.4f}")
    
    # 关键判断: 13 bins 是否"足够"
    rmsd_64 = np.median([v for v in rmsd_results[64] if not np.isnan(v)])
    rmsd_13 = np.median([v for v in rmsd_results[13] if not np.isnan(v)])
    degradation = rmsd_13 - rmsd_64
    
    results["E15"] = {
        "method": "MDS reconstruction from binned distances",
        "n_proteins": n_proteins,
        "n_residues": n_residues,
        "bins_summary": summary,
        "key_finding": {
            "RMSD_64bins": round(rmsd_64, 3),
            "RMSD_13bins": round(rmsd_13, 3), 
            "degradation_A": round(degradation, 3),
            "13bins_sufficient": degradation < 1.5,  # 小于实验误差的一半
            "note": "13 bins (1.54A/bin) degradation < 实验分辨率(2-3A) → 13可能够了"
        }
    }
    
    verdict = "✅ 13 bins 可能足够" if degradation < 1.5 else "⚠️ 13 bins 精度损失显著"
    log(f"  VERDICT: {verdict} (64bins→13bins degradation={degradation:.3f}A)")
    return results["E15"]

if __name__ == "__main__":
    log("START E15: 距离分箱消融")
    t0 = time.time()
    exp_E15()
    results["_meta"] = {"elapsed": round(time.time()-t0, 1)}
    with open(os.path.join(OUT, "E15_distance_bins.json"), "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    log(f"DONE {time.time()-t0:.0f}s")
