#!/usr/bin/env python3
""" Jellium最优路径工程价值图 — 3面板 """
import math, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.font_manager as fm
_cache = matplotlib.get_cachedir()
for _f in os.listdir(_cache):
    if _f.endswith('.json'):
        try: os.remove(os.path.join(_cache, _f))
        except OSError: pass
fm._load_fontmanager(try_read_cache=False)
import matplotlib.pyplot as plt; import numpy as np
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["SimHei"] + plt.rcParams["font.sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams.update({"font.size":10,"axes.titlesize":13,"figure.dpi":150,"savefig.dpi":200,"savefig.bbox":"tight"})
SCRIPT = os.path.dirname(os.path.abspath(__file__))

J = [2,8,18,20,28,34,40,50,58,68,82,90,92,106,112,126,138,148,166,184,196,198,212,234,268,278,296,322,324]
def jd(N): return sum(1 for q in J if N%q==0)

# Optimal path data
path = [
    (1, 2, "2", [2]),
    (2, 8, "2^3", [2,8]),
    (4, 40, "2^3*5", [2,8,20,40]),
    (6, 360, "2^3*3^2*5", [2,8,18,20,40,90]),
    (8, 2520, "2^3*3^2*5*7", [2,8,18,20,28,40,90,126]),
    (9, 5040, "2^4*3^2*5*7", [2,8,18,20,28,40,90,112,126]),
    (10, 25200, "x5", [2,8,18,20,28,40,50,90,112,126]),
    (11, 85680, "x17", [2,8,18,20,28,34,40,68,90,112,126]),
    (13, 115920, "x23", [2,8,18,20,28,40,90,92,112,126,138,184,322]),
    (15, 1970640, "x17*23", [2,8,18,20,28,34,40,68,90,92,112,126,138,184,322]),
]
ns = [p[0] for p in path]
vals = [p[1] for p in path]
formulas = [p[2] for p in path]

fig = plt.figure(figsize=(16, 9))

# ==== Panel A: 左上 — log(N)阶梯图 ====
ax1 = fig.add_axes([0.05, 0.55, 0.42, 0.40])
ax1.plot(ns, [math.log10(v) for v in vals], 'o-', color="#8B5CF6", linewidth=2.5, markersize=9, zorder=3)
for i,(n,v,f) in enumerate(zip(ns,vals,formulas)):
    offset = 0.2 if i%2==0 else -0.28
    ax1.annotate(f"N={v:,}\n{f}", (n, math.log10(v)),
                fontsize=7.5, ha="center", color="#6D28D9",
                xytext=(0, offset*8), textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="#F5F3FF", alpha=0.85))
ax1.set_xlabel("Jellium幻数整除个数 n")
ax1.set_ylabel("log10(N)")
ax1.set_title("最小N随Jellium除数增长 (对数尺度)", fontweight="bold")
# Mark 5040 line
ax1.axhline(y=math.log10(5040), color="#DC2626", linestyle="--", alpha=0.5, linewidth=1)
ax1.annotate("5040基准", (1, math.log10(5040)+0.3), fontsize=9, color="#DC2626")
# Mark Searl range
ax1.fill_between([0,9], math.log10(2205), math.log10(80000), alpha=0.08, color="#2563EB")
ax1.annotate("Searl范围", (2, math.log10(40000)), fontsize=9, color="#2563EB")
ax1.grid(alpha=0.3)

# ==== Panel B: 右上 — 边际效率条形图 ====
ax2 = fig.add_axes([0.53, 0.55, 0.44, 0.40])
factors = ["5^2", "7^2", "3^4", "29", "17", "23", "37", "11+13", "41", "53"]
unlocks = [1, 1, 1, 1, 2, 4, 2, 4, 1, 2]
multipliers = [5, 7, 9, 29, 17, 23, 37, 143, 41, 53]
efficiency = [u/m for u,m in zip(unlocks, multipliers)]
colors = ["#2563EB" if e>=0.05 else "#D97706" if e>=0.02 else "#DC2626" for e in efficiency]
bars = ax2.barh(factors, efficiency, color=colors, alpha=0.85, edgecolor="white", linewidth=1)
for b,e,u,m in zip(bars,efficiency,unlocks,multipliers):
    ax2.text(b.get_width()+0.002, b.get_y()+b.get_height()/2,
             f"+{u}个 / x{m} = {e:.3f}", fontsize=9, va="center")
ax2.set_xlabel("边际效率 (新增Jellium数 / 成本倍数)")
ax2.set_title("各素数的边际效率", fontweight="bold")
ax2.grid(axis="x", alpha=0.3)
# Legend
from matplotlib.patches import Patch
ax2.legend(handles=[
    Patch(color="#2563EB", label="高: >=0.05"),
    Patch(color="#D97706", label="中: 0.02-0.05"),
    Patch(color="#DC2626", label="低: <0.02"),
], fontsize=8, loc="lower right")

# ==== Panel C: 下半部分 — 工程价值解释 ====
ax3 = fig.add_axes([0.03, 0.02, 0.94, 0.48])
ax3.axis("off")

lines = [
    ("工程价值:", 0, 0.95, "#DC2626", 14),
    ("", 0, 0, "#333", 10),
    ("  n=9  (5040):  基准SEG — Jellium全覆盖的最小质量/磁极数。相当于\"SEG最优种子\"", 0, 0.85, "#8B5CF6", 11),
    ("  n=10 (25200):  乘5 → +50解锁。只需5倍成本换1个额外Jellium对齐。适合低成本升级", 0, 0.78, "#2563EB", 11),
    ("  n=11 (85680):  乘17 → +34,68解锁。17倍成本换2个Jellium。适合轻量化设计", 0, 0.71, "#2563EB", 11),
    ("  n=13 (115920): 乘23 → +92,138,184,322解锁。最划算单素数因子(4个Jellium/23倍成本)", 0, 0.64, "#059669", 11),
    ("  n=15 (1970640): 乘17*23 → 联合解锁。磁极数/质量进入另一量级，定子环需要更大的幻方结构", 0, 0.57, "#DC2626", 11),
    ("", 0, 0.50, "#333", 10),
    ("  实际含义:", 0, 0.43, "#DC2626", 14),
    ("    * 5040作为种子: 对应SEG定子磁极数 = 5040 = 168*30 = Jellium全激活最小单元", 0, 0.36, "#333", 10.5),
    ("    * 每个分叉路径 = 一种SEG设计变体: 不同素数解锁不同Jellium幻数族, 对应不同的磁极共鸣模式", 0, 0.30, "#333", 10.5),
    ("    * 23(92,138,184,322) 与 17(34,68) 不可互换: 选23=增加含7/23的共振, 选17=增加含17的共振", 0, 0.24, "#333", 10.5),
    ("    * 在幻方真值表中搜索这些N: 如果N出现在共享线和列表中 → Jellium共振被幻方几何验证 → 双重保障", 0, 0.18, "#333", 10.5),
    ("    * 设计决策: 选5040*5(25200)=钱少质轻但Jellium覆盖少; 选5040*17*23(1970640)=钱多质重但覆盖最全", 0, 0.12, "#333", 10.5),
    ("", 0, 0.05, "#333", 10),
    ("  [结论] 23和17是SEG的\"黄金素数\"— 它们以最小的成本解锁最多的Jellium幻数, 且互不重叠", 0, 0.0, "#DC2626", 11),
]
for text, x, y, color, size in lines:
    ax3.text(x, y, text, fontsize=size, color=color, fontweight="bold" if size>=12 else "normal", va="top")

fig.suptitle("Jellium通项 — 最优路径与SEG工程价值",
             fontsize=15, fontweight="bold", y=1.01)
p = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig11_jellium_engineering_value.png"
fig.savefig(p); plt.close(fig)
print(f"[OK] {p}")
