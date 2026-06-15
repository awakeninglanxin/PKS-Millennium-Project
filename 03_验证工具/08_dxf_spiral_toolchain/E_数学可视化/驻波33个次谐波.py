import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# 参数设定
fundamental_freq = 1.45  # 主频 (Hz)
amplitude = 12  # 主频振幅 (V)
num_harmonics = 33  # 次谐波数量
frequency_upper_limit = 60  # 上限频率 (Hz)

# 生成次谐波频率、振幅和相位
frequencies = [fundamental_freq * (n + 1) for n in range(num_harmonics)]
phases = [0 for _ in range(num_harmonics)]  # 假设相位为 0
amplitudes = [amplitude / (n + 1) for n in range(num_harmonics)]  # 假设振幅衰减

# 仅保留符合频率上限的次谐波
filtered_frequencies = [f for f in frequencies if f <= frequency_upper_limit]
filtered_amplitudes = [amplitudes[i] for i, f in enumerate(frequencies) if f <= frequency_upper_limit]

# 设置图形大小时，预留legend的空间
plt.figure(figsize=(10, 8))  # 增加了高度以适应底部的图例

# 绘制频率分布图
for i, (freq, amp) in enumerate(zip(filtered_frequencies, filtered_amplitudes)):
    x = np.linspace(0, 1.1, 500)  # 空间范围 (X)
    y1 = amp * np.sin(2 * np.pi * freq * x)  # 正弦波形
    y2 = -amp * np.sin(2 * np.pi * freq * x)  # 正弦波形
    plt.plot(x, y1, linestyle='--', linewidth=0.5, label=f"Harmonic {i + 1} ({freq:.2f} Hz)")
    plt.plot(x, y2, linestyle='--', linewidth=0.5)

# 图表设置
plt.title("Distribution of Harmonic Frequencies Along the Resonator Cavity")
plt.xlabel("X [-]")
plt.ylabel("Amplitude [V]")
plt.grid(True)

# 调整图例位置到底部
plt.legend(bbox_to_anchor=(0.5, -0.15), # x, y坐标
          loc='upper center',  # 锚点位置
          ncol=4,             # 每行显示的项目数
          fontsize='small',
          bbox_transform=plt.gcf().transFigure)  # 使用图形坐标系

# 调整布局以确保图例完全可见
plt.tight_layout()

plt.show()

# 保存次谐波数据为 CSV 文件
harmonics_data = pd.DataFrame({
    "Harmonic": np.arange(1, len(filtered_frequencies) + 1),
    "Frequency (Hz)": filtered_frequencies,
    "Amplitude (V)": filtered_amplitudes,
    "Phase (rad)": phases[:len(filtered_frequencies)],
})
output_file = "harmonic_filtered_data.csv"
harmonics_data.to_csv(output_file, index=False)
print(f"次谐波数据已保存到 {output_file}")