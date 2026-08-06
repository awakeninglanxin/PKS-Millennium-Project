# SEG / IGV 几何引擎与三环磁极优化 — 主入口

**主交付物**: `seg_orbit_spin.html`  
**版本**: v3.2 | **日期**: 2026-08-06

---

## 项目概述

`seg_orbit_spin.html` 是一个**单文件交互式 Web 引擎**，实现 SEG（Searl 效应发电机）和 IGV（反重力装置）的完整几何建模、约束优化与 2D 可视磁极显示。

核心功能：
- **9 种几何方案**（从已知尺寸反算 → 质量驱动 → 等体积质量模式）
- **9 步约束清洗流水线**（正厚度 → 间隙 → 排序 → 等厚/等间距 → 轨道重算）
- **三环磁极布局可视化**（unifiedVis 统一段数 + ☑全极数直绘模式全局可选 + 8 片/滚筒）
- **平滑评分算法**（gcd 互质 + cross-gcd 去耦 + LCM 寿命 + 滚筒统一性）
- **CSV 质量推荐数据源**（`seg.csv` 5319 行 / `igv.csv` 86 行）
- **双层高度约束**（k1 比例约束 + k2 间隙约束，二选一动态切换）
- **📷一键截长图**（html2canvas 2倍高清导出 PNG，含全页面）
- **材料密度 DNA 自动计算**（SEG 4 层 / IGV 6 层）

---

## 9 种几何方案速览

| 方案 | 控制模式 | 核心驱动 | e系数 |
|:---|:---|:---|:---:|
| 1 | size | 已知尺寸求体积 (Yr, Br₀, n, e) | ✅ |
| 2 | volume | 已知体积求高度 (Bv, Yr) | ❌ |
| 3 | size | BR = Yr·num·n/2（默认 n=3.5） | ✅ |
| 4 | size | 体积等差 + 等厚 (nFac=2) | ✅ |
| 5 | size | 等差 + 等厚等间距 | ✅ |
| 6 | size | BR = (2Yr+n)/(2sin(π/num)) 三角函数法 | ✅ |
| 7 | mass | 质量密度体积 (mᵢ/ρ) | ❌ |
| 8 | mass | 等体积质量模式: Bv = (Σm)/(3ρ) | ❌ |
| 9 | mass | 等体积 + sp=质量数 + rp=P34 | ❌ |

---

## 当前约束体系

### 几何约束（9 步流水线）
① BR ≥ Br+1 正厚度 → ② 间隙 Br ≥ BR + 2Yr + clearanceGap → ③ 后环正厚度 → ④ 厚度排序 t₀≥t₁≥t₂ → ⑤ 方案5 等间距 → ⑥ 方案4/5 等厚 → ⑦ 间隙复查 → ⑧ 绝对排序 → ⑨ 轨道重算

### 高度约束
- 每环滚筒高 ≤ 定子高 (hR[i] ≤ hS[i])
- 引擎级高度排序: hS₀≥hS₁≥hS₂, hR₀≥hR₁≥hR₂
- k1 比例约束 (hR ≤ hS/k, 默认 k=1.2)
- k2 间隙约束 (hR = hS−2×k2, 默认 k2=1cm)

### 滑条硬限制
- 间隙: 1-5cm，默认 1cm
- k1: 1-1.5，k2: 0-9cm
- Br₀: 0-2000cm, step=0.5
- 滚筒片质量: 8片×34g=272g/颗
- V定子环min (仅检查定子)
- 滚筒数量: num₀<num₁<num₂

---

## 关键文档

| 文档 | 内容 |
|:---|:---|
| `SEG_IGV_几何引擎说明.md` | 完整几何公式、9种方案、9步流水线、全极数直绘 |
| `磁极颜色与评分算法说明.md` | unifiedVis、全极数直绘模式、评分公式、k1/k2 |
| `SEG磁极设计_小白版.md` | 互质/lcm 通俗解释、9种方案说明 |
| `SEG磁极优化算法v3_正式说明书.md` | v3.2 正式版：评分、搜索算法、最优配置表 |
| `SEG仿真工具链评估_MHD_WarpX_magpylib_2026-07-18.md` | L1-L4 仿真可行性评估 |
| `SEG最优磁极数设计教程_完整推导.md` | 完整数学推导、unifiedVis 算法 |
| `三十二相_数学审美算法映射.md` | 32相→数学审美：unifiedVis GCD 联结 |

### 补充脚本
| 文件 | 说明 |
|:---|:---|
| `seg参数尺寸出图.py` | Python 7种方案参数生成 (matplotlib) |
| `圆周内摆线searl机.py` | Rhino 内摆线曲线 |
| `圆周外摆线searl机.py` | Rhino 外摆线曲线 |
| `德布罗意波debroglie.py` | Rhino 德布罗意波生成 |

---

### CSV 数据
| 文件 | 行数 | 对应设备 |
|:---|:---:|:---|
| `seg.csv` | 5319 | SEG (4层, base=30) |
| `igv.csv` | 86 | IGV (6层, base=105) |

---

## 使用方式

1. 浏览器打开 `seg_orbit_spin.html`
2. 下拉菜单选择方案 (1-9)
3. 调节滑条实时看几何变化
4. 观察 2D 俯视/正视图中的磁极与间隙
5. 查看评分栏和 info 行获取关键参数

---

*更新于 2026-08-06*

---

> ⚠️ **重要声明 / Important Disclaimer**
> 
> 本文档由 AI 辅助生成，部分结论可能存在 AI 幻觉导致的论证不严谨之处。
> 文中提出的数学、物理及相关跨学科观点，需要经过专业数学家、物理学家
> 及相关领域专家共同验证与检验。
> 如有疏漏、错误或不同见解，敬请指正，不胜感激。
> 
> **This document was AI-assisted. Some conclusions may contain inaccuracies
> due to AI hallucination. All mathematical, physical, and interdisciplinary
> claims require verification by professional mathematicians, physicists,
> and subject-matter experts. Corrections and feedback are warmly welcomed.**
