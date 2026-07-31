# -*- coding: utf-8 -*-
"""
素数算法基准测试 — 快速版
生成对比图: benchmark_results.png
"""
import sys, os, time, gc

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'dejavusans'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from all_sieves import SIEVE_REGISTRY

BENCH_RANGES = [1000, 5000, 10000, 50000, 100000]
TIMEOUT = 30.0


def run():
    print("=" * 60)
    print("素数算法基准测试")
    print("=" * 60)
    results = {}

    for name, (fn, comp, space) in SIEVE_REGISTRY.items():
        print(f"\n{name} ({comp})")
        results[name] = []
        
        max_r = 100_000 if "试除" in name else 100_000
        for limit in [r for r in BENCH_RANGES if r <= max_r]:
            gc.collect()
            t0 = time.perf_counter()
            try:
                primes = fn(limit)
                t1 = time.perf_counter()
                count = len(primes)
                results[name].append((limit, t1 - t0, count))
                rate = count / (t1 - t0) if (t1 - t0) > 0 else 0
                print(f"  pi({limit:>7,})={count:>5}  {t1-t0:.4f}s  {rate:>8,.0f}/s")
                if t1 - t0 > TIMEOUT:
                    print("  (timeout)")
                    break
            except Exception as e:
                print(f"  ERROR: {e}")
                break

    # 验证
    print("\n" + "=" * 60)
    print("正确性验证")
    print("=" * 60)
    ref_count = len([n for n in range(2, 100001) if all(n%d!=0 for d in range(2,int(n**0.5)+1))])
    for name in results:
        data = results[name]
        for d in data:
            if d[0] == 100000:
                ok = "OK" if d[2] == ref_count else f"FAIL ({d[2]} vs {ref_count})"
                print(f"  {ok}  {name}")
                break

    # 画图
    plot(results)
    print("\n完成! benchmark_results.png")


def plot(results):
    colors = {
        "Croft 螺旋筛": "#d4a853", "埃拉托色尼筛": "#5090c0",
        "Sundaram 筛": "#9060c0", "Atkin 筛": "#50a060",
        "试除法": "#c05050", "6k±1 试除法": "#c08050",
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), facecolor='#0a0a0f')
    fig.suptitle("素数生成算法对比基准 — Croft 螺旋筛 vs 经典算法",
                 fontsize=15, color='#d4a853', fontweight='bold', y=0.98)

    # [0,0] 运行时间
    ax = axes[0, 0]
    ax.set_title("运行时间 (对数坐标)", fontsize=13, color='#d0d0d8')
    ax.set_xlabel("上限 n", color='#9090a0')
    ax.set_ylabel("耗时 (秒)", color='#9090a0')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.set_facecolor('#0d0d15')
    for name, color in colors.items():
        if name in results:
            d = results[name]
            if d:
                xs = [p[0] for p in d]; ys = [p[1] for p in d]
                ax.plot(xs, ys, 'o-', color=color, lw=2, ms=6, label=name, alpha=0.85)
    ax.legend(fontsize=8, loc='upper left')

    # [0,1] 速度比率
    ax = axes[0, 1]
    ax.set_title("相对 Croft 的速度比率 (倍数)", fontsize=13, color='#d0d0d8')
    ax.set_xlabel("上限 n", color='#9090a0')
    ax.set_ylabel("倍数 (算法耗时 / Croft耗时)", color='#9090a0')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.axhline(y=1.0, color='#d4a853', ls='--', lw=1, alpha=0.4)
    ax.set_facecolor('#0d0d15')
    ct = {d[0]: d[1] for d in results.get("Croft 螺旋筛", [])}
    for name, color in colors.items():
        if name == "Croft 螺旋筛" or name not in results: continue
        xs, rs = [], []
        for d in results[name]:
            if d[0] in ct and ct[d[0]] > 0:
                xs.append(d[0]); rs.append(d[1] / ct[d[0]])
        if xs:
            ax.plot(xs, rs, 's-', color=color, lw=2, ms=6, label=name, alpha=0.85)
    ax.legend(fontsize=8, loc='upper left')

    # [1,0] 每素数耗时
    ax = axes[1, 0]
    ax.set_title("每个素数的平均耗时 (us/prime)", fontsize=13, color='#d0d0d8')
    ax.set_xlabel("上限 n", color='#9090a0')
    ax.set_ylabel("us / 素数", color='#9090a0')
    ax.set_xscale('log')
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.set_facecolor('#0d0d15')
    for name, color in colors.items():
        if name in results:
            d = results[name]
            if d:
                xs = [p[0] for p in d]
                ys = [p[1]*1e6/p[2] if p[2]>0 else 0 for p in d]
                ax.plot(xs, ys, 'D-', color=color, lw=1.5, ms=5, label=name, alpha=0.8)
    ax.legend(fontsize=8, loc='upper left')

    # [1,1] 复杂度表
    ax = axes[1, 1]
    ax.axis('off')
    ax.set_title("复杂度与实测性能", fontsize=13, color='#d0d0d8', y=1.02)
    headers = ["算法", "时间复杂度", "空间", "10万耗时", "vs Croft"]
    rows = [headers]
    ct100k = None
    for d in results.get("Croft 螺旋筛", []):
        if d[0] == 100000: ct100k = d[1]; break
    for name, (fn, comp, space) in SIEVE_REGISTRY.items():
        if name not in results: continue
        t100k = None
        for d in results[name]:
            if d[0] == 100000: t100k = d[1]; break
        ts = f"{t100k:.4f}s" if t100k else "N/A"
        ratio = ""
        if ct100k and t100k and ct100k > 0:
            r = t100k / ct100k
            ratio = f"{r:.1f}x"
        rows.append([name, comp, space, ts, ratio])
    
    tb = ax.table(cellText=rows, cellLoc='center', loc='center',
                  colWidths=[0.22, 0.28, 0.17, 0.18, 0.15])
    tb.auto_set_font_size(False); tb.set_fontsize(9); tb.scale(1.0, 1.6)
    for j in range(5):
        tb[0, j].set_facecolor('#1a1a2e')
        tb[0, j].set_text_props(color='#d4a853', fontweight='bold')
    for r in range(1, len(rows)):
        is_croft = rows[r][0] == "Croft 螺旋筛"
        for j in range(5):
            tb[r, j].set_facecolor('#2a2a15' if is_croft else '#111118')
            tb[r, j].set_text_props(color='#d4a853' if is_croft else '#d0d0d8')

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_results.png")
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#0a0a0f')
    plt.close()
    print(f"图表: {out}")


if __name__ == "__main__":
    run()
