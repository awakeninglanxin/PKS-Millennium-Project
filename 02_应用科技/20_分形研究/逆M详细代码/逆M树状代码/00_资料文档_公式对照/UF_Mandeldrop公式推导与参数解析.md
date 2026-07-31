# UF Mandeldrop 公式推导与参数解析

> 来源: UF 论坛 "Formula Question" 讨论 (2015), UF 官方 API 文档

---

## 1. 原始公式推导

### Otto Magus 的 Mandeldrop

```
init:  z = 1/#pixel      ← #pixel 是 UF 的屏幕坐标 (复平面上的 w)
loop:  z = z^2 + (1/#pixel)
bailout: |z| < 4
```

**Python 等效**:
```python
c_eff = 1.0 / w       # w = IM + i*RE (屏幕坐标)
z = c_eff              # 初始化为 1/w
for n in range(maxiter):
    z = z**2 + c_eff   # 标准 Mandelbrot 迭代
    if |z| > 4: break
```

### aelah 的精炼版

```
init:  z = (0, 0)
loop:  z = sqr(z) + 1/#pixel
bailout: |z| <= @bailout
```

**关键差异**: z 初始化为 0 而非 1/c。数学上两者在迭代第2步收敛到相同轨道。

### 与标准 Mandelbrot 的关系

```
标准 M: z = z² + c        (c = #pixel)
逆 M:   z = z² + 1/#pixel  (c = 1/#pixel)
```

---

## 2. UF Inverse 变换的内部实现

### 源码 (Standard.ulb, Standard_Inverse class)

```
return @center + @radius / (pz - @center)
```

**展开**:
$$c_{\text{out}} = C + \frac{R}{c_{\text{in}} - C}$$

### 参数说明

| 参数 | 默认值 | 作用 |
|:---|:---|:---|
| `radius` | 1.0 | 反演圆半径。越大 → 分形放大 |
| `center` | (0,0) | 反演圆心。改变 → 形状剧烈变化 |
| `usescreen` | false | 用屏幕中心代替 Center |

### 标准反演 (C=0, R=1)

$$c_{\text{out}} = \frac{1}{c_{\text{in}}}$$

这是最常见的 Inverse 用法。UF 论坛中所有参数文件都使用 `p_radius=1.0, p_center=0/0`。

---

## 3. 参数文件深度解析

### 3.1 Peter Shepheard 的参数 (2015)

```plaintext
mapping: center=1.004849/0 magn=0.4 angle=270
formula: maxiter=100 p_bailout=1e20
outside: density=2 transfer=linear
         filename="Standard.ucl" entry="Basic" p_type=Iteration
```

**解读**:
- `center=1.004849/0`: 视口中心在逆M水滴颈部的 Re≈1.0 处, 聚焦于心形体附着球区域
- `magn=0.4`: 0.4倍标准放大, 水滴水滴恰好充满画面
- `angle=270`: 270°旋转 = -90° = 水滴尖朝上
- `p_bailout=1e20`: 天文数字级bailout — 防止反演核心的假逃逸
- `entry="Basic" p_type=Iteration`: 按原始迭代次数着色 (无平滑)
- `density=2`: 颜色重复2次, 增加层次感

### 3.2 Velvet--Glove 的参数 (UF 4.04, 2002)

```plaintext
mapping: center=1.15437880685/-0.040077532 magn=0.87348074 angle=-90
formula: maxiter=250 p_bailout=128
outside: entry="Smooth" p_power=2/0 p_bailout=128.0
```

**解读**:
- `center=1.154/-0.040`: 心形体附近, 微偏移捕捉分形细节
- `magn=0.87`: 比Peter的放大倍数大 (画面拉近)
- `angle=-90`: 等同 angle=270
- `p_bailout=128`: UF官方标准bailout
- `entry="Smooth" p_power=2/0`: 平方根平滑着色 ($\sqrt{\text{iter}}$)
- UF 4.04 兼容: 使用 `Fractint.uxf` 而非 `Standard.uxf` 的 Inverse

---

## 4. 关键参数对视觉的影响

### bailout 的选择

| bailout | 效果 |
|:---|:---|
| 4.0 (Otto) | 快速逃逸, 粗犷边界 |
| 128 (Velvet) | UF标准, 平衡 |
| 1e20 (Peter) | 极慢逃逸, 细致分形细节, 消除反演假逃逸 |
| 50 (Mitch) | 第三方参考, 中等 |

### center 的选择

| center | 聚焦区域 |
|:---|:---|
| 0.01/0.12 | 水滴正中心 (原点附近) |
| 1.004/0 | 心形体颈部 (周期泡芽附着处) |
| 1.154/-0.04 | 心形体上方区域 |

### magn 与视口的关系

UF 的 magn 是相对于"标准视口"的放大倍数。标准视口大致覆盖 Mandelbrot 心形体。

| magn | 覆盖范围 (大致) |
|:---|:---|
| 0.4 | ~5个单位宽, 看到完整水滴+背景 |
| 0.7 | ~3个单位, 标准视口 |
| 0.87 | ~2.3个单位, 聚焦心形体局部 |
| 6 | ~0.33个单位, 深度放大 |

---

## 5. 公式兼容性矩阵

| UF 版本 | 直接公式法 | Inverse 变换法 |
|:---|:---|:---|
| Express Edition | ✅ | ❌ (无 Transformations) |
| Creative Edition | ✅ | ✅ |
| Extended Edition | ✅ | ✅ |
| UF 4.04 (2002) | ✅ | ✅ (Fractint.uxf) |
| UF 5/6 (现代) | ✅ | ✅ (Standard.uxf) |

---

## 6. 颜色梯度 (Gradient) 参数

UF 使用 0-399 索引的渐变系统。关键色谱:

### Otto 的渐变
```
0   → 8716288  (深紫)
100 → 16121855 (亮蓝)
200 → 46591   (暗蓝)
300 → 156     (几乎黑)
```

### Peter 的渐变 (UF 默认)
```
123 → 368977   (深蓝)
170 → 65278    (青绿)
298 → 156      (暗黑)
-3  → 16384000 (红棕)
```

### Velvet 的渐变
```
0   → 3278080  (深蓝)
182 → 13701632 (天蓝)
229 → 16777215 (白)
258 → 16777215 (白)
399 → 0        (黑)
```
