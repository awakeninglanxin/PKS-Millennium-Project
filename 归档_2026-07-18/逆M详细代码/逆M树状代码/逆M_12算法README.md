# 逆Mandelbrot Application — 12种着色算法实现

## 项目结构

```
逆M树状代码/
├── 1_二分棋盘格素描/    ← UF1 (XOR) + UF1b (XOR+Sobel壳线)
├── 2_连续势能流光/      ← UF2 plasma渐变 + v2同心环
├── 3_有理外部射线/      ← UF3 + v3/v5/v7射线原型
├── 4_距离估计壳线/      ← UF4 DEM光晕
├── 5_轨道陷阱网格/      ← UF5
├── 6_拓扑交错瓦片/      ← UF6
├── 7_轨迹排斥树枝/      ← UF7
├── 8_对偶三角网扩散/    ← UF8 + v4/v8原型
├── 9_光照效果/          ← UF9 3D法线打光
├── 10_浮雕效果/         ← UF10 Sobel浮雕
├── 11_三角不等式平均/   ← UF11 TIA
├── 12_高斯整数/         ← UF12 floor(Re/Im)模
├── 原型参考/            ← v1基准 + 超简版
├── UF_*.md              ← 资料汇编/公式对照
└── 工作日志/心得/README ← 项目文档
```

## 算法速查

| # | 算法 | 文件名 | 视觉效果 |
|:---:|:---|:---|:---|
| 1 | Binary Decomposition | `1_*/UF1*.py` | 纯黑白XOR三角网 |
| 2 | Smooth Potential | `2_*/main.py` | plasma渐变 |
| 3 | External Rays | `3_*/main.py` | 树状叶脉分叉 |
| 4 | Distance Estimator | `4_*/main.py` | DEM绿色光晕 |
| 5 | Orbit Traps | `5_*/main.py` | 网格线灰度 |
| 6 | Topo Decomposition | `6_*/main.py` | 4级镶嵌 |
| 7 | Trajectory Tree | `7_*/main.py` | 轨道可视化 |
| 8 | Dual Triangle Net | `8_*/main.py` | 内部网+外渐变+金边 |
| 9 | Lighting | `9_*/main.py` | 3D法线光照 |
| 10 | Emboss | `10_*/main.py` | Sobel浮雕 |
| 11 | TIA | `11_*/main.py` | 轨道比值累加 |
| 12 | Gaussian Integer | `12_*/main.py` | floor(Re/Im)四色 |

## 统一引擎

```python
c_eff = |c|^(-1) * exp(-i*arg(c))  # c^α α=-1
bailout = 50
MAXITER = 250
viewport: Re[-1.833,4.5] Im[-2.124,2.124]
rot90(k=3): 水滴尖朝上
```

## 核心原则

逆M中所有着色算法的公式与正M**完全相同**, 仅着色区域**内外反转**:
- 正M: 集合外部(逃逸) → 着色
- 逆M: 水滴内部(逃逸) → 着色 (对应正M外部)
