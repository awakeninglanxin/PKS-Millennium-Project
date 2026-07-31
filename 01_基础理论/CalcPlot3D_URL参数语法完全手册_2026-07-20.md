# CalcPlot3D URL 参数语法完全手册

> **来源**：CalcPlot3D 官方帮助文档 4 个页面完整研读  
> **研读页面**：
> - Implicit Surfaces (`section-implicit-surfaces.html`)
> - Parameter Sliders (`section-sliders.html`)
> - List of Available Functions (`appendix-availablefunctions.html`)
> - Dynamic Figures with Controls (`section-53.html`)
> **日期**：2026-07-20

---

## 一、核心发现：`~` = 等号

URL 中 `=` 是参数分隔符（`key=value`），所以方程式的等号**必须用 `~` 替代**：

| 你写的方程 | URL 编码后 |
|:---|:---|
| `ax² + ay² + cz² = 1 - z³` | `ax^2+ay^2+cz^2~1-z^3` |
| `x² + y² = 1 + d x² y²` | `x^2+y^2~1+d*x^2*y^2` |

**指数**：`^` 可直写或用 `%5E` 编码（两者都行）

---

## 二、URL 查询字符串结构

CalcPlot3D 的 URL 由多个**对象块**组成，每个对象块以 `type=` 开头，用 `&` 连接。**`type=window` 必须放在最后。**

```
https://c3d.libretexts.org/CalcPlot3D/index.html?
  type=implicit; equation=...; cubes=60; ... &
  type=slider; slider=a; value=1; ... &
  type=slider; slider=b; value=1; ... &
  type=window; ... (总是最后一个)
```

---

## 三、隐式曲面 (type=implicit) 参数表

| 参数 | 说明 | 示例 |
|:---|:---|:---|
| `equation=LHS~RHS` | 方程（用 ~ 替代 =） | `equation=x^2+y^2+z^2~1` |
| `cubes=N` | Marching cubes 分辨率（默认 30） | `cubes=60` |
| `visible=true/false` | 是否显示 | `visible=true` |
| `fixdomain=true/false` | 是否锁定域 | `fixdomain=true` |
| `xmin=N; xmax=N` | x 轴范围 | `xmin=-1.5; xmax=1.5` |
| `ymin=N; ymax=N` | y 轴范围 | `ymin=-1.5; ymax=1.5` |
| `zmin=N; zmax=N` | z 轴范围 | `zmin=-1.2; zmax=1.5` |
| `constcol=rgb(R,G,B)` | 曲面颜色 | `constcol=rgb(255,80,80)` |
| `format=normal` | 着色方式 | `format=normal` |
| `alpha=N` | 透明度 (0-255) | `alpha=140` |
| `view=0` | 视角模式 | `view=0` |
| `hidemyedges=false` | 隐藏边缘 | `hidemyedges=false` |

### 支持的坐标系
- **笛卡尔**：使用 x, y, z
- **柱坐标**：使用 r, θ(theta), z
- **球坐标**：使用 ρ(rho), θ(theta), ϕ(phi)

---

## 四、参数滑块 (type=slider) 参数表

**可用参数名**：只支持 `a`, `b`, `c`, `d`, `t`（t 不能用于 Space Curves）

| 参数 | 说明 | 示例 |
|:---|:---|:---|
| `slider=a` | 参数名 | `slider=a` |
| `value=N` | 初始值 | `value=1` |
| `steps=N` | 滑动步数 | `steps=100` |
| `pmin=N` | 最小值 | `pmin=0` |
| `pmax=N` | 最大值 | `pmax=3` |
| `repeat=true/false` | 连续动画 | `repeat=true` |
| `bounce=true/false` | 来回弹跳 | `bounce=true` |
| `waittime=N` | 动画速度 (1-1000) | `waittime=1` |
| `careful=true/false` | 仅允许步进值 | `careful=false` |
| `noanimate=true/false` | **隐藏播放按钮** | `noanimate=false` |
| `name=xxx` | **自定义标签**（支持 LaTeX） | `name=n_x` |

---

## 五、窗口设置 (type=window) 参数表

**必须放在 URL 最后**

| 参数 | 说明 | 示例 |
|:---|:---|:---|
| `hsrmode=3` | 隐藏面移除模式 | `hsrmode=3` |
| `center=x,y,z,w` | 旋转中心 | `center=0,0,0,1` |
| `focus=x,y,z,w` | 焦点 | `focus=0,0,0,1` |
| `up=x,y,z,w` | 上方向量 | `up=0,0,1,1` |
| `perspective=true/false` | 透视投影 | `perspective=true` |
| `edgeson=true/false` | 显示边 | `edgeson=true` |
| `faceson=true/false` | 显示面 | `faceson=true` |
| `showbox=true/false` | 显示边框 | `showbox=true` |
| `showaxes=true/false` | 显示坐标轴 | `showaxes=true` |
| `showticks=true/false` | 显示刻度 | `showticks=true` |
| `autospin=true/false` | 自动旋转 | `autospin=true` |
| `transparent=false` | 背景透明 | `transparent=false` |
| `alpha=140` | 透明度 | `alpha=140` |
| `zoom=N` | 缩放 | `zoom=1.4` |
| `centerxpercent=N` | 水平居中比例 | `centerxpercent=0.5` |
| `centerypercent=N` | 垂直居中比例 | `centerypercent=0.45` |
| `xmin/xmax/ymin/ymax/zmin/zmax` | 视口范围 | `xmin=-1.5; xmax=1.5` |
| `xscale/yscale/zscale` | 各轴缩放 | `xscale=1` |
| `hidexysliders=true` | 隐藏 xy 滑块 | `hidexysliders=true` |
| `hidetracevalue=true` | 隐藏轨迹值 | `hidetracevalue=true` |

---

## 六、全部可用数学函数

| 类别 | 函数 |
|:---|:---|
| 基本 | `+`, `-`, `*`, `/`, `^` (幂) |
| 三角 | `sin`, `cos`, `tan`, `cot`, `sec`, `csc` |
| 反三角 | `arcsin`, `arccos`, `arctan`, `arccot`, `arcsec`, `arccsc` |
| 双曲 | `sinh`, `cosh`, `tanh`, `coth`, `sech`, `csch` |
| 指数/对数 | `e^()` 或 `exp()`, `ln()`, `log()` |
| 根号 | `sqrt()` |
| 绝对值 | `abs()` 或 `\|x\|` |
| 取整 | `floor()`, `int()`, `ceil()` |
| 符号 | `sign()` 或 `sgn()` |
| 阶乘 | `5!` |

---

## 七、如何自己生成链接而不进界面

**方法 1：界面操作**
1. 在 CalcPlot3D 里加好所有对象（曲面 + 滑块 + 调整视角）
2. File 菜单 → "Encode View in URL"
3. 浏览器地址栏自动更新 → 复制即可

**方法 2：手工构造**（你现在做的）
- 知道 `type=implicit` / `type=slider` / `type=window` 的完整参数表（见上）
- 用 `&` 连接对象
- `window` 始终放在最后
- 方程式中 `=` 用 `~` 替代

---

## 八、对你的 3D 蛋面链接的修正建议

之前我给的链接中用了 `~1-z^3` 和 `~1+d*x^2*z^2`——根据手册，这是正确的语法。

但有两点可以优化：
1. **方程中使用 `*` 显式乘号**（CalcPlot3D 支持 `5x` 这样的隐式乘法但 `d*x^2*z^2` 更安全）
2. **不需要 `fixdomain=true`** 当 xmin/xmax 已在 window 参数中设定时

优化后的 Edwards 风格蛋面链接：

```
equation=ax^2+ay^2+cz^2~1+d*x^2*z^2
```
