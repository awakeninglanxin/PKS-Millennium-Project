# 蛋形→sin波转换系列（档案）

> **来源**: 2025-08-25 ~ 2025-09-01 在 pythonProject 中生成的实验性代码
> **数学贡献**: Schauberger 蛋形曲线 → sin 波转换 + 双曲线锥螺旋 3D 可视化

---

## 核心数学原理

### 统一的蛋形参数方程

所有文件共用同一组 Schauberger 蛋形公式：

```
x(t) = 2a·sin(t) / (b + √(b² - 4k·cos(t)))
y(t) = a·(m·term1 + term2)
```

其中标准八度蛋参数:
- k = 2/3
- b = 5/3  
- m = 2/3
- a = 2π

### 蛋形→sin波的关键转换

将二维蛋形闭合曲线 (x(t), y(t)) 投影为随时间展开的一维 sin 波，揭示了:
1. **蛋形不对称性 → sin 波非对称**：蛋的尖端(快速变化)对应 sin 波的陡峭段
2. **谐波衰减律**：通过连续对数积分衰减 `amp(t) = 1/(t·ln(n+1))` 模拟粘性耗散
3. **双曲线族**：`k(t)=1/(t/T)` 和 `b(t)=2/√(t/T)` 实现蛋形参数随时间的动态演化

### 阴阳双曲锥体系

| 参数序列 | 蛋形变化 | z轴运动 | 物理类比 |
|---------|---------|--------|---------|
| 2^n (阳/白银比) | 逐渐变扁 | r=2^(-t/2π) | Burgers 涡轴向拉伸 |
| φ^n (阴/黄金比) | 逐渐变圆 | r=φ^(-t/2π) | 涡核自然收敛 |
| 2^n + φ^n (复合) | 先扁后圆 | 双螺旋叠加 | 湍流能谱 |

### 卍字符 (Swastika) 数学

通过线性旋转 `θ(t) = -user_num·9°/点` 将 sin 波投影到 2D 平面，产生对称的卍形图案。数学本质是：
- 时间维度上均匀旋转
- 空间维度上指数衰减
- 两者叠加产生分形自相似结构

---

## 文件索引

| # | 文件 | 核心创新 | 与现有模块关系 |
|---|------|---------|-------------|
| 01 | `01_basic_egg_to_sinwave_log_decay.py` | 蛋形→sin波基本转换 + 对数衰减 | `egg_curve.py` 的 sin 波投影 |
| 02 | `02_egg_to_sinwave_4quadrant.py` | 四象限展开显示 | 蛋形不对称性的四象限分析 |
| 03 | `03_egg_to_sinwave_linear_rotation.py` | 线性旋转螺旋曲线 | 旋转+衰减的复合运动 |
| 04 | `04_egg_to_sinwave_swastika.py` | 卍字符对称图案 | PKS 十字螺旋的几何实现 |
| 05 | `05_egg_to_sinwave_hyperbolic_cut.py` | 双曲线比值切割 | k(t), b(t) 动态参数化 |
| 06 | `06_egg_to_sinwave_octave_cut.py` | 八度音程切割 | 音乐八度与蛋形级数对应 |

### 3D 螺旋系列 (在 03_simulation/)

| 文件 | 核心创新 |
|------|---------|
| `hyperbolic_yin_spiral_3d_swastika.py` | 阴螺旋(φ^n)×3D×卍字符 |
| `hyperbolic_yang_spiral_3d_swastika.py` | 阳螺旋(2^n)×3D×卍字符 |
| `hyperbolic_phi_spiral_becoming_round_3d.py` | φ^n 蛋形逐渐变圆 |
| `hyperbolic_octave_spiral_becoming_flat_3d.py` | 2^n 蛋形逐渐变扁 |
| `hyperbolic_yinyang_union_3d.py` | 阴阳双曲线合一 |
| `hyperbolic_composite_octave_phi_3d.py` | 2^n+φ^n 复合螺旋 |

---

## 与核心项目的互补关系

这些文件**不重复**现有代码。它们探索的是:
- **蛋形曲线的动态演化**（参数 k 和 b 随时间变化）
- **sin 波转换视角**（不同于 `egg_shell_metrics.py` 的静态度量分析）
- **卍字符对称性**（不同于 `yang_yin_spiral.py` 的阴阳对比）

作为技术支撑，它们为未来的 NS 方程验证提供了额外的可视化方案和数学变换视角。

---

*归档日期: 2026-05-28*
*原始来源: E:\pythonProject\pythonProject\program (2025-08-25 ~ 2025-09-01)*
