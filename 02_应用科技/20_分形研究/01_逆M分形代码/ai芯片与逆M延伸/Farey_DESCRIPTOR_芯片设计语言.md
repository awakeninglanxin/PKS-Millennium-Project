# Farey DESCRIPTOR — 从分形参数化到芯片设计语言

> 2026-07-13 | Farey_Native × DESCRIPTOR 格式扩展 + 普林斯顿空间频率启示

---

## 一、Farey DESCRIPTOR 定义

```json
{
  "schema": "farey-chip-descriptor/1.0",
  "farey_period": [2, 3, 4, 5, 6, 7, 8, 9],
  "anchors": {"total": 15},
  "topology": {"type": "farey_tree", "routing": "sharkovsky_order", "weights": "euler_totient"},
  "die_layout": {"count": 15, "coordinates": "farey_anchors_on_cardioid"},
  "performance": {"target_frequency_ghz": 2.4},
  "style": {"spatial_frequency": "high", "layout_mode": "pixelated"}
}
```

### 关键字段

| 字段 | 数学来源 | 芯片映射 |
|------|------|------|
| `anchors.total=15` | $\sum_{k=2}^9 \lceil\varphi(k)/2\rceil = 15$ | 15-die Chiplet |
| `topology.routing` | Sharkovsky: 3▷5▷7▷...▷4▷2▷1 | 无死锁调度 |
| `weights` | $\varphi(n)$ Euler totient | 互联带宽 |
| `style.spatial_frequency` | 普林斯顿三频切换 | 版图可读性vs性能 |

---

## 二、与普林斯顿空间频率对接

| 空间频率 | Farey 周期 | 视觉效果 |
|:--:|:--:|------|
| `"low"` | period 2-4 | 经典对称，4 节点 |
| `"medium"` | period 2-6 | 迷宫，7 节点 |
| `"high"` | period 2-9 | 像素化创新，15 节点 |

普林斯顿的空间频率是无结构连续参数 → Farey 的空间频率有**内在离散结构**，跨频率可确定性转换（加 period = 加锚点）。

---

## 三、与 Verkor 219 词对比

| | Verkor 219 词 | Farey DESCRIPTOR |
|------|:--|:--|
| 长度 | ~1KB | ~500B |
| 歧义 | Agent 需解读 | 结构化无歧义 |
| 调度 | Agent 自由决定 | Sharkovsky 预定义 |
| 数学保证 | 无 | Farey 树唯一拓扑 |

Farey DESCRIPTOR 不给 Agent 留"猜架构"的余地——拓扑已由 Farey 数学预先确定。

---

## 四、完整压缩链

```
Farey DESCRIPTOR (500B JSON)
  → Farey 拓扑解释器 (<1ms)
    → Die 坐标 + φ(n) 权重
      → 扩散模型 (Farey Mode + 空间频率)
        → 芯片版图 (256×256)
          → CNN EM 仿真器 (ms 级)
            → GDSII (~10MB)

压缩: 500B → 10MB = 20,000:1
```

与分形 DESCRIPTOR 同质不同域：存生成规则，不存像素/走线。
