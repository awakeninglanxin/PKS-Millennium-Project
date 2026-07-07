import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

# 定义三种分布函数
def gue_distribution(s):
    """GUE (Gaussian Unitary Ensemble)"""
    return (32/np.pi**2) * s**2 * np.exp(-4*s**2/np.pi)

def goe_distribution(s):
    """GOE (Gaussian Orthogonal Ensemble)"""
    return (np.pi/2) * s * np.exp(-np.pi*s**2/4)

def poisson_distribution(s):
    """Poisson distribution"""
    return np.exp(-s)

# 创建数据点
s = np.linspace(0, 4, 1000)
gue = gue_distribution(s)
goe = goe_distribution(s)
poisson = poisson_distribution(s)

# 绘图
plt.figure(figsize=(12, 8))
plt.plot(s, gue, 'b-', label='GUE Distribution', linewidth=2)
plt.plot(s, goe, 'r--', label='GOE Distribution', linewidth=2)
plt.plot(s, poisson, 'g:', label='Poisson Distribution', linewidth=2)

plt.xlabel('Normalized Level Spacing (s)', fontsize=12)
plt.ylabel('Probability Density P(s)', fontsize=12)
plt.title('Level Spacing Distributions Comparison', fontsize=14)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)

# 添加说明文本
plt.text(2.5, 0.8, 'GUE (Quantum Chaos):\n' +
         'P(s) = (32s²/π²)exp(-4s²/π)',
         bbox=dict(facecolor='white', alpha=0.8))

plt.text(2.5, 0.5, 'GOE (Time Reversal):\n' +
         'P(s) = (πs/2)exp(-πs²/4)',
         bbox=dict(facecolor='white', alpha=0.8))

plt.text(2.5, 0.2, 'Poisson (Integrable):\n' +
         'P(s) = exp(-s)',
         bbox=dict(facecolor='white', alpha=0.8))

plt.show()