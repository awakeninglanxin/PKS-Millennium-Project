# PKS 项目 Python 出图教程：PNG 可视化 + DXF 工程导出

> 本文教你在本项目环境下，如何运行 Python 脚本生成 PNG 图片和 DXF 文件。
> 本项目自带 PIL(Pillow)、pdf2image、matplotlib、ezdxf 等依赖包，减少安装步骤。
> 归档：2026-07-07

---

## 一、环境准备

### 1.1 检查 Python 环境

本项目所有脚本基于 **Python 3.12**，推荐使用 `D:\Program Files\Python312\python.exe`：

```batch
D:\Program Files\Python312\python.exe --version
```

### 1.2 已包含的 Python 包

项目根目录自带了以下包，**无需 pip install**：

| 目录 | 用途 |
|------|------|
| `PIL/` | Pillow 图像处理库（PNG 读写、合成） |
| `pdf2image/` | PDF 转 PNG 工具 |
| `pdf2image-1.17.0.dist-info/` | pdf2image 元数据 |
| `pillow-12.2.0.dist-info/` | Pillow 元数据 |

另外脚本中常用的 `numpy`、`matplotlib`、`ezdxf`、`scipy` 等库已假设系统安装，**如果缺失可执行一次**：

```batch
D:\Program Files\Python312\python.exe -m pip install numpy matplotlib ezdxf scipy pandas
```

### 1.3 工作目录建议

所有脚本在当前目录下寻找资源文件，建议 **cd 到脚本所在目录** 后再执行：

```batch
cd D:\AAA我的文件\PKS_千禧难题_统一解\03_验证工具\08_dxf_spiral_toolchain\A_螺旋管DXF生成器
D:\Program Files\Python312\python.exe 脚本名.py
```

---

## 二、生成 PNG 图片

### 示例 1：螺旋曲线可视化图

**脚本位置**：
```
03_验证工具\08_dxf_spiral_toolchain\A_螺旋管DXF生成器\
  1组螺线生成正+侧视图png多图2的n次曲线t=4pi为起点.py
  5组螺线生成正+侧视图png多图ln曲线t=pi为起点.py
```

**功能**：生成 1 组或 5 组螺旋线的正视图和侧视图 PNG 图片。

**执行方法**：
```batch
cd D:\AAA我的文件\PKS_千禧难题_统一解\03_验证工具\08_dxf_spiral_toolchain\A_螺旋管DXF生成器
D:\Program Files\Python312\python.exe "1组螺线生成正+侧视图png多图2的n次曲线t=4pi为起点.py"
```

**输出**：PNG 图片保存在脚本同目录下，文件名以 `spiral_plot_*.png` 或 `curve_*.png` 命名。

**数学原理**（以该脚本为例）：
- 使用黄金比倒数 $\phi = (\sqrt{5}-1)/2 \approx 0.618$
- 螺旋公式：$x = r \cdot 2^{-t/(360\pi/180)} \cdot \cos(t)$，$y = r \cdot 2^{-t/(360\pi/180)} \cdot \sin(t)$
- 用 matplotlib 的 `savefig` 直接保存为 PNG

### 示例 2：蛋形曲线 PNG

**脚本位置**：
```
03_验证工具\01_geometry\egg_curve.py
03_验证工具\01_geometry\egg_variations.py
```

**功能**：生成舒伯格蛋形曲线的不同形态 PNG（蛋形、蛋→sin波转化、螺旋蛋等）。

**执行方法**：
```batch
cd D:\AAA我的文件\PKS_千禧难题_统一解\03_验证工具\01_geometry
D:\Program Files\Python312\python.exe egg_curve.py
```

### 示例 3：数学可视化图像

**脚本位置**：
```
03_验证工具\08_dxf_spiral_toolchain\E_数学可视化\
  双曲线与3条斜度线_visual.py
  4种波纹最佳截面曲线_ln线_visual.py
  火的螺旋结构.py
  舒曼频率次谐波 .py
```

**功能**：各种数学曲线的可视化展示，直接运行即可输出 PNG。

---

## 三、生成 DXF 文件

### 示例 1：直锥螺旋管 DXF（最简模板）

**脚本位置**：
```
01_基础理论\16_schauberger系数学与书籍与出dxf图的程序\
  DXF生成程序集\01_直锥螺旋管\最简原始模版用于生成直锥螺旋管.py
```

**功能**：生成一段直锥螺旋管的 DXF 文件，可直接导入 Rhino、AutoCAD、FreeCAD。

**依赖**：需要 `ezdxf` 库（`pip install ezdxf`），以及同目录下的断面数据 CSV 文件。

**执行方法**：
```batch
cd D:\AAA我的文件\PKS_千禧难题_统一解\01_基础理论\16_schauberger系数学与书籍与出dxf图的程序\DXF生成程序集\01_直锥螺旋管
D:\Program Files\Python312\python.exe "最简原始模版用于生成直锥螺旋管.py"
```

**输出**：`*.dxf` 文件，可用 Rhino 或 AutoCAD 直接打开。

### 示例 2：螺旋管家族 DXF（26 种变体）

**脚本位置**：
```
03_验证工具\08_dxf_spiral_toolchain\A_螺旋管DXF生成器\
  spiral.py  /  spiral-2d.py  /  spiral-3d tube1.py  /  spiral-3d tube2.py
  最简原始模版用于生成直锥螺旋管 - stp*.py （多个变体）
  最简原始模版用于生成螺锥88° - dxf*.py
  最简原始模版用于生成GL25螺纹 - dxf -完美.py
  最简原始模版用于生成斜螺锥.py
  最简原始模版用于生成曲锥螺旋管.py
```

**功能**：覆盖直锥、斜锥、曲锥、螺纹、弹簧等不同变体。

```batch
cd D:\AAA我的文件\PKS_千禧难题_统一解\03_验证工具\08_dxf_spiral_toolchain\A_螺旋管DXF生成器
D:\Program Files\Python312\python.exe spiral-3d tube1.py
```

### 示例 3：工程应用 DXF（泵体/花洒/羚羊角管）

**脚本位置**：
```
03_验证工具\08_dxf_spiral_toolchain\G_螺旋泵与花洒生成器\
  舒式螺旋斜流泵+多断面 -dxf*.py
  羚羊角管中心线与蛋尖双轨 -dxf*.py
  旋叶发电机+多断面 -dxf*.py
  舒式螺旋漏斗+多断面 -dxf*.py
```

**功能**：生成 Schauberger 风格的流体机械 DXF 设计图。

### 示例 4：蛋形曲线 DXF

**脚本位置**：
```
03_验证工具\08_dxf_spiral_toolchain\B_蛋形曲线模型\
  anu3d曲线.py
  舒伯格蛋Die Ei-Kurve -蛋螺旋*.py
  蛋咬一口公式生成法.py
```

**功能**：生成蛋形截面曲线和螺旋蛋的 DXF 文件。

---

## 四、推荐学习路径

如果你是第一次用本项目出图，按顺序尝试：

```
Step 1: 运行螺旋 PNG 生成
  → A_螺旋管DXF生成器/1组螺线生成正+侧视图png...
  → 看到 PNG 图片输出，确认环境正常

Step 2: 运行蛋形曲线 PNG
  → 01_geometry/egg_curve.py
  → 看到蛋形 -> sin波 -> 螺旋蛋的演变图

Step 3: 运行最简 DXF 模板
  → DXF生成程序集/01_直锥螺旋管/最简原始模版...
  → 得到第一个 DXF 文件，在 Rhino/AutoCAD 中打开

Step 4: 尝试螺旋管 DXF 变体
  → A_螺旋管DXF生成器/spiral-3d tube1.py
  → 对比不同参数下的 DXF 输出
```

---

## 五、常见问题

### Q1: 提示 `ModuleNotFoundError: No module named 'ezdxf'`
```batch
D:\Program Files\Python312\python.exe -m pip install ezdxf
```

### Q2: 提示 `ModuleNotFoundError: No module named 'numpy'`
```batch
D:\Program Files\Python312\python.exe -m pip install numpy matplotlib scipy pandas
```

### Q3: 生成 DXF 后如何查看？
- **Rhino 3D**：`File → Open`，选择 DXF，导入后可用 `_Zoom` `_Extents` 查看
- **AutoCAD**：`OPEN` 命令打开 DXF
- **FreeCAD**：免费开源，`File → Open` 导入
- **在线查看**：https://sharecad.org 或 https://viewer.autodesk.com

### Q4: PNG 在哪里？
默认保存在脚本 **同目录** 下，文件名以 `*.png` 结尾。

### Q5: 想调整螺旋圈数/锥度/尺寸？
打开脚本找到 `__init__` 或开头的参数定义区域，修改 `t_min`、`t_max`（控制角度范围）、`d`（直径）、`amp`（振幅）等参数后重新运行即可。

---

## 六、核心包速查

| 包名 | 导入写法 | 典型用途 |
|------|---------|---------|
| PIL/Pillow | `from PIL import Image` | 图片读取、合成、格式转换 |
| matplotlib | `import matplotlib.pyplot as plt` | 数据可视化、保存 PNG |
| ezdxf | `import ezdxf` | 生成 DXF 工程文件 |
| numpy | `import numpy as np` | 数值计算、数组操作 |
| scipy | `from scipy.interpolate import ...` | 曲线插值、平滑 |

---

> **提示**：除 PIL/pdf2image/pillow 已在项目中预置外，ezdxf、numpy、matplotlib、scipy 需系统安装。
> 所有脚本运行前请确保 Python 环境正常，建议用 `D:\Program Files\Python312\python.exe` 执行。
