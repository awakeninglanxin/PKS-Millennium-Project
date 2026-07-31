import numpy as np
import matplotlib.pyplot as plt

# Parameters
A = 1  # Amplitude
omega = 2 * np.pi  # Angular frequency
t_vals = np.linspace(0, 2, 500)  # Time array for 1 period (T=2)
n_terms = 108  # Number of terms in Fourier series

# Full k values: Compute sawtooth wave using Fourier series
sawtooth_full_k = np.zeros_like(t_vals)
for k in range(1, n_terms + 1):
    sawtooth_full_k += ((-1) ** (k + 1)) * (A / k) * np.sin(k * omega * t_vals)
# Normalize amplitude
sawtooth_full_k *= (2 / np.pi)

# Prime k values: Compute sawtooth wave for prime k values only
prime_k_values = [k for k in range(1, n_terms + 1) if k > 1 and all(k % i != 0 for i in range(2, int(k ** 0.5) + 1))]
sawtooth_prime_k = np.zeros_like(t_vals)
for k in prime_k_values:
    sawtooth_prime_k += ((-1) ** (k + 1)) * (A / k) * np.sin(k * omega * t_vals)
# Normalize amplitude
sawtooth_prime_k *= (2 / np.pi)

# Locas k values: Generate Locas sequence
locas_k_values = []
a, b = 1, 3  # Initial values
while len(locas_k_values) < n_terms:  # Generate enough terms
    locas_k_values.append(a)
    a, b = b, a + b
sawtooth_locas_k = np.zeros_like(t_vals)
for k in locas_k_values:
    sawtooth_locas_k += ((-1) ** (k + 1)) * (A / k) * np.sin(k * omega * t_vals)
# Normalize amplitude
sawtooth_locas_k *= (2 / np.pi)

# Solar k values: Generate 2^n sequence
solar_k_values = [2 ** i for i in range(1, int(np.log2(n_terms)) + 2) if 2 ** i <= n_terms]
sawtooth_solar_k = np.zeros_like(t_vals)
for k in solar_k_values:
    sawtooth_solar_k += ((-1) ** (k + 1)) * (A / k) * np.sin(k * omega * t_vals)
# Normalize amplitude
sawtooth_solar_k *= (2 / np.pi)

# Plot the first figure: Full k values
plt.figure(figsize=(12, 6))
plt.plot(t_vals, sawtooth_full_k, label="Sawtooth Wave (Full k)", linestyle="-", color="red")
plt.xlabel("t (Time)")
plt.ylabel("Amplitude")
plt.title("Sawtooth Wave (Full k Values)")
plt.legend()
plt.grid()

# Plot the second figure: Prime k values
plt.figure(figsize=(12, 6))
plt.plot(t_vals, sawtooth_prime_k, label="Sawtooth Wave (Prime k)", linestyle="--", color="blue")
plt.xlabel("t (Time)")
plt.ylabel("Amplitude")
plt.title("Sawtooth Wave (Prime k Values)")
plt.legend()
plt.grid()

# Plot the third figure: Locas k values
plt.figure(figsize=(12, 6))
plt.plot(t_vals, sawtooth_locas_k, label="Sawtooth Wave (Locas k)", linestyle=":", color="green")
plt.xlabel("t (Time)")
plt.ylabel("Amplitude")
plt.title("Sawtooth Wave (Locas k Values)")
plt.legend()
plt.grid()

# Plot the fourth figure: Solar k values
plt.figure(figsize=(12, 6))
plt.plot(t_vals, sawtooth_solar_k, label="Sawtooth Wave (Solar k)", linestyle="dashdot", color="purple")
plt.xlabel("t (Time)")
plt.ylabel("Amplitude")
plt.title("Sawtooth Wave (Solar k Values)")
plt.legend()
plt.grid()

# Show all plots
plt.show()
