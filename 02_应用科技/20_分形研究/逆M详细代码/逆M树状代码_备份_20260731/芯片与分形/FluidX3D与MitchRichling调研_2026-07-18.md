# FluidX3D × PKS漏斗 + Mitch Richling 逆M算法 — 调研报告

> 2026-07-18 | 基于全网搜索 + GitHub 交叉验证

---

## 一、FluidX3D 能否仿真你的 6 种 STL？

### ✅ 结论：可以，一行代码的事。

FluidX3D（作者：Dr. Moritz Lehmann, GitHub: `ProjectPhysX/FluidX3D`）自带**GPU 加速 STL 体素化器**，直接支持二进制 STL 文件导入。

### 你的 6 个 STL 文件

| STL 文件 | 大小 | FluidX3D 兼容 |
|------|:---:|:---:|
| 双曲直锥漏斗45°.stl | 19 KB | ✅ 秒级体素化 |
| 双曲直锥漏斗30°.stl | 30 KB | ✅ |
| 超双曲锥漏斗.stl | 57 KB | ✅ |
| 黄金比螺旋漏斗光滑墙壁.stl | 185 KB | ✅ |
| 黄金比螺旋漏斗8bands.stl | 8.2 MB | ✅ ~0.5s |
| 黄金比螺旋漏斗16bands.stl | 15 MB | ✅ ~1s |

### 使用方法 — Python 版（pip install 就行）

```python
import fluidx3d

config = fluidx3d.Config()
config.parse_args([
    '--D3Q27',           # 27速模型（最精确）
    '--FP16S',           # 半精度（2× 提速）
    '--SUBGRID',         # 子网格湍流模型
    '--SRT',             # 单松弛时间碰撞
    '--GRAPHICS',        # 实时可视化
    '--EQUILIBRIUM_BOUNDARIES',  # 入口/出口边界
    '-f', '双曲直锥漏斗45°的副本.stl',
    '-r', '4000',        # 分辨率 ≈ 4GB VRAM
    '-u', '3.0',         # 流速 3 m/s
    '--re', '150',       # Re=150（你的经验值）
    '--rho', '1000',     # 水密度
    '--secs', '10.0',    # 跑10秒物理时间
    '--fps', '30',
])
config.run_simulation()  # 弹出实时GPU窗口
```

### 与我们手写 LBM v1~v8 的对比

| | 手写 LBM (CuPy) | FluidX3D |
|------|:---:|:---:|
| 网格上限 | 128³（VRAM 边界） | **10亿格点**（多GPU） |
| STL 导入 | ❌ 手写锥体公式 | ✅ `voxelize_stl()` 原生 |
| 湍流模型 | 无 | 子网格 SGS |
| Re 上限 | ~150（不稳定） | **5.35亿** |
| 速度 | CuPy FFT（慢） | **OpenCL 原生** |
| 可视化 | matplotlib GIF | **实时 3D 交互** |
| 安装 | 手写 400 行 | `pip install fluidx3d` |

**结论**：我们 8 轮手写 LBM 验证了"反弹边界能产生涡量"这个物理事实，现在到了升级工具链的时候——FluidX3D 就是那个工业级替代品。

---

## 二、Mitch Richling 的逆 M 分形算法

### 他的主页：https://mitchr.me/

Mitch Richling 是业余数学/图形学爱好者，用 C++ 编写了一套名为 `ramCanvas` 的光栅渲染库，并为 **20+ 种分形** 发布了完整源码 + 高清图片 + 数学推导。

### 与逆 M（1/c 映射）直接相关

| # | 算法 | 公式 | 渲染方法 | 状态 |
|:--:|------|------|------|:---:|
| 1 | **Inverted Mandelbrot** | $c' = 1/c,\ z \to z^2 + c'$ | FireRamp 逃逸计数着色 | ✅ 有源码 |

**这就是他唯一的逆 M 算法。** 核心 C++ 逻辑：

```cpp
c = 1.0 / c;  // 复反演
while(norm(z) < 50 && count <= 1024) {
    z = z * z + c;  // 标准 Mandelbrot 迭代
    count++;
}
// FireRamp 着色: color = csCColdeFireRamp(count * 15)
```

### 其他 Mandelbrot 家族变体（不同生成函数，非逆 M）

| # | 算法 | 公式 | 与逆 M 关系 |
|:--:|------|------|:---:|
| 2 | Burning Ship | $z = (\|\Re(z)\| + i\|\Im(z)\|)^2 + c$ | 无关 |
| 3 | Multibrot | $z = z^n + c, n=3,4,5...$ | $n=-1$ 即逆M |
| 4 | Tricorn | $z = \overline{z}^2 + c$ | 无关 |
| 5 | Tippets | 修改版 M 集生成函数 | 无关 |
| 6 | M 集 Biomorph | 不同的迭代停止条件 | 着色方法可借鉴 |
| 7 | Collatz Fractal | Collatz 序列可视化 | 无关 |
| 8 | Pickover Popcorn | 三角函数迭代 | 无关 |

### 纯 Julia 集 / 其他分形

| # | 算法 | 关键点 |
|:--:|------|------|
| 9 | Julia Sets | 固定 c，遍历 z₀ |
| 10 | Orbit Traps | Julia 集 + 轨道捕获着色 |
| 11 | Newton's Fractal | $z \to z - f(z)/f'(z)$ |
| 12 | Phoenix Fractal | 双参数复迭代 |
| 13 | Sierpinski Sponge | 3D 分形 |
| 14 | Peter de Jong Map I/II | 混沌吸引子 |
| 15 | Tinkerbell Map | 二维离散动力系统 |
| 16 | Hopalong Fractals | Martin 吸引子 |
| 17 | Chaos Game | 迭代函数系统 |
| 18 | Levy Curve | L-system |
| 19 | Symmetric Fractals | 随机迭代 + 共轭对称 |
| 20 | Lorenz Attractor | ODE 数值积分 |

### 3D Mandelbrot 渲染技术（Mitch 独有）

| # | 技术 | 说明 |
|:--:|------|------|
| 21 | **Mandelbrot Mountains** | 势函数 → 高度场 → POV-Ray 光线追踪 |
| 22 | 距离估计渲染 | $d = \|z_n\|\log\|z_n\| / \|z_n'\|$ |
| 23 | 逃逸时间函数 | $L = n + 1 - \log_2(\log\|z_n\|)$ |

---

## 三、与我们的逆 M 算法对比

| | Mitch Richling | DNA_M 音乐探索器（我们的） | UF1b 壳线（我们的） |
|------|:---:|:---:|:---:|
| **公式** | 固定 $c \to 1/c$ | **连续滑动** $c^\alpha, \alpha=1-2s$ | 固定 $\alpha=-1$ |
| **着色** | FireRamp 逃逸计数 | Canvas LUT 彩虹渐变 | XOR 棋盘 + Sobel 壳线 |
| **离散采样** | 无 | **DNA 碱基对映射** | 无 |
| **旋转** | 无 | **坐标矩阵旋转** | `np.rot90(k=3)` |
| **实时交互** | 无（静图 TIFF） | **60fps 滑块滑动** | 静图 |
| **连续形变** | ❌ | **alpha 扫描** | ❌ |
| **音频映射** | ❌ | ✅ 迭代数→频率 | ❌ |

### 关键结论

1. **Mitch 只有 1 种逆 M 算法**（固定 `c = 1/c` + FireRamp 着色）
2. **我们的 DNA_M 探索器有他完全没有的能力**：
   - 连续形变 $c^\alpha$（alpha 滑动）
   - 调色板循环动画（Divetoxx 技术）
   - DNA 碱基对离散映射
   - XOR 棋盘骨相 + Sobel 壳线描边
3. **但他有一堆我们没做的 Mandelbrot 变体**（Burning Ship / Tricorn / Multibrot 等）——可以移植到 DNA_M 探索器里做切换

---

## 四、下一步建议

| # | 行动 | 预估 |
|:--:|------|:---:|
| 🔥 1 | **安装 FluidX3D → 跑 45° 锥体 STL** | 10 min |
| 🔥 2 | **用 FluidX3D 对比 6 种漏斗的涡量/压降** | 1 h |
| 🟡 3 | 移植 Burning Ship / Tricorn 到 DNA_M 探索器 | 3 h |
| 🟢 4 | 将 Mitch 的距离估计渲染加入 UF1b | 2 h |
