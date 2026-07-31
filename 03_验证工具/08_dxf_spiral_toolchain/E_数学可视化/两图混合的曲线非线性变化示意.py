import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 设置参数
num_t = 945 * 2
t_normalized = np.linspace(0, 1, num_t)
k_values = [0.1, 0.248473, 2, 3.0]  # 不同k值进行比较

plt.figure(figsize=(12, 8))

for k in k_values:
    # 计算频率和混合系数
    freq = np.power(2, k * t_normalized)
    min_freq, max_freq = np.min(freq), np.max(freq)
    blend_factors = (freq - min_freq) / (max_freq - min_freq)

    # 绘制曲线
    plt.plot(t_normalized, blend_factors, label=f'k={k}', linewidth=2)

# 添加线性混合作为对比
linear_blend = t_normalized
plt.plot(t_normalized, linear_blend, 'k--', label='线性混合', linewidth=2)

# 设置图表属性
plt.title('简化版非线性混合系数曲线 (指数变化)', fontsize=16)
plt.xlabel('归一化参数 t', fontsize=14)
plt.ylabel('混合系数', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=12)
plt.xlim(0, 1)
plt.ylim(0, 1)

plt.tight_layout()
plt.savefig('simplified_nonlinear_blend_factors.png', dpi=300, bbox_inches='tight')
plt.show()