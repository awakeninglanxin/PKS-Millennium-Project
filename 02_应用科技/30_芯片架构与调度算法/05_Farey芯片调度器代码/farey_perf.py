"""
Farey分相：翻转降80%，算力降多少？
考虑实际物理约束：IR drop + L·di/dt 限制最大频率
"""
import numpy as np

n = 5
N = n * n  # 25 tiles

# ── 场景1: 均匀分相（全同步）──
# 所有tile同时翻转 → 峰值电流 = N × I_per_tile
# 封装电感产生 L·di/dt → 地弹/电源噪声
# 必须降低频率以保证噪声在容忍范围内

# ── 场景2: Farey分相 ──
# 同时翻转≤5 tiles → 峰值电流 = 5 × I_per_tile
# 噪声降低了 N/5 = 5x → 可以跑更高频率

# 关键参数
I_per_tile = 10e-3      # 每tile翻转电流 10mA
L_pkg = 1e-9             # 封装电感 1nH
V_dd = 1.0               # 电源电压
V_noise_max = 0.05       # 最大允许噪声 5% Vdd
tr = 100e-12             # 翻转时间 100ps

# 均匀分相
N_flip_uniform = N       # 最坏同时25个
I_peak_uniform = N_flip_uniform * I_per_tile
di_dt_uniform = I_peak_uniform / tr
V_noise_uniform = L_pkg * di_dt_uniform
f_max_uniform = V_noise_max / (L_pkg * I_peak_uniform / tr) if I_peak_uniform > 0 else float('inf')

# Farey分相
N_flip_farey = 5         # 最多5个
I_peak_farey = N_flip_farey * I_per_tile
di_dt_farey = I_peak_farey / tr
V_noise_farey = L_pkg * di_dt_farey
f_max_farey = V_noise_max / (L_pkg * I_peak_farey / tr) if I_peak_farey > 0 else float('inf')

# 频率比
freq_ratio = f_max_farey / f_max_uniform

# ── 算力对比 ──
# 算力 = 频率 × 有效tile数 × 占空比
# 占空比相同(D≈16%)，有效tile数相同(25个都干活)
# 区别仅在于频率上限

print("="*60)
print("Farey分相: 性能不降反升分析")
print("="*60)

print(f"\n物理约束:")
print(f"  单tile翻转电流: {I_per_tile*1e3}mA, 翻转时间: {tr*1e12}ps")
print(f"  封装电感: {L_pkg*1e9}nH, 允许噪声: {V_noise_max*1e3}mV")

print(f"\n均匀分相:")
print(f"  同时翻转: {N_flip_uniform} tiles")
print(f"  峰值电流: {I_peak_uniform*1e3:.0f}mA")
print(f"  di/dt: {di_dt_uniform*1e-9:.1f} GA/s")
print(f"  地弹噪声: {V_noise_uniform*1e3:.0f}mV")
print(f"  允许最大频率: {f_max_uniform*1e-6:.0f}MHz (受噪声约束)")

print(f"\nFarey分相:")
print(f"  同时翻转: {N_flip_farey} tiles")
print(f"  峰值电流: {I_peak_farey*1e3:.0f}mA")
print(f"  di/dt: {di_dt_farey*1e-9:.1f} GA/s")
print(f"  地弹噪声: {V_noise_farey*1e3:.0f}mV")
print(f"  允许最大频率: {f_max_farey*1e-6:.0f}MHz (受噪声约束)")

print(f"\n═══════════════════════════════════")
print(f"  Farey允许频率 = {freq_ratio:.1f}× 均匀允许频率")
print(f"  算力比 = 频率比 = {freq_ratio:.1f}×")
print(f"═══════════════════════════════════")

# ── di/dt详细分析 ──
print(f"\n封装di/dt详细:")
for N_flip, label in [(25, '均匀(25翻)'), (5, 'Farey(5翻)'), (3, 'Farey最佳(3翻)')]:
    I = N_flip * I_per_tile
    didt = I / tr
    Vn = L_pkg * didt
    print(f"  {label}: I={I*1e3:.0f}mA, di/dt={didt*1e-9:.1f}GA/s, "
          f"Vnoise={Vn*1e3:.0f}mV, f_max={V_noise_max/Vn*1e9:.0f}MHz")

# ── 关键结论表格 ──
print(f"\n关键结论:")
print(f"  翻转数降幅: {(1-N_flip_farey/N_flip_uniform)*100:.0f}%")
print(f"  峰值电流降幅: {(1-I_peak_farey/I_peak_uniform)*100:.0f}%")
print(f"  噪声降幅: {(1-V_noise_farey/V_noise_uniform)*100:.0f}%")
print(f"  频率升幅: {(freq_ratio-1)*100:.0f}%")
print(f"  算力变化: +{(freq_ratio-1)*100:.0f}% (因为频率可以更高)")
print(f"\n核心: Farey不牺牲算力——它通过降噪让你能跑更高频率，算力反而可能提升。")
