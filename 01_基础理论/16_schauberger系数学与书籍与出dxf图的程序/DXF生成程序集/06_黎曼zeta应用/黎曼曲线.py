import numpy as np
import matplotlib.pyplot as plt
from mpmath import zeta
import mpmath


def compute_critical_line(t_start=0, t_end=300, points=3000):
    mpmath.mp.dps = 25
    t = np.linspace(t_start, t_end, points)
    zeta_values = [zeta(complex(0.5, y)) for y in t]
    real_parts = [float(mpmath.re(z)) for z in zeta_values]
    imag_parts = [float(mpmath.im(z)) for z in zeta_values]
    return real_parts, imag_parts, t


def plot_critical_line():
    try:
        real_parts, imag_parts, t_values = compute_critical_line()

        plt.figure(figsize=(12, 12))
        plt.plot(real_parts, imag_parts, 'k-', linewidth=0.8, label='ζ(1/2 + it)')

        # Find points where real part is zero (crosses imaginary axis)
        for i in range(1, len(real_parts)):
            # Check for imaginary axis crossings (real part = 0)
            if real_parts[i - 1] * real_parts[i] <= 0:
                t_ratio = abs(real_parts[i - 1]) / (abs(real_parts[i - 1]) + abs(real_parts[i]))
                t_cross = t_values[i - 1] + t_ratio * (t_values[i] - t_values[i - 1])
                y_cross = imag_parts[i - 1] + t_ratio * (imag_parts[i] - imag_parts[i - 1])

                plt.plot(0, y_cross, 'ro', markersize=8)
                plt.annotate(f't ≈ {t_cross:.3f}',
                             xy=(0, y_cross),
                             xytext=(0.5, y_cross),
                             arrowprops=dict(facecolor='red', shrink=0.05),
                             bbox=dict(facecolor='white', edgecolor='red', alpha=0.7))

            # Check for real axis crossings (imaginary part = 0)
            if imag_parts[i - 1] * imag_parts[i] <= 0:
                t_ratio = abs(imag_parts[i - 1]) / (abs(imag_parts[i - 1]) + abs(imag_parts[i]))
                t_cross = t_values[i - 1] + t_ratio * (t_values[i] - t_values[i - 1])
                x_cross = real_parts[i - 1] + t_ratio * (real_parts[i] - real_parts[i - 1])

                plt.plot(x_cross, 0, 'bo', markersize=8)
                plt.annotate(f't ≈ {t_cross:.3f}',
                             xy=(x_cross, 0),
                             xytext=(x_cross, 0.5),
                             arrowprops=dict(facecolor='blue', shrink=0.05),
                             bbox=dict(facecolor='white', edgecolor='blue', alpha=0.7))

        plt.grid(True)
        plt.xlabel('Re(ζ(s))')
        plt.ylabel('Im(ζ(s))')
        plt.title(
            'Riemann Zeta Function on Critical Line (s = 1/2 + it)\nRed: Imaginary Axis Crossings, Blue: Real Axis Crossings')
        plt.axis('equal')

        plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
        plt.legend()

        plt.show()

    except Exception as e:
        print(f"Error occurred: {str(e)}")


if __name__ == "__main__":
    plot_critical_line()