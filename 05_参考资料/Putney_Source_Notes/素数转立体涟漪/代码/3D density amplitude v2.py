
# prime_wavefield_demo.py (excerpt)
import numpy as np

def gaps_to_freqs(primes):
    gaps = np.diff(primes)
    return 1.0 / gaps

def prime_wave_field(primes, phases=None):
    freqs = gaps_to_freqs(primes)
    if phases is None:
        phases = np.zeros_like(freqs)
    # toy superposition (1D)
    x = np.linspace(0, 1, 2000)
    field = sum(np.cos(2*np.pi*f*x + p) for f, p in zip(freqs, phases))
    return x, field

# ... (put your full script here)
# prime_sine_forest_3d_range.py
# 3-D “stacked rings” of prime modes with flexible PRIME SELECTION.

# adjacent_prime_interference_density.py
# Heatmap (filled disk) of adjacent-prime pair interference on concentric rings

import numpy as np
import matplotlib.pyplot as plt

# ---------------- user controls ----------------
N_PAIRS   = 1000        # how many adjacent-prime pairs (rings)
THETA_SAMPLES = 2048    # angular samples per ring (columns)
R0        = 0           # first ring radius (pixels/units)
DR        = 1           # ring spacing (pixels/units)

ALPHA     = 0.02        # amplitude falloff A_m = m^(-ALPHA)  (very weak)
MODE      = 'sum'       # 'sum' or 'product'
PER_RING_SCALE = True   # normalize each ring by its own max|z|
CMAP      = 'viridis'
TITLE     = 'Adjacent-prime interference rings (line version, gradient)'
ANNOTATE_DIAGONAL = True
# ------------------------------------------------

def first_n_primes(n: int):
    if n <= 0: return []
    size = max(20, int(n * (np.log(max(3,n)) + np.log(max(3,np.log(max(3,n))))) + 10))
    while True:
        sieve = np.ones(size, dtype=bool)
        sieve[:2] = False
        for p in range(2, int(size**0.5)+1):
            if sieve[p]:
                sieve[p*p:size:p] = False
        ps = np.flatnonzero(sieve)
        if len(ps) >= n:
            return ps[:n].tolist()
        size *= 2

def prime_pairs(n_pairs: int):
    ps = first_n_primes(n_pairs + 1)
    return np.array([ps[:-1], ps[1:]]).T  # shape (n_pairs, 2)

def ring_interference(theta, m1, m2, alpha=0.02, mode='sum'):
    A1 = m1**(-alpha)
    A2 = m2**(-alpha)
    u1 = A1*np.cos(m1*theta)
    u2 = A2*np.cos(m2*theta)
    return (u1 + u2) if mode == 'sum' else (u1*u2)

def main():
    pairs = prime_pairs(N_PAIRS)                 # (N,2)
    theta = np.linspace(0, 2*np.pi, THETA_SAMPLES, endpoint=False)  # (T,)

    # compute z for each ring (vectorized over theta)
    Z = np.empty((N_PAIRS, THETA_SAMPLES), dtype=np.float32)
    for i, (m1, m2) in enumerate(pairs):
        z = ring_interference(theta, int(m1), int(m2), alpha=ALPHA, mode=MODE)
        if PER_RING_SCALE:
            s = np.max(np.abs(z))
            if s > 1e-15: z = z / s
        Z[i] = z

    # optional: map z from [-1,1] -> [0,1] for colormap
    Zc = 0.5*(Z + 1.0)

    # build polar grid and render as a filled disk
    r = R0 + np.arange(N_PAIRS)*DR                    # (N,)
    R, T = np.meshgrid(r, theta, indexing='ij')       # (N,T)
    X = R*np.cos(T); Y = R*np.sin(T)

    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal', 'box')
    ax.set_axis_off()

    # pcolormesh wants bin corners; make simple half-step edges
    re = np.concatenate([r - 0.5*DR, [r[-1] + 0.5*DR]])
    te = np.concatenate([theta, [2*np.pi]])
    Re, Te = np.meshgrid(re, te, indexing='ij')
    Xe = Re*np.cos(Te); Ye = Re*np.sin(Te)

    # draw the heatmap
    pm = ax.pcolormesh(Xe, Ye, Zc, shading='auto', cmap=CMAP)

    # outer circular boundary
    Rmax = r[-1] + 0.5*DR
    circ = plt.Circle((0,0), Rmax, edgecolor='0.5', facecolor='none', lw=2)
    ax.add_patch(circ)

    # diagonal seam (just a guide for the eye)
    if ANNOTATE_DIAGONAL:
        ax.plot([-Rmax, Rmax], [Rmax, -Rmax], ls='--', lw=1.5, color='0.6', alpha=0.8)

    # colorbar
    cb = fig.colorbar(pm, ax=ax, shrink=0.85, pad=0.02)
    cb.set_label('normalized pair interference (z)')

    ax.set_title(f"{TITLE}\nN_pairs={N_PAIRS}, α={ALPHA}, mode={MODE}, "
                 f"DR={DR}, per_ring_scale={PER_RING_SCALE}", pad=12)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()


      