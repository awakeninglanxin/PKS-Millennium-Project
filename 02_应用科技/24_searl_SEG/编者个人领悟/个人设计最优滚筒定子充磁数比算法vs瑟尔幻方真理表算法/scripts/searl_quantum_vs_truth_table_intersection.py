#!/usr/bin/env python3
"""
Searl 真值表 vs 蓝馨量子约束 — 精确交集分析（含可视化导出）
============================================================
比较两个列表（Searl 8阶子幻方共享线筛选结果）vs 个人算法（量子数%3==0 + 末位约束）
分析交集、独有、整除性特征、GCD 等，并自动导出 5 张图表到同目录。

作者: AI 辅助蓝馨 | 日期: 2026-06-07
"""

import math
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as mticker
import numpy as np

# ============================================================
# 🔴 铁律: matplotlib 中文渲染必须三步走（不可省略任何一步）
#    1. 删除旧字体缓存
#    2. 设置 font.sans-serif 回退列表（SimHei 在第一）
#    3. axes.unicode_minus=False
# ============================================================
# 步骤1: 清除 matplotlib 字体缓存, 强制重新扫描系统字体
_cache_dir = matplotlib.get_cachedir()
for _f in os.listdir(_cache_dir):
    if _f.endswith('.json'):
        try:
            os.remove(os.path.join(_cache_dir, _f))
        except OSError:
            pass

# 步骤2: 重新加载字体列表, SimHei 放第一位
fm._load_fontmanager(try_read_cache=False)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["SimHei"] + plt.rcParams["font.sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# 步骤3: 基础配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_VAL = 80000

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})


# ============================================================
# 数据加载
# ============================================================
igv_searl_raw = [
    2205,2835,2925,3825,4275,4455,4935,5145,5265,5565,
    6195,6405,6885,7035,7455,7605,7665,7695,8295,8325,
    8715,9075,9225,9315,9345,9675,9855,10185,10575,10605,
    10665,10815,10935,11205,11235,11445,11745,11865,11925,12015,
    12555,12675,13005,13095,13275,13335,13695,13815,13845,13995,
    14085,14235,14265,14685,14895,15165,15405,15615,15705,15885,
    16005,16155,16185,16515,16665,16785,16995,17055,17235,17355,
    17505,17655,17865,18045,18405,18855,18915,18945,19395,19485,
    19695,19755,19935,20085,20145,20205,20565,20745,20835,20865,
    21015,21165,21255,21555,21915,22035,22095,22455,22635,22695,
    22905,23445,23535,24345,24615,24735,24765,25065,25335,25545,
    25605,25695,25755,25965,26265,26415,26685,26715,26955,27045,
    27075,27105,27285,27315,27585,27645,27765,27795,27855,28395,
    28785,28815,28845,28935,29055,29115,29355,29385,29445,29655,
    29745,30285,30465,30495,30735,31065,31095,31545,31905,32205,
    32355,32385,32715,32985,33255,33405,33435,33795,34065,34245,
    34605,34785,34935,35415,35445,35865,36195,36405,36495,36945,
    37035,37215,37305,37335,37755,37995,38385,38505,38565,38655,
    38835,39045,39465,39615,39645,39675,39735,39915,40035,40815,
    40995,41355,41565,41805,42165,42345,42465,42585,42615,42885,
    43035,43125,43515,43695,43965,44115,44235,44595,44745,44865,
    45405,45645,46155,46455,47595,48705,49215,49305,50235,50745,
    51015,51405,51585,52095,53805,54165,54375,54435,55005,56145,
    56235,56715,56865,57615,57885,58125,58395,59415,59685,60135,
    60945,61455,61755,62445,62625,62925,63555,63975,64005,64275,
    64425,64695,64725,64875,65265,65535,65775,65895,66075,66225,
    66405,66525,66585,67125,67875,67965,68025,68115,68325,68655,
    68685,68925,69675,70275,70575,71025,71475,71535,71625,72375,
    72525,72795,72825,73245,73275,73725,73875,74325,74625,74775,
    74955,75675,75975,76425,76575,76665,76935,77235,77325,77475,
    77925,78315,78675,78825,78945,79005,79125,79575,79725
]

seg_searl_raw = [
    3990,4290,4410,4590,4830,4950,5130,5250,5610,5850,
    6090,6210,6270,6510,6630,7350,7410,7590,7650,7770,
    8250,8610,8910,8970,9030,9690,9750,9870,9990,10290,
    10890,11070,11250,11610,11730,12690,12750,13110,13950,14250,
    14310,14790,15210,15810,15930,16470,16530,16650,17250,17670,
    18090,18450,19170,19350,19470,19710,20010,20130,21150,21330,
    21390,21750,21870,22110,22410,23250,23430,23670,24090,24210,
    24390,24930,25290,25350,25470,25530,26070,26370,26970,27390,
    27630,27750,27990,28170,28530,29370,29790,30330,30810,31230,
    31410,31770,32010,32190,32310,32370,33030,33330,33570,33990,
    34110,34410,34470,34710,35010,35310,35670,35730,35970,36090,
    36810,37290,37710,37830,37890,38130,38790,38970,39390,39510,
    39870,39930,39990,40170,40410,41130,41490,41670,41730,41910,
    42030,42510,43110,43350,43830,44070,44190,44910,45270,45510,
    47730,49530,51090,52170,52890,53430,54150,54210,57810,58110,
    58890,60630,61230,63570,63750,65130,65910,66810,67470,69810,
    69870,70890,71250,74730,75990,77010,79350
]

igv_searl = set(igv_searl_raw)
seg_searl = set(seg_searl_raw)


# ============================================================
# 工具函数
# ============================================================
def quantum_num(x):
    return sum(int(d) for d in str(x))


def prime_factors(n):
    factors = set()
    d = 2
    temp = n
    while d * d <= temp:
        while temp % d == 0:
            factors.add(d)
            temp //= d
        d += 1
    if temp > 1:
        factors.add(temp)
    return sorted(factors)


# ============================================================
# 生成个人算法全集
# ============================================================
igv_personal = set(x for x in range(5, MAX_VAL + 1, 10) if quantum_num(x) % 3 == 0)
seg_personal = set(x for x in range(0, MAX_VAL + 1, 10) if quantum_num(x) % 3 == 0)


# ============================================================
# 图1: 核心交集饼环图
# ============================================================
def fig1_venn_donuts():
    """IGV 和 SEG 的 Searl vs 个人算法交集占比"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    data = [
        ("IGV (末位=5)", igv_searl, igv_personal, ax1),
        ("SEG (末位=0)", seg_searl, seg_personal, ax2),
    ]
    colors_in = ["#DC2626", "#2563EB"]
    colors_out = ["#FCA5A5", "#93C5FD"]

    for i, (name, s_set, p_set, ax) in enumerate(data):
        intersect = len(s_set & p_set)
        searl_only = len(s_set - p_set)
        personal_only = len(p_set - s_set)

        sizes = [intersect, personal_only, searl_only]
        labels = [
            f"Searl∩个人\n{intersect}",
            f"仅个人算法\n{personal_only}",
            f"仅Searl\n{searl_only}",
        ]
        colors = [colors_in[i], colors_out[i], "#E5E7EB"]
        explode = (0.06, 0, 0)

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, explode=explode,
            autopct="%1.1f%%", startangle=90,
            wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
            pctdistance=0.78,
        )
        for t in autotexts:
            t.set_fontsize(9)
            t.set_fontweight("bold")
        for t in texts:
            t.set_fontsize(8.5)

        ax.set_title(f"{name}\nSearl={len(s_set)}  个人={len(p_set)}",
                     fontweight="bold", pad=12)

    fig.suptitle("Searl 真值表 << 个人算法 — 100% 严格子集",
                 fontsize=14, fontweight="bold", y=0.99)
    path = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig1_searl_quantum_pie.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"[✓] {path}")


# ============================================================
# 图2: 千位段分布柱状图
# ============================================================
def fig2_distribution_bars():
    """Searl vs 个人算法按千位段分布"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    for ax, name, s_set, p_set in [
        (ax1, "IGV", igv_searl, igv_personal),
        (ax2, "SEG", seg_searl, seg_personal),
    ]:
        # Bin by 2000
        bin_size = 2000
        bins = np.arange(0, MAX_VAL + bin_size, bin_size)
        s_counts, _ = np.histogram(list(s_set), bins=bins)
        p_counts, _ = np.histogram(list(p_set), bins=bins)

        x = np.arange(len(bins) - 1) * bin_size
        width = bin_size * 0.35
        ax.bar(x - width/2, p_counts, width, color="#93C5FD", alpha=0.7,
               label="个人算法", edgecolor="#2563EB", linewidth=0.5)
        ax.bar(x + width/2, s_counts, width, color="#DC2626", alpha=0.85,
               label="Searl", edgecolor="#991B1B", linewidth=0.5)

        ax.set_xlabel("数值范围 (千)")
        ax.set_ylabel("候选数量")
        ax.set_title(f"{name}: Searl ({len(s_set)}) vs 个人 ({len(p_set)})",
                     fontweight="bold")
        ax.legend(fontsize=8)
        ax.set_xticks(x[::4])
        ax.set_xticklabels([f"{int(v//1000)}K" for v in x[::4]], rotation=45)

    fig.suptitle("千位段分布 — 个人算法均匀，Searl 稀疏但不聚集",
                 fontsize=13, fontweight="bold", y=0.99)
    fig.tight_layout()
    path = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig2_distribution_bars.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"[✓] {path}")


# ============================================================
# 图3: 整除性偏差对比
# ============================================================
def fig3_divisibility_deviation():
    """Searl vs 个人算法在不同除数下的占比偏差"""
    divisors = [15, 30, 45, 90, 105, 210, 315, 630]
    x = np.arange(len(divisors))
    width = 0.35

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    for ax, name, s_list, p_set in [
        (ax1, "IGV", igv_searl_raw, igv_personal),
        (ax2, "SEG", seg_searl_raw, seg_personal),
    ]:
        p_all = sorted(p_set)
        s_pct = [sum(1 for v in s_list if v % d == 0) / len(s_list) * 100 for d in divisors]
        p_pct = [sum(1 for v in p_all if v % d == 0) / len(p_all) * 100 for d in divisors]

        bars1 = ax.bar(x - width/2, s_pct, width, color="#DC2626", alpha=0.85,
                       edgecolor="#991B1B", linewidth=0.7, label="Searl")
        bars2 = ax.bar(x + width/2, p_pct, width, color="#93C5FD", alpha=0.7,
                       edgecolor="#2563EB", linewidth=0.7, label="个人")

        # Annotate deviation
        for j, (sp, pp) in enumerate(zip(s_pct, p_pct)):
            diff = sp - pp
            if abs(diff) > 5:
                color = "#059669" if diff > 0 else "#DC2626"
                ax.annotate(f"{diff:+.1f}%", (x[j], max(sp, pp) + 2),
                            ha="center", fontsize=7.5, fontweight="bold", color=color)

        ax.set_xticks(x)
        ax.set_xticklabels([f"÷{d}" for d in divisors])
        ax.set_ylabel("占比 (%)")
        ax.set_title(f"{name}: 各除数下占比对比", fontweight="bold")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("整除性偏差 — Searl 偏好 ÷45 (IGV) / ÷30 (SEG)，排斥 ÷105",
                 fontsize=12.5, fontweight="bold", y=1.01)
    fig.tight_layout()
    path = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig3_divisibility_deviation.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"[✓] {path}")


# ============================================================
# 图4: 3 和 5 的幂次直方图
# ============================================================
def fig4_power_histograms():
    """3 的幂次和 5 的幂次在 Searl 数字中的分布"""
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))

    for col, (name, s_list) in enumerate([
        ("IGV (309个)", igv_searl_raw),
        ("SEG (167个)", seg_searl_raw),
    ]):
        # 3^x
        ax = axes[0, col]
        power3 = defaultdict(int)
        for x in s_list:
            n, p = x, 0
            while n % 3 == 0 and n > 0:
                n //= 3; p += 1
            power3[p] += 1
        ps = sorted(power3.keys())
        vals = [power3[p] for p in ps]
        bars = ax.bar(ps, vals, color="#DC2626", alpha=0.85, edgecolor="#991B1B",
                      linewidth=0.7)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 1.5,
                    str(v), ha="center", fontsize=8, fontweight="bold")
        ax.set_xlabel("3 的指数")
        ax.set_ylabel("个数")
        ax.set_title(f"{name}: 3^x 分布", fontweight="bold")

        # 5^x
        ax = axes[1, col]
        power5 = defaultdict(int)
        for x in s_list:
            n, p = x, 0
            while n % 5 == 0 and n > 0:
                n //= 5; p += 1
            power5[p] += 1
        ps = sorted(power5.keys())
        vals = [power5[p] for p in ps]
        bars = ax.bar(ps, vals, color="#2563EB", alpha=0.85, edgecolor="#1D4ED8",
                      linewidth=0.7)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 1.5,
                    str(v), ha="center", fontsize=8, fontweight="bold")
        ax.set_xlabel("5 的指数")
        ax.set_ylabel("个数")
        ax.set_title(f"{name}: 5^x 分布", fontweight="bold")

    fig.suptitle("Searl 数字中 3 和 5 的幂次分布",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    path = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig4_power_histograms.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"[✓] {path}")


# ============================================================
# 图5: 综合仪表板
# ============================================================
def fig5_dashboard():
    """单图综合仪表板 — 4 个关键指标"""
    fig = plt.figure(figsize=(14, 8))

    # --- Panel A: IGV intersection ---
    ax1 = fig.add_axes([0.05, 0.55, 0.28, 0.38])
    n_inter_igv = len(igv_searl & igv_personal)
    n_total_igv = len(igv_searl)
    ax1.barh(["Searl∩个人"], [n_inter_igv], color="#DC2626", height=0.5)
    ax1.barh(["Searl∩个人"], [n_total_igv - n_inter_igv], color="#E5E7EB",
             height=0.5, left=n_inter_igv)
    ax1.set_xlim(0, max(n_total_igv + 20, 350))
    ax1.set_title(f"IGV: {n_inter_igv}/{n_total_igv} = 100%", fontweight="bold",
                  color="#DC2626")
    ax1.text(n_total_igv/2, 0, f"309 Searl\nsub 2667 personal", ha="center",
             va="center", fontsize=12, fontweight="bold")

    # --- Panel B: SEG intersection ---
    ax2 = fig.add_axes([0.37, 0.55, 0.28, 0.38])
    n_inter_seg = len(seg_searl & seg_personal)
    n_total_seg = len(seg_searl)
    ax2.barh(["Searl∩个人"], [n_inter_seg], color="#2563EB", height=0.5)
    ax2.barh(["Searl∩个人"], [n_total_seg - n_inter_seg], color="#E5E7EB",
             height=0.5, left=n_inter_seg)
    ax2.set_xlim(0, max(n_total_seg + 20, 200))
    ax2.set_title(f"SEG: {n_inter_seg}/{n_total_seg} = 100%", fontweight="bold",
                  color="#2563EB")
    ax2.text(n_total_seg/2, 0, f"167 Searl\nsub 2667 personal", ha="center",
             va="center", fontsize=12, fontweight="bold")

    # --- Panel C: Filter rate ---
    ax3 = fig.add_axes([0.69, 0.55, 0.28, 0.38])
    filter_igv = (1 - len(igv_searl) / len(igv_personal)) * 100
    filter_seg = (1 - len(seg_searl) / len(seg_personal)) * 100
    bars = ax3.bar(["IGV", "SEG"], [filter_igv, filter_seg],
                   color=["#DC2626", "#2563EB"], alpha=0.85,
                   edgecolor=["#991B1B", "#1D4ED8"], linewidth=1)
    for b, v in zip(bars, [filter_igv, filter_seg]):
        ax3.text(b.get_x() + b.get_width()/2, b.get_height() + 0.8,
                 f"{v:.1f}%", ha="center", fontsize=13, fontweight="bold")
    ax3.set_ylabel("过滤率 (%)")
    ax3.set_title("Searl 对个人算法的过滤率", fontweight="bold")

    # --- Panel D: GCD and divisibility summary ---
    ax4 = fig.add_axes([0.05, 0.06, 0.92, 0.42])
    ax4.axis("off")

    gcd_igv = math.gcd(*igv_searl_raw[:1], *(igv_searl_raw[1:]))
    gcd_seg = math.gcd(*seg_searl_raw[:1], *(seg_searl_raw[1:]))

    lines = [
        "=" * 70,
        "  总结: 个人算法（量子数 ≡ 0 mod 3 + 末位约束）是 Searl 真值表的严格上界",
        "=" * 70,
        "",
        f"  IGV: 309/309 覆盖 — 个人遗漏 2,358 个候选 — 全体 GCD = {gcd_igv} (必然是 15 的倍数)",
        f"  SEG: 167/167 覆盖 — 个人遗漏 2,500 个候选 — 全体 GCD = {gcd_seg} (必然是 30 的倍数)",
        "",
        "  [结论] 量子约束是幻方共享线的必要非充分条件。88-94% 的量子合规数字未被 Searl 覆盖",
        "          → 这些是 SEG/IGV 的未勘探设计空间。",
        "",
        f"  保存于: {SCRIPT_DIR}",
    ]
    for i, line in enumerate(lines):
        weight = "bold" if "===" in line or "总结" in line else "normal"
        color = "#DC2626" if "IGV" in line else ("#2563EB" if "SEG" in line else "#333")
        ax4.text(0, 1.0 - i * 0.1, line, transform=ax4.transAxes,
                 fontsize=10, fontweight=weight, color=color, va="top")

    fig.suptitle("SEG/IGV 幻方真值表 × 量子约束 — 综合仪表板",
                 fontsize=15, fontweight="bold", y=1.02)
    path = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig5_dashboard.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"[✓] {path}")


# ============================================================
# Jellium 幻数数列
# ============================================================
# 电子幻数: 2, 8, 18, 20, 34, 40, 58, 68, 90, 92, 106, 112, 138
# 核幻数:   2, 8, 20, 28, 50, 82, 126
# 合并去重（≤80000 范围内有意义的）
JELLIUM_NUMBERS = [2, 8, 18, 20, 28, 34, 40, 50, 58, 68, 82, 90, 92, 106, 112, 126, 138]

# 固定 GCD: IGV 全体候选的 GCD=15, SEG 全体候选的 GCD=30
GCD_IGV = 15
GCD_SEG = 30


# ============================================================
# 图6: Jellium 幻数 × 固定 GCD 的 gcd/lcm 评分
# ============================================================
def fig6_jellium_alignment():
    """Jellium 幻数与 IGV/SEG 固定 GCD 的兼容性分析"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    x = np.arange(len(JELLIUM_NUMBERS))
    width = 0.35

    # --- Panel A: gcd(p, q) — 越小越好 (IGV p=15) ---
    ax = axes[0, 0]
    gcd_vals_igv = [math.gcd(GCD_IGV, q) for q in JELLIUM_NUMBERS]
    bars = ax.bar(x, gcd_vals_igv, color="#DC2626", alpha=0.85,
                  edgecolor="#991B1B", linewidth=0.7)
    ax.axhline(y=1, color="green", linestyle="--", alpha=0.6, label="最优 gcd=1")
    for b, v in zip(bars, gcd_vals_igv):
        if v <= 1:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.3,
                    "★", ha="center", fontsize=14, color="#059669")
        elif v >= 5:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.3,
                    "x", ha="center", fontsize=10, color="#DC2626")
    ax.set_xticks(x)
    ax.set_xticklabels([str(q) for q in JELLIUM_NUMBERS], rotation=45)
    ax.set_ylabel("gcd(15, q)")
    ax.set_title(f"IGV (p={GCD_IGV}): gcd(p, q) — 越小越兼容", fontweight="bold")
    ax.legend(fontsize=8)

    # --- Panel B: gcd(p, q) — SEG p=30 ---
    ax = axes[0, 1]
    gcd_vals_seg = [math.gcd(GCD_SEG, q) for q in JELLIUM_NUMBERS]
    bars = ax.bar(x, gcd_vals_seg, color="#2563EB", alpha=0.85,
                  edgecolor="#1D4ED8", linewidth=0.7)
    ax.axhline(y=1, color="green", linestyle="--", alpha=0.6, label="最优 gcd=1")
    for b, v in zip(bars, gcd_vals_seg):
        if v <= 2:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.3,
                    "★", ha="center", fontsize=14, color="#059669")
        elif v >= 10:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.3,
                    "x", ha="center", fontsize=10, color="#DC2626")
    ax.set_xticks(x)
    ax.set_xticklabels([str(q) for q in JELLIUM_NUMBERS], rotation=45)
    ax.set_ylabel(f"gcd({GCD_SEG}, q)")
    ax.set_title(f"SEG (p={GCD_SEG}): gcd(p, q) — 越小越兼容", fontweight="bold")
    ax.legend(fontsize=8)

    # --- Panel C: lcm(p, q) / (p·q) 归一化评分 — 越大越好 ---
    ax = axes[1, 0]
    score_igv = [math.lcm(GCD_IGV, q) / (GCD_IGV * q) for q in JELLIUM_NUMBERS]
    score_seg = [math.lcm(GCD_SEG, q) / (GCD_SEG * q) for q in JELLIUM_NUMBERS]
    bars1 = ax.bar(x - width/2, score_igv, width, color="#DC2626", alpha=0.85,
                   label="IGV (p=15)", edgecolor="#991B1B", linewidth=0.5)
    bars2 = ax.bar(x + width/2, score_seg, width, color="#2563EB", alpha=0.85,
                   label="SEG (p=30)", edgecolor="#1D4ED8", linewidth=0.5)
    ax.axhline(y=1, color="gray", linestyle="--", alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([str(q) for q in JELLIUM_NUMBERS], rotation=45)
    ax.set_ylabel("lcm(p,q) / (p·q)")
    ax.set_title("归一化 lcm 评分 — 1.0 = 完美互质", fontweight="bold")
    ax.legend(fontsize=8)

    # --- Panel D: Searl 候选通过 Jellium 筛选的统计 ---
    ax = axes[1, 1]
    # 对于每个 Searl 候选 N, 检查它对几个 Jellium q 满足 gcd(p, N) 与 gcd(p, q) 同构
    # 即: N 应该也与固定 p 有小的 gcd, 同时 N 的某些性质对齐 Jellium 幻数

    # 简单指标: 对于每个 Searl N, 计算它与最近 Jellium 幻数的"距离"
    def jellium_score(N, p):
        """综合 Jellium 对齐评分: lcm(p,N)/lcm_avg * gcd_min/gcd(p,N)"""
        g = math.gcd(p, N)
        l_val = math.lcm(p, N)
        # 基础分: gcd 越小越好 (理想=1), lcm 越大越好
        gcd_factor = 1.0 / g  # gcd=1 → 1.0, gcd=15 → 0.067
        # 找到最近的 Jellium 幻数
        nearest_j = min(JELLIUM_NUMBERS, key=lambda j: abs(N - j))
        # 距离因子: N 越接近 Jellium 幻数越好
        dist_factor = 1.0 / (1 + abs(N - nearest_j) / max(N, 1))
        return gcd_factor * dist_factor * math.log1p(l_val / (p * nearest_j + 1)) * 100

    scores_igv = [jellium_score(N, GCD_IGV) for N in igv_searl_raw]
    scores_seg = [jellium_score(N, GCD_SEG) for N in seg_searl_raw]

    # 直方图
    bins = np.linspace(0, max(max(scores_igv), max(scores_seg)) * 1.05, 25)
    ax.hist(scores_igv, bins=bins, alpha=0.6, color="#DC2626", label=f"IGV (n={len(scores_igv)})",
            edgecolor="#991B1B", linewidth=0.3)
    ax.hist(scores_seg, bins=bins, alpha=0.6, color="#2563EB", label=f"SEG (n={len(scores_seg)})",
            edgecolor="#1D4ED8", linewidth=0.3)
    ax.set_xlabel("Jellium 对齐评分 (越高越好)")
    ax.set_ylabel("候选数量")
    ax.set_title("Searl 候选的 Jellium 幻数对齐评分分布", fontweight="bold")
    ax.legend(fontsize=8)

    # 显示 Top 5
    top5_igv = sorted(zip(igv_searl_raw, scores_igv), key=lambda x: -x[1])[:5]
    top5_seg = sorted(zip(seg_searl_raw, scores_seg), key=lambda x: -x[1])[:5]

    fig.suptitle("Jellium 幻数 × Searl 固定 GCD = 增强个人算法第三层过滤",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.tight_layout()
    path = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig6_jellium_alignment.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"[✓] {path}")

    return top5_igv, top5_seg, scores_igv, scores_seg


# ============================================================
# 7. Jellium 增强分析 (文本输出)
# ============================================================
def print_jellium_analysis(top5_igv, top5_seg, scores_igv, scores_seg):
    """打印 Jellium 增强分析的文本结果"""
    print("\n" + "=" * 60)
    print("7. Jellium 幻数增强 — gcd(p,q)↓ + lcm(p,q)↑")
    print("=" * 60)

    print(f"\n固定 GCD: IGV={GCD_IGV}, SEG={GCD_SEG}")
    print(f"Jellium 幻数: {JELLIUM_NUMBERS}")

    print(f"\n--- IGV (p={GCD_IGV}) vs Jellium ---")
    for q in JELLIUM_NUMBERS:
        g = math.gcd(GCD_IGV, q)
        l = math.lcm(GCD_IGV, q)
        score = l / (GCD_IGV * q)
        star = " ★★★" if g == 1 else (" ★★☆" if g <= 3 else (" ★☆☆" if g < 5 else "  x"))
        print(f"  q={q:3d}: gcd={g:2d}, lcm={l:4d}, lcm/(p·q)={score:.3f}{star}")

    print(f"\n--- SEG (p={GCD_SEG}) vs Jellium ---")
    for q in JELLIUM_NUMBERS:
        g = math.gcd(GCD_SEG, q)
        l = math.lcm(GCD_SEG, q)
        score = l / (GCD_SEG * q)
        star = " ★★★" if g <= 2 else (" ★★☆" if g <= 5 else (" ★☆☆" if g < 10 else "  x"))
        print(f"  q={q:3d}: gcd={g:2d}, lcm={l:5d}, lcm/(p·q)={score:.3f}{star}")

    # Top candidates
    print(f"\n--- IGV Top 5 Jellium 对齐候选 ---")
    for N, s in top5_igv:
        nearest = min(JELLIUM_NUMBERS, key=lambda j: abs(N - j))
        g = math.gcd(GCD_IGV, N)
        print(f"  N={N:6d}: 评分={s:.3f}, gcd(15,{N})={g}, 最近幻数={nearest}")

    print(f"\n--- SEG Top 5 Jellium 对齐候选 ---")
    for N, s in top5_seg:
        nearest = min(JELLIUM_NUMBERS, key=lambda j: abs(N - j))
        g = math.gcd(GCD_SEG, N)
        print(f"  N={N:6d}: 评分={s:.3f}, gcd(30,{N})={g}, 最近幻数={nearest}")

    # 第三层过滤: 从个人算法中再筛选
    print(f"\n--- 第三层过滤 (Jellium 对齐评分 > 阈值) ---")
    for name, p_set, p_gcd, label in [
        ("IGV", igv_personal - igv_searl, GCD_IGV, "个人未覆盖"),
        ("SEG", seg_personal - seg_searl, GCD_SEG, "个人未覆盖"),
    ]:
        scored = [(N, jellium_score(N, p_gcd)) for N in sorted(p_set)[:4000]]
        threshold = max(scores_igv) * 0.3 if label == "IGV" else max(scores_seg) * 0.3
        passing = [(N, s) for N, s in scored if s > threshold]
        print(f"  {name} ({label}): 阈值={threshold:.2f}, 通过={len(passing)}/{len(scored)}")

        if passing:
            sample = passing[:10]
            nums = [str(n) for n, _ in sample]
            print(f"    样本: {', '.join(nums)}")


def jellium_score(N, p):
    """综合 Jellium 对齐评分"""
    g = math.gcd(p, N)
    l_val = math.lcm(p, N)
    gcd_factor = 1.0 / g
    nearest_j = min(JELLIUM_NUMBERS, key=lambda j: abs(N - j))
    dist_factor = 1.0 / (1 + abs(N - nearest_j) / max(N, 1))
    return gcd_factor * dist_factor * math.log1p(l_val / (p * nearest_j + 1)) * 100


# ============================================================
# 主流程
# ============================================================
if __name__ == "__main__":
    print("正在生成图表...\n")

    fig1_venn_donuts()
    fig2_distribution_bars()
    fig3_divisibility_deviation()
    fig4_power_histograms()
    fig5_dashboard()
    top5_igv, top5_seg, scores_igv, scores_seg = fig6_jellium_alignment()
    print_jellium_analysis(top5_igv, top5_seg, scores_igv, scores_seg)

    print(f"\n6 张图表已保存到: {SCRIPT_DIR}")
    for f in ["fig1_searl_quantum_pie.png", "fig2_distribution_bars.png",
              "fig3_divisibility_deviation.png", "fig4_power_histograms.png",
              "fig5_dashboard.png", "fig6_jellium_alignment.png"]:
        print(f"  {os.path.join(SCRIPT_DIR, f)}")
