#!/usr/bin/env python3
""" Jellium通项公式可视化 — LCM树 + 素数解锁图 """
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

# ==== Tree data ====
nodes = [
    # (name,x,y,value,jellium_count,color,parents)
    ("5040",       0, 4, 5040, 9, "#8B5CF6", []),
    ("5040\n+23",  2, 3, 115920, 14, "#DC2626", ["5040"]),
    ("5040\n+17", -1, 3, 85680, 11, "#2563EB", ["5040"]),
    ("5040\n+11·13", -2.5, 3, 720720, 12, "#D97706", ["5040"]),
    ("+17+23",    2, 1, 1970640, 16, "#DC2626", ["5040\n+23"]),
    ("+17+23+29", -0.5, 0.5, 57148560, 17, "#059669", ["5040\n+17","5040\n+23"]),
    ("2520\n(seed)", -1, 5, 2520, 8, "#9CA3AF", []),
    ("Searl\n7650", -0.5, 2, 7650, 5, "#93C5FD", ["5040\n+17"]),
    ("Searl\n18450", 1, 2, 18450, 5, "#93C5FD", ["5040\n+23"]),
]
# Edges (from, to)
edges = [
    ("5040","5040\n+23"),("5040","5040\n+17"),("5040","5040\n+11·13"),
    ("5040\n+23","+17+23"),("5040\n+17","+17+23+29"),("5040\n+23","+17+23+29"),
    ("5040\n+17","Searl\n7650"),("5040\n+23","Searl\n18450"),
]

pos = {}
labels = {}
colors = {}
for name,x,y,val,jc,c,_ in nodes:
    pos[name] = (x,y)
    labels[name] = f"{name}\n{jc}个Jellium"
    colors[name] = c

fig, ax = plt.subplots(figsize=(15, 8))

# Edges
for src,dst in edges:
    sx,sy = pos[src]; dx,dy = pos[dst]
    ax.plot([sx,dx],[sy,dy], color="#D1D5DB", linewidth=1.5, zorder=1)

# Nodes
for name,x,y,val,jc,c,parents in nodes:
    size = 800 + jc * 60
    ax.scatter(x, y, s=size, c=c, alpha=0.85, edgecolor="white", linewidth=2, zorder=2)
    ax.annotate(f"{name}\n={val}\n{jc}个Jellium", (x,y),
                ha="center", va="center", fontsize=8.5, fontweight="bold",
                color="white" if c in ["#8B5CF6","#DC2626","#2563EB","#D97706","#059669"] else "#333")

# Legend on the right
legend_data = [
    ("2520 = 2^3·3^2·5·7", "种子 (8个)"), ("5040 = 7! = 2^4·3^2·5·7", "核心种子 (9个)"),
    ("+23解锁: 92,138,184,322", "+4个Jellium"), ("+17解锁: 34,68", "+2个Jellium"),
    ("+11·13解锁: 198,234", "+2个Jellium"), ("+29解锁: 58", "+1个Jellium"),
]
ax2 = ax.twinx(); ax2.set_ylim(0,10); ax2.set_xlim(-4.5, 4)
for i,(prim,desc) in enumerate(legend_data):
    ax.text(2.5, 5-i*0.55, f"{prim}  {desc}", fontsize=9, color="#555", va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#F3F4F6", alpha=0.8))

# Formula box
ax.text(-3.5, -1.2, "N = 5040 · Prod(素数)\n= 2^4·3^2·5·7 · p_1·p_2·...\n每个素数解锁特定Jellium族",
        fontsize=10, fontweight="bold", color="#DC2626", ha="center",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FEF2F2", edgecolor="#DC2626", alpha=0.9))

ax.set_xlim(-4.5, 4); ax.set_ylim(-2, 6.5)
ax.axis("off")
fig.suptitle("Jellium通项公式 — LCM树 + 素数解锁图 (29幻数完整序列)",
             fontsize=14, fontweight="bold", y=1.01)
fig.tight_layout()
p = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig10_jellium_formula_tree.png"
fig.savefig(p); plt.close(fig); print(f"[OK] {p}")
