# -*- coding: utf-8 -*-
"""
Combine two spiral families into one richer script:
- Family A: Octave (2^n) variant
- Family B: Phi^n variant

Features (for EACH family):
1) 2D Polar Array (HSV colors, rotated copies of the already decayed & per-point rotated curve)
2) t–x(t) & t–y(t) curves
3) 3D Polar Array (HSV colors + XY projection)
PLUS:
4) Combined overlay mode (optional): draw both families together (2D/3D polar arrays)

No PNG saving. Every axis has legend. At the end: plt.tight_layout(); plt.show()
"""

# ===================== Imports & Base =====================
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# ===================== Global Defaults (can be overridden per family) =====================
# You can change these once to quickly try different looks
GLOBAL_T = 2 * np.pi
GLOBAL_user_num = 21        # default periods
GLOBAL_spiral_deg = -45.0    # per-period self-rotation in degrees (0 = no self-rotation)
GLOBAL_polar_array = 9      # number of directions in the polar array (evenly dividing 360°)
GLOBAL_SHIFT = 5

# Drawing aesthetics
LINE_W = 1.0
ALPHA  = 0.9

# Combined overlay toggles (extra feature)
ENABLE_COMBINED_2D = True
ENABLE_COMBINED_3D = True

# ===================== Common helpers =====================
def x_fun(t, b, k, a):
    return a * (2 * np.sin(t) / (b + np.sqrt(b**2 - 4 * k * np.cos(t))))

def y_fun(t, b, k, a, m):
    term1 = -((np.sqrt(1 + k**2) * (-np.sqrt(b**2 - 4*k) + np.sqrt(b**2 - 4*k*np.cos(np.pi)))) / (2*k))
    term2 = ((1 / (2*np.sqrt(1 + k**2))) * (((k**2 - 1)/k) * b + ((k**2 + 1)/k) * np.sqrt(b**2 - 4*k*np.cos(t)))) - \
            ((b * (-1 + k**2) + np.sqrt(b**2 - 4*k) * (1 + k**2)) / (2*k*np.sqrt(1 + k**2)))
    return a * (m*term1 + term2)

def x_minus(t, b, k, a, shift_radian):
    return a * (2 * np.sin(t) / (b + np.sqrt(b**2 - 4 * k * np.cos(t)))) - shift_radian

def y_add(t, b, k, a, m, shift_radian):
    term1 = -((np.sqrt(1 + k**2) * (-np.sqrt(b**2 - 4*k) + np.sqrt(b**2 - 4*k*np.cos(np.pi)))) / (2*k))
    term2 = ((1 / (2*np.sqrt(1 + k**2))) * (((k**2 - 1)/k) * b + ((k**2 + 1)/k) * np.sqrt(b**2 - 4*k*np.cos(t)))) - \
            ((b * (-1 + k**2) + np.sqrt(b**2 - 4*k) * (1 + k**2)) / (2*k*np.sqrt(1 + k**2)))
    return a * (m*term1 + term2) + shift_radian

def rotate_curve_degrees(x, y, angle_deg):
    """Rigid rotation in the plane by angle (degrees)."""
    ang = np.radians(angle_deg)
    ca, sa = np.cos(ang), np.sin(ang)
    xr = x * ca - y * sa
    yr = x * sa + y * ca
    return xr, yr

def apply_rotation_and_decay_per_point(x_data, y_data, amp_factor, rotation_angles_rad):
    """Point-wise rotation (angle varies with t) then amplitude scaling."""
    x_rot = np.zeros_like(x_data)
    y_rot = np.zeros_like(y_data)
    for i in range(len(x_data)):
        ca = np.cos(rotation_angles_rad[i]); sa = np.sin(rotation_angles_rad[i])
        x_rot[i] = x_data[i] * ca - y_data[i] * sa
        y_rot[i] = x_data[i] * sa + y_data[i] * ca
    return x_rot * amp_factor, y_rot * amp_factor

def make_rotation_schedule(user_num, spiral_deg, N):
    """Linear schedule from 0° to user_num*spiral_deg over N samples, in radians."""
    total_deg = user_num * spiral_deg
    degs = np.linspace(0.0, total_deg, N)
    return np.radians(degs)

def auto_equal_xy(ax, xs, ys, pad=1.1):
    xmax = np.max(np.abs(xs)); ymax = np.max(np.abs(ys))
    r = pad * max(xmax, ymax)
    ax.set_xlim(-r, r); ax.set_ylim(-r, r)
    ax.set_aspect('equal', adjustable='box')

# ===================== Family configurations =====================
# Shared params in families
a, m = np.pi, 2/3

def family_2pow_config():
    """
    Family A: Octave (2^n) variant
    Derived from your '2^n' script: k_fun, b_fun, amp_continuous(t).
    """
    T = GLOBAL_T
    def k_fun(t):
        return (4 ** (t / T)) / 6
    def b_fun(t):
        return (5 * (2 ** (t / T)) / 6)
    def amp_continuous(t):
        # your "双曲线" default: (2^(t/T)) / sqrt(9 + 2^(4*(t/T)-2)) / t
        return (2 ** (t/T)) / (np.sqrt(9 + 2 ** (4 * (t/T) - 2))) / t
    # Per-family overrides (matching your original): user_num=21, spiral_deg=45, polar_array=9
    return {
        "name": "Octave 2^n",
        "T": GLOBAL_T,
        "user_num": GLOBAL_user_num,
        "spiral_deg": GLOBAL_spiral_deg,
        "polar_array": GLOBAL_polar_array,
        "shift": GLOBAL_SHIFT,
        "k_fun": k_fun,
        "b_fun": b_fun,
        "amp_fun": amp_continuous,
        "z_fun": lambda t: t / T,
    }

def family_phi_config():
    """
    Family B: Phi^n variant
    Derived from your 'phi^n' script: k_fun, b_fun, amp_continuous(k_n, b_n).
    """
    T = GLOBAL_T
    phi = (np.sqrt(5) - 1) / 2
    def k_fun(t):
        n = t / T
        return phi ** (n + 1)
    def b_fun(t):
        n = t / T
        return np.sqrt(n) + (phi ** (n + 1)) / np.sqrt(n)
    def amp_continuous_from_kb(t):
        # amp depends on k_n, b_n (per your script)
        k_n = k_fun(t); b_n = b_fun(t)
        numerator = np.sqrt(1 + k_n**2)
        denominator = 2 * k_n
        sqrt_term1 = np.sqrt(b_n**2 + 4 * k_n)
        sqrt_term2 = np.sqrt(b_n**2 - 4 * k_n)
        L_n = (numerator / denominator) * (sqrt_term1 - sqrt_term2)
        return 1 / (t * L_n)    # your default: 双曲漏斗状
    # Per-family overrides (matching your original): user_num=21, spiral_deg=45, polar_array=9
    return {
        "name": "Phi^n",
        "T": GLOBAL_T,
        "user_num": GLOBAL_user_num,
        "spiral_deg": GLOBAL_spiral_deg,
        "polar_array": GLOBAL_polar_array,
        "shift": GLOBAL_SHIFT,
        "k_fun": k_fun,
        "b_fun": b_fun,
        "amp_fun": amp_continuous_from_kb,
        "z_fun": lambda t: t / T,
    }

FAMILIES = [family_2pow_config(), family_phi_config()]

# ===================== Compute & Plot per family =====================
all_overlay_curves_2d = {}   # for combined overlay (2D)
all_overlay_curves_3d = {}   # for combined overlay (3D)

for fam in FAMILIES:
    name        = fam["name"]
    T           = fam["T"]
    user_num    = fam["user_num"]
    spiral_deg  = fam["spiral_deg"]
    polar_array = fam["polar_array"]
    shift       = fam["shift"]
    k_fun       = fam["k_fun"]
    b_fun       = fam["b_fun"]
    amp_fun     = fam["amp_fun"]
    z_fun       = fam["z_fun"]

    # ---- sampling over multiple periods ----
    t_min = T
    t_max = T + T * user_num
    t = np.linspace(t_min, t_max, 81 * user_num)

    # ---- base curves using your pair x_minus / y_add ----
    x_add = x_minus(t, b_fun(t), k_fun(t), a, shift)
    y_min = y_add(t,   b_fun(t), k_fun(t), a, m, shift)

    # ---- per-point rotation (spiral_deg) + decay ----
    rot_sched = make_rotation_schedule(user_num, spiral_deg, len(t))
    amp = amp_fun(t)
    x_rot, y_rot = apply_rotation_and_decay_per_point(x_add, y_min, amp, rot_sched)

    # ---- 2D polar array (HSV) ----
    fig2d, ax2d = plt.subplots(figsize=(10, 10))
    ax2d.set_title(f'{name} — 2D Polar Array (N={polar_array})')
    ax2d.set_xlabel('x(t)'); ax2d.set_ylabel('y(t)')
    ax2d.grid(True, alpha=0.3)

    colors = plt.cm.hsv(np.linspace(0, 1, polar_array, endpoint=False))
    family_curves_2d = []  # store for overlay
    for i in range(polar_array):
        angle_deg = i * (360.0 / polar_array)
        xr, yr = rotate_curve_degrees(x_rot, y_rot, angle_deg)
        family_curves_2d.append((xr, yr))
        label = f'Rot {angle_deg:.0f}°' if i == 0 else None
        ax2d.plot(xr, yr, color=colors[i], linewidth=LINE_W, alpha=ALPHA, label=label)

    auto_equal_xy(ax2d, np.concatenate([c[0] for c in family_curves_2d]),
                        np.concatenate([c[1] for c in family_curves_2d]))
    ax2d.legend(loc='upper right')

    # ---- t–x(t) & t–y(t) ----
    fig_tx, ax_tx = plt.subplots(figsize=(12, 4.5))
    ax_tx.plot(t, x_rot, color='tab:blue',  label='x_add(t)',  alpha=ALPHA, linewidth=LINE_W)
    ax_tx.plot(t, y_rot, color='tab:red',   label='y_add(t)',  alpha=ALPHA, linewidth=LINE_W)
    # helper reference (optional): -1/t for visual comparison, like your scripts
    with np.errstate(divide='ignore'):
        ax_tx.plot(t, -1.0/t, color='tab:purple', label='-1/t', alpha=0.7, linewidth=1.0)
    ax_tx.set_title(f'{name} — t vs x(t), y(t)')
    ax_tx.set_xlabel('t'); ax_tx.set_ylabel('Value')
    ax_tx.grid(True, alpha=0.3)
    ax_tx.legend()

    # ---- 3D polar array (HSV + XY projection) ----
    z_vals = z_fun(t)
    fig3d = plt.figure(figsize=(11, 10))
    ax3d = fig3d.add_subplot(111, projection='3d')
    ax3d.set_title(f'{name} — 3D Polar Array (spiral_deg={spiral_deg}°)')
    ax3d.set_xlabel('X'); ax3d.set_ylabel('Y'); ax3d.set_zlabel('Z')

    allx, ally, allz = [], [], []
    family_curves_3d = []  # store for overlay
    colors3d = plt.cm.hsv(np.linspace(0, 1, polar_array, endpoint=False))
    for i, (xr, yr) in enumerate(family_curves_2d):
        # store for overlay
        family_curves_3d.append((xr, yr, z_vals))
        # collect bounds
        allx.extend(xr); ally.extend(yr); allz.extend(z_vals)
        # 3D curve
        label = f'Rot {i*(360/polar_array):.0f}°' if i == 0 else None
        ax3d.plot(xr, yr, z_vals, color=colors3d[i], linewidth=0.8, alpha=0.9, label=label)
        # XY projection
        ax3d.plot(xr, yr, np.zeros_like(z_vals), color=colors3d[i], linewidth=0.7, alpha=0.6, linestyle='--')

    # set equal-ish xy bounds
    x_min, x_max = min(allx), max(allx)
    y_min, y_max = min(ally), max(ally)
    z_min, z_max = min(allz), max(allz)
    x_ctr, y_ctr = (x_min + x_max)/2, (y_min + y_max)/2
    max_xy = max(x_max - x_min, y_max - y_min)
    ax3d.set_xlim(x_ctr - max_xy/2, x_ctr + max_xy/2)
    ax3d.set_ylim(y_ctr - max_xy/2, y_ctr + max_xy/2)
    ax3d.set_zlim(z_min, z_max)
    ax3d.legend(loc='upper left')

    # store for combined overlays
    all_overlay_curves_2d[name] = family_curves_2d
    all_overlay_curves_3d[name] = family_curves_3d

# ===================== Combined Overlays (Extra) =====================
# 2D combined overlay
if ENABLE_COMBINED_2D:
    fig_oc2d, ax_oc2d = plt.subplots(figsize=(10, 10))
    ax_oc2d.set_title('Combined — 2D Polar Arrays (HSV per family)')
    ax_oc2d.set_xlabel('x(t)'); ax_oc2d.set_ylabel('y(t)')
    ax_oc2d.grid(True, alpha=0.3)

    # Assign each family a half-spectrum for better separation
    fam_colorspaces = {
        list(all_overlay_curves_2d.keys())[0]: plt.cm.hsv(np.linspace(0.0, 0.5, len(all_overlay_curves_2d[list(all_overlay_curves_2d.keys())[0]]), endpoint=False)),
        list(all_overlay_curves_2d.keys())[1]: plt.cm.hsv(np.linspace(0.5, 1.0, len(all_overlay_curves_2d[list(all_overlay_curves_2d.keys())[1]]), endpoint=False)),
    }

    xs_all = []; ys_all = []
    for fam_name, curves in all_overlay_curves_2d.items():
        pal = fam_colorspaces[fam_name]
        for i, (xr, yr) in enumerate(curves):
            lab = f'{fam_name} (Rot 0°)' if i == 0 else None
            ax_oc2d.plot(xr, yr, color=pal[i], linewidth=LINE_W, alpha=ALPHA, label=lab)
            xs_all.append(xr); ys_all.append(yr)

    auto_equal_xy(ax_oc2d, np.concatenate(xs_all), np.concatenate(ys_all))
    ax_oc2d.legend(loc='upper right')

# 3D combined overlay
if ENABLE_COMBINED_3D:
    fig_oc3d = plt.figure(figsize=(11, 10))
    ax_oc3d = fig_oc3d.add_subplot(111, projection='3d')
    ax_oc3d.set_title('Combined — 3D Polar Arrays (HSV per family)')
    ax_oc3d.set_xlabel('X'); ax_oc3d.set_ylabel('Y'); ax_oc3d.set_zlabel('Z')

    fam_names = list(all_overlay_curves_3d.keys())
    palA = plt.cm.hsv(np.linspace(0.0, 0.5, len(all_overlay_curves_3d[fam_names[0]]), endpoint=False))
    palB = plt.cm.hsv(np.linspace(0.5, 1.0, len(all_overlay_curves_3d[fam_names[1]]), endpoint=False))

    allx, ally, allz = [], [], []
    for i, (xr, yr, z_vals) in enumerate(all_overlay_curves_3d[fam_names[0]]):
        lab = f'{fam_names[0]} (Rot 0°)' if i == 0 else None
        ax_oc3d.plot(xr, yr, z_vals, color=palA[i], linewidth=0.8, alpha=0.9, label=lab)
        ax_oc3d.plot(xr, yr, np.zeros_like(z_vals), color=palA[i], linewidth=0.7, alpha=0.6, linestyle='--')
        allx.extend(xr); ally.extend(yr); allz.extend(z_vals)

    for i, (xr, yr, z_vals) in enumerate(all_overlay_curves_3d[fam_names[1]]):
        lab = f'{fam_names[1]} (Rot 0°)' if i == 0 else None
        ax_oc3d.plot(xr, yr, z_vals, color=palB[i], linewidth=0.8, alpha=0.9, label=lab)
        ax_oc3d.plot(xr, yr, np.zeros_like(z_vals), color=palB[i], linewidth=0.7, alpha=0.6, linestyle='--')
        allx.extend(xr); ally.extend(yr); allz.extend(z_vals)

    # equal-ish xy bounds
    x_min, x_max = min(allx), max(allx)
    y_min, y_max = min(ally), max(ally)
    z_min, z_max = min(allz), max(allz)
    x_ctr, y_ctr = (x_min + x_max)/2, (y_min + y_max)/2
    max_xy = max(x_max - x_min, y_max - y_min)
    ax_oc3d.set_xlim(x_ctr - max_xy/2, x_ctr + max_xy/2)
    ax_oc3d.set_ylim(y_ctr - max_xy/2, y_ctr + max_xy/2)
    ax_oc3d.set_zlim(z_min, z_max)
    ax_oc3d.legend(loc='upper left')

# ===================== Show =====================
plt.tight_layout()
plt.show()
