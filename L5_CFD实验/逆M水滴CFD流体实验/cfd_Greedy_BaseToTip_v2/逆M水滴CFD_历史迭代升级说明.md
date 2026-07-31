# 逆M水滴CFD流体实验 — 历史迭代升级说明

> **实验目录**：`cfd_Greedy_BaseToTip_v2/`
> **水滴模型**：逆M集水滴解析轮廓 (droplet_invM_analytic.csv)
> **仿真方法**：格子Boltzmann方法 (LBM) D2Q9

---

## 一、版本演进总览

| 版本 | 文件标识 | 网格 | 算法 | 来流方式 | sway | fps | 结果 |
|:---:|:---|:---:|:---|:---|:---:|:---:|:---|
| v4 | `BaseToTip_v4` | — | BGK | 双向对冲 | — | — | 🔴 乱流 |
| v5 | `v5_fixed` | — | BGK | 双向修正 | — | — | 🟡 修正 |
| v6 | `v6` | — | MRT | — | — | — | 🔴 崩了 |
| v8 | `MRT_v8` | 350×175 | BGK | 单向恒定 | 0 | — | 🟢 太直 |
| v9 | `v9_sway` | 350×175 | BGK | 摆动入流 | 0.012 | — | 🟢 初版 |
| v9b | `v9b_sway` | 400×200 | BGK | 1.5×入流 | 0.018 | 12 | 🟢 |
| v9c | `v9c_sway` | 400×200 | BGK | 快频慢放 | 0.018 | 3 | 🟢 |
| v12 | `v12_coarse` | 300×180 | CuPy fp32 | 粗网格 | 0.12 | 24 | 🟢 |
| v12b | `v12b_*` | 300×180 | CuPy fp32 | 半幅摆 | 0.06 | 12 | 🟢 |
| **v12c** | `v12c_*` | 300×180 | CuPy fp32 | **1/8原版幅+半频** | **0.03** | **12** | 🟢 **当前最优** |
| v10 | `v10_cupy` | 420×240 | CuPy fp64 | — | 0.12 | — | 🔴 16% util→0KB |
| v11 | `v11_fused` | 420×240 | CuPy fp32 | bug: 碰撞不回写 | — | — | 🔴 无碰撞 |
| v13 | `v13_*` | 300×180 | RawKernel | 编译失败 | — | — | 🔴 NVRTC error |

---

## 二、各版本详解

### v4 — 双向冲水 (2026-07-11 12:38)

**思路**：水滴钝端→尖端是气流方向(逆M水滴的物理流向)，同时尖端→钝端也放一股来流，形成"对冲"尾流。

**实现**：LBM BGK，左边界(钝端) + 右边界(尖端) 同时入流。

**问题**：
- 两股对冲流在尾部相遇，涡量相互抵消
- 23MB 文件大小 = 高分辨率但乱流
- 未形成清晰的卡门涡街

**教训**：双向对冲不是物理上合理的模拟场景——真实水滴只有单一风向。

---

### v5 — 双向修正 (2026-07-11 14:17)

**改进**：调整左右入流速度比，加强钝端来流，减弱尖端来流。

**结果**：12MB，涡街开始出现但不稳定。反弹边界在尖端的镜面反射仍存残留。

---

### v6 — MRT尝试 (2026-07-11 16:14)

**尝试**：用多松弛时间(MRT)替代BGK碰撞算子。

**问题**：144KB → 几乎无内容，可能数值发散。MRT参数矩阵不匹配D=125的粗网格。

**教训**：小网格(350×175)下BGK已经足够。MRT的稳定性优势在大Re数才显现。

---

### v8 — 单向恒定入流 (2026-07-11 22:34)

**思路**：放弃双向对冲，改用标准圆柱绕流配置——左边界恒定入流(u0=0.04)，右边界自由出流。

**实现**：
- NX=350, NY=175, τ=0.60, Re≈1200
- Zou-He 入流边界条件
- 反弹边界 + 自由出流
- 涡量(vorticity) + 涡街(vortex) 双版本输出

**成果**：
- `droplet_MRT_v8_vortex.gif` (7.6MB) — ✅ **唯一合格**
- `droplet_MRT_v8_vorticity.gif` (6.3MB) — 涡量伪彩色
- `droplet_MRT_v8_Re169_vorticity.gif` (609KB) — 低Re对比
- `droplet_MRT_v8_Re372_vorticity.gif` (671KB) — 中Re对比
- `droplet_MRT_v8_Re1200_vorticity.gif` (716KB) — 高Re对比

**缺陷**：
- **左边界入流太直**——入流是恒定水平速度，无任何上下摆动
- 涡街虽然清晰，但尾流的交叉卷曲不够美
- 实际物理中，来流总有不稳定扰动——完全平直入流是理想化的

---

### v9 — 摆动入流 ✦ (2026-07-20)

**核心改进**：入流不只是水平方向的 u0，而是叠加了垂直方向的正弦摆动：

$$u_y(t) = A \sin\left(\frac{2\pi t}{T}\right)$$

$$u_x(t) = u_0 \quad (\text{恒定})$$

**实现**：修改 Zou-He 入流边界条件，增加 uy 分量到 f5, f8 分布函数中。

**参数**：
| 参数 | 值 | 说明 |
|:---|:---:|:---|
| u0 | 0.04 | 水平入流速度 |
| A (摆幅) | 0.012 | 垂直摆动速度幅值 = u0的30% |
| T (周期) | 400步 | 约10个完整周期覆盖仿真 |
| τ | 0.60 | 松弛时间 |
| NX×NY | 350×175 | 网格分辨率 |
| Re | ~1200 | 等效雷诺数 |

**预期效果**：
- 入流周期性上下摆动 → 尾流产生交叉涡卷
- 类似"八字舞"的涡街图案
- 比恒定入流更接近真实物理（自然界来流从不完美平直）

**公式变更** (v8→v9)：

```
# v8 (恒定入流，只含ux):
rho[1,jy] = (...)/(1-u0)
f[1,jy,1] = f3 + 2/3*rho*u0
f[1,jy,5] = f7 - 0.5*(f2-f4) + 1/6*rho*u0
f[1,jy,8] = f6 + 0.5*(f2-f4) + 1/6*rho*u0

# v9 (摆动入流，含ux+uy):
uy_sway = A * sin(2π*t/T)
rho[1,jy] = (...)/(1-u0)              # 不变
f[1,jy,1] = f3 + 2/3*rho*u0          # 不变 (ux占主导)
f[1,jy,5] = f7 - 0.5*(f2-f4) + 1/2*rho*uy_sway + 1/6*rho*u0  ← 新增uy项
f[1,jy,8] = f6 + 0.5*(f2-f4) + 1/2*rho*uy_sway + 1/6*rho*u0  ← 新增uy项
```

---

## 三、技术积累与教训

### 3.1 LBM 网格选择

| 网格 | Re范围 | 稳定性 | 适用 |
|:---|:---|:---|:---|
| 350×175 | <2000 | 🟢 BGK稳定 | 快速验证、参数扫描 |
| 500×250 | <5000 | 🟡 BGK临界 | 精密涡街 |
| 600×300 | <8000 | 🔴 需MRT | 高Re湍流 |

### 3.2 入流边界条件

| 方法 | 精度 | 复杂度 | 适用 |
|:---|:---|:---|:---|
| Zou-He 恒定 | ★★★ | 低 | 基准对照 |
| **Zou-He 摆动** ✦ | ★★★ | 低 | **当前最优** |
| 正弦速度剖面 | ★★★★ | 中 | 层流入口 |
| 湍流入口 | ★★★★★ | 高 | DNS/LES |

### 3.3 水滴轮廓精度

- 98 点 Greedy 轮廓 (v4-v6) → 精度高但计算重
- 解析 CSV 全轮廓 (v8-v9) → 直接加载，N_half=500+点

---

## 四、未来方向

| 优先级 | 方向 | 说明 |
|:---:|:---|:---|
| P0 | v9 验证 | 确认摆动入流是否产生预期交叉涡卷 | ✅ 已完成 |
| P1 | GPU加速 | 用 CuPy 重写 LBM 碰撞/流步骤，10×加速 | ✅ v12 CuPy |
| P2 | 多振幅对比 | A=0.008/0.012/0.020 三档对比涡街差异 | ✅ v12b/v12c |
| P3 | 真实水滴尺寸 | NX=600, Re=5000+ 的精密涡街 | 待做 |
| P4 | 3D LBM D3Q19 | 真正三维水滴绕流 | 待做 |

---

## 五、v9→v12 完整迭代日志（2026-07-20）

### v9 → v9b (加速入流)
- 日期：2026-07-20 08:55
- u0: 0.04→0.06 (1.5×), STEPS: 4000→8000 (2×)
- 网格: 350×175→400×200, 摆动周期T=400→600
- GIF: `droplet_MRT_v9b_sway_vortex/vorticity.gif`

### v9 → v9c (快频+慢放)
- 日期：2026-07-20 09:29
- 摆动频率×2 (T=600→300), 截图间隔 25→100 步
- 播放 3fps 慢放 4×, 文件名 `droplet_MRT_v9c_*`
- **铁律80b启用: GPU出图标题全英文**

### v10 CuPy GPU (失败)
- 日期：2026-07-20 09:51
- np→cp CuPy, collision vectorized, fp64
- 问题: 18次独立 cp.roll kernel 发射 → GPU util ~16%
- 最终被 pkill 杀死 → 0KB 文件

### v11 fused (bug)
- 日期：2026-07-20 09:54
- fp32 + 全向量化碰撞
- **Bug**: f.transpose(2,0,1).copy() 碰撞结果写回临时副本 fT, 从未写入原 f → 无碰撞
- 同翻重 bounce-back 代码, 更慢了

### v12 CuPy 粗网格 (首版成功)
- 日期：2026-07-20 10:00
- 网格: 420×240→300×180, fp32, in-place (1,1,9) broadcast 碰撞
- sway=0.12, 24fps, vmax=0.12-0.15 vivid color
- 389s for 40000 steps (~9.7ms/step)
- GIF: `droplet_v12_coarse_vortex/vorticity.gif` 16MB each

### v12b (半幅摆)
- 日期：2026-07-20 13:40
- sway: 0.12→0.06 (half), fps: 24→12
- vmax: 0.08-0.10 更浓尾流
- GIF: `droplet_v12b_vortex/vorticity.gif` 20-21MB

### v12c (再半幅+半频)
- 日期：2026-07-20 14:02
- sway: 0.06→0.03 (1/8原版), T: 300→600 (half freq)
- fps=12, vmax=0.08-0.10
- GIF: `droplet_v12c_vortex/vorticity.gif` 23-24MB
- **铁律80启用: 文件名含唯一版本号后缀**

### v13 RawKernel (编译失败)
- 日期：2026-07-20 13:39
- 尝试单 kernel 碰撞+流合并 → 100% GPU
- NVRTC_ERROR_COMPILATION: bounce_back kernel 缺 cx/cy 参数
- 修复后仍失败 → 放弃 RawKernel, 回退 v12 稳定架构

---

## 六、技术教训汇总

### 教训1: 文件名唯一化 (铁律80)
- 复用旧名 → SFTP 覆盖 → 0KB → 批次报废
- **每次迭代必须换新名**（如 v12b_*, v12c_*）

### 教训2: GPU 标题全英文 (铁律80b)
- GPU 无中文字体 → matplotlib 缺字 → 方框
- 本地可中文, GPU 必须全英文

### 教训3: RawKernel 编译脆弱性
- CuPy RawKernel 参数传递复杂, 缺一个参数整个报错
- 稳定方案: CuPy 高级 API (broadcast + cp.roll), 虽然 GPU util 低但 100% 出图

### 教训4: collison 必须原位写回
- transpose+copy 创建临时副本, 忘记写回 → 无碰撞
- 用 (1,1,9) broadcast 直接原位修改 f

### 教训5: 0KB 文件立即清理
- 多次 0KB 文件残留导致后续检查混乱
- 完成立即 rm, 不保留僵尸文件

---

## 七、文件清单

```
cfd_Greedy_BaseToTip_v2/
├── cfd_mrt_droplet_v9.py                     v9 源码
├── cfd_mrt_droplet_v12.py / v12b.py / v12c.py v12系列源码
├── droplet_BaseToTip_vorticity_v4.gif         (23MB) v4
├── droplet_BaseToTip_vorticity_v5_fixed.gif   (12MB) v5
├── droplet_MRT_v8_vortex.gif                  (7.3MB) v8 ✅唯一定性
├── droplet_MRT_v9_sway_vortex.gif             (7.8MB) v9
├── droplet_MRT_v9b_sway_vortex.gif            (15MB) v9b 1.5×入流
├── droplet_MRT_v9c_sway_vortex.gif            (3.9MB) v9c 快频慢放
├── droplet_v12b_vortex.gif                    (21MB) v12b 半幅摆
├── droplet_v12b_vorticity.gif                 (20MB) v12b 涡量版
├── droplet_v12c_vortex.gif                    (24MB) v12c 最终版
├── droplet_v12c_vorticity.gif                 (23MB) v12c 涡量版
└── 逆M水滴CFD_历史迭代升级说明.md            (本文档)
```

---

*最后更新: 2026-07-20 17:50 | 覆盖 v4→v12c 全版本*

---

## 五、文件清单

```
cfd_Greedy_BaseToTip_v2/
├── droplet_BaseToTip_vorticity_v4.gif       (23MB) v4 双向对冲
├── droplet_BaseToTip_vorticity_v5_fixed.gif  (12MB) v5 修正
├── droplet_BaseToTip_vorticity_v6.gif       (144KB) v6 失败
├── droplet_MRT_v8_vortex.gif                (7.6MB) v8 ✅ 唯一定性
├── droplet_MRT_v8_vorticity.gif             (6.3MB) v8 涡量
├── droplet_MRT_v8_Re169_vorticity.gif       (609KB) v8 低Re
├── droplet_MRT_v8_Re372_vorticity.gif       (671KB) v8 中Re
├── droplet_MRT_v8_Re1200_vorticity.gif      (716KB) v8 高Re
├── droplet_MRT_v9_sway_vortex.gif           (NEW)   v9 摆动涡街
└── droplet_MRT_v9_sway_vorticity.gif         (NEW)   v9 摆动涡量
```

---

*创建于 2026-07-20 | 基于 cfd_mrt_droplet_v8.py → v9 升级*
