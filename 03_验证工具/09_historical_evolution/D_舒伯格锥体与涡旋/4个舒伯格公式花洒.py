import numpy as np
import matplotlib.pyplot as plt


# Define a function to plot each of the equations
def plot_equation(equation_id):
    x = np.linspace(-5, 5, 400)

    plt.figure(figsize=(6, 6))

    if equation_id == 1:
        # Equation I: x^2 + x - 2 = 0
        y = x ** 2 + x - 2
        plt.plot(x, y, label=r'$y = x^2 + x - 2$', color='blue')

    elif equation_id == 2:
        # Equation II: x^2 - 3x - 1 = 0
        y = x ** 2 + 4 * x +3
        plt.plot(x, y, label=r'$y = x^2  + 4 * x +3$', color='green')

    elif equation_id == 3:
        # Equation III: -3x + 1 = 0
        y = x ** 2 - 1.5 * x -1
        plt.plot(x, y, label=r'$y = x^2 - 1.5 * x -1$', color='red')

    elif equation_id == 4:
        # Equation IV: x^2 - x - 1 = 0
        y = x ** 2 +3*x/4 - 1/4
        plt.plot(x, y, label=r'$y = x^2 +3*x/4 - 1/4$', color='purple')

    # Plot formatting
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.title(f'Equation {equation_id} Plot')
    plt.xlabel('x-axis')
    plt.ylabel('y-axis')
    plt.legend()
    plt.ylim(-10, 10)
    plt.show()


# Plot all four equations
for i in range(1, 5):
    plot_equation(i)
