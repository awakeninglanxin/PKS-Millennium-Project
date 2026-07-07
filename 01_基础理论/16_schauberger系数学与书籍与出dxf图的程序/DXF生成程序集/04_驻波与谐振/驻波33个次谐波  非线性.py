import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt


class AcousticResonator:
    def __init__(self, length=0.15, c0=343, gamma=1.4, rho0=1.2):
        """
        Initialize acoustic resonator parameters

        Parameters:
        length : float
            Resonator length in meters (default 15cm)
        c0 : float
            Small-signal sound speed (m/s)
        gamma : float
            Ratio of specific heats
        rho0 : float
            Ambient density (kg/m³)
        """
        self.l = length
        self.c0 = c0
        self.gamma = gamma
        self.rho0 = rho0
        self.omega0 = np.pi * c0 / length  # Fundamental resonant frequency

        # Numerical parameters
        self.N = 33  # Number of harmonics to consider (as mentioned in your original requirement)
        self.GTV = 1e-2  # Viscosity coefficient
        self.D = 0  # Boundary layer coefficient

    def set_boundary_conditions(self, R0=1.0, R1=1.0):
        """Set reflection coefficients at resonator walls"""
        self.R0 = R0
        self.R1 = R1

    def calculate_wave_components(self, X, Omega, A):
        """
        Calculate forward and backward propagating wave components

        Parameters:
        X : array
            Non-dimensional spatial coordinates
        Omega : float
            Non-dimensional frequency (ω/ω0)
        A : float
            Non-dimensional acceleration amplitude
        """
        # Initialize arrays for forward and backward waves
        V_plus = np.zeros((len(X), self.N), dtype=complex)
        V_minus = np.zeros((len(X), self.N), dtype=complex)

        def wave_ode(t, y):
            """ODE system for wave components based on eq. (20) in paper"""
            # Split state vector into V+ and V- components
            Vp = y[:self.N]
            Vm = y[self.N:]

            dVp = np.zeros_like(Vp, dtype=complex)
            dVm = np.zeros_like(Vm, dtype=complex)

            # Calculate derivatives for each harmonic
            for n in range(self.N):
                k = n + 1  # Harmonic number

                # Terms from equation (20)
                nonlinear_term = 1j * np.pi ** 2 * (self.gamma + 1) / (2 * Omega)
                driving_term = 1j * k * np.pi ** 2 * Omega * t * A / 4  # t is X in this context
                viscous_term = -np.pi * self.GTV * Omega / 2 * k ** 2
                boundary_term = -np.pi * np.sqrt(abs(k) / 2) * Omega * self.D * (1 + 1j * np.sign(k))

                # Forward wave
                dVp[n] = (nonlinear_term * np.sum([m * Vp[m - 1] * Vp[k - m - 1]
                                                   for m in range(1, k) if m < self.N and k - m < self.N]) +
                          driving_term * np.exp(-1j * k * np.pi * t) +
                          (viscous_term + boundary_term) * Vp[n])

                # Backward wave
                dVm[n] = (-nonlinear_term * np.sum([m * Vm[m - 1] * Vm[k - m - 1]
                                                    for m in range(1, k) if m < self.N and k - m < self.N]) +
                          driving_term * np.exp(1j * k * np.pi * t) +
                          (viscous_term - boundary_term) * Vm[n])

            return np.concatenate([dVp, dVm])

        # Initial conditions
        V0_plus = np.ones(self.N, dtype=complex) * 1e-3
        V0 = np.concatenate([V0_plus, -self.R0 * V0_plus])

        # Solve IVP
        sol = solve_ivp(
            wave_ode,
            [0, 1],
            V0,
            t_eval=X,
            method='RK45',
            rtol=1e-6,
            atol=1e-8
        )

        V_plus = sol.y[:self.N, :].T
        V_minus = sol.y[self.N:, :].T

        return V_plus, V_minus

    def calculate_pressure_velocity(self, V_plus, V_minus, X):
        """Calculate pressure and velocity fields from wave components"""
        P = np.zeros_like(X, dtype=complex)
        v = np.zeros_like(X, dtype=complex)

        for k in range(self.N):
            # Phase terms
            phase_plus = np.exp(-1j * (k + 1) * np.pi * X)
            phase_minus = np.exp(1j * (k + 1) * np.pi * X)

            # Pressure from eq. (18)
            P += (V_plus[:, k] * phase_plus + V_minus[:, k] * phase_minus) / np.pi

            # Velocity from eq. (22)
            v += V_plus[:, k] * phase_plus + V_minus[:, k] * phase_minus

        return np.real(P), np.real(v)

    def plot_results(self, X, P, v):
        """Plot pressure and velocity distributions"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        ax1.plot(X, P)
        ax1.set_title('Acoustic Pressure Distribution')
        ax1.set_xlabel('X [-]')
        ax1.set_ylabel('p [Pa]')
        ax1.grid(True)

        ax2.plot(X, v)
        ax2.set_title('Acoustic Velocity Distribution')
        ax2.set_xlabel('X [-]')
        ax2.set_ylabel('v [m/s]')
        ax2.grid(True)

        plt.tight_layout()
        plt.show()


# Example usage
if __name__ == "__main__":
    # Create resonator instance
    resonator = AcousticResonator()
    resonator.set_boundary_conditions(R0=1.0, R1=-1.0)

    # Spatial grid
    X = np.linspace(0, 1, 200)

    # Calculate wave components
    Omega = 1.5  # Resonance condition
    A = 5e-4  # Non-dimensional acceleration
    V_plus, V_minus = resonator.calculate_wave_components(X, Omega, A)

    # Calculate pressure and velocity fields
    P, v = resonator.calculate_pressure_velocity(V_plus, V_minus, X)

    # Plot results
    resonator.plot_results(X, P, v)