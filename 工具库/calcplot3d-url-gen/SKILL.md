# CalcPlot3D URL Generator v2.1

> 🔗 **GitHub 公开仓库**: `awakeninglanxin/PKS-Millennium-Project/工具库/calcplot3d-url-gen/`
> **版本**: v2.1 | **日期**: 2026-07-20

---

## 一句话简介

给定任意 3D 数学方程，**自动识别类型**，生成可直接打开的正确 CalcPlot3D 可视化链接。支持全部 6 种 3D 对象类型。

## 自动识别规则

| 输入模式 | 识别为 | 触发条件 |
|:---|:--:|:---|
| `z = f(x,y)` | function | 以 `z=` 开头，右侧无 `=` |
| `x=...; y=...; z=...` (含 u,v) | parametric | 含 `u` 或 `v` 变量 |
| `x=...; y=...; z=...` (含 t) | spacecurve | 含 `t` 变量（无 u,v） |
| `m=...; n=...; p=...` | vectorfield | 含 `m=` 和 `n=` |
| `f(x)=... ; a=... ; b=...` | revolution | 含 `f(x)=` 且无 `z=` |
| 其他含 `=` 的方程 | implicit | 默认兜底 |

## 快速上手（无需指定类型！）

```bash
# 直接扔任何公式，自动识别
python generate.py "z=sin(x)*cos(y)" --open
python generate.py "x^2+y^2+z^2=1-z^3" --open
python generate.py "x=cos(3t);y=sin(2t);z=0" --open
python generate.py "f(x)=x^2; a=0; b=2" --open
python generate.py "m=x-4y;n=5x+y;p=0" --open
python generate.py "x=cos(u)sinh(v);y=sin(u)cosh(v);z=v" --open

# 或手动指定类型 (覆盖自动识别)
python generate.py --type implicit "x^2+y^2+z^2=1"
```

## 踩坑记录（为什么需要这个工具）

| 坑 | 教训 |
|:---|:---|
| `=` 被 URL 吃掉 | 方程中的 `=` 必须用 `~` 替代 |
| `center/focus/up` 是四元数 | 不能手填 `(0,0,0,1)` — 已验证的模板在代码里 |
| `type=window` 放错位置 | window 必须是 URL 的**最后**一个参数块 |
| 方程中 `^` 被破坏 | `%5E` URL 编码 |
| 相机默认值不通用 | 隐式曲面和函数曲面用同一套；向量场和旋转体各有专用相机 |

## 技术细节

### 每个对象的关键参数

| 类型 | URL type= | 核心参数 |
|:---|:---|:---|
| 隐式 | `implicit` | `equation=LHS~RHS`; `cubes`(分辨率); `xmin..zmax` |
| 函数 | `z` | `z=<表达式>`; `umin..vmax`(域); `grid`(网格) |
| 空间曲线 | `spacecurve` | `x=<t>;y=<t>;z=<t>`; `tmin..tmax`; `tsteps` |
| 参数曲面 | `parametric` | `x=<u,v>;y=<u,v>;z=<u,v>`; `umin..vsteps` |
| 向量场 | `vectorfield` | `m=<x,y>;n=<x,y>;p=<x,y>`; `scale`; `nx,ny,nz` |
| 旋转体 | `volrev` | `top2d=<f(x)>`; `umin,umax`; `axisvar,axisval`; `grid` |

### 参数自动检测

方程中出现的 `a,b,c,d` 自动加滑块（value=1, range=[0,3]）。不自动检测 `t`（空间曲线的自变量）和 `u,v`（参数曲面的自变量）。

### 可用数学函数

`sin, cos, tan, arcsin, arccos, arctan, sinh, cosh, tanh, ln, log, exp, e^(), sqrt, abs, floor, ceil, sign`

### 特殊符号

- `pi` / `π` — 圆周率
- `e` — 自然常数
- `^` — 幂运算（URL 编码为 `%5E`）

## 已知限制

- 相机参数使用固定模板（如需精细视角需先在 CalcPlot3D 界面调整后 File→Encode View in URL）
- 自动域范围为保守默认值（`implicit: [-3.2,3.2]`, `function: [-3,3]`, `revolution: [-4,4]`）
- 不在市场（WorkBuddy Marketplace）中 — 手动安装：将本项目拷贝到 `~/.workbuddy/skills/calcplot3d-url-gen/`
