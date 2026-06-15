
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

#!/usr/bin/env python3
# Stacked 1D prime waves with vertical dotted lines at every crest (tip).
# Lowest primes are at the BOTTOM; higher primes stack upward.

import numpy as np
import math
import matplotlib.pyplot as plt

# ------------ knobs ------------
N_LINES       = 60           # how many primes to show (first N)
R_MAX         = 120.0        # plot r from 0 .. R_MAX (units)
SAMPLES       = 20000         # x resolution

k_base        = 0.055        # rad / unit
k_power       = 1.0          # k(p) = k_base * p**k_power
phase_mode    = "zero"       # "zero" or "random"
phase_jitter  = 0.         # rad, if phase_mode == "random"

amp_scale     =.06         # same amplitude for every line
line_spacing  = .1         # vertical gap between stacked lines
draw_sum      = False        # add the sum as the last (top) line
wave_linewidth = 0.3         # line width for waves


# Crest (tip) markers
DRAW_TIP_LINES = False      # make true to see verticle lines through crest tips for comparison
TIP_LINE_MODE  = "full"      # "full" spans the whole figure; "local" draws a short segment per line
TIP_LOCAL_FRAC = 0.45        # half-height of local segment as a fraction of line_spacing
TIP_COLOR      = (0, 0, 0, 0.35)
TIP_LW         = .1
TIP_STYLE      = "-"         # dotted

# Clean layout toggles
SHOW_LABELS = False          # left-side per-line labels (prime/k/λ)
SHOW_TITLE  = True           # overall title
SAVE_PATH   = None           # e.g., "stacked_prime_lines.png" or None to skip saving

# ------------ primes ------------
def first_n_primes(n: int):
    if n <= 0:
        return []
    if n < 6:
        limit = 15
    else:
        nn = float(n)
        limit = int(nn*(math.log(nn) + math.log(math.log(nn))) + 10*nn)
    sieve = np.ones(limit+1, dtype=bool)
    sieve[:2] = False
    for p in range(2, int(limit**0.5)+1):
        if sieve[p]:
            sieve[p*p::p] = False
    return np.flatnonzero(sieve)[:n].tolist()

primes = first_n_primes(N_LINES)

# ------------ x-axis (radius) ------------
r = np.linspace(0.0, R_MAX, SAMPLES)

# ------------ crest (tip) positions ------------
def crest_positions(k: float, phi: float, r_max: float):
    """Return radii r where cos(k r + phi) = +1 (crests) within [0, r_max]."""
    twopi = 2*np.pi
    # smallest n with r >= 0
    n = int(np.ceil(phi / twopi))
    rs = []
    while True:
        rr = (twopi*n - phi) / k
        if rr > r_max + 1e-12:
            break
        if rr >= 0.0:
            rs.append(rr)
        n += 1
    return np.array(rs, float)

# ------------ build lines ------------
rng = np.random.default_rng(123)
lines, labels, crest_lists = [], [], []

for p in primes:
    k   = k_base * (p**k_power)
    phi = 0.0 if phase_mode == "zero" else rng.uniform(-phase_jitter, phase_jitter)
    z   = amp_scale * np.cos(k*r + phi)
    lines.append(z)
    crest_lists.append(crest_positions(k, phi, R_MAX))

    lam = 2*np.pi/k
    labels.append(f"p={p}  k={k:.3f}  λ={lam:.1f}")

if draw_sum:
    lines.append(np.sum(np.stack(lines, axis=0), axis=0))
    crest_lists.append(np.array([]))   # skip crest markers for the sum
    labels.append("sum of above")

# ------------ plot (stacked; LOW primes at BOTTOM) ------------
nrows  = len(lines)
height = max(6, 1.2*nrows)
fig, ax = plt.subplots(figsize=(10, height))

# clean sketch look
ax.set_xticks([]); ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

# vertical offsets from bottom upward
offsets = np.arange(0, nrows) * line_spacing  # 0, 1s, 2s, ...

for z, off, lab, tips in zip(lines, offsets, labels, crest_lists):
    ax.plot(r, z + off, color="black", linewidth=wave_linewidth)
    if SHOW_LABELS:
        ax.text(r[0], off, lab, va="center", ha="left", fontsize=10)

    if DRAW_TIP_LINES and tips.size:
        if TIP_LINE_MODE == "full":
            for rr in tips:
                ax.axvline(rr, linestyle=TIP_STYLE, color=TIP_COLOR, linewidth=TIP_LW)
        else:
            y0 = off - TIP_LOCAL_FRAC*line_spacing
            y1 = off + TIP_LOCAL_FRAC*line_spacing
            for rr in tips:
                ax.plot([rr, rr], [y0, y1], linestyle=TIP_STYLE, color=TIP_COLOR, linewidth=TIP_LW)

ax.set_xlim(r.min(), r.max())
ax.set_ylim(-line_spacing, offsets.max() + line_spacing)

if SHOW_TITLE:
    ax.set_title("Stacked 1D prime waves — crests marked with vertical dotted lines")

plt.tight_layout()
plt.subplots_adjust(left=0.03)  # tighten left margin (good when labels are hidden)

if SAVE_PATH:
    plt.savefig(SAVE_PATH, dpi=150, bbox_inches="tight")

plt.show()


      