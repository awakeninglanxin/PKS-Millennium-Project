# 韩国YouTube — 坐标体系与噪声生成器

> 来源：Play_with_geometry / Play_with_noise  
> 整理：2026-07-16

---

## 一、极坐标 → 球面 → 环面：三条升级路线

```
极坐标 (2D)
  ├── 玫瑰线 r=cos(kθ)        → Farey 周期泡映射
  ├── 阿基米德螺旋 r=a+bθ     → 对数螺线锥体母线
  └── 利萨如 r=sin(aθ)cos(bθ) → 多频干涉（同 SPF 噪声原理）

      ↓ 升级到 3D

球面坐标 (3D)
  ├── 球面螺旋                → 涡线在球面上的缠绕
  ├── 凹凸球 sin(mθ)sin(nφ)   → 多极展开的球面谐波
  └── 噪声球面                → 湍流速度场模型

      ↓ 升级到环面

环面坐标 (3D)
  ├── 标准环面 R+r*cos(φ)    → PKS 蛋形截面
  ├── 环面螺旋                → 锥体壁面涡流轨迹
  ├── Klein 瓶                → 非定向流形（YM 规范场）
  └── 环面利萨如              → 多频涡流干涉图案
```

---

## 二、Perlin 噪声 — 湍流建模的简化入口

### 2.1 1D 噪声 → 流体速度脉动

$$u'(t) = A \cdot \text{noise}(\omega t)$$

- 振幅 A = 湍流强度
- 频率 ω = 涡流尺度倒数

### 2.2 2D 噪声 → 自由表面波

$$h(x,y,t) = A \cdot \text{noise}(\alpha x, \beta y, \gamma t)$$

对应 NS 方程的线性化自由表面边界条件。

### 2.3 3D 噪声 → 湍流速度场

$$\mathbf{u}(\mathbf{x},t) = \nabla \times (\text{noise}(x,y,z,t))$$

取旋度自动满足 $\nabla \cdot \mathbf{u} = 0$（不可压缩条件）。

### 2.4 噪声循环技巧

```javascript
// 生成无缝球面纹理：在圆上采样噪声
function noiseLoop(d, min, max, R){
  let angle = TWO_PI * t;
  let x = R * cos(angle);
  let y = R * sin(angle);
  return map(noise(x, y), 0, 1, min, max);
}
```

应用于球面的 $\theta, \phi$ 参数域 → 连续、无缝的球面纹理。

---

## 三、3D 数学花 — 完整参数空间

### 3.1 主函数签名

```
flower(A, k_petals, a_power, b_decay, 
       perturb_amp, perturb_freq, perturb_power,
       n_layers, phi_step, theta_step)
```

### 3.2 参数映射表

| 参数 | 物理意义 | PKS 对应 |
|------|------|------|
| A | 花的高度 | 锥体长度 L |
| k_petals | 花瓣数 | Farey q（周期） |
| a_power | 花瓣锐度 | 锥体收缩指数 |
| b_decay | 衰减速度 | 柔化截断参数 |
| perturb_amp | 褶皱强度 | 壁面粗糙度 |
| perturb_freq | 褶皱频率 | 涡流波数 |
| n_layers | 层叠数 | 锥体分段数 |

---

## 四、效果滤镜（p5_hacks）

| 效果 | 用途 | PKS 关联 |
|------|------|------|
| Glow | 发光晕染 | CFD 涡量等值面可视化 |
| Gradient | 渐变填充 | 势能场的平滑着色 |
| Fast Blur | 快速模糊 | SSAA 降采样替代方案 |
| Cut-out | 剪影效果 | 分形集边界提取 |

---

## 五、API 集成

| API | 功能 | 千禧难题关联 |
|------|------|------|
| Facemesh | 468点面部网格 | 格点规范理论的可视化类比 |
| HandPose | 21点手部骨架 | 流形上的坐标参数化 |
| BodySeg | 人体分割 | 复杂几何的分区方法 |

---

> **与 PKS 的直接接口**：噪声生成器可用于 NS 湍流的初始条件生成；球面/环面参数化对应 PKS 锥体的 3D STL 几何表达；vShape 参数扫描可优化 Servi 柔化函数。
