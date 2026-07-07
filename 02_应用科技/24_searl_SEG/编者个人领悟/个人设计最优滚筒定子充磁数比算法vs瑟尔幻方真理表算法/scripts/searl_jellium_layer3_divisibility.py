#!/usr/bin/env python3
"""
增强个人算法(三层) vs Searl 原版 — 精确交集对比 (Jellium整除修正版)
=================================================================
三层过滤 (修正):
  L1: 末位 = 0(SEG)/5(IGV)
  L2: 量子数 % 3 == 0
  L3: N % q == 0, q in Jellium幻数 (N/q为正整数, q是Jellium之一)
      评分为能整除N的Jellium幻数个数

范围: 2205 ≤ N < 80000

🔴 关键发现: 所有Jellium幻数(2,8,18,20,28,34,40,50,58,68,82,90,92,106,112,126,138)都是偶数!
            → IGV(末位5=奇数)永远无法被任何Jellium整除
            → IGV的L3恒为0, 只能靠幻方共享线条件
            → SEG(末位0=偶数)可以用Jellium整除个数评分

作者: AI辅助蓝馨 | 日期: 2026-06-07
"""

import math, os
from collections import defaultdict
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
plt.rcParams.update({"font.size":10,"axes.titlesize":13,"axes.labelsize":11,
                      "figure.dpi":150,"savefig.dpi":200,"savefig.bbox":"tight"})

SCRIPT = os.path.dirname(os.path.abspath(__file__))
MINV, MAXV = 2205, 80000
JELLIUM = [2,8,18,20,28,34,40,50,58,68,82,90,92,106,112,126,138]
GCD_IGV, GCD_SEG = 15, 30
def qn(x): return sum(int(d) for d in str(x))
def jellium_div_count(N): return sum(1 for q in JELLIUM if N % q == 0)
def jellium_divisors(N): return [q for q in JELLIUM if N % q == 0]

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

# ============================================================
# L1+L2: 个人算法全集
# ============================================================
igv_all = {x for x in range(MINV, MAXV+1, 10) if qn(x) % 3 == 0}
seg_start = ((MINV // 10) + 1) * 10
while qn(seg_start) % 3 != 0: seg_start += 10
seg_all = {x for x in range(seg_start, MAXV+1, 10) if qn(x) % 3 == 0}

# ============================================================
# L3: Jellium整除个数评分
# ============================================================

# IGV: 所有Jellium都是偶数, IGV全奇数 → jellium_div_count恒=0
# SEG: 可以计算
igv_scores = [(N, jellium_div_count(N)) for N in sorted(igv_all)]
seg_scores = [(N, jellium_div_count(N)) for N in sorted(seg_all)]

# 取有Jellium整除的前N个
# SEG: 按jellium_div_count降序, 取与Searl同数量级(167)的候选
seg_with_div = [(N,c) for N,c in seg_scores if c >= 1]
seg_enh = {N for N,c in sorted(seg_with_div, key=lambda x:-x[1])[:len(seg_searl_all)]}

igv_inter = set()  # IGV: Jellium整除恒=0, 对IGV无交集
seg_inter = seg_enh & {x for x in seg_searl_all if x >= MINV}

print("=" * 70)
print("修正版: L3 = N被Jellium幻数整除的个数")
print("=" * 70)
print(f"\nIGV (末位5=奇数): 所有Jellium幻数均为偶数 → 无IGV能被任何Jellium整除")
print(f"  IGV L3永远=0, 对IGV无过滤效果. IGV的约束完全来自幻方共享线.")

print(f"\nSEG: 个人算法{len(seg_all)}个, 其中Jellium整除>=1的共{len(seg_with_div)}个")
print(f"  Searl={len(seg_searl_all)}, SEG增强={len(seg_enh)}, 交集={len(seg_inter)}")

# SEG交集详情
print(f"\n--- SEG 交集 ({len(seg_inter)}个, Jellium整除个数降序) ---")
seg_inter_sorted = sorted(seg_inter, key=lambda N: -jellium_div_count(N))
for N in seg_inter_sorted:
    divs = jellium_divisors(N)
    print(f"  {N:6d}: {len(divs)}个Jellium整除={divs}  N/30={N//30}")

# SEG Searl不在此增强集中的
seg_missed = {x for x in seg_searl_all if x >= MINV} - seg_enh
print(f"\n--- SEG Searl有但增强无 ({len(seg_missed)}个) ---")
for N in sorted(seg_missed)[:15]:
    print(f"  {N}: Jellium整除={jellium_div_count(N)}")

# SEG增强推荐
seg_enh_only = seg_enh - {x for x in seg_searl_all if x >= MINV}
print(f"\n--- SEG 增强推荐 (不在Searl中, 取前20, Jellium整除最多) ---")
top = sorted(seg_enh_only, key=lambda N: -jellium_div_count(N))[:20]
for N in top:
    divs = jellium_divisors(N)
    print(f"  {N:6d}: {len(divs)}个={divs}  N/30={N//30}  量子={qn(N)}")


# ============================================================
# 图: SEG Jellium整除分布
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Fig A: SEG Searl的Jellium整除数分布
ax = axes[0]
searl_divs = [jellium_div_count(N) for N in seg_searl_all if N >= MINV]
enh_divs  = [jellium_div_count(N) for N in seg_enh]
bins = np.arange(-0.5, 7.5, 1)
ax.hist(searl_divs, bins=bins, alpha=0.7, color="#2563EB",
        label=f"Searl(n={len(searl_divs)})", edgecolor="#1D4ED8", linewidth=0.5)
ax.hist(enh_divs, bins=bins, alpha=0.5, color="#10B981",
        label=f"增强(n={len(enh_divs)})", edgecolor="#047857", linewidth=0.5)
ax.set_xlabel("Jellium幻数整除个数")
ax.set_ylabel("候选数量")
ax.set_title("SEG: Jellium整除个数分布 (L3评分)", fontweight="bold")
ax.legend(fontsize=9)
ax.set_xticks(range(7))
ax.grid(axis="y", alpha=0.3)

# Fig B: N/30商 vs Jellium整除数 散点
ax = axes[1]
s_x = [N//GCD_SEG for N in sorted(seg_searl_all) if N >= MINV]
s_y = [jellium_div_count(N) for N in sorted(seg_searl_all) if N >= MINV]
e_x = [N//GCD_SEG for N in sorted(seg_enh_only)[:100]]
e_y = [jellium_div_count(N) for N in sorted(seg_enh_only)[:100]]

ax.scatter(s_x, s_y, c="#2563EB", alpha=0.4, s=20,
           label=f"Searl({len(s_x)})", edgecolors="none")
ax.scatter(e_x, e_y, c="#10B981", alpha=0.6, s=18, marker="^",
           label=f"增强新增({len(seg_enh_only)})", edgecolors="#047857", linewidth=0.3)

# 标注Jellium幻数在N/30轴上的位置
for j in JELLIUM:
    if j >= min(s_x)*0.5:
        ax.axvline(x=j, color="gray", linestyle=":", alpha=0.25, linewidth=0.5)

ax.set_xlabel("N/30 商")
ax.set_ylabel("Jellium整除个数")
ax.set_title("SEG: N/30 vs Jellium整除数", fontweight="bold")
ax.legend(fontsize=8)
ax.grid(alpha=0.2)

fig.suptitle("SEG增强个人算法(L3=Jellium整除) vs Searl真值表 [2205~80000]",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
p = r"D:\AAA我的文件\PKS_千禧难题_统一解\02_应用科技\24_searl_SEG\编者个人领悟\个人设计最优滚筒定子充磁数比算法vs瑟尔幻方真理表算法\chartsig9_jellium_divisibility.png"
fig.savefig(p); plt.close(fig)
print(f"\n[OK] {p}")
print("Done.")
