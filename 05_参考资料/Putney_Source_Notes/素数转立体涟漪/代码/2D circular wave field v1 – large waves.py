
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

# ... (full script here)
# 3-D “stacked rings” of prime modes with flexible PRIME SELECTION.


import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import matplotlib.colors as mcolors
import matplotlib.cm as cm

# ───────────────── CONFIG ─────────────────

# ----- How to choose which primes to plot -----
PRIMES_MODE = "index_range"   # one of: "first_n" | "index_range" | "value_range" | "explicit"

FIRST_N        = 1             # used if PRIMES_MODE == "first_n"
INDEX_RANGE    = (2,50000)   # inclusive ordinals (1-indexed): (start_k, end_k), used if "index_range"
VALUE_RANGE    = (2, 3)   # inclusive values (p_min, p_max), used if "value_range"
EXPLICIT_LIST  = [3,5,]    # used if "explicit"

SAMPLE_EVERY   = 5         # keep every k-th selected prime (1 = keep all)

# ----- Geometry/visuals -----
R_base = 10                 # base circle radius
theta_samples = 10000         # resolution around the circle (lower -> faster)
amplitude0 = 2              # overall ripple amplitude scale
amp_exponent = 0.0            # amplitude ~ amplitude0 * p**amp_exponent (0=equal, >0 emphasize larger primes)
phase_jitter = 0.0            # random phase per ring (radians); 0 disables

lw_ring = .1                   # line width for each ring
alpha_ring = .05               # line alpha
radial_growth_per_prime =1     # outward push per ring (try 0.5..3 for clarity)
z_step = 0.0                    # vertical separation per ring (0 = flat “puddle”)

#fancy color shit
#cmap = cm.get_cmap("BrGr")


# solid red colormap
cmap = mcolors.ListedColormap(["Blue"])


RNG  = np.random.default_rng(0)  # deterministic visuals

# ──────────────── prime utils ────────────────

def sieve_up_to(limit: int) -> np.ndarray:
    """Return all primes <= limit (simple vectorized sieve)."""
    if limit < 2:
        return np.array([], dtype=int)
    sieve = np.ones(limit + 1, dtype=bool)
    sieve[:2] = False
    for p in range(2, int(limit**0.5) + 1):
        if sieve[p]:
            sieve[p*p::p] = False
    return np.flatnonzero(sieve)

def first_n_primes(n: int) -> np.ndarray:
    """Return the first n primes (uses a loose upper bound for nth prime)."""
    if n <= 0:
        return np.array([], dtype=int)
    if n < 6:
        limit = 15
    else:
        nn = float(n)
        # Rosser–Schoenfeld-ish bound + safety
        limit = int(nn * (np.log(nn) + np.log(np.log(nn))) + 20)
    ps = sieve_up_to(limit)
    # If our bound was too low (rare), increase and try again.
    while ps.size < n:
        limit *= 2
        ps = sieve_up_to(limit)
    return ps[:n]

def primes_by_index_range(k_start: int, k_end: int) -> np.ndarray:
    """Return primes with ordinals k_start..k_end (1-indexed, inclusive)."""
    if k_end < k_start:
        return np.array([], dtype=int)
    ps = first_n_primes(k_end)
    return ps[k_start-1:k_end]

def primes_by_value_range(p_min: int, p_max: int) -> np.ndarray:
    """Return all primes in [p_min, p_max]."""
    if p_max < 2 or p_max < p_min:
        return np.array([], dtype=int)
    ps = sieve_up_to(p_max)
    return ps[(ps >= p_min) & (ps <= p_max)]

# ─────────────── choose primes ───────────────

if PRIMES_MODE == "first_n":
    primes = first_n_primes(FIRST_N)

elif PRIMES_MODE == "index_range":
    k0, k1 = INDEX_RANGE
    primes = primes_by_index_range(k0, k1)

elif PRIMES_MODE == "value_range":
    p0, p1 = VALUE_RANGE
    primes = primes_by_value_range(p0, p1)

elif PRIMES_MODE == "explicit":
    primes = np.array(sorted(set(EXPLICIT_LIST)), dtype=int)

else:
    raise ValueError("PRIMES_MODE must be one of: first_n | index_range | value_range | explicit")

# optional thinning
if SAMPLE_EVERY > 1:
    primes = primes[::SAMPLE_EVERY]

num_primes = primes.size
if num_primes == 0:
    raise RuntimeError("No primes selected with the current configuration.")

# ─────────────── build rings ───────────────

theta = np.linspace(0, 2*np.pi, theta_samples, endpoint=True)

fig = plt.figure(figsize=(11, 8))
ax  = fig.add_subplot(111, projection="3d")
# descriptive title
if PRIMES_MODE == "first_n":
    subtitle = f"first_n={FIRST_N}"
elif PRIMES_MODE == "index_range":
    subtitle = f"k∈[{INDEX_RANGE[0]},{INDEX_RANGE[1]}]"
elif PRIMES_MODE == "value_range":
    subtitle = f"p∈[{VALUE_RANGE[0]},{VALUE_RANGE[1]}]"
else:
    subtitle = f"explicit({num_primes})"

ax.set_title(f"Prime sine modes stacked in 3D — selected {num_primes} primes ({subtitle})")
ax.set_axis_off()

# faint base circle
x0 = R_base*np.cos(theta); y0 = R_base*np.sin(theta)
ax.plot(x0, y0, np.zeros_like(theta), color="0.85", lw=0.8, alpha=0.5)

segs, rgba, lws = [], [], []

for i, p in enumerate(primes):
    a   = amplitude0 * (p**amp_exponent)
    R_i = R_base + radial_growth_per_prime * i
    phi = 0.0 if phase_jitter == 0 else RNG.uniform(-phase_jitter, phase_jitter)

    r = R_i + a * np.sin(p*theta + phi)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = np.full_like(theta, i * z_step)

    segs.append(np.stack([x, y, z], axis=1))
    c = cmap(i / max(1, num_primes - 1))
    rgba.append((c[0], c[1], c[2], alpha_ring))
    lws.append(lw_ring)

coll = Line3DCollection(segs, colors=rgba, linewidths=lws)
ax.add_collection(coll)

# autoscale cube
rmax   = (R_base
          + radial_growth_per_prime*(num_primes-1)
          + amplitude0 * (primes.max()**amp_exponent)
          + 0.1)
extent = rmax * 1.15
ax.set_xlim(-extent, extent)
ax.set_ylim(-extent, extent)
ax.set_zlim(-z_step*0.5, z_step*(num_primes-1) + z_step)
ax.view_init(elev=90, azim=0)



plt.tight_layout()
plt.show()


      