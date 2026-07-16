# 韩国YouTube公开莲花算法模型 — 工具与公式总汇

> 来源：YouTube 채널 "Play with geometry" + "p5.js hacks"  
> 作者：韩国开发者 (p5.js 기반)  
> 整理日期：2026-07-16  
> 目录：`03_验证工具/韩国youtube公开莲花算法模型/`

---

## 一、3D 数学花生成算法（核心）

### 1.1 Part 1 — 基础3D花朵

```javascript
function draw(){
  for(let theta = 0; theta < 60; theta += 1){
    for(let phi = 0; phi < 360; phi += 2){
      let r = (70 * pow(abs(sin(phi*3)), 1) + 225) * theta/60;
      let x = r * cos(phi);
      let y = r * sin(phi);
      let z = vShape(350, r/100, 0.8, 0.15) - 200 
             + perturbation(1.5, r/100, 12, phi);
      vertex(x, y, z);
    }
  }
}
```

### 1.2 vShape 函数 — 花的垂直轮廓

$$v(r) = A \cdot e^{-b|r|^{1.5}} \cdot |r|^a$$

- **A=350**：振幅/高度缩放
- **a=0.8**：幂次，控制花瓣尖端锐度
- **b=0.15**：指数衰减系数，控制花瓣宽度
- **r**：极坐标半径（归一化到 0~1）

**数学本质**：**指数衰减 × 幂律增长** 的乘积——这就是 Servi 柔化函数 $\varphi(n/N)$ 的同类结构！两者都是"在0附近增长（幂律），在远处衰减（指数）"的钟形函数。

### 1.3 perturbation 函数 — 花瓣褶皱

$$p(r, \phi) = 1 + A \cdot r^2 \cdot \sin(k\phi)$$

- **A=1.5**：褶皱振幅
- **k=12**：褶皱频率（12瓣）
- **r² 因子**：褶皱在花瓣尖端更强，在中心消失

### 1.4 Part 2 — 双花瓣变体

```javascript
// 双层花瓣：外层+内层交错
r1 = (70*pow(abs(sin(phi*5)), 1) + 200)*theta/60;  // 外层5瓣
r2 = (50*pow(abs(sin(phi*3)), 1) + 150)*theta/60;  // 内层3瓣
```

### 1.5 关键参数速查

| 参数 | 值 | 效果 |
|------|:---:|------|
| sin(φ×k) 的 k | 3,5,12 | 花瓣数量 |
| vShape 的 a | 0.8 | 尖端锐度 |
| vShape 的 b | 0.15 | 花瓣宽度 |
| perturbation 的 k | 12 | 表面褶皱频率 |
| theta 循环 | 0~60 | 层数（花的层叠数） |

---

## 二、极坐标体系

### 2.1 极坐标玫瑰线

$$r = \cos(k\theta)$$

```javascript
// k=4 → 8瓣玫瑰
for(let theta=0; theta<360; theta+=0.1){
  let r = 200 * cos(4*theta);
  let x = r * cos(theta);
  let y = r * sin(theta);
}
```

| k | 花瓣数 | 形状 |
|:---:|:---:|------|
| 2 | 4 | 四叶草 |
| 3 | 3 | 三叶草 |
| 4 | 8 | 八瓣玫瑰 |
| 5 | 5 | 五瓣花 |
| n/d (分数) | 复杂 | 达芬奇玫瑰 |

### 2.2 极坐标利萨如图形

$$r = A\sin(a\theta + \delta), \quad x = r\cos(b\theta), \quad y = r\sin(b\theta)$$

### 2.3 阿基米德螺旋

$$r = a + b\theta$$

---

## 三、球面坐标系

### 3.1 基础球面参数化

```javascript
let x = r * sin(phi) * cos(theta);
let y = r * sin(phi) * sin(theta);
let z = r * cos(phi);
```

### 3.2 球面螺旋

$$r(\theta,\phi) = R_0 + A \cdot \frac{\phi}{2\pi}$$

### 3.3 凹凸球（bumpy sphere）

$$r(\theta,\phi) = R_0 + A \cdot \sin(m\theta) \cdot \sin(n\phi)$$

- **m,n**：经纬方向的凸起频率

---

## 四、环面坐标系（Torus）

### 4.1 标准环面

```javascript
x = (R + r*cos(phi)) * cos(theta);
y = (R + r*cos(phi)) * sin(theta);
z = r * sin(phi);
```

### 4.2 Klein 瓶

```javascript
// 使用环面坐标系的非定向曲面
// 自交于一点，无内外之分
```

### 4.3 环面利萨如曲线

$$r(\theta,\phi) = R + A \cdot \sin(a\theta) \cdot \sin(b\phi)$$

---

## 五、Perlin 噪声生成器

### 5.1 水表面模拟

```javascript
for(let x=0; x<width; x+=10){
  for(let y=0; y<height; y+=10){
    let z = noise(x*0.02, y*0.02, t) * 100;
    // z = 高度 → 模拟水面波动
  }
}
```

### 5.2 噪声球面纹理

$$r(\theta,\phi) = R_0 + \text{noise}(A\theta, B\phi, t) \cdot C$$

### 5.3 极坐标噪声环

```javascript
// 噪声循环：无缝球面纹理
function noiseLoop(diameter, min, max, noiseRadius){
  let cx = noiseRadius * cos(angle);
  let cy = noiseRadius * sin(angle);
  return map(noise(cx, cy), 0, 1, min, max);
}
```

---

## 六、与 PKS 千禧难题的关联

### 6.1 vShape ↔ Servi 柔化函数

| | vShape | Servi φ |
|------|------|------|
| 形式 | $A e^{-b|r|^{1.5}} \cdot |r|^a$ | $\varphi(n/N)$ |
| 特征 | 0附近幂律增长 + 远处指数衰减 | 同结构 |
| 用途 | 花瓣轮廓 | Servi-Croft 核截断 |

**结论**：两种函数是同一种"钟形截断"的变体。vShape 的参数优化经验（a=0.8, b=0.15）可直接指导 Servi 柔化函数的参数调优。

### 6.2 极坐标玫瑰线 ↔ Farey 周期泡

玫瑰线 $r=\cos(k\theta)$ 的 k 瓣结构与 M 集主心形上 angle-doubling 的 k-周期泡**拓扑同构**。花瓣间的"楔形"对应 Farey 树的分叉。

### 6.3 球面噪声 ↔ NS 湍流建模

Perlin 噪声生成的连续随机场是湍流速度场的简化模型。水表面模拟直接对应 NS 方程的自由表面边界条件。

### 6.4 环面坐标 ↔ PKS 锥体

PKS 双曲锥的 3D 扫掠路径本质上是**对数螺线在环面上的投影**。环面利萨如曲线的叠加模式可用于建模锥体壁面上的涡流轨迹。

---

> **归纳**：韩国 YouTuber 的这些 p5.js 代码虽不直接解决千禧难题，但其数学骨架（vShape、极坐标玫瑰、球面参数化、噪声生成）覆盖了我们已有的 Servi-Croft 核、Farey 分相、CFD 湍流建模。值得将 vShape 的参数空间扫描加入 GPU 任务队列。
