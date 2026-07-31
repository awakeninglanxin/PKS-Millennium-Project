#!/usr/bin/env python3
"""
增强个人算法(三层) vs Searl 原版真值表 — 精确交集对比 (修正版)
===============================================================
范围: IGV/SEG 均取 2205 (含) ~ 80000
修正: SEG 起始值对齐到末位=0 (即 2205->2210)

三层过滤:
  L1: 末位 = 0(SEG)/5(IGV)
  L2: 量子数 % 3 == 0
  L3: Jellium幻数对齐 (N/p 商与Jellium的距离 + gcd(p,q)偏好)

作者: AI辅助蓝馨 | 日期: 2026-06-07
"""

import math, os
from collections import defaultdict

import matplotlib; matplotlib.use("Agg")
import matplotlib.font_manager as fm

# ==== 铁律57 ====
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
plt.rcParams.update({"font.size":10,"axes.titlesize":13,"axes.labelsize":11,
                      "figure.dpi":150,"savefig.dpi":200,"savefig.bbox":"tight"})

SCRIPT = os.path.dirname(os.path.abspath(__file__))
MINV, MAXV = 2205, 80000

# ============================================================
# 数据加载
# ============================================================
igv_searl = {2205,2835,2925,3825,4275,4455,4935,5145,5265,5565,6195,6405,6885,7035,
             7455,7605,7665,7695,8295,8325,8715,9075,9225,9315,9345,9675,9855,10185,
             10575,10605,10665,10815,10935,11205,11235,11445,11745,11865,11925,12015,
             12555,12675,13005,13095,13275,13335,13695,13815,13845,13995,14085,14235,
             14265,14685,14895,15165,15405,15615,15705,15885,16005,16155,16185,16515,
             16665,16785,16995,17055,17235,17355,17505,17655,17865,18045,18405,18855,
             18915,18945,19395,19485,19695,19755,19935,20085,20145,20205,20565,20745,
             20835,20865,21015,21165,21255,21555,21915,22035,22095,22455,22635,22695,
             22905,23445,23535,24345,24615,24735,24765,25065,25335,25545,25605,25695,
             25755,25965,26265,26415,26685,26715,26955,27045,27075,27105,27285,27315,
             27585,27645,27765,27795,27855,28395,28785,28815,28845,28935,29055,29115,
             29355,29385,29445,29655,29745,30285,30465,30495,30735,31065,31095,31545,
             31905,32205,32355,32385,32715,32985,33255,33405,33435,33795,34065,34245,
             34605,34785,34935,35415,35445,35865,36195,36405,36495,36945,37035,37215,
             37305,37335,37755,37995,38385,38505,38565,38655,38835,39045,39465,39615,
             39645,39675,39735,39915,40035,40815,40995,41355,41565,41805,42165,42345,
             42465,42585,42615,42885,43035,43125,43515,43695,43965,44115,44235,44595,
             44745,44865,45405,45645,46155,46455,47595,48705,49215,49305,50235,50745,
             51015,51405,51585,52095,53805,54165,54375,54435,55005,56145,56235,56715,
             56865,57615,57885,58125,58395,59415,59685,60135,60945,61455,61755,62445,
             62625,62925,63555,63975,64005,64275,64425,64695,64725,64875,65265,65535,
             65775,65895,66075,66225,66405,66525,66585,67125,67875,67965,68025,68115,
             68325,68655,68685,68925,69675,70275,70575,71025,71475,71535,71625,72375,
             72525,72795,72825,73245,73275,73725,73875,74325,74625,74775,74955,75675,
             75975,76425,76575,76665,76935,77235,77325,77475,77925,78315,78675,78825,
             78945,79005,79125,79575,79725}

seg_searl_all = [3990,4290,4410,4590,4830,4950,5130,5250,5610,5850,6090,6210,6270,
                 6510,6630,7350,7410,7590,7650,7770,8250,8610,8910,8970,9030,9690,
                 9750,9870,9990,10290,10890,11070,11250,11610,11730,12690,12750,13110,
                 13950,14250,14310,14790,15210,15810,15930,16470,16530,16650,17250,
                 17670,18090,18450,19170,19350,19470,19710,20010,20130,21150,21330,
                 21390,21750,21870,22110,22410,23250,23430,23670,24090,24210,24390,
                 24930,25290,25350,25470,25530,26070,26370,26970,27390,27630,27750,
                 27990,28170,28530,29370,29790,30330,30810,31230,31410,31770,32010,
                 32190,32310,32370,33030,33330,33570,33990,34110,34410,34470,34710,
                 35010,35310,35670,35730,35970,36090,36810,37290,37710,37830,37890,
                 38130,38790,38970,39390,39510,39870,39930,39990,40170,40410,41130,
                 41490,41670,41730,41910,42030,42510,43110,43350,43830,44070,44190,
                 44910,45270,45510,47730,49530,51090,52170,52890,53430,54150,54210,
                 57810,58110,58890,60630,61230,63570,63750,65130,65910,66810,67470,
                 69810,69870,70890,71250,74730,75990,77010,79350]

JELLIUM = [2,8,18,20,28,34,40,50,58,68,82,90,92,106,112,126,138]
GCD_IGV, GCD_SEG = 15, 30

def qn(x): return sum(int(d) for d in str(x))

# ============================================================
# 个人算法全集 (区间修正!)
# ============================================================
# IGV: start=2205 (末位=5, 自身满足) -> range(2205, MAXV+1, 10)
igv_all = {x for x in range(MINV, MAXV+1, 10) if qn(x) % 3 == 0}
# SEG: start 对齐到第一个 >=2205 且末位=0 且 qn%3==0
# 2210: qn=5 no. 2220: qn=6 yes. 2230: qn=7 no. 2240: qn=8 no. 2250: qn=9 yes.
seg_start = ((MINV // 10) + 1) * 10  # 2210
while qn(seg_start) % 3 != 0:
    seg_start += 10
seg_all = {x for x in range(seg_start, MAXV+1, 10) if qn(x) % 3 == 0}
print(f"SEG start={seg_start}, count={len(seg_all)}")

# 验证交集
igv_inter_all = igv_all & igv_searl
seg_inter_all = seg_all & {x for x in seg_searl_all if x >= MINV}
print(f"IGV L1+L2 交集: {len(igv_inter_all)}/309 = {len(igv_inter_all)/len(igv_searl)*100:.1f}%")
print(f"SEG L1+L2 交集: {len(seg_inter_all)}/167 = {len(seg_inter_all)/len({x for x in seg_searl_all if x>=MINV})*100:.1f}%")


# ============================================================
# 第三层: N/p 对 Jellium 对齐
# ============================================================
def jellium_align(N, p):
    """N/p 商与最近Jellium幻数的距离倒数 + Jellium间gcd偏好"""
    quotient = N // p
    g_pN = math.gcd(p, N)
    # 哪些Jellium q 和这个N/p的商最接近?
    nearest_j = min(JELLIUM, key=lambda j: abs(quotient - j))
    dist = abs(quotient - nearest_j)
    # 同时考虑: nearest_j与p的gcd (从Jellium表知道偏好)
    g_pj = math.gcd(p, nearest_j)
    # 商+Jellium的lcm
    lcm_val = math.lcm(p, nearest_j)
    # 综合评分
    dist_factor = 1.0 / (1.0 + dist)
    jellium_gcd_factor = 1.0 / g_pj
    return dist_factor * jellium_gcd_factor * math.log1p(lcm_val)


# 对每个集合打分
igv_scores_all = [(N, jellium_align(N, GCD_IGV)) for N in sorted(igv_all)]
seg_scores_all = [(N, jellium_align(N, GCD_SEG)) for N in sorted(seg_all)]

# 按评分排序，取前20% (与Searl的 ~11%过滤率可比较)
pct = 20
igv_enh = {N for N, _ in sorted(igv_scores_all, key=lambda x:-x[1])[:int(len(igv_scores_all)*pct/100)]}
seg_enh = {N for N, _ in sorted(seg_scores_all, key=lambda x:-x[1])[:int(len(seg_scores_all)*pct/100)]}

igv_inter = igv_enh & igv_searl
seg_inter = seg_enh & {x for x in seg_searl_all if x >= MINV}

igv_enh_only = igv_enh - igv_searl
seg_enh_only = seg_enh - {x for x in seg_searl_all if x >= MINV}

print(f"\n=== 交集结果 (前{pct}%) ===")
print(f"IGV: Searl={len(igv_searl)}, 增强={len(igv_enh)}, 交集={len(igv_inter)} ({len(igv_inter)/len(igv_searl)*100:.1f}%)")
print(f"SEG: Searl=167, 增强={len(seg_enh)}, 交集={len(seg_inter)} ({len(seg_inter)/167*100:.1f}%)")

# ============================================================
# 打印交集列表
# ============================================================
print(f"\n--- IGV 交集 ({len(igv_inter)}个) ---")
for N in sorted(igv_inter):
    q = N // GCD_IGV
    nj = min(JELLIUM, key=lambda j: abs(q - j))
    print(f"  {N}: N/15={q}, 最近Jellium={nj}, 距离={abs(q-nj)}")

print(f"\n--- SEG 交集 ({len(seg_inter)}个) ---")
for N in sorted(seg_inter):
    q = N // GCD_SEG
    nj = min(JELLIUM, key=lambda j: abs(q - j))
    print(f"  {N}: N/30={q}, 最近Jellium={nj}, 距离={abs(q-nj)}")

# ============================================================
# IGV 增强算法推荐 (不在Searl中, 取前20)
# ============================================================
print(f"\n--- IGV 增强推荐 (不在Searl中, 取前20) ---")
top_new = sorted(igv_enh_only, key=lambda N: -jellium_align(N, GCD_IGV))[:20]
for N in top_new:
    q = N // GCD_IGV
    nj = min(JELLIUM, key=lambda j: abs(q - j))
    print(f"  {N}: N/15={q}, 最近Jellium={nj}, 距离={abs(q-nj)}, 量子={qn(N)}")

print(f"\n--- SEG 增强推荐 (不在Searl中, 取前20) ---")
top_new_seg = sorted(seg_enh_only, key=lambda N: -jellium_align(N, GCD_SEG))[:20]
for N in top_new_seg:
    q = N // GCD_SEG
    nj = min(JELLIUM, key=lambda j: abs(q - j))
    print(f"  {N}: N/30={q}, 最近Jellium={nj}, 距离={abs(q-nj)}, 量子={qn(N)}")


# ============================================================
# 图: 交集柱状图 + 散点分布
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
colors_searl = {"IGV": "#DC2626", "SEG": "#2563EB"}
colors_enh  = {"IGV": "#FCA5A5", "SEG": "#93C5FD"}

x = np.arange(2)
width = 0.3

for ax, (name, searl, enh, inter) in [
    (axes[0], ("IGV", igv_searl, igv_enh, igv_inter)),
    (axes[1], ("SEG", {x for x in seg_searl_all if x>=MINV}, seg_enh, seg_inter)),
]:
    n_searl = len(searl)
    n_enh = len(enh)
    n_inter = len(inter)

    ax.bar(0, n_searl, width, color=colors_searl[name], label="Searl原版")
    ax.bar(1, n_enh, width, color=colors_enh[name], label="增强个人(3层)")
    # 交集标记
    ax.text(0.5, max(n_searl, n_enh)*0.5,
            f"交集={n_inter}\n覆盖率={n_inter/n_searl*100:.1f}%",
            ha="center", fontsize=12, fontweight="bold", color="#059669",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#ECFDF5", edgecolor="#059669", alpha=0.9))

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Searl", "增强3层"])
    ax.set_ylabel("候选数量")
    ax.set_title(f"{name} (Searl={n_searl}, 增强={n_enh})", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)

fig.suptitle("增强个人算法(三层Jellium) vs Searl真值表 — 交集对比 [2205~80000]",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
p1 = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig7_enhanced_vs_searl.png"
fig.savefig(p1); plt.close(fig); print(f"\n[OK] {p1}")


# ============================================================
# 图: N/15(N/30) vs Jellium 对齐散点
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

for ax, name, searl_set, enh_set, p_gcd, col_s, col_e in [
    (ax1, "IGV", igv_searl, igv_enh_only, GCD_IGV, "#DC2626", "#10B981"),
    (ax2, "SEG", {x for x in seg_searl_all if x>=MINV}, seg_enh_only, GCD_SEG, "#2563EB", "#10B981"),
]:
    s_q = [N//p_gcd for N in sorted(searl_set)]
    s_y = [jellium_align(N, p_gcd) for N in sorted(searl_set)]
    e_q = [N//p_gcd for N in sorted(enh_set)][:200]
    e_y = [jellium_align(N, p_gcd) for N in sorted(enh_set)][:200]

    ax.scatter(s_q, s_y, c=col_s, alpha=0.4, s=15, label=f"Searl({len(s_q)})", edgecolors="none")
    ax.scatter(e_q, e_y, c=col_e, alpha=0.5, s=12, marker="^",
               label=f"增强新增({len(enh_set)})", edgecolors="none")

    # 标注 Jellium 幻数线
    for j in JELLIUM:
        if min(s_q + e_q[:50], default=0) * 0.8 <= j <= max(s_q + e_q[:50], default=0) * 1.2:
            ax.axvline(x=j, color="gray", linestyle=":", alpha=0.3, linewidth=0.5)

    ax.set_xlabel(f"N / {p_gcd} 商")
    ax.set_ylabel("Jellium对齐评分")
    ax.set_title(f"{name}: N/{p_gcd} vs Jellium幻数", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)

fig.suptitle("增强算法 vs Searl — N/p 商的 Jellium幻数对齐分布",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
p2 = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig8_enhanced_scatter.png"
fig.savefig(p2); plt.close(fig); print(f"[OK] {p2}")

print("\nDone.")
