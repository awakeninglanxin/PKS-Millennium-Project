"""
egg_coordinate_analysis.py — 蛋形坐标映射 + 谐波分析
=======================================================
将CFD数值结果映射到蛋形曲线的自然坐标系 (s, η):
  s — 沿蛋形曲线的弧长
  η — 从曲线向内/向外的法向距离

============================================
数学原理
============================================

1. 蛋形自然坐标系 (s, η):
   对蛋形曲线 γ(s) = (x(s), y(s)), s 为弧长:
     切向量: T(s) = (dx/ds, dy/ds)
     法向量: N(s) = (-dy/ds, dx/ds) (指向内部)
     曲率: κ(s) = |x'y'' - y'x''|/(x'²+y'²)^(3/2)
   坐标系变换: (x,y) → (s,η), 其中 η 从边界沿法向向内

2. 谐波分析 (FFT):
   对边界切向速度 v_θ(s) 做FFT:
     v̂(f) = ∫ v_θ(s)·e^{-i2πfs} ds
   
   Schauberger假设: 幅值 A_n ∝ 1/n (谐波序列衰减)
   验证: log(A_n) vs log(n) 的斜率 ≈ -1

3. 极性原理:
   Schauberger: p·q = const → v_θ(r)·r = const
   验证: 计算变异系数 σ/μ, < 0.3 则认为成立
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '01_geometry'))
from egg_curve import EggCurve, EggParams


class EggCoordinateMapper:
    """蛋形自然坐标系映射器"""

    def __init__(self, egg_params: EggParams):
        self.egg = EggCurve(egg_params)
        self.ep = egg_params

    def map_to_egg_coords(self, X: np.ndarray, Y: np.ndarray,
                           ux: np.ndarray, uy: np.ndarray,
                           mask: np.ndarray) -> dict:
        """
        将笛卡尔坐标的CFD结果映射到蛋形曲线坐标系

        返回:
            {
                's': 弧长坐标 (沿蛋形曲线),
                'eta': 法向距离 (从边界向内),
                'v_tangential': 沿蛋形曲线的切向速度,
                'v_normal': 法向速度,
                'kappa': 曲率,
                'dist_from_center': 到中心轴的距离,
            }
        """
        # 获取蛋形曲线详细数据
        s_curve, x_curve, y_curve = self.egg.arc_length(2000)
        _, kappa_curve = self.egg.curvature(2000)
        L = s_curve[-1]  # 总弧长

        # 对蛋形曲线上的每个点, 计算切向和法向
        dx = np.gradient(x_curve, s_curve)
        dy = np.gradient(y_curve, s_curve)
        ds_local = np.sqrt(dx**2 + dy**2)
        tx = dx / ds_local  # 切向量x
        ty = dy / ds_local  # 切向量y
        nx = -ty            # 法向量x (指向内部)
        ny = tx             # 法向量y (指向内部)

        # 在蛋形曲线上均匀采样N个点
        N_sample = 200
        s_sample = np.linspace(0, L, N_sample, endpoint=False)

        # 插值获取采样点的几何信息
        x_sample = np.interp(s_sample, s_curve, x_curve)
        y_sample = np.interp(s_sample, s_curve, y_curve)
        tx_sample = np.interp(s_sample, s_curve, tx)
        ty_sample = np.interp(s_sample, s_curve, ty)
        nx_sample = np.interp(s_sample, s_curve, nx)
        ny_sample = np.interp(s_sample, s_curve, ny)
        kappa_sample = np.interp(s_sample, s_curve, kappa_curve)

        # 中心点
        x_bnd, y_bnd = self.egg.get_curve_points(500)
        cx = 0.0
        cy = (np.max(y_bnd) + np.min(y_bnd)) / 2

        # 对于蛋形曲线上的每个采样点, 沿法向采样内部点
        N_radial = 30
        max_eta = 0.8 * min(np.max(np.abs(x_bnd)), np.max(np.abs(y_bnd)))

        v_tang_map = np.zeros((N_sample, N_radial))
        v_norm_map = np.zeros((N_sample, N_radial))
        eta_vals = np.linspace(0, max_eta, N_radial)

        dx_grid = X[0, 1] - X[0, 0] if X.ndim == 2 else 0.01
        dy_grid = Y[1, 0] - Y[0, 0] if Y.ndim == 2 else 0.01

        for i in range(N_sample):
            for j in range(N_radial):
                # 内部点坐标
                xp = x_sample[i] + nx_sample[i] * eta_vals[j]
                yp = y_sample[i] + ny_sample[i] * eta_vals[j]

                # 在CFD网格上插值速度
                # 找最近的网格点
                if X.ndim == 2:
                    ix = int((xp - X[0, 0]) / dx_grid)
                    iy = int((yp - Y[0, 0]) / dy_grid)
                    ix = np.clip(ix, 0, X.shape[1] - 1)
                    iy = np.clip(iy, 0, X.shape[0] - 1)

                    if mask[iy, ix] > 0:
                        ux_p = ux[iy, ix]
                        uy_p = uy[iy, ix]
                    else:
                        ux_p, uy_p = 0.0, 0.0
                else:
                    ux_p, uy_p = 0.0, 0.0

                # 投影到切向和法向
                v_tang_map[i, j] = ux_p * tx_sample[i] + uy_p * ty_sample[i]
                v_norm_map[i, j] = ux_p * nx_sample[i] + uy_p * ny_sample[i]

        return {
            's': s_sample,
            's_norm': s_sample / L,
            'eta': eta_vals,
            'v_tangential': v_tang_map,
            'v_normal': v_norm_map,
            'kappa': kappa_sample,
            'x_sample': x_sample,
            'y_sample': y_sample,
        }


class HarmonicAnalyzer:
    """谐波分析器 — 验证 Schauberger 1/n 衰减假设"""

    def __init__(self, mapped_data: dict, egg_params: EggParams = None):
        self.data = mapped_data
        self.ep = egg_params or EggParams(z1=1, z2=2)
        self.egg = EggCurve(self.ep)

    def boundary_velocity_fft(self) -> dict:
        """
        对蛋形边界上的切向速度做FFT分析
        验证: 主要频率分量是否对应谐波序列 1, 1/2, 1/3, ...
        """
        v_tang = self.data['v_tangential'][:, 0]  # 边界上的切向速度
        s = self.data['s']
        N = len(s)
        L = s[-1] - s[0]

        # FFT
        v_hat = np.fft.fft(v_tang)
        freqs = np.fft.fftfreq(N, d=L/N)
        amplitudes = 2.0 / N * np.abs(v_hat)

        # 只取正频率
        pos_mask = freqs > 0
        freqs_pos = freqs[pos_mask]
        amps_pos = amplitudes[pos_mask]

        # 找峰值
        peak_indices = []
        for i in range(1, len(amps_pos) - 1):
            if amps_pos[i] > amps_pos[i-1] and amps_pos[i] > amps_pos[i+1]:
                if amps_pos[i] > 0.01 * np.max(amps_pos):
                    peak_indices.append(i)

        return {
            'frequencies': freqs_pos,
            'amplitudes': amps_pos,
            'peak_indices': peak_indices,
            'peak_freqs': freqs_pos[peak_indices] if peak_indices else [],
            'peak_amps': amps_pos[peak_indices] if peak_indices else [],
        }

    def test_1_over_n_decay(self) -> dict:
        """
        验证速度幅值是否符合 1/n 衰减
        
        如果 v_θ 沿蛋形曲线的分布遵循 Schauberger 谐波序列,
        则FFT幅值应该满足 A_n ∝ 1/n
        """
        fft_result = self.boundary_velocity_fft()
        peak_amps = fft_result['peak_amps']

        if len(peak_amps) < 3:
            return {'conclusion': '数据不足, 无法判断'}

        # 拟合 A_n = C / n^p, 求p
        n_vals = np.arange(1, len(peak_amps) + 1)
        log_n = np.log(n_vals)
        log_A = np.log(peak_amps)

        # 线性拟合
        coeffs = np.polyfit(log_n, log_A, 1)
        p_fit = -coeffs[0]  # 斜率的负值 = 衰减指数
        C_fit = np.exp(coeffs[1])

        return {
            'conclusion': f'衰减指数 p = {p_fit:.3f} (Schauberger预测: p=1.0)',
            'decay_exponent': p_fit,
            'amplitude_constant': C_fit,
            'n_values': n_vals,
            'peak_amplitudes': peak_amps,
            'is_harmonic': abs(p_fit - 1.0) < 0.3,
        }

    def polarity_principle_test(self) -> dict:
        """
        验证极性原理: v_θ · r = const ? (在蛋形截面上)
        
        如果Schauberger的 p·q=const 在流体中成立,
        则 v_θ(s) · r(s) 应该近似为常数 (r(s)是到中心轴的距离)
        """
        v_tang = self.data['v_tangential'][:, 0]  # 边界切向速度
        x_s = self.data['x_sample']
        y_s = self.data['y_sample']

        # 中心
        x_bnd, y_bnd = self.egg.get_curve_points(500)
        cy = (np.max(y_bnd) + np.min(y_bnd)) / 2

        r_s = np.sqrt(x_s**2 + (y_s - cy)**2)
        r_safe = np.where(r_s < 1e-10, 1e-10, r_s)

        product = v_tang * r_safe
        mean_product = np.mean(np.abs(product))
        std_product = np.std(np.abs(product))
        relative_variation = std_product / mean_product if mean_product > 0 else np.inf

        return {
            'v_theta_times_r': product,
            'mean': mean_product,
            'std': std_product,
            'relative_variation': relative_variation,
            'is_const': relative_variation < 0.3,
            'conclusion': f'v_θ·r 变异系数 = {relative_variation:.3f} (≈0 表示极性原理成立)',
        }


def analyze_synthetic_data():
    """
    用合成数据(非CFD结果)演示分析流程
    在实际使用时, 替换为CFD求解器的输出
    """
    ep = EggParams(z1=1, z2=2)
    egg = EggCurve(ep)
    mapper = EggCoordinateMapper(ep)

    # === 合成数据: Burgers涡在蛋形截面上 ===
    n_grid = 150
    x_bnd, y_bnd = egg.get_curve_points(500)
    xmin, xmax = np.min(x_bnd), np.max(x_bnd)
    ymin, ymax = np.min(y_bnd), np.max(y_bnd)
    margin = 0.05
    x = np.linspace(xmin - margin, xmax + margin, n_grid)
    y = np.linspace(ymin - margin, ymax + margin, n_grid)
    X, Y = np.meshgrid(x, y)

    # 蛋形掩码
    z0, sa, ca = ep.z0, ep.sin_a, ep.cos_a
    inner = 1.0 / (z0 - Y * sa)**2 - (Y * ca)**2
    mask = ((inner > 0) & (X**2 < inner)).astype(float)

    # Burgers涡速度
    cy = (ymax + ymin) / 2
    R = np.sqrt(X**2 + (Y - cy)**2)
    R_safe = np.where(R < 1e-10, 1e-10, R)
    Theta = np.arctan2(Y - cy, X)

    Gamma, gamma_val, nu = 1.0, 1.0, 0.02
    vtheta = Gamma / (2 * np.pi * R_safe) * (1 - np.exp(-gamma_val * R_safe**2 / (4 * nu)))
    vr = -gamma_val * R_safe / 2

    ux = -vtheta * np.sin(Theta) + vr * np.cos(Theta)
    uy = vtheta * np.cos(Theta) + vr * np.sin(Theta)
    ux *= mask
    uy *= mask

    # === 映射到蛋形坐标 ===
    mapped = mapper.map_to_egg_coords(X, Y, ux, uy, mask)

    # === 谐波分析 ===
    analyzer = HarmonicAnalyzer(mapped)
    fft_result = analyzer.boundary_velocity_fft()
    decay_result = analyzer.test_1_over_n_decay()
    polarity_result = analyzer.polarity_principle_test()

    # === 可视化 ===
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # 1. 边界切向速度
    ax = axes[0, 0]
    ax.plot(mapped['s_norm'], mapped['v_tangential'][:, 0], 'b-', linewidth=1.5)
    ax.set_xlabel('归一化弧长 s/L', fontsize=12)
    ax.set_ylabel('v_θ (切向)', fontsize=12)
    ax.set_title('蛋形边界上的切向速度', fontsize=13)
    ax.grid(True, alpha=0.3)

    # 2. 速度沿法向的衰减
    ax = axes[0, 1]
    for i in [0, 50, 100, 150]:
        if i < mapped['v_tangential'].shape[0]:
            ax.plot(mapped['eta'], mapped['v_tangential'][i, :],
                    label=f's/L={mapped["s_norm"][i]:.2f}')
    ax.set_xlabel('法向距离 η', fontsize=12)
    ax.set_ylabel('v_θ', fontsize=12)
    ax.set_title('切向速度的法向衰减', fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 3. FFT频谱
    ax = axes[0, 2]
    ax.semilogy(fft_result['frequencies'], fft_result['amplitudes'], 'b-', linewidth=0.8)
    if len(fft_result['peak_freqs']) > 0:
        ax.plot(fft_result['peak_freqs'], fft_result['peak_amps'], 'ro', markersize=8)
    ax.set_xlabel('频率', fontsize=12)
    ax.set_ylabel('幅值', fontsize=12)
    ax.set_title('边界速度FFT频谱', fontsize=13)
    ax.grid(True, alpha=0.3)

    # 4. 1/n衰减验证
    ax = axes[1, 0]
    if 'n_values' in decay_result:
        n_v = decay_result['n_values']
        a_v = decay_result['peak_amplitudes']
        ax.loglog(n_v, a_v, 'bo-', label='FFT峰值')
        # 1/n参考线
        n_ref = np.linspace(1, max(n_v), 100)
        ax.loglog(n_ref, decay_result['amplitude_constant'] / n_ref, 'r--',
                  label=f'C/n^p, p={decay_result["decay_exponent"]:.2f}')
        ax.set_xlabel('谐波阶数 n', fontsize=12)
        ax.set_ylabel('幅值 A_n', fontsize=12)
        ax.set_title(f'谐波衰减验证: {decay_result["conclusion"]}', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, which='both')

    # 5. 极性原理验证
    ax = axes[1, 1]
    product = polarity_result['v_theta_times_r']
    ax.plot(mapped['s_norm'], product, 'g-', linewidth=1.5)
    ax.axhline(y=polarity_result['mean'], color='r', linestyle='--', label=f'均值={polarity_result["mean"]:.4f}')
    ax.set_xlabel('归一化弧长 s/L', fontsize=12)
    ax.set_ylabel('v_θ · r', fontsize=12)
    ax.set_title(f'极性原理验证: {polarity_result["conclusion"]}', fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # 6. 曲率 vs 速度
    ax = axes[1, 2]
    kappa = mapped['kappa']
    v_boundary = np.abs(mapped['v_tangential'][:, 0])
    ax.scatter(kappa, v_boundary, s=10, alpha=0.6, c='purple')
    ax.set_xlabel('曲率 κ', fontsize=12)
    ax.set_ylabel('|v_θ|', fontsize=12)
    ax.set_title('曲率 vs 边界速度', fontsize=13)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/sandbox/workspace/egg_vortex_cfd/output/05_harmonic_analysis.png', dpi=150)
    plt.close()
    print("✅ 谐波分析可视化已保存")

    # 打印分析结论
    print(f"\n{'='*60}")
    print("谐波分析结论")
    print(f"{'='*60}")
    print(f"  {decay_result['conclusion']}")
    print(f"  {polarity_result['conclusion']}")
    print(f"{'='*60}")


if __name__ == '__main__':
    analyze_synthetic_data()
