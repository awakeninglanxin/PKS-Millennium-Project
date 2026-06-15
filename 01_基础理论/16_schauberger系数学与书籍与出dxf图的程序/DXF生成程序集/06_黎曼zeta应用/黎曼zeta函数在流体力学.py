import numpy as np
import matplotlib.pyplot as plt
from mpmath import zeta
import mpmath


def compute_fluid_modes(t_max=30, points=1000):
    """
    计算Riemann-Siegel流体模型中的模式
    """
    mpmath.mp.dps = 25
    t = np.linspace(0, t_max, points)

    # 计算zeta函数在临界线上的值
    zeta_values = [zeta(complex(0.5, y)) for y in t]

    # 提取实部和虚部作为两个流体模式
    mode1 = [float(mpmath.re(z)) for z in zeta_values]
    mode2 = [float(mpmath.im(z)) for z in zeta_values]

    return t, mode1, mode2


# 计算和绘制流体模式
t, mode1, mode2 = compute_fluid_modes()

plt.figure(figsize=(12, 8))
plt.subplot(211)
plt.plot(t, mode1, 'b-', label='Mode 1 (Real Part)')
plt.grid(True)
plt.legend()
plt.title('Riemann-Siegel Fluid Model Modes')

plt.subplot(212)
plt.plot(t, mode2, 'r-', label='Mode 2 (Imaginary Part)')
plt.grid(True)
plt.legend()
plt.xlabel('t')

plt.tight_layout()
plt.show()


# 计算模式的能量谱
def compute_energy_spectrum(mode, dt=0.03):
    """计算能量谱"""
    N = len(mode)
    spectrum = np.abs(np.fft.fft(mode)) ** 2
    freqs = np.fft.fftfreq(N, dt)

    # 只返回正频率部分
    positive_freqs = freqs[freqs > 0]
    positive_spectrum = spectrum[freqs > 0]

    return positive_freqs, positive_spectrum


# 计算并绘制能量谱
freqs1, spectrum1 = compute_energy_spectrum(mode1)
freqs2, spectrum2 = compute_energy_spectrum(mode2)

plt.figure(figsize=(12, 6))
plt.loglog(freqs1, spectrum1, 'b-', label='Mode 1 Spectrum')
plt.loglog(freqs2, spectrum2, 'r--', label='Mode 2 Spectrum')
plt.grid(True)
plt.xlabel('Frequency')
plt.ylabel('Energy')
plt.title('Energy Spectrum of Riemann-Siegel Fluid Modes')
plt.legend()
plt.show()