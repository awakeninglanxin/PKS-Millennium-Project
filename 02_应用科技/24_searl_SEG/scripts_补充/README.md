# SEG/Searl补充脚本

**目录**: `D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\scripts_补充`
**文件数**: 4 个 .py 文件

---

## 文件说明与参数详解

### 📄 seg参数尺寸出图.py

**功能描述**: Searl效应发生器七种方案参数生成原理数学说明 通用符号定义： - YrN: 第N环滚筒半径 - YhN: 第N环滚筒高度 - YvN: 第N环滚筒体积 - BrN: 第N环定子内径 - BRN: 第N环定子外径 - BhN: 第N环定子高度 - BvN: 第N环定子体积 - nN: 第N环稀疏因子 - numN: 第N环滚筒数量 - aN, bN: 定子与滚筒高度关系参数 - suN, sdN...

**依赖**:
- `import numpy as np`
- `import matplotlib.pyplot as plt`
- `from mpl_toolkits.mplot3d import Axes3D`
- `import matplotlib.colors as mcolors`
- `import colorsys`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 3.5 | 基本参数 | (见源码注释) |
| `a` | 0.8 | 基本参数 | (见源码注释) |
| `alpha` | 0.8 | 权重/阈值 | (见源码注释) |

**关键数学逻辑**:

```python
2. 定子环体积公式：BvN = π × (BRN² - BrN²) × BhN
3. 定子外径计算：BRN = (numN × nN × YrN) / 2
4. 定子滚筒高度关系：BhN = (YhN + aN) × bN 或 YhN = BhN/bN - aN
1. 计算滚筒高度：YhN = BhN/bN - aN
2. 计算定子外径：BRN = (numN × nN × YrN)/2
```

**函数流程**:
- `print_scheme1_math()`
- `print_scheme2_math()`
- `print_scheme3_math()`
- `print_scheme4_math()`
- `print_scheme5_math()`
- `print_scheme6_math()`
- `print_scheme7_math()`
- `print_common_mathematical_framework()`
- `__init__()`
- `solve_selected_scheme()`

---

### 📄 圆周内摆线searl机.py

**功能描述**: Parameters for the inner involute

**依赖**:
- `import rhinoscriptsyntax as rs`
- `import math`

**关键数学逻辑**:

```python
x = (R - r) * math.cos(t) + r * math.cos(((R - r) / r) * t)
y = (R - r) * math.sin(t) - r * math.sin(((R - r) / r) * t)
t_start =-math.pi
```

**函数流程**:
- `involute_curve()`

---

### 📄 圆周外摆线searl机.py

**功能描述**: Ensure the curve is closed by adding the first point at the end

**依赖**:
- `import rhinoscriptsyntax as rs`
- `import math`

**关键数学逻辑**:

```python
x = (R + r) * math.cos(t) - r * math.cos(((R + r) / r) * t)
y = (R + r) * math.sin(t) - r * math.sin(((R + r) / r) * t)
t_start = -math.pi
```

**函数流程**:
- `evolute_curve()`

---

### 📄 德布罗意波debroglie.py

**功能描述**: Get the points of the curve

**依赖**:
- `import rhinoscriptsyntax as rs`
- `import math`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `k` | 6 | 基本参数 | (见源码注释) |
| `amplitude` | 1 | 几何参数 | (见源码注释) |
| `frequency` | 1 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
x = amplitude * math.cos(k * point[0] + phase)  # y-value of the wave, varies with x
y= amplitude * math.sin(k * point[1] + phase)
```

**函数流程**:
- `generate_de_broglie_wave()`

---

## 使用说明

### 运行环境

- 大部分文件需 **Rhino 3D**（`import rhinoscriptsyntax`）
- 少数文件可在标准 Python 环境运行（`matplotlib`/`numpy`）
- 音乐算法文件需 `pygame` 或 `pyaudio` 播放 MIDI

### 参数调节原则

1. **几何参数**（`k`, `b`, `a`, `m`）— 控制曲线形状
2. **缩放参数**（`scale`, `amplitude`, `n`）— 控制幅度/圈数
3. **权重参数**（`weight`, `alpha`, `beta`）— 控制混合比例

### 输出

- Rhino 脚本：直接在 Rhino 视口中生成曲线/曲面
- matplotlib 脚本：输出 `.png` 可视化文件
- 音乐算法：播放音频或输出 MIDI

---

*本说明由 AI 自动生成于 2026-06-15 19:51*