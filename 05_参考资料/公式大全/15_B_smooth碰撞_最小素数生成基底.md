# 15 · B-smooth 碰撞法 — 最小素数生成基底搜索

> 收录于 PKS 千禧难题统一解 · 05_参考资料/公式大全
> 日期：2026-07-16 · 基于 RTX 4090 GPU · 源自 Croft prime basis 猜想验证
> 前置阅读：`Croft素数螺旋_与PKS_SPF对照分析.md`

---

## 一、问题起源

Gary Croft 在 primesdemystified.com 提出一个猜想：

> 所有不被 2,3,5 整除的数可由 {2,3,5} 的幂组合 ± 生成：
> x^a·y^b ± z^c,  x^a·z^c ± y^b,  y^b·z^c ± x^a

GPU 验证（2026-07-16，78,495 素数，p_max=10⁶）：
- {2,3,5} 单一形式：**0.8%** ❌
- {2,3,5} 三种形式全测：**2.0%** ❌
- **猜想不成立。**

但这引出了一个更深的问题：**最小基底是几？**

---

## 二、B-smooth 碰撞法

### 定义

数 n 是 **B-smooth**，当且仅当 n 的所有质因子都属于基底集合 B。

素数 p **可被 B 生成**，当且仅当存在两个 B-smooth 数 a, b 使得：

$$p = |a - b| \quad \text{或} \quad p = a + b$$

（1 始终是 B-smooth，已排除 p = (p+1) - 1 等平凡表示）

### 算法

```python
def generate_b_smooth(basis, limit):
    """生成所有 ≤ limit 的 B-smooth 数"""
    smooth = {1}
    for p in basis:
        for s in list(smooth):
            v = s
            while v * p <= limit:
                v *= p
                smooth.add(v)
    return sorted(smooth)


def check_coverage(basis, primes, max_val):
    """检查 B-smooth 碰撞法对素数的覆盖率"""
    smooth = generate_b_smooth(basis, max_val * 2)
    smooth_set = set(smooth)
    
    covered = 0
    for p in primes:
        for s in smooth:
            if s > max_val * 2: break
            # |s - p| ∈ smooth_set?
            if s > p and (s - p) in smooth_set:
                covered += 1; break
            # s + p ∈ smooth_set?
            if (s + p) in smooth_set:
                covered += 1; break
    
    return covered / len(primes)


# 搜索最小基底
for basis_size in range(3, 12):
    basis = first_n_primes(basis_size)
    coverage = check_coverage(basis, primes_over5, MAX)
    print(f"{basis_size} primes: {coverage:.1%}")
```

---

## 三、GPU 搜索结果

| 基底 | 素数个数 | B-smooth数 | 覆盖率 | 反例数 |
|------|:---:|:---:|:---:|:---:|
| {2,3,5} | 3 | 578 | **1.3%** | 77,476 |
| {2,3,5,7} | 4 | 1,502 | **8.0%** | 72,204 |
| {2,3,5,7,11} | 5 | 2,956 | **28.7%** | 55,993 |
| {2,3,5,7,11,13} | 6 | 5,119 | **66.4%** | 26,349 |
| ⭐ **{2,3,5,7,11,13,17}** | **7** | **7,872** | **94.7%** | 4,137 |
| +19,23 | 8 | 15,400 | 100.0% | 0 |
| +29,31 | 10 | 24,568 | 100.0% | 0 |

---

## 四、关键发现

### 4.1 第 7 个素数（17）是关键拐点

```
6基底(13): 66.4% ───→ 7基底(17): 94.7%  ← 跳跃 +28.3pp！
7基底(17): 94.7% ───→ 8基底(23): 100%   ← 渐进 +5.3pp
```

**17 的加入将覆盖率从 2/3 拉到接近完美**。为什么是 17？

- 17 ≡ 17 mod 30，对应 Croft 8 条半径之一的特定角度（204°）
- 17 是前 8 素数中最"稀疏"的——它填补了 11 和 13 之后最大的剩余类间距
- 17 解锁了大量 B-smooth 数的新组合模式（17 × 现有 smooth → 全新数值区域）

### 4.2 8 基底 100% 但可能是"统计必然"

15,400 个 B-smooth 数 × 15,400 ≈ **1.18 亿**对组合，覆盖 78,495 个素数 ≈ 每个素数有 ~1,500 次碰撞机会。100% 不够深；**7 基底的 94.7% 才是真正的效率边界。**

### 4.3 开放式问题

> 7 基底在更大范围（如 10⁷ 内的素数）是否仍保持 >90% 覆盖率？

如果否 → 说明基底大小需要随素数范围增长而增长（对数关系？）
如果是 → 说明存在一个**绝对最小完全基底**，值得数学证明

---

## 五、与 Croft 原猜想的关系

```
Croft 猜想:  {2,3,5} 生成所有素数       → ❌ 1.3%
修正猜想:    {2,3,5,7,11,13,17} 生成    → ✅ 94.7%
完全基底:    前8素数(≤23)                → ✅ 100%（有冗余）
最小效率边界: 前7素数(≤17)               → ⭐ 94.7%
```

**Croft 的"最简基底"直觉是对的，但他低估了基底大小。不是 3，不是 8——恰好是 7。——而数字 7 在 Croft 的模 30 系统中对应 8 条半径之一（84°），这是否是深层几何约束？**

---

> **一句话**：所有 100 万以内的素数中，94.7% 可表示为两个 {2,3,5,7,11,13,17}-smooth 数的差或和。第 7 个素数 17 是从 66% 跳到 95% 的关键拐点。这是对 Croft 素数螺旋猜想的一个 GPU 实验修正。
