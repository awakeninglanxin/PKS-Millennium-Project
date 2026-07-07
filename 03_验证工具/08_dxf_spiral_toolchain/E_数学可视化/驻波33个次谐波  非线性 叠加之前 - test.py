import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt


class AcousticResonator:
    def __init__(self, length=0.15, c0=343, gamma=1.4, rho0=1.2, N=5):
        """
        Initialize acoustic resonator parameters

        Parameters:
        N : int
            Number of harmonics in each direction (-N to +N)
        """
        self.l = length
        self.c0 = c0
        self.gamma = gamma
        self.rho0 = rho0
        self.omega0 = np.pi * c0 / length

        # Numerical parameters
        self.N = N  # Will consider harmonics from -N to +N
        self.harm_indices = np.arange(-N, N + 1)  # Array of harmonic indices
        self.n_harmonics = 2 * N + 1  # Total number of harmonics including 0
        self.GTV = 1e-2
        self.D = 0

    def set_boundary_conditions(self, R0=1.0, R1=1.0):
        """Set reflection coefficients at resonator walls"""
        self.R0 = R0
        self.R1 = R1

    def wave_equations(self, X, Y, Omega, A):
        """
        Implementation of equation (20) from the paper:
        dV±k/dX = jπ²[(γ+1)/2Ω]Σ(k-m)V±mV±(k-m) + jkπ²ΩXAk/4·e^(±jkπΩX)
                  ∓ πk²GTVΩ/2·V±k ∓ π√(|k|/2)ΩD[1+j·sign(k)]V±k
        """
        V_plus = Y[:self.n_harmonics]
        V_minus = Y[self.n_harmonics:]

        dVplus = np.zeros(self.n_harmonics, dtype=complex)
        dVminus = np.zeros(self.n_harmonics, dtype=complex)

        for idx, k in enumerate(self.harm_indices):
            if k == 0:  # Skip k=0 as it represents DC component
                continue

            # Nonlinear terms (first term in eq. 17)
            nonlinear_sum = 0
            for m_idx, m in enumerate(self.harm_indices):
                n = k - m
                if abs(n) <= self.N:
                    n_idx = n + self.N
                    nonlinear_sum += m * V_plus[m_idx] * V_plus[n_idx]

            # Terms from equation (17)
            nonlinear_term = np.pi ** 2 * (self.gamma + 1) / (2 * Omega) * nonlinear_sum
            driving_term = np.pi ** 2 * Omega * X * k * A / 2
            viscous_term = np.pi * self.GTV * (Omega / 2) * k ** 2
            boundary_term = np.pi * Omega * self.D * np.sqrt(abs(k) / 2) * (1 + 1j * np.sign(k))

            # Forward wave equation
            dVplus[idx] = (1j * nonlinear_term +
                           driving_term * np.exp(-1j * k * np.pi * Omega * X) -
                           viscous_term * V_plus[idx] -
                           boundary_term * V_plus[idx])

            # Backward wave equation
            dVminus[idx] = (-1j * nonlinear_term +
                            driving_term * np.exp(1j * k * np.pi * Omega * X) -
                            viscous_term * V_minus[idx] +
                            boundary_term * V_minus[idx])

        return np.concatenate([dVplus, dVminus])

    def solve_system(self, X, Omega=1.0, A=5e-4):
        """Solve the coupled wave equations with boundary conditions from eq (21a,21b)"""
        # Initialize forward wave amplitudes with physically correct scaling
        Y0_plus = np.zeros(self.n_harmonics, dtype=complex)

        # Set base frequency amplitude
        base_amplitude = 1e-3

        for idx, k in enumerate(self.harm_indices):
            if k == 0:  # Skip DC component
                continue
            # Amplitude should decrease with harmonic number
            # Higher harmonics should have much smaller amplitudes
            if k > 0:  # Positive harmonics
                amplitude = base_amplitude * np.exp(-abs(k - 1))  # Exponential decay for higher harmonics
            else:  # Negative harmonics
                amplitude = base_amplitude * np.exp(-abs(k + 1))

            # Phase for symmetry
            phase = -k * np.pi * 0.5
            Y0_plus[idx] = amplitude * np.exp(1j * phase)

        # Apply boundary condition at X=0: R0V+ + V- = 0
        Y0_minus = -self.R0 * Y0_plus
        Y0 = np.concatenate([Y0_plus, Y0_minus])

        # Solve ODE system
        t_span = [0, 12]
        sol = solve_ivp(
            lambda x, y: self.wave_equations(x, y, Omega, A),
            t_span,
            Y0,
            t_eval=X,
            method='RK45',
            rtol=1e-8,
            atol=1e-10
        )

        return sol.y[:self.n_harmonics, :].T, sol.y[self.n_harmonics:, :].T

        return sol.y[:self.n_harmonics, :].T, sol.y[self.n_harmonics:, :].T

    def calculate_pressure_components(self, V_plus, V_minus, X):
        """Calculate non-dimensional pressure components using equation (18)"""
        P_components = np.zeros((self.n_harmonics, len(X)), dtype=complex)

        for idx, k in enumerate(self.harm_indices):
            if k == 0:  # Skip DC component
                continue
            # Calculate pressure using non-dimensional form P± = ±V±/π
            P_components[idx] = (V_plus[:, idx] * np.exp(-1j * k * np.pi * X) +
                                 V_minus[:, idx] * np.exp(1j * k * np.pi * X)) / np.pi

        # Convert to dimensional pressure
        P_components = P_components * (np.pi ** 2 * self.rho0 * self.c0 ** 2)
        return P_components

    def calculate_velocity_time_domain(self, V_plus, V_minus, X, T):
        """
        Calculate velocity in time domain using equation (23)
        v(X,T) = 2πc0 Σ{[(V+k + V-k)cos kπΩX + (V+k - V-k)sin kπΩX]cos kT -
                 [(V+k + V-k)cos kπΩX + (V+k - V-k)sin kπΩX]sin kT}
        """
        v = np.zeros((len(X), len(T)), dtype=float)

        for idx, k in enumerate(self.harm_indices):
            if k == 0:
                continue

            # Terms from equation (23)
            sum_V = V_plus[:, idx] + V_minus[:, idx]
            diff_V = V_plus[:, idx] - V_minus[:, idx]

            for t_idx, t in enumerate(T):
                cos_term = (sum_V * np.cos(k * np.pi * self.Omega * X) +
                            diff_V * np.sin(k * np.pi * self.Omega * X))
                v[:, t_idx] += 2 * np.pi * self.c0 * (
                        cos_term * np.cos(k * t) -
                        cos_term * np.sin(k * t)
                )

        return v

        return np.real(P_components)

    def plot_results(self, X, P_components):
        """Plot pressure distribution for each harmonic (only positive values)"""
        plt.figure(figsize=(12, 8))

        # Plot each harmonic component separately
        for idx, k in enumerate(self.harm_indices):
            if k == 0:  # Skip DC component
                continue
            P = P_components[idx]
            # Only plot if component has significant amplitude
            if np.max(np.abs(P)) > 1e-10:
                plt.plot(X, np.abs(P), label=f'k={abs(k)}')

        plt.xlabel('X [-]')
        plt.ylabel('p [Pa]')
        plt.title('Distribution of acoustic pressure spectra along the resonator cavity')
        plt.grid(True)
        plt.ylim(bottom=0)  # Only show positive pressure values
        plt.legend()
        plt.show()


# Example usage
if __name__ == "__main__":
    # Create resonator with N=5 (harmonics from -5 to +5)
    resonator = AcousticResonator(N=5)
    resonator.set_boundary_conditions(R0=1.0, R1=1.0)

    # Spatial grid
    X = np.linspace(0, 1, 200)

    # Calculate wave components
    V_plus, V_minus = resonator.solve_system(X, Omega=1.0, A=5e-4)

    # Calculate pressure field components
    P_components = resonator.calculate_pressure_components(V_plus, V_minus, X)

    # Plot results showing all harmonics separately
    resonator.plot_results(X, P_components)