# 归档索引 — 2026-07-18 会话全部产出

> 本目录分类归档了本次会话中散落在 `C:\Users\ThinkPad\WorkBuddy\2026-07-01-16-57-11\` 的**全部脚本、数据、报告、图片**。
> ⚠️ GitHub 版最终报告在 `D:\AAA我的文件\PKS_千禧难题_GitHub版\`，本目录存本地工作副本。

---

## 📂 01_锚点2_X星k定律（核心产出）

### 证据链

```
命题: C_k: 素数 p 可由 B-smooth 碰撞表示
↓
本地 CPU 验证 (verify_9base..) → 发现 k=9 在 1e7 有 2 个反例
↓
深检 D=1e12 (deep_check_counterexamples..) → 确认 9,734,639 零表示
↓
GPU 阶梯1 (smooth_gpu.py + run_ladder.sh) → k=7..11 × X=1e8/1e9 全部数据
↓
GPU 阶梯2 (run_ladder2.sh) → k=12/13 扩展
↓
综合报告 md (PKS GitHub) + 意义阐释 md + 归档
```

| 文件 | 角色 | 说明 |
|------|------|------|
| **脚本_GPU核心/** | | |
| `smooth_gpu.py` | 主算法 | CuPy 加速 B-smooth 碰撞覆盖计算, X*(k) 首反例搜索 |
| `run_ladder.sh` | 批处理1 | k=7..11 × X=1e8/1e9 阶梯执行 |
| `run_ladder2.sh` | 批处理2 | k=12 X=1e8/1e9 + k=13 X=1e9 |
| `deep_check_remote.py` | 深检 | 对 GPU 产出的 miss 扩大部件搜索 (D=1e13) |
| **脚本_本地验证/** | | |
| `verify_9base_smooth_coverage.py` | 本地全栈验证 | 4 阶段: 覆盖率曲线 + 1e7反例搜索 + E(p)实测 + k(X)外推 |
| `deep_check_counterexamples.py` | 本地深检 | D=1e12 确认 9,734,639/9,982,241 零表示 |
| `gpu2_helper.py` | GPU 连接器 | paramiko SSH/SFTP 远程执行助手 (port 20220) |
| `gpu_probe.py` | GPU 探测 | 登录实例验证 CUDA/CuPy/显存/占用 |
| `dl_all.py` / `dl_k12.py` | 下载器 | SFTP 批量拉取 GPU 产出的 miss 文件和 summary |
| **数据/** | | |
| `basis_1e7_results.json` | 早期结果 | k=7 baseline 在 1e7 的局部测试数据 |
| **日志/** | (空，主要日志在 PKS GitHub 的 `锚点2_GPU验证结果_*/` 中) | |

### 完整 GPU 数据集（在 PKS GitHub 中）
```
PKS_千禧难题_GitHub版/锚点2_GPU验证结果_2026-07-18/
├── summary.jsonl         ← 12 组配置完整汇总
├── ladder.log            ← 阶梯1 原始日志
├── ladder2.log           ← 阶梯2 原始日志
├── miss_k*_X*.txt        ← 各配置缺失素数列表 (k=7..13)
├── smooth_gpu.py         ← GPU 源码副本
├── deep_check_remote.py  ← 深检源码副本
└── verify_9base_smooth_coverage.py ← 本地验证源码副本
```

---

## 📂 02_Glynn分形渲染

| 文件 | 版本 | 说明 |
|------|------|------|
| `render_glynn.py` | v1 | 失败版（escape 半径太小 + 无索引压缩，250s 全黑） |
| `render_glynn2.py` | v2 | 临界轨道溢出修复 + 自动取景 |
| `render_glynn3.py` | v3 | 色板最近邻链，绿带偏窄 |
| `render_glynn4.py` | **v4 最终** | 按参考图色系占比三段分带，直方图均衡，2×超采样 |

最终渲染在：`D:\...\julia-set分形相关\Glynn_z1p5_c-0p2_仿参考渲染_2026-07-18.png`

---

## 📂 03_逆M树状代码生成器P0

| 文件 | 说明 |
|------|------|
| `inverse_m_tree.py` | Eq12 ±√(z−c) 分叉 + Eq13 2^N 满二叉树 + 去重; 可选 CuPy |
| `run_batch.sh` | GPU 批处理: seahorse 高清 + 四经典 |
| `gpu_run.py` | paramiko 远端执行 |
| `remote_put.py` / `remote_get.py` | SFTP 上传/下载 |
| `remote_run.py` / `gpu_check.py` | 远端探测工具 |

最终输出在：`D:\...\逆M树状代码生成器_P0_2026-07-18\`

---

## 📂 04_PKS子项目_脚本

历史遗留脚本（t1-t6、CFD、BSD、GPU benchmark 等），以 `_` 前缀标记为临时/实验性质：
- `_pks_t1t6_gpu.py`, `_tasks1234.py`, `_t1234.py` — T1-T6 GPU 实验
- `_cfd_v3.py`, `_cfd_real.py`, `_cfd_vortex_v2.py` — CFD 仿真
- `_bsd_gpu_cupy.py` — BSD CuPy 实现
- `_croft_goldbach.py`, `_basis_search.py` — Croft/Goldbach 探索
- `pks_backtest.py` / `_v2.py` — 回测脚本
- `validate_*.py` — 参数独立性和路由器验证

---

## 📂 05_分析报告与图片

| 文件 | 说明 |
|------|------|
| `PKSxAI_GPU最终实验报告.md` | |
| `PKSxT1-T6_小白说明_你的数学怎么帮AI.md` | |
| `PKS工具xT1-T6采样理论_工程交叉分析.md` | |
| `PKS算法xAI落地应用价值分析.md` | |
| `PKSx扩散模型采样理论_论文提纲.md` | |
| `01_farey_noise_schedule.png` ~ `04_bsmooth_dp.png` | 可视化图片 |
| `tasks123_summary.png` / `tasks1234.png` | 任务汇总图 |
| `pks_t1t6_results.json` / `results.json` | 结果数据 |

---

## 🔗 外部链接

- **PKS GitHub 完整报告**：`D:\AAA我的文件\PKS_千禧难题_GitHub版\PKS_锚点2_B-smooth碰撞覆盖_X星k指数定律_2026-07-18.md`
- **意义阐释**：`D:\AAA我的文件\PKS_千禧难题_GitHub版\PKS_锚点2_X星k指数定律_三层意义与跨界类比_2026-07-18.md`
- **Julia 集相关工作**：`D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M详细代码\逆M树状代码\julia-set分形相关\`
- **逆M树状代码 P0**：`D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M详细代码\逆M树状代码\逆M树状代码生成器_P0_2026-07-18\`
