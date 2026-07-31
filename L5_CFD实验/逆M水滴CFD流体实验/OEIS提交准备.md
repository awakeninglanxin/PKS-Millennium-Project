# OEIS 提交准备：逆M心形 Douglas-Peucker 拐点序列

> **两个候选序列均在 OEIS 中不存在**（2026-07-11 搜索确认）。
> 提交网址: https://oeis.org/Submit.html

---

## 候选序列 A：标准序列 (19项)

```
34, 44, 50, 68, 84, 96, 102, 134, 168, 188, 216, 244, 264, 290, 312, 330, 362, 414, 492
```

### 提交信息

**Name**: Greedy Douglas-Peucker inflection points (total vertices) for the Inverse Mandelbrot set main cardioid, starting from the 12 Farey fraction anchors (periods 1 through 8).

**Comments**: Starting from the 12 upper-half-plane Farey anchors of periods 1-8 on the main cardioid of the Mandelbrot set inverted via c→1/c, the Douglas-Peucker-like greedy insertion algorithm adds vertices one at a time to the point of maximum deviation. The sequence lists the total vertex counts (including the initial 24 seed vertices) at which the 5-point sliding-window slope ratio of marginal efficiency drops below a factor of 3, indicating a fundamental change in the optimization landscape. The sequence converges at 492 vertices, beyond which no further inflections (slope ratio > 3) are detected.

**Formula**: Starting from 12 Farey fraction seeds (= 24 vertices) at periods 2−8 on the inverse Mandelbrot cardioid, greedily insert a vertex at argmax(max_dev(gap_i)) until max_dev < 5×10⁻⁵. Record vertex counts where 5-point slope ratio of consecutive max_dev values exceeds 3, and then filter out adjacent pairs differing by 2.

**Keywords**: `cons` `fini` `full` — convergent finite sequence, fully enumerated

**Links**: (Your preferred link to the technical document)

**Example**: For M=12 seeds (periods 1-8, 24 vertices), the greedy algorithm finds the first inflection at 34 total vertices, meaning the marginal efficiency of adding vertices dropped dramatically after 10 additional vertices. The last inflection occurs at 492, after which the algorithm enters a smooth convergence phase with Δn=2 (constant spacing).

---

## 候选序列 B：极简序列 (11项)

```
18, 46, 50, 100, 156, 198, 250, 310, 370, 430, 472
```

### 提交信息

**Name**: Greedy Douglas-Peucker inflection points (total vertices) for the Inverse Mandelbrot set main cardioid, starting from 4 Farey fraction anchors (periods 1 through 4).

**Comments**: Minimal case with only 4 seed anchors (=8 vertices). Despite having the fewest possible seeds that still capture the cardioid's basic topology, the sequence exhibits 11 inflection points before converging. Noteworthy: this has the fewest inflection points among all period 2−25 variants but the longest convergence tail (140 additional vertices before geometric convergence).

**Keywords**: `cons` `fini` `full` `hard` — convergent finite, hard to compute due to large number of greedy insertions

---

## 候选序列 C (备选)：纯增量序列

```
10, 20, 26, 44, 60, 72, 78, 110, 144, 164, 192, 220, 240, 266, 288, 306, 338, 390, 468
```

纯增量 = 候选序列A各项 - 24（12种子×2顶点）。

---

## 配套材料

建议提交时附带：

| 材料 | 路径 | 说明 |
|------|------|------|
| 原理图 | `droplet_9special_compare.png` | 9种M的锚点+拐点可视化 |
| 算法原理 | `拐点序列通项公式与收敛极限.md` | 收敛极限570的推导 |
| 对比文档 | `9种特殊M极值分析.md` | M=2~101极值分析 |
| 数论背景 | `逆M水滴_Euler_Totient与泡拓扑.md` | φ(n)与Farey锚点 |
| 生成代码 | `multiM_inflection.py` | 可复现的Python代码 |

---

## 提交检查清单

| 项目 | 候选A | 候选B |
|------|:---:|:---:|
| 整数序列 ≥4项 | ✅ 19项 | ✅ 11项 |
| 不在OEIS | ✅ 已确认 | ✅ 已确认 |
| 数学定义明确 | ✅ | ✅ |
| 可复现 | ✅ Python代码 | ✅ |
| 足够项填3行 | ⚠ 19项≈200字符 | ⚠ 11项≈120字符 |
| Keywords适当 | cons,fini,full | cons,fini,full |
| 有参考文献 | MD文档完整 | MD文档完整 |

---

## 推荐提交策略

提交**候选A**作为主序列，在Comments中提及候选B的存在。这样既满足OEIS的唯一性要求，又不丢失极简序列的信息。如果审稿人接受，可后续追加候选B作为交叉引用。

> ⚠️ OEIS 格式要求序列成员以逗号分隔，不包含括号或省略号。建议额外增加 1-2 项以填满 3 行（约需 260 字符 ≈ 30 项）。可通过降低斜率阈值（2x代替3x）获得更多项，但需注明阈值参数。
