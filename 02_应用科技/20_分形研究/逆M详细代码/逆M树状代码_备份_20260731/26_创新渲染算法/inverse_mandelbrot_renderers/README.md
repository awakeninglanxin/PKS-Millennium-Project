# Inverse Mandelbrot — Rendering Toolkit

**Formula:** $z_{n+1} = z_n^2 + \frac{1}{c}, \quad z_0 = 0$

**Viewport:** $\text{Re}(c) \in [-3, 7], \quad \text{Im}(c) \in [-4, 4]$

**Orientation:** Positive real axis pointing UP (vertical flip)

---

## Quick Start

```bash
# 1. Install dependencies (one time)
pip install numpy matplotlib scipy

# 2. Run the baseline (should take ~10 seconds)
python 01_escape_time_basic.py

# 3. Run the orbit-trap version (the key texture script)
python 02_orbittrap_rays.py

# 4. Run the high-quality combined renderer
python 04_hires_combined.py

# 5. Or explore parameters freely
python 05_explore_params.py 800 640 8000 36
```

---

## File Guide

| Script | Purpose | What it produces |
|--------|---------|------------------|
| `01_escape_time_basic.py` | Baseline escape-time + smooth coloring | Simple teardrop outline, no fan texture |
| `02_orbittrap_rays.py` | **Core algorithm** — orbit traps + radial lines | Teardrop + radial triangular fan spokes |
| `03_density_histogram.py` | Density histogram of full trajectories | z-space "flow cloud" (different perspective) |
| `04_hires_combined.py` | **Best quality** — all techniques combined | Publication-grade upright teardrop |
| `05_explore_params.py` | CLI parameter explorer | Quick A/B testing of settings |

---

## How the "Non-Sticky" Look Works

The ethereal, noiseless appearance is a **three-layer effect**:

1. **Smooth potential field** (Hubbard-Douady): gives the gradual relief
2. **Orbit traps** (radial lines + axes): draws the geometric skeleton — the "fans"
3. **Logarithmic tone mapping**: $\text{output} = \frac{\log(1 + x \cdot k)}{\log(1 + k)}$ compresses bright cores and lifts faint structures

### Why "orbit traps" produce fans

At each iteration step, we measure:
- Distance from $z_n$ to the nearest radial line through origin
- Distance from $z_n$ to the real/imaginary axes

Points whose orbits repeatedly come close to a radial line get brighter. Since the inverse Mandelbrot dynamics has rotational symmetry about the real axis, the orbits naturally align with specific angular sectors → **triangular fan pattern**.

---

## Tuning Parameters

In `04_hires_combined.py`, edit these at the top:

| Parameter | Default | Effect |
|-----------|---------|--------|
| `MAX_ITER` | 10000 | Higher = more detailed boundary & fans |
| `N_RAYS` | 48 | More = sharper, denser spokes |
| `W_POTENTIAL` | 0.25 | Higher = smoother, less fan contrast |
| `W_RADIAL` | 0.60 | Higher = brighter fan lines |
| `LOG_FACTOR` | 12.0 | Higher = more ethereal/flat |
| `BLUR_SIGMA` | 0.8 | Higher = softer edges |

---

## Performance Expectations

On a typical laptop (Apple M2 / Intel i7):

| Resolution | MAX_ITER | N_RAYS | Time |
|------------|----------|--------|------|
| 400×320 | 3000 | 24 | ~10 sec |
| 800×640 | 8000 | 36 | ~2 min |
| 1200×960 | 10000 | 48 | ~5 min |
| 2400×1920 | 50000 | 72 | ~30 min |

Installing `numba` (`pip install numba`) can speed up the iteration loop by 10-50x.

---

## The Five Scripts in Order

```
01 → establishes the formula works (bare teardrop)
02 → adds the orbit-trap fans (the "aha!" moment)
03 → alternative: density histogram approach
04 → combines everything at high quality
05 → explore & tune freely
```

---

## About This Project

This rendering toolkit is part of the **Inverse Mandelbrot Application** project,
exploring the mathematical, visual, and philosophical dimensions of the inverse
Mandelbrot set — from pure complex dynamics to sacred geometry.

GitHub: https://github.com/awakeninglanxin/inverse-Mandelbrot-application

---

> ⚠️ **重要声明 / Important Disclaimer**
> 
> 本文档由 AI 辅助生成，部分结论可能存在 AI 幻觉导致的论证不严谨之处。
> 文中提出的数学、物理及相关跨学科观点，需要经过专业数学家、物理学家
> 及相关领域专家共同验证与检验。
> 如有疏漏、错误或不同见解，敬请指正，不胜感激。
> 
> **This document was AI-assisted. Some conclusions may contain inaccuracies
> due to AI hallucination. All mathematical, physical, and interdisciplinary
> claims require verification by professional mathematicians, physicists,
> and subject-matter experts. Corrections and feedback are warmly welcomed.**
