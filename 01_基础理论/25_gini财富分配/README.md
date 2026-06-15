# Gini系数与财富分配算法

**目录**: `D:\AAA我的文件\PKS_千禧难题_统一解\01_基础理论\25_gini财富分配`
**文件数**: 12 个 .py 文件

---

## 文件说明与参数详解

### 📄 gini—fibonacci.py

**功能描述**: 生成从3开始的前10个Fibonacci数列的数字

**依赖**:
- `import numpy as np`
- `import plotly.graph_objects as go`

**关键数学逻辑**:

```python
fib_sequence = [start, start + 1]  # 3, 5作为起始数列
individual_group_income = total_income / num_levels
individual_incomes = [individual_group_income // num_people for num_people in fib_sequence]
incomes = [income * num_people for income, num_people in zip(individual_incomes, fib_sequence)]
cw = [sum(sequence[:i + 1]) / sum(sequence) for i in range(sampleCount)]
```

**函数流程**:
- `fibonacci_sequence()`

---

### 📄 gini—fibonacci的平方.py

**功能描述**: 生成从3^2开始的前10个Fibonacci数列的平方数

**依赖**:
- `import numpy as np  # 导入NumPy库，用于数值计算`
- `import plotly.graph_objects as go  # 导入Plotly库，用于绘制图形`

**关键数学逻辑**:

```python
fib_sequence = [start**2, (start + 2)**2]  # 3^2, (3+2)^2作为起始数列
next_fib = np.sqrt(fib_sequence[-1]) + np.sqrt(fib_sequence[-2])
individual_group_income = total_income / num_levels  # 每个阶层的总收入
individual_incomes = [individual_group_income // num_people for num_people in fib_sequence]  # 每个人的收入
cw = [sum(sequence[:i + 1]) / sum(sequence) for i in range(sampleCount)]  # 累积财富占比
```

**函数流程**:
- `fibonacci_sequence_squared()`

---

### 📄 gini—平方数.py

**功能描述**: 生成从3^2开始的前10个Fibonacci数列的平方数

**依赖**:
- `import numpy as np  # 导入NumPy库，用于数值计算`
- `import plotly.graph_objects as go  # 导入Plotly库，用于绘制图形`

**关键数学逻辑**:

```python
squared_sequence = [start**2]  # 3^2, (3+2)^2作为起始数列
next_fib = np.sqrt(squared_sequence[-1]) + 1
individual_group_income = total_income / num_levels  # 每个阶层的总收入
individual_incomes = [individual_group_income // num_people for num_people in squared_sequence]  # 每个人的收入
cw = [sum(sequence[:i + 1]) / sum(sequence) for i in range(sampleCount)]  # 累积财富占比
```

**函数流程**:
- `sequence_squared()`

---

### 📄 magicgini - 2.py

**功能描述**: 设置中文字体为SimHei

**依赖**:
- `import matplotlib.pyplot as plt`
- `import plotly.graph_objects as go`
- `from plotly.subplots import make_subplots`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 3 | 基本参数 | (见源码注释) |

**关键数学逻辑**:

```python
left_positions_n = [(max(results_n) - d) / 2 for d in results_n]
left_positions_L = [(max(results_L) - d) / 2 for d in results_L]
left_positions_E = [(max(results_E) - d) / 2 for d in results_E]
salary_per_person = S / n_values[i]  # 每个阶层个人的工资
totalWealth = cw[-1]  # 社会总财富
```

**函数流程**:
- `L()`

---

### 📄 magicgini.py

**功能描述**: 设置中文字体为SimHei

**依赖**:
- `import matplotlib.pyplot as plt`
- `import plotly.graph_objects as go`
- `from plotly.subplots import make_subplots`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 3 | 基本参数 | (见源码注释) |

**关键数学逻辑**:

```python
left_positions_n = [(max(results_n) - d) / 2 for d in results_n]
left_positions_L = [(max(results_L) - d) / 2 for d in results_L]
left_positions_E = [(max(results_E) - d) / 2 for d in results_E]
salary_per_person = E_values[i] / n2_values[i]  # 每个阶层的工资
totalWealth = cw[-1]  # 社会总财富
```

**函数流程**:
- `L()`

---

### 📄 magicsquaretable.py

**功能描述**: 设置中文字体为SimHei

**依赖**:
- `import matplotlib.pyplot as plt`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 1 | 基本参数 | (见源码注释) |

**关键数学逻辑**:

```python
left_positions_n = [(max(results_n) - d) / 2 for d in results_n]
left_positions_L = [(max(results_L) - d) / 2 for d in results_L]
left_positions_E = [(max(results_E) - d) / 2 for d in results_E]
```

**函数流程**:
- `L()`

---

### 📄 magictable.py

**功能描述**: 检测n是否为素数，更高效的方法 if n <= 1: return False if n <= 3: return True if n % 2 == 0 or n % 3 == 0: return False i = 5 while i * i <= n: if n % i == 0 or n % (i + 2) == 0: return False i += 6 return True def ...

**依赖**:
- `import concurrent.futures`
- `from concurrent.futures import ProcessPoolExecutor, as_completed`
- `import time`
- `import csv`
- `import pandas as pd`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `n` | 1 | 基本参数 | (见源码注释) |

**关键数学逻辑**:

```python
if n % i == 0 or n % (i + 2) == 0:
ranges = [(i, min(i + chunk_size, end)) for i in range(start, end, chunk_size)]
max_n = results[-1][0] if results else None
sum_n_squared = sum(n ** 2 for n, _ in results)
ranges = [(i, min(i + chunk_size, end)) for i in range(start, end, chunk_size)]
```

**函数流程**:
- `count_distinct_prime_factors()`
- `is_prime()`
- `L()`
- `is_valid()`
- `filter_S_l()`
- `S_l_list()`
- `process_S()`
- `S_l_list()`
- `output_result_tofile()`
- `main()`

---

### 📄 schauberger-gini-female.py

**功能描述**: Adjustable odd number n (must be an odd number)

**依赖**:
- `import numpy as np`
- `import plotly.graph_objects as go`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `a` | 1 | 基本参数 | (见源码注释) |
| `n` | 4 | 基本参数 | (见源码注释) |
| `m` | 5000 | 基本参数 | (见源码注释) |

**关键数学逻辑**:

```python
intervals = [2 * np.pi]
next_interval = intervals[-1] + (2*i-1) * 2 * np.pi
t_values = np.linspace(2 * np.pi, next_interval, female_num+1)  # Avoid t=0 to prevent division by zero
count = np.sum((t_values >= intervals[i]) & (t_values < intervals[i + 1]))
b = total_wealth / len(points_in_intervals)
```

**函数流程**:
- `x()`
- `y()`
- `z()`

---

### 📄 schauberger-gini-male.py

**功能描述**: Adjustable odd number n (must be an odd number)

**依赖**:
- `import numpy as np`
- `import plotly.graph_objects as go`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `a` | 1 | 基本参数 | (见源码注释) |
| `n` | 4 | 基本参数 | (见源码注释) |
| `m` | 10000 | 基本参数 | (见源码注释) |

**关键数学逻辑**:

```python
t_values = np.linspace(4 * np.pi, 2**(n+2) * np.pi, male_num+1)  # Avoid t=0 to prevent division by zero
intervals = [2**i * np.pi for i in range(2, 3+n)]
count = np.sum((t_values >= intervals[i]) & (t_values < intervals[i + 1]))
b = total_wealth / len(points_in_intervals)
c = b / count
```

**函数流程**:
- `x()`
- `y()`
- `z()`

---

### 📄 schauberger-gini.py

**功能描述**: Define the function to calculate wealth distribution and plot Lorenz curve

**依赖**:
- `import numpy as np`
- `import plotly.graph_objects as go`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `m` | 950 | 基本参数 | (见源码注释) |
| `n` | 3 | 基本参数 | (见源码注释) |

**关键数学逻辑**:

```python
count = np.sum((t_values >= intervals[i]) & (t_values < intervals[i + 1]))
b = total_wealth / len(points_in_intervals)
c = b / count
total_wealth = cw[-1]
cw = [0] + cw
```

**函数流程**:
- `calculate_gini_curve()`
- `compute_lorenz_curve()`

---

### 📄 幻方四数harmonograph.py

**功能描述**: -*- coding: utf-8 -*-

**依赖**:
- `import rhinoscriptsyntax as rs`
- `import math`

**关键数学逻辑**:

```python
t_start = -math.pi
avg_num_points = ((a + b)/2)*3  # 平均点数基于 (a+b)/2
min_step = 1e-5        # 最小步长（避免极端密集）
max_step = (t_end - t_start) / ((a + b)/32)  # 最大步长（避免极端稀疏）
dx_dt = a * math.cos(a * t) - b * math.cos(b * t)
```

**函数流程**:
- `draw_parametric_curve_adaptive()`
- `compute_speed()`

---

### 📄 幻方四数harmonograph五角星.py

**功能描述**: -*- coding: utf-8 -*-

**依赖**:
- `import rhinoscriptsyntax as rs`
- `import math`

**可调参数**:

| 参数名 | 默认值 | 类别 | 说明 |
|--------|--------|------|------|
| `scale` | 50 | 几何参数 | (见源码注释) |

**关键数学逻辑**:

```python
t = -math.pi + (2 * math.pi * i / steps)
x = math.sin(a1 * t) - math.sin(b1 * t)
y = math.cos(b1 * t) - math.cos(a1 * t)
```

**函数流程**:
- `compute_points()`
- `draw_two_parametric_curves()`

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