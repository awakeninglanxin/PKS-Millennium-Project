# Croft 素数螺旋筛 — 算法原理与性能分析

> 📐 收录于 PKS 千禧难题统一解 · 03_验证工具/09_croft_benchmark/
> 🔗 [primesdemystified.com](https://www.primesdemystified.com/)

---

## 一、算法思想

Croft 螺旋筛 (Prime Spiral Sieve) 基于模 30 轮筛法——仅筛选与 30 互质的自然数。

**核心观察**: 所有素数 > 5 必定与 30 互质 (即 n ≢ 0,2,3,4,5,6,8,9,10,12,14,15,16,18,20,21,22,24,25,26,27,28 mod 30)

Euler totient: φ(30) = 8

**8 个素数根 (模 30 互质剩余类)**:
```
n ≌ {1, 7, 11, 13, 17, 19, 23, 29} mod 30
```

**周期-8 递推差值 (8拍回文)**:
```
{6, 4, 2, 4, 2, 4, 6, 2}  →  重复无限
```

生成序列: 1 → 7 → 11 → 13 → 17 → 19 → 23 → 29 → 31 → 37 → ...

---

## 二、算法复杂度

| 维度 | Croft 螺旋筛 | 经典埃拉托色尼 |
|------|-------------|--------------|
| 候选数占比 | 8/30 ≈ 26.67% | 100% |
| 外循环加速 | 3.75× | 1× |
| 时间复杂度 | O(0.27 n log log n) | O(n log log n) |
| 空间复杂度 | O(n) (bool 数组) | O(n) |
| 实测加速比 (n=10⁵) | **1.9×** | 1× |

---

## 三、Python 参考实现

```python
def sieve_croft(limit):
    """Croft 螺旋筛 — 模30 外循环优化"""
    if limit < 2: return []
    if limit < 7: return [p for p in [2,3,5] if p <= limit]

    s = [True] * (limit + 1)
    s[0] = s[1] = False

    # 仅遍历与30互质的候选数 (跳过73.33%的自然数)
    deltas = [6, 4, 2, 4, 2, 4, 6, 2]
    n, di = 7, 1
    while n * n <= limit:
        if s[n]:
            for m in range(n * n, limit + 1, n):
                s[m] = False
        n += deltas[di]
        di = (di + 1) % 8

    # 在候选空间中收集结果 (同样跳过73.33%)
    result = [2, 3, 5]
    n, di = 7, 1
    while n <= limit:
        if s[n]:
            result.append(n)
        n += deltas[di]
        di = (di + 1) % 8
    return result
```

---

## 四、本机基准测试 (Python 3.13, Windows x64)

| 算法 | π(10⁵)耗时 | vs Croft | primes/s |
|------|-----------|----------|----------|
| **Croft 螺旋筛** | **0.0145s** | 🥇 1× | 659k |
| 埃拉托色尼筛 | 0.0274s | 1.9× | 350k |
| Sundaram 筛 | 0.0762s | 5.3× | 126k |
| Atkin 筛 | 0.0759s | 5.2× | 126k |
| 试除法 | 0.3719s | 25.6× | 26k |
| 6k±1 试除法 | 0.2242s | 15.5× | 43k |

---

## 五、与其他已知基准的对比

| 来源 | Croft vs Eratos 加速比 | 测试范围 |
|------|----------------------|---------|
| Python Tutor 2011 | Croft "fastest, >1000× 比 trial division" | 5分钟极限 |
| Rosetta Code | Croft = 最快确定性算法 | 10⁶ |
| 本机 2026-06-12 | 1.9× (n=10⁵) | 10³~10⁵ |
| primesdemystified.com | 理论 ~3.75× (外循环) | ∞ |

---

## 六、素数计数的无试除方法

利用 Croft 筛的 576 个模 90 因式分解二元组，可以不识别任何具体素数的情况下计算 π(x):

```
π(x) = |{n ≤ x : n ≌ {1,7,11,13,17,19,23,29} mod 30}| − |合数二元组数| + 3
```

其中 "+3" 为素数 2, 3, 5。

---

## 七、模 90 扩展

| 模数 | φ(n) | 剩余类数 | 候选占比 |
|------|------|---------|---------|
| 30 | 8 | 8 | 26.67% |
| 90 | 24 | 24 | 26.67% |
| 210 | 48 | 48 | 22.86% |

模 90 产生 24 周期数字根循环 + Magic Mirror Matrix (24×24 拉丁方阵，576 二元组)。

---

*算法来源*: Gary W. Croft, Prime Spiral Sieve — [primesdemystified.com](https://www.primesdemystified.com/)
*实现参考*: [pyprimes (Google Code)](https://code.google.com/archive/p/pyprimes/), [Rosetta Code](https://rosettacode.org/wiki/Prime_decomposition#Python:_Using_Croft_Spiral_sieve)
*本机基准*: `03_验证工具/09_croft_benchmark/benchmark.py`
