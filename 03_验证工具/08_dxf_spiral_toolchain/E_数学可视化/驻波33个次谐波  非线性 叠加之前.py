import numpy as np
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

        # Calculate fundamental frequency (f0) and angular frequency (omega0)
        self.f0 = c0 / (2 * length)  # Fundamental frequency
        self.omega0 = 2 * np.pi * self.f0  # Fundamental angular frequency

        # Numerical parameters
        self.N = 33  # Number of harmonics to consider

    def calculate_wave_components(self, X):
        """
        Calculate individual harmonic components of acoustic pressure distribution.

        Parameters:
        X : array
            Non-dimensional spatial coordinates
        """
        harmonics = []  # List to store each harmonic component

        A_base = 4500  # Base amplitude for fundamental frequency

        for k in range(self.N):
            # Wave number calculation for each harmonic
            k_n = (k + 1) * np.pi  # Wave number for the nth harmonic

            # Amplitude calculation with exponential decay for higher harmonics
            if k == 0:
                amplitude = A_base
            else:
                amplitude = A_base * np.exp(-k * np.log(2) / (np.pi))  # Adjusted decay rate

            # Calculate individual harmonic component
            P_k = amplitude * np.sin(k_n * X)
            harmonics.append(P_k)

        return harmonics

    def plot_all_harmonics(self, harmonics, X):
        """
        Plot all harmonic components in a single coordinate system.

        Parameters:
        harmonics : list of arrays
            List of individual harmonic components
        X : array
            Non-dimensional spatial coordinates
        """
        plt.figure(figsize=(12, 8))

        # Plot each harmonic
        for k, P_k in enumerate(harmonics):
            # Plot each harmonic and add label
            plt.plot(
                X,
                abs(P_k),
                label=f"{k+1}th harmonic ({k+1} × f0)",
                alpha=0.5,
                linewidth=0.5
            )
            # plt.plot(
            #     X,
            #     -P_k,
            #     alpha=0.5,
            #     linewidth=0.5
            # )

        # Plot formatting
        plt.title('Individual Harmonic Components of Acoustic Pressure', fontsize=14)
        plt.xlabel('X [-]', fontsize=12)
        plt.ylabel('p\' [Pa]', fontsize=12)
        plt.legend(loc='upper right', fontsize=8, ncol=2)  # Add legend
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()


def main():
    # Create resonator instance
    resonator = AcousticResonator()

    # Spatial grid from 0 to 1
    X = np.linspace(0, 1, 200)

    # Calculate all harmonic components
    harmonics = resonator.calculate_wave_components(X)

    # Plot all harmonics in a single coordinate system
    resonator.plot_all_harmonics(harmonics, X)


if __name__ == "__main__":
    main()
