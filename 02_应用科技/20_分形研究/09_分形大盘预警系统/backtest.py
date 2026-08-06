# -*- coding: utf-8 -*-
"""
backtest.py — 簇跳率崩盘预警回测（验证准确率与提前量）
=========================================================
双重验证:
  1. 合成数据: 已知崩盘日(植入), 检验簇跳率能否提前预警
  2. 真实数据: 上证指数大跌日(腾讯行情), 检验簇跳率预警表现

评估指标:
  - 检出率: 崩盘事件中被预警覆盖的比例
  - 提前天数: 预警触发日到崩盘日的间隔(正=提前)
  - 漏报率: 崩盘前无预警的比例
  - 误报率: 非崩盘窗口触发预警的比例

用法: python backtest.py
作者: AI · v1.0 2026-08-03
"""

import numpy as np
from fractal_analysis import (
    build_cjr_timeline, alert_engine, gen_synthetic_panel,
)


# ------------------------------------------------------------
# 合成数据回测 (已知崩盘日)
# ------------------------------------------------------------
# ------------------------------------------------------------
# 改进版预警触发: z-score 相对异常 (滚动扩张窗口, 不用未来数据)
# 触发条件: z > 1.5 且 cjr > 0.30 (绝对下限防小波动)
# ------------------------------------------------------------
def zscore_trigger(series, z_thresh=1.5, abs_floor=0.30):
    """扩张窗口 z-score: 当前值相对历史均值的异常程度"""
    n = len(series)
    trig = np.zeros(n, dtype=bool)
    for i in range(n):
        if i < 5:  # 冷启动窗口
            continue
        hist = series[:i]
        mu = np.mean(hist)
        sd = np.std(hist)
        if sd < 1e-9:
            continue
        z = (series[i] - mu) / sd
        if z > z_thresh and series[i] > abs_floor:
            trig[i] = True
    return trig


def backtest_synthetic(seed=42, n_stocks=40, T=800, n_crash=3):
    print("=" * 62)
    print("① 合成数据回测 (40只 x 800日, 植入崩盘日)")
    print("=" * 62)

    panel, codes, crash_days, industries = gen_synthetic_panel(
        n_stocks=n_stocks, T=T, n_crash=n_crash, seed=seed)
    tl = build_cjr_timeline(panel, window=120, step=20, cuts=(3, 5, 8))

    # 窗口时间轴: 每个窗口的结束日(绝对日期索引)
    win_end = tl["window_end"]
    n_win = len(win_end)
    cjr_mid = np.array(tl["cjr"][5])
    cjr_fine = np.array(tl["cjr"][8])

    # 改进: z-score 相对异常触发 (mid 或 fine 任一触发)
    trig_mid = zscore_trigger(cjr_mid)
    trig_fine = zscore_trigger(cjr_fine, z_thresh=1.5, abs_floor=0.35)
    trigger = trig_mid | trig_fine

    print(f"崩盘日: {crash_days}")
    print(f"窗口数: {n_win}, 窗宽120日/步长20日")
    print(f"预警触发窗口: {np.where(trigger)[0].tolist()}")
    print(f"mid簇跳率: min={cjr_mid.min():.1%} max={cjr_mid.max():.1%} mean={cjr_mid.mean():.1%}")
    print(f"fine簇跳率: min={cjr_fine.min():.1%} max={cjr_fine.max():.1%} mean={cjr_fine.mean():.1%}")

    # 对每个崩盘日评估: 崩盘前 40 日内是否有预警
    print("\n[逐崩盘事件评估]")
    results = []
    for tc in crash_days:
        # 找崩盘日所在窗口
        win_idx = next((i for i, e in enumerate(win_end) if e >= tc), None)
        # 检查崩盘前窗口(向前找 3 个窗口 ≈ 60 日)是否有预警
        window_lead = 3
        covered = False
        lead_days = None
        for back in range(1, window_lead + 1):
            idx = win_idx - back
            if idx >= 0 and trigger[idx]:
                covered = True
                lead_days = win_end[win_idx] - win_end[idx] if win_idx else 0
                break
        results.append((tc, covered, lead_days))
        status = f"✅ 提前 {lead_days} 天预警" if covered else "❌ 漏报"
        print(f"  崩盘日 t={tc}: {status}")

    # 整体统计
    covered_n = sum(1 for _, c, _ in results if c)
    detection = covered_n / len(crash_days)
    leads = [l for _, c, l in results if c and l is not None]
    avg_lead = np.mean(leads) if leads else 0
    # 误报率: 非崩盘窗口的触发比例
    crash_windows = set()
    for tc in crash_days:
        wi = next((i for i, e in enumerate(win_end) if e >= tc), None)
        if wi is not None:
            for back in range(0, 4):
                crash_windows.add(wi - back)
    non_crash = [i for i in range(n_win) if i not in crash_windows]
    false_alarm = np.mean(trigger[non_crash]) if non_crash else 0

    print("\n[合成回测汇总]")
    print(f"  检出率:  {detection:.0%} ({covered_n}/{len(crash_days)})")
    print(f"  平均提前: {avg_lead:.0f} 天")
    print(f"  漏报率:  {1-detection:.0%}")
    print(f"  误报率:  {false_alarm:.0%} (非崩盘窗口触发比例)")

    return {"detection": detection, "avg_lead": avg_lead,
            "false_alarm": false_alarm, "details": results}


# ------------------------------------------------------------
# 真实数据回测 (上证指数大跌日)
# ------------------------------------------------------------
def backtest_real():
    print("\n" + "=" * 62)
    print("② 真实数据回测 (上证指数大跌日 2025-2026)")
    print("=" * 62)
    try:
        from traditional_indicators import fetch_index_kline
    except ImportError:
        print("❌ 无法导入数据模块")
        return None

    kline = fetch_index_kline("sh000001", count=500)
    close = kline["close"]
    dates = kline["date"]

    # 定义"大跌事件": 单日跌幅 < -1.8% (大盘级别)
    ret = np.diff(close) / close[:-1]
    crash_idx = np.where(ret < -0.018)[0] + 1  # 转换回 close 索引
    if len(crash_idx) == 0:
        print("❌ 回测窗口内无大跌日 (2025-2026 相对平稳)")
        # 放宽阈值
        crash_idx = np.where(ret < -0.012)[0] + 1
        print(f"   放宽阈值 -1.2% 后: {len(crash_idx)} 个下跌日")

    crash_dates = [dates[i] for i in crash_idx]
    print(f"大跌日 ({len(crash_dates)} 个): {crash_dates[-8:]}")

    # 用 20 只代表股票做面板 (从常见权重股中抽样, 简化用随机)
    # 注意: 真实场景应拉全成分股; 这里演示面板构建
    sample_codes = [
        "sh600519", "sh601318", "sh600036", "sz000858", "sz300750",
        "sh601899", "sh600900", "sz002594", "sh601166", "sh600030",
        "sh600887", "sz000333", "sh601012", "sz300059", "sh600276",
        "sz002415", "sh601888", "sh600028", "sz000001", "sh601398",
    ]
    panel = {}
    from traditional_indicators import fetch_index_kline as fetch_k
    for code in sample_codes:
        try:
            k = fetch_k(code, count=500)
            c = k["close"]
            if len(c) > 200:
                panel[code] = np.diff(np.log(c))
        except Exception:
            continue
    print(f"面板: {len(panel)} 只股票 × {min(len(v) for v in panel.values())} 日")

    if len(panel) < 10:
        print("⚠️ 面板过小, 结果仅供参考")
        return None

    # 统一长度
    T = min(len(v) for v in panel.values())
    panel = {c: v[-T:] for c, v in panel.items()}

    tl = build_cjr_timeline(panel, window=120, step=20, cuts=(3, 5, 8))
    win_end = tl["window_end"]
    cjr_mid = np.array(tl["cjr"][5])
    cjr_fine = np.array(tl["cjr"][8])
    trig_mid = zscore_trigger(cjr_mid)
    trig_fine = zscore_trigger(cjr_fine, z_thresh=1.5, abs_floor=0.35)
    trigger = trig_mid | trig_fine
    print(f"mid簇跳率: min={cjr_mid.min():.1%} max={cjr_mid.max():.1%} mean={cjr_mid.mean():.1%}")
    print(f"fine簇跳率: min={cjr_fine.min():.1%} max={cjr_fine.max():.1%} mean={cjr_fine.mean():.1%}")

    # 大跌日映射到窗口
    print("\n[逐大跌事件评估] (近 3 窗口内预警=有效)")
    results = []
    for tc in crash_idx:
        wi = next((i for i, e in enumerate(win_end) if e >= tc), None)
        if wi is None:
            continue
        covered = False
        lead_days = None
        for back in range(1, 4):
            idx = wi - back
            if idx >= 0 and trigger[idx]:
                covered = True
                lead_days = win_end[wi] - win_end[idx]
                break
        results.append((dates[tc], covered, lead_days))

    covered_n = sum(1 for _, c, _ in results if c)
    detection = covered_n / len(results) if results else 0
    leads = [l for _, c, l in results if c and l is not None]
    avg_lead = np.mean(leads) if leads else 0

    # 误报率
    crash_windows = set()
    for tc in crash_idx:
        wi = next((i for i, e in enumerate(win_end) if e >= tc), None)
        if wi is not None:
            for back in range(0, 4):
                crash_windows.add(wi - back)
    non_crash = [i for i in range(len(win_end)) if i not in crash_windows]
    false_alarm = np.mean(trigger[non_crash]) if non_crash else 0

    print("\n[真实回测汇总]")
    print(f"  大跌事件: {len(results)} 个")
    print(f"  检出率:  {detection:.0%} ({covered_n}/{len(results)})")
    print(f"  平均提前: {avg_lead:.0f} 天")
    print(f"  误报率:  {false_alarm:.0%}")

    return {"detection": detection, "avg_lead": avg_lead,
            "false_alarm": false_alarm, "details": results}


# ------------------------------------------------------------
# 与纯 Hurst 基线对比
# ------------------------------------------------------------
def hurst_baseline(panel, crash_days):
    """纯 Hurst 预警基线: Hurst 跌破 0.4 视为预警"""
    from fractal_analysis import hurst_rs
    T = min(len(v) for v in panel.values())
    window = 120
    win_ends = list(range(window, T, 20))
    h_series = []
    for end in win_ends:
        hs = [hurst_rs(v[end-window:end]) for v in panel.values()]
        h_series.append(np.nanmean(hs))
    h_series = np.array(h_series)
    trigger = h_series < 0.40

    print("\n[纯 Hurst 基线对比] (H<0.4 视为预警)")
    covered_n = 0
    leads = []
    for tc in crash_days:
        wi = next((i for i, e in enumerate(win_ends) if e >= tc), None)
        if wi is None:
            continue
        covered = False
        for back in range(1, 4):
            idx = wi - back
            if idx >= 0 and trigger[idx]:
                covered = True
                leads.append(win_ends[wi] - win_ends[idx])
                break
        if covered:
            covered_n += 1
    n_events = len(crash_days)
    print(f"  检出率: {covered_n/n_events:.0%} ({covered_n}/{n_events})")
    print(f"  平均提前: {np.mean(leads):.0f} 天" if leads else "  平均提前: N/A")
    return covered_n / n_events if n_events else 0


if __name__ == "__main__":
    print("分形大盘预警 · 回测实证报告")
    print("算法: 簇跳率(Cluster Jump Rate) vs 纯 Hurst 基线\n")

    syn = backtest_synthetic()

    # Hurst 基线 (合成数据)
    panel, codes, crash_days, industries = gen_synthetic_panel(
        n_stocks=40, T=800, n_crash=3, seed=42)
    hurst_det = hurst_baseline(panel, crash_days)

    real = backtest_real()

    print("\n" + "=" * 62)
    print("总结: 簇跳率 vs 纯 Hurst 对比")
    print("=" * 62)
    print(f"  合成数据簇跳率检出率: {syn['detection']:.0%}, 提前 {syn['avg_lead']:.0f} 天")
    print(f"  合成数据纯Hurst检出率: {hurst_det:.0%}")
    if real:
        print(f"  真实数据簇跳率检出率: {real['detection']:.0%}, 提前 {real['avg_lead']:.0f} 天")
