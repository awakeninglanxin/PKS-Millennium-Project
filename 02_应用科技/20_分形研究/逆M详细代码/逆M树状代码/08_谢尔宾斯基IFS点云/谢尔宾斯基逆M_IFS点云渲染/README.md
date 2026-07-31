# 谢尔宾斯基三角 调制 逆M 水滴边界逃逸

> **更新**: 2026-07-26 | 原版三层解耦架构已被增强版替代  
> **归档位置**: `逆M树状代码/11_谢尔宾斯基逆M_IFS点云渲染/`

---

## 当前文件

| 文件 | 说明 |
|------|------|
| `D_sierpinski_verify.png` | 谢尔宾斯基三角校验 (80K pts, Chaos Game) |
| `enhanced_boundary_escape.py` | **增强版渲染器** — 结构级融合 |
| `enhanced_output/` | 增强版 8 张输出 (E1~E8) |

## 增强版算法 (enhanced_boundary_escape.py)

### 核心创新：结构级融合

原版三层解耦（Chaos Game → 单点c → 概率IFS），增强版实现**空间c-场调制边界逃逸**：

| 步骤 | 操作 |
|------|------|
| 1 | 逆M水滴 dwell map + 梯度边界检测 |
| 2 | Sierpinski 密度场 → 空间c-场 `c(x,y) = c0 + A·density(x,y)` |
| 3 | 边界条件逃逸: 仅边界带迭代，每像素用自己的 `c(x,y)` |
| 4 | 四层辉光融合: 水滴内部(深蓝) + 边界逃逸(火焰光晕) |

### 关键参数

- `c_drop = -1.0+0j` (Basilica Julia 集, 8.8% interior)
- 1/c_drop 必须在 Mandelbrot 集内才有连通 Julia 集
- 梯度法边界检测比二值法更鲁棒

### 使用方法

```bash
# 快速测试 (400x400)
python enhanced_boundary_escape.py --quick

# 标准渲染 (800x800)
python enhanced_boundary_escape.py

# 探索不同水滴形状
python enhanced_boundary_escape.py --c-real -1.25 --c-imag 0.0

# 调整 Sierpinski 调制强度
python enhanced_boundary_escape.py --amplitude 0.5
```

### 依赖

```
numpy, matplotlib, numba, scipy
```
