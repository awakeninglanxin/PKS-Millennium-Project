# 调色板循环 — Divetoxx 技术迁移至 DNA_M 音乐探索器

> 源技术：GitHub/Divetoxx Mandelbrot + Wikipedia 1080p Color Cycling Video (Aokoroko)  
> 迁移目标：DNA_M 音乐探索器 · 正逆 M 集实时交互  
> 日期：2026-07-16

---

## 一、技术来源

Divetoxx 的 Mandelbrot 渲染器采用"两遍法"：

```
第一遍：计算原始迭代数地图 iterMap[x,y]        ← 最重，O(W×H×maxIter)
第二遍：对 255 帧，每帧仅偏移调色板索引         ← 极轻，O(W×H)
        colorIdx = (iterMap - frame + 255) % 255
        pixel = palette[colorIdx]
```

**关键洞察**：迭代数学结果不依赖颜色。把数学和着色完全分离后，变色不需要重算分形。

---

## 二、数学原理

### 2.1 分形渲染的本质

Mandelbrot 迭代 `z → z² + c` 的输出是两个独立维度的信息：

| 维度 | 内容 | 改变时机 |
|------|------|------|
| **数学层** | 逃逸迭代数 i、势能 pot、轨道陷阱 trap | 仅当 `c` 变化时需重算 |
| **着色层** | 将 `v = f(i, pot, trap)` 映射到 RGB | 可独立变化 |

传统渲染把两层绑定在一起——每次改颜色都要重跑迭代。Divetoxx 分离了它们。

### 2.2 调色板循环的数学

```
原始着色:  pixel = LUT[⌊v × 255⌋]

循环着色:  pixel = LUT[⌊(v × 255 + shift) mod 256⌋]
                    shift = frame_number mod 256
```

`v` 是每个像素的归一化迭代值（0~1），计算一次后存入 `Float32Array`。之后每帧只需做整数加法和取模——零浮点运算。

### 2.3 复杂度对比

| 阶段 | 操作数 | 说明 |
|------|:---:|------|
| 计算 iterMap | W×H×maxIter ≈ 400×400×90 = 14.4M | 一次性 |
| 循环着色（每帧） | W×H ≈ 160K | requestAnimationFrame @ 60fps |

**加速比**：每帧着色 vs 每帧重算 = 14.4M / 160K = **90×**。

---

## 三、在 DNA_M 音乐探索器中的实现

### 3.1 数据流

```
s 滑块变化 → alpha=1-2s 变化 → 重算 iterMap + 渲染
                                    ↓
                               iterMap 缓存到 Float32Array
                                    ↓
调色板循环模式 ON → cycleLoop() 每帧从 iterMap 重新着色
                    ↓                  ↓
              LUT 不变 (固定配色)     LUT 切换 → 配色 ▸ 按钮
```

### 3.2 关键代码

```javascript
// ① 计算时缓存原始迭代值
const idx = py * W + px;
iterMap[idx] = v;              // v ∈ [0, 1]

// ② 循环时仅偏移着色
function cycleLoop() {
    const shift = cycleFrame & 255;
    for (let i = 0; i < iterMap.length; i++) {
        const v = iterMap[i];
        const li = ((v * 255 + shift) & 255);
        data[i*4] = LUT[li*3];
        // ...
    }
    ctx.putImageData(img, 0, 0);
    requestAnimationFrame(cycleLoop);
}
```

### 3.3 内存开销

| 分辨率 | iterMap 大小 | 内存 |
|:---:|:---:|:---:|
| 180×180 | 32,400 | **~130 KB** |
| 420×420 | 176,400 | **~700 KB** |

完全可忽略。

---

## 四、与原版 Divetoxx 的异同

| 维度 | Divetoxx 原版 | 我们的移植 |
|------|------|------|
| 语言 | C++ + OpenMP | JavaScript (浏览器) |
| 输出 | 255 张 BMP → ffmpeg → MP4 | Canvas 实时 60fps |
| 精度 | 80-bit long double / MPFR 5000-bit | JS double (53-bit) |
| 使用场景 | 离线渲染电影级动画 | 实时交互探索 |
| 迭代次数 | 50,000（极深缩放） | 46~90（交互级） |
| 核心思想 | **同样：数学-着色分离 + 调色板偏移** | ✅ |

---

## 五、适用场景与限制

### ✅ 适用

- 固定 `c`（或固定 `s`）下的纯变色动画
- 切换配色方案时的零成本预览
- 音画同步：音符节奏驱动调色板偏移速度

### ❌ 不适用

- 改变 `s` 滑块（alpha 变化 → 必须重算 iterMap）
- 缩放/平移（c 变化 → 必须重算）
- 切换到不同基因序列（泡中心变化）

### 混合策略

```
s 变化时：      重算 iterMap → 触发一次完整渲染（~200ms @ 180px）
s 不变时：      调色板循环 → 60fps 呼吸色（零延迟）
```

---

## 六、Divetoxx 其他可迁移技术

| 技术 | 状态 | 说明 |
|------|:---:|------|
| 调色板循环 | ✅ 已迁移 | 本文 |
| RGB 空间 SSAA 积分 | ⏳ 可迁移 | UF1b 棋盘格抗锯齿 |
| cos/sin 自然调色板 | ✅ 已有 | LUT 生成函数 `makeLUT()` |
| 微扰理论 | — | 不需要（我们不深缩放） |
| 参考重置 | — | 不需要 |

---

> **一句话**：Divetoxx 的"计算一次、变色调无数次"的架构哲学，通过 30 行 JS 迁移到了 DNA_M 音乐探索器。s 滑块不变时，水滴以 60fps 呼吸色动画运行，零额外数学计算。
