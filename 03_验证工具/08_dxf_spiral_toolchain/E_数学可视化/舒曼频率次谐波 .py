import numpy as np
import matplotlib.pyplot as plt

# 使用之前代码中的频率和振幅数据
fundamental_freq = 1.45
num_harmonics = 33
frequency_upper_limit = 60

frequencies = [fundamental_freq * (n + 1) for n in range(num_harmonics)]
amplitudes = [12 / (n + 1) for n in range(num_harmonics)]

# 仅保留符合频率上限的数据
filtered_frequencies = [f for f in frequencies if f <= frequency_upper_limit]
filtered_amplitudes = [amplitudes[i] for i, f in enumerate(frequencies) if f <= frequency_upper_limit]

# 创建网格
size = 1000
x = np.linspace(-5, 5, size)
y = np.linspace(-5, 5, size)
X, Y = np.meshgrid(x, y)

# 创建干涉图案
wave = np.zeros_like(X)
for freq, amp in zip(filtered_frequencies, filtered_amplitudes):
    # 计算从中心点出发的波
    r = np.sqrt(X**2 + Y**2)
    # 添加径向波，频率和振幅按照谐波序列设置
    wave += amp * np.sin(2 * np.pi * freq * r) / (r + 1)  # 添加1以避免除以零

# 绘制图案
plt.figure(figsize=(12, 12))
plt.imshow(wave,
          cmap='magma',  # 使用粉红-蓝色色谱
          extent=[-5, 5, -5, 5])
plt.axis('off')
plt.title('Harmonic Resonance Pattern')

# 添加颜色条
plt.colorbar(label='Amplitude')

plt.show()