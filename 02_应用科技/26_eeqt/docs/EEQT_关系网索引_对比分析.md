# EEQT 项目关系网索引 & 功能对比报告

> 生成时间：2026-04-25
> 分析文件：`REF_plus_hemi_v3.html` vs `EEQT_fixed_c60.html`
> 基础路径：`C:\Users\ThinkPad\WorkBuddy\20260425104509\eeqt\`

---

## 一、两个文件核心定位对比

| 维度 | `REF_plus_hemi_v3.html` | `EEQT_fixed_c60.html` |
|---|---|---|
| **模式** | 单固体模式（一次渲染一种几何体） | 多固体复合模式（一次叠加多个几何体） |
| **代码规模** | 20.38 KB，435行 | 47.18 KB，584行 |
| **定位** | 快速探索单一分形 / **半球体研究专用** | 复合实验 / **丰富交互控制** |
| **C60变体** | ✅ 完整四面体+五边形+六边形半球 | ❌ 只有完整C60 |
| **多固体叠加** | ❌ 不支持 | ✅ 支持 |
| **对齐模式切换** | ❌ 不支持 | ✅ 每种固体3种对齐（align 0/1/2） |
| **代码风格** | 过程式，函数集中 | 结构化，SOLIDS元数据驱动 |

---

## 二、详细功能逐项对比

### 2.1 几何体（Geometry）支持

| 几何体 | 顶点数 | REF_plus_hemi_v3 | EEQT_fixed_c60 | 备注 |
|---|---|---|---|---|
| Octahedron | 6 | ✅ | ✅ | 经典EEQT基准 |
| Tetrahedron | 4 | ✅ | ✅ | 最少顶点数 |
| Cube | 8 | ✅ | ✅ | 8顶点 |
| Merkaba / Star Tetrahedron | 8 | ✅ | ✅ | 双四面体嵌套 |
| Icosahedron | 12 | ✅ | ✅ | 黄金比例精密 |
| Dodecahedron | 20 | ✅ | ✅ | 十二面体 |
| Rhombic Dodecahedron | 14 | ✅ | ✅ | 菱形十二面体 |
| C60 Fullerene（完整） | 60 | ✅ buckyball | ✅ buckyball | 富勒烯 |
| **C60 Pentagon Hemisphere** | **30** | ✅ 独有 | ❌ | **v3独有优势** |
| **C60 Hexagon Hemisphere** | **30** | ✅ 独有 | ❌ | **v3独有优势** |

> `REF_plus_hemi_v3` 在半球体研究上有**绝对优势**，提供了预计算的精确半球坐标（PENTAGON_HEMI / HEXAGON_HEMI，164-165行）。

---

### 2.2 投影方式（Projection）

| 投影类型 | REF_plus_hemi_v3 | EEQT_fixed_c60 |
|---|---|---|
| Stereographic（球极平面） | ✅ | ✅ |
| Lambert（等面积） | ✅ | ✅ |
| Orthographic（正交） | ✅ | ✅ |

两者完全一致，无差异。

---

### 2.3 渲染架构

| 渲染特性 | REF_plus_hemi_v3 | EEQT_fixed_c60 |
|---|---|---|
| 渲染方式 | 直接ImageData单次绘制 | ImageData + drawCircle混合 |
| 点大小 | 固定像素叠加（alpha=0.25） | **可调点大小**（ptSize 0~0.4） |
| 亮度控制 | 无 | **✅ K系数**（bright滑块 0~100） |
| 深度着色 | ❌ 固定颜色 | ✅ z-depth插值（越靠前越白/亮） |
| 多固体叠加渲染 | ❌ | ✅ activeSolids循环 |
| 圆形点渲染 | ❌ 纯像素 | ✅ drawCircle函数（396-412行） |

> `EEQT_fixed_c60` 的渲染更灵活，支持点大小和亮度实时调节，深度着色使图像更有层次感。

---

### 2.4 用户交互控制

| 控件 | REF_plus_hemi_v3 | EEQT_fixed_c60 |
|---|---|---|
| epsilon 滑块 | ✅ 5-999 | ✅ 5-999 |
| **epsilon 文本框编辑** | ❌ 只读显示 | ✅ **双击可编辑** |
| points 滑块 | ✅ 20K-2M | ✅ 20K-120K（较窄） |
| **points 文本框编辑** | ❌ 只读显示 | ✅ **双击可编辑** |
| **brightness 滑块** | ❌ | ✅ K系数 |
| **pt size 滑块** | ❌ | ✅ 可调点大小 |
| solid 选择器 | 下拉菜单（单选） | **复选框（多选）** |
| projection 选择 | ✅ 下拉 | ✅ 下拉 |
| generate 按钮 | ✅ | ✅ |
| **对齐模式按钮** | ❌ | ✅ 每固体右下角循环按钮 |
| **自动epsilon预设** | ✅ SOLID_EPS表 | ❌ 需手动切换 |

> `EEQT_fixed_c60` 交互更丰富，但`REF_plus_hemi_v3`的自动epsilon预设对新手更友好。

---

### 2.5 C60特殊处理

| C60特性 | REF_plus_hemi_v3 | EEQT_fixed_c60 |
|---|---|---|
| 4组颜色（A/B/C/D） | ✅ | ✅ |
| 顶点组标注（A:8 B:12 C:24 D:16） | ✅ 画布底部标注 | ❌ |
| 特殊缩放（scale×1.55） | ✅ ND===60时 | ❌ |
| C60精确坐标生成 | ✅ makeA/B/C/D分组归一化 | ⚠️ genC60仅用球面参数化 |
| **半球坐标** | ✅ 预计算精确 | ❌ |

---

### 2.6 顶点标记

| 特性 | REF_plus_hemi_v3 | EEQT_fixed_c60 |
|---|---|---|
| 非C60顶点标记 | ✅ 大圆点（6顶点时r=5，其他r=3） | ✅ 小圆点（6顶点时r=1.25，其他r=0.75） |
| C60组标注 | ✅ A/B/C/D彩色圆+文字 | ❌ |
| 深度着色 | ❌ | ✅ 顶点颜色随z变化 |

---

### 2.7 数学核心（EEQT动力学）

两者完全一致，共享同一套数学公式：

```
T(r,n,eps) = Mobius变换（彭罗斯万有覆叠）
detProb   = 检测概率
pick      = 轮盘赌选择
hausdorffDim = 盒计数法维数
```

---

## 三、各自核心优势总结

### `REF_plus_hemi_v3.html` 的优势

1. **✅ C60半球体研究专用**：pentagon_hemi / hexagon_hemi 是唯一支持完整半球分形的版本
2. **✅ 自动epsilon预设**：切换几何体自动设置最优值（SOLID_EPS表，414行）
3. **✅ C60分组标注**：A/B/C/D顶点在画布底部有图例说明
4. **✅ C60特殊缩放**：非正交投影时scale×1.55充分利用画布
5. **✅ 顶点标记更大更清晰**：适合教学/演示
6. **✅ points上限更高**：支持到2,000,000点（fixed_c60只到120,000）
7. **✅ 代码更简洁**：轻量，适合作为学习起点
8. **✅ 过程式代码**：函数一一对应，易读易改

### `EEQT_fixed_c60.html` 的优势

1. **✅ 多固体复合叠加**：可同时选择多个几何体，产生干涉图样
2. **✅ 对齐模式切换**：每种固体3种旋转对齐，探索更多构型
3. **✅ 可调亮度（K）**：bright滑块控制叠加亮度
4. **✅ 可调点大小**：ptSize滑块，兼顾精度和性能
5. **✅ 深度着色**：z轴颜色插值，图像更有3D层次感
6. **✅ 文本框直接编辑**：双击epsilon/points即可输入精确值
7. **✅ HSV动态配色**：每种几何体用不同色调（hue 0°~295°），易于区分
8. **✅ SOLIDS元数据结构**：代码可维护性更强，适合扩展

---

## 四、关键函数调用关系图

```
调用关系（共同依赖的核心函数）
──────────────────────────────────────────────────────

getDirections(type)         ← EEQT动力学几何入口
    ├── getOctahedron()
    ├── getTetrahedron()
    ├── getCube()
    ├── getMerkaba()
    ├── getIcosahedron()
    ├── getDodecahedron()
    ├── getRhombicDodecahedron()
    ├── genC60()            ← [EEQT_fixed_c60 用球面参数化] / [v3 用分组归一化]
    ├── genC60PentagonHemi()  ← 仅 v3 独有
    └── genC60HexagonHemi()   ← 仅 v3 独有

getDirsByAlign(type, mode) ← 仅 EEQT_fixed_c60
    └── getDirections(type)  fallback

projStereo / projLambert / projOrtho  ← 投影函数（两者相同）

T(r, n, eps)               ← EEQT Mobius变换（两者相同）
detProb(r, n, eps, N)      ← 检测概率（两者相同）
pick(r, dirs, eps)         ← 随机选择（两者相同）
hausdorffDim(pts3d, projFn) ← 盒计数维数（两者相同）
```

---

## 五、文件调用指南

### 如何引用这些HTML文件

在Python/JS中直接用浏览器打开：

```python
import webbrowser
path = r"C:\Users\ThinkPad\WorkBuddy\20260425104509\eeqt\REF_plus_hemi_v3.html"
webbrowser.open(f"file:///{path}")
```

### 独立JS/Python模块调用

| 文件 | 类型 | 用途 |
|---|---|---|
| `c60_coords.js` | JS | C60坐标计算工具 |
| `c60_final_v3.js` | JS | C60最终测试版 |
| `gen_animation.js` | JS | 生成动画HTML |
| `peak_search_v1.py` | Python | 峰值搜索算法 |
| `analyze_ref.py` | Python | 分析REF输出 |
| `compare_render*.py` | Python | 渲染对比 |
| `build_final.py` | Python | 构建最终报告 |
| `gen_report.py` | Python | 生成报告 |

### 推荐的Python调用示例

```python
# 读取并分析C60坐标
with open(r"eeqt\c60_coords.js") as f:
    content = f.read()

# 调用peak_search分析
import subprocess
result = subprocess.run(
    ["python", "eeqt\\peak_search_v1.py"],
    capture_output=True, text=True
)
```

---

## 六、建议的整合方向（达尔文进化策略）

如果要**合并两个文件的最佳特性**，建议优先级：

| 优先级 | 合并目标 | 来自 |
|---|---|---|
| P0 | 多固体复选框UI | `EEQT_fixed_c60` |
| P0 | 对齐模式切换 | `EEQT_fixed_c60` |
| P0 | 亮度/点大小控制 | `EEQT_fixed_c60` |
| P1 | **C60半球体支持** | `REF_plus_hemi_v3` |
| P1 | 自动epsilon预设 | `REF_plus_hemi_v3` |
| P1 | C60分组标注图例 | `REF_plus_hemi_v3` |
| P2 | C60精确分组坐标（makeA/B/C/D） | `REF_plus_hemi_v3` |
| P2 | 深度着色 | `EEQT_fixed_c60` |
| P3 | HSV动态配色 | `EEQT_fixed_c60` |
| P3 | 文本框直接编辑 | `EEQT_fixed_c60` |

---

## 七、目录结构速查

```
eeqt/
├── REF_plus_hemi_v3.html       ← 单固体探索 + C60半球研究
├── EEQT_fixed_c60.html         ← 多固体复合 + 丰富交互
├── c60_hemisphere_src/         ← 半球体源码库（47文件）
│   ├── REF_plus_hemi_v4.html
│   └── c60_*.js / *.py
├── 含C60的eeqt/                ← 含C60的eeqt版本
├── backup_py_20260411/         ← Python备份
├── peak_search_v1.py           ← 峰值搜索主程序
├── analyze_*.py                ← 分析工具
├── compare_*.py                ← 对比工具
├── gen_*.py / gen_*.js        ← 生成器
└── BUG_ANALYSIS.md             ← Bug记录
```
