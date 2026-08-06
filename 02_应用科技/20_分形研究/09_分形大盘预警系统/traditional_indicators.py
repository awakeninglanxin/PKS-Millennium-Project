# -*- coding: utf-8 -*-
"""
traditional_indicators.py — 传统大盘预警系统对照模块
=====================================================
计算上证指数传统技术指标 + 传统预警信号:
  MA(5/10/20/60) 均线系统, MACD(12,26,9), RSI(14),
  BOLL(20,2) 布林带, KDJ(9,3,3), 成交量
输出传统信号灯 (与分形簇跳率预警并排对照)

作者: AI · v1.0 2026-08-03
"""

import numpy as np
import urllib.request
import json


# ------------------------------------------------------------
# 数据获取: 腾讯K线API (免注册, 前复权)
# ------------------------------------------------------------
def fetch_index_kline(code="sh000001", count=500):
    """
    拉取指数日K (腾讯API)
    返回 dict(date=[], close=[], high=[], low=[], open=[], volume=[])
    """
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
           f"?param={code},day,,,{count},qfq")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    node = raw["data"][code]
    days = node.get("day") or node.get("qfqday") or []
    dates, closes, highs, lows, opens, vols = [], [], [], [], [], []
    for row in days:
        dates.append(row[0])
        closes.append(float(row[2]))
        highs.append(float(row[3]))
        lows.append(float(row[4]))
        opens.append(float(row[1]))
        vols.append(float(row[5]) if len(row) > 5 else 0.0)
    return {"date": dates, "close": np.array(closes), "high": np.array(highs),
            "low": np.array(lows), "open": np.array(opens),
            "volume": np.array(vols)}


# ------------------------------------------------------------
# 传统指标
# ------------------------------------------------------------
def sma(x, n):
    """简单移动平均"""
    x = np.asarray(x, dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        for i in range(n - 1, len(x)):
            out[i] = np.mean(x[i - n + 1:i + 1])
    return out


def ema(x, n):
    """指数移动平均"""
    x = np.asarray(x, dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) == 0:
        return out
    k = 2.0 / (n + 1)
    prev = x[0]
    out[0] = prev
    for i in range(1, len(x)):
        prev = k * x[i] + (1 - k) * prev
        out[i] = prev
    return out


def macd(close, fast=12, slow=26, signal=9):
    """MACD: DIF, DEA, HIST"""
    ema_f = ema(close, fast)
    ema_s = ema(close, slow)
    dif = ema_f - ema_s
    dea = ema(dif, signal)
    hist = (dif - dea) * 2
    return dif, dea, hist


def rsi(close, n=14):
    """RSI: 相对强弱指数"""
    c = np.asarray(close, dtype=float)
    out = np.full(len(c), np.nan)
    if len(c) <= n:
        return out
    delta = np.diff(c)
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_g = np.mean(gain[:n])
    avg_l = np.mean(loss[:n])
    for i in range(n, len(c)):
        if i > n:
            avg_g = (avg_g * (n - 1) + gain[i - 1]) / n
            avg_l = (avg_l * (n - 1) + loss[i - 1]) / n
        if avg_l == 0:
            out[i] = 100.0
        else:
            rs = avg_g / avg_l
            out[i] = 100 - 100 / (1 + rs)
    return out


def boll(close, n=20, k=2.0):
    """BOLL: 中轨MA, 上轨, 下轨, %B"""
    mid = sma(close, n)
    up = np.full(len(close), np.nan)
    low = np.full(len(close), np.nan)
    pctb = np.full(len(close), np.nan)
    for i in range(n - 1, len(close)):
        sd = np.std(close[i - n + 1:i + 1], ddof=1)
        up[i] = mid[i] + k * sd
        low[i] = mid[i] - k * sd
        if up[i] > low[i]:
            pctb[i] = (close[i] - low[i]) / (up[i] - low[i])
    return mid, up, low, pctb


def kdj(high, low, close, n=9, m1=3, m2=3):
    """KDJ: K, D, J"""
    h = np.asarray(high, dtype=float)
    l = np.asarray(low, dtype=float)
    c = np.asarray(close, dtype=float)
    N = len(c)
    K = np.full(N, 50.0)
    D = np.full(N, 50.0)
    J = np.full(N, 0.0)
    for i in range(N):
        lo = max(0, i - n + 1)
        hh = np.max(h[lo:i + 1])
        ll = np.min(l[lo:i + 1])
        rsv = 50.0 if hh == ll else (c[i] - ll) / (hh - ll) * 100
        K[i] = (2 / 3) * (K[i - 1] if i > 0 else 50.0) + (1 / 3) * rsv
        D[i] = (2 / 3) * (D[i - 1] if i > 0 else 50.0) + (1 / 3) * K[i]
        J[i] = 3 * K[i] - 2 * D[i]
    return K, D, J


# ------------------------------------------------------------
# 传统预警信号引擎 (与分形预警引擎对照)
# ------------------------------------------------------------
def traditional_alert(close, ma5, ma10, ma20, ma60, dif, dea, hist,
                      rsi14, pctb, k, d, j):
    """
    基于经典技术分析的预警:
      - 均线系统: 收盘 < MA60 → 中期空头; 5日下穿20日 → 死叉
      - MACD: DIF 下穿 DEA → 死叉
      - RSI: <30 超卖(底部信号) / >70 超买
      - BOLL %B: >1 突破上轨(强势/超买), <0 跌破下轨(弱势)
      - KDJ: J >100 超买 / J <0 超卖
    返回: (level, color, msg, 信号列表, 仓位建议, 依据明细)
    """
    signals = []
    rationale = []  # 分析依据 (带具体数值)
    c = close[-1]
    # 均线
    if np.isfinite(ma60[-1]):
        if c < ma60[-1]:
            signals.append("收盘跌破MA60 (中期空头)")
            rationale.append(f"收盘价 {c:.0f} < MA60 {ma60[-1]:.0f} (偏离 {(c/ma60[-1]-1)*100:+.1f}%) → 中期趋势转空")
        if np.isfinite(ma5[-1]) and np.isfinite(ma20[-1]) and ma5[-1] < ma20[-1]:
            signals.append("MA5 < MA20 (短期空头排列)")
            rationale.append(f"MA5 {ma5[-1]:.0f} < MA20 {ma20[-1]:.0f} → 短期均线空头排列")
        elif np.isfinite(ma5[-1]) and np.isfinite(ma20[-1]) and ma5[-1] > ma20[-1]:
            signals.append("MA5 > MA20 (短期多头排列)")
            rationale.append(f"MA5 {ma5[-1]:.0f} > MA20 {ma20[-1]:.0f} → 短期均线多头排列")
    # MACD
    if np.isfinite(dif[-1]) and np.isfinite(dea[-1]) and np.isfinite(dif[-2]) and np.isfinite(dea[-2]):
        if dif[-2] >= dea[-2] and dif[-1] < dea[-1]:
            signals.append("MACD 死叉")
            rationale.append(f"MACD死叉: DIF {dif[-1]:.1f} 下穿 DEA {dea[-1]:.1f} (柱 {hist[-1]:.1f}) → 动能转负")
        elif dif[-2] <= dea[-2] and dif[-1] > dea[-1]:
            signals.append("MACD 金叉")
            rationale.append(f"MACD金叉: DIF {dif[-1]:.1f} 上穿 DEA {dea[-1]:.1f} → 动能转正")
    # RSI
    if np.isfinite(rsi14[-1]):
        if rsi14[-1] > 70:
            signals.append(f"RSI {rsi14[-1]:.0f} 超买")
            rationale.append(f"RSI(14)={rsi14[-1]:.0f} > 70 → 短线超买, 回调风险上升")
        elif rsi14[-1] < 30:
            signals.append(f"RSI {rsi14[-1]:.0f} 超卖")
            rationale.append(f"RSI(14)={rsi14[-1]:.0f} < 30 → 短线超卖, 或有超跌反弹")
        else:
            rationale.append(f"RSI(14)={rsi14[-1]:.0f} 中性区间")
    # BOLL
    if np.isfinite(pctb[-1]):
        if pctb[-1] > 1:
            signals.append("突破布林上轨 (强势)")
            rationale.append(f"%B={pctb[-1]:.2f} > 1 → 突破布林上轨, 强势但超买")
        elif pctb[-1] < 0:
            signals.append("跌破布林下轨 (弱势)")
            rationale.append(f"%B={pctb[-1]:.2f} < 0 → 跌破布林下轨, 弱势超卖")
        else:
            rationale.append(f"%B={pctb[-1]:.2f} 处于布林带内")
    # KDJ
    if np.isfinite(j[-1]):
        if j[-1] > 100:
            signals.append(f"KDJ J={j[-1]:.0f} 超买")
            rationale.append(f"KDJ J={j[-1]:.0f} > 100 → 超买区")
        elif j[-1] < 0:
            signals.append(f"KDJ J={j[-1]:.0f} 超卖")
            rationale.append(f"KDJ J={j[-1]:.0f} < 0 → 超卖区")
        else:
            rationale.append(f"KDJ J={j[-1]:.0f} 中性")

    # 综合判定 → 仓位建议 (0-100%)
    bear_cnt = sum(1 for s in signals if any(kw in s for kw in ["死叉", "空头", "跌破", "下轨"]))
    bull_cnt = sum(1 for s in signals if any(kw in s for kw in ["金叉", "多头", "突破", "上轨"]))
    over_buy = any("超买" in s for s in signals)
    over_sell = any("超卖" in s for s in signals)

    if bear_cnt >= 3:
        level, color = "红", "red"
        msg = "传统指标: 空头排列共振 (撤退信号)"
        action = "撤退 / 大幅减仓至 20% 以下"
        pos = "≤20%"
        sug = (f"MA60下方+MA5<MA20+MACD死叉等多重空头共振({bear_cnt}个空头信号), "
               f"传统技术面全面转空 → 建议撤退或大幅减仓, 保留现金等待结构修复")
    elif bear_cnt == 2:
        level, color = "橙", "orange"
        msg = "传统指标: 双空头信号 (减仓)"
        action = "减仓至 40% 以下"
        pos = "≤40%"
        sug = (f"出现{bear_cnt}个空头信号共振, 趋势转弱确认中 → 建议减仓至4成以下, 反弹减磅")
    elif bear_cnt == 1 and not over_buy:
        level, color = "黄", "gold"
        msg = "传统指标: 单空头信号 (观望)"
        action = "减仓至 60% 或观望"
        pos = "50-60%"
        sug = (f"出现1个空头信号: {signals[-1]} → 趋势初现转弱, 建议降低仓位至5-6成并密切跟踪")
    elif over_buy and bear_cnt >= 1:
        level, color = "黄", "orange"
        msg = "传统指标: 超买+转弱 (警惕回调)"
        action = "减仓至 50% 以下"
        pos = "≤50%"
        sug = ("超买区(RSI/KDJ高位)同时出现转弱信号 → 高位风险聚集, 建议减仓至5成以下, 不追高")
    elif over_sell and bull_cnt >= 1:
        level, color = "黄绿", "gold"
        msg = "传统指标: 超卖+转强 (关注反弹)"
        action = "轻仓试探 30-50%"
        pos = "30-50%"
        sug = ("超卖区(RSI/KDJ低位)出现金叉/突破 → 超跌反弹机会, 可轻仓试探, 严格止损")
    elif bull_cnt >= 2:
        level, color = "绿", "green"
        msg = "传统指标: 多头信号 (持有/增持)"
        action = "维持 60-80% 仓位"
        pos = "60-80%"
        sug = (f"出现{bull_cnt}个多头信号(金叉/多头排列/突破) → 趋势健康, 建议维持6-8成仓位")
    else:
        level, color = "绿", "green"
        msg = "传统指标: 中性 (持有)"
        action = "维持 50-70% 仓位"
        pos = "50-70%"
        sug = "传统技术面无显著风险信号, 结构中性 → 维持5-7成仓位, 跟随分形预警信号联动"

    return {"level": level, "color": color, "msg": msg,
            "suggestion": sug, "signals": signals,
            "action": action, "pos": pos, "rationale": rationale}


# ------------------------------------------------------------
# 事件检测: BOLL 突破/跌破 + MACD 金叉/死叉
# ------------------------------------------------------------
def detect_boll_events(dates, close, boll_up, boll_low, lookback=120):
    """
    检测 BOLL 突破/跌破事件
    返回: [{"date","type":"break_up|break_dn","price"}, ...] 仅最近 lookback 内
    """
    events = []
    start = max(1, len(close) - lookback)
    for i in range(start, len(close)):
        if not (np.isfinite(boll_up[i]) and np.isfinite(boll_low[i])):
            continue
        # 突破上轨: 今日收盘 > 上轨 且 昨日 <= 上轨
        if i >= 1 and close[i] > boll_up[i] and close[i-1] <= boll_up[i-1]:
            events.append({"date": dates[i], "type": "break_up",
                           "price": float(close[i])})
        # 跌破下轨: 今日收盘 < 下轨 且 昨日 >= 下轨
        if i >= 1 and close[i] < boll_low[i] and close[i-1] >= boll_low[i-1]:
            events.append({"date": dates[i], "type": "break_dn",
                           "price": float(close[i])})
    return events


def detect_macd_events(dates, dif, dea, lookback=120):
    """
    检测 MACD 金叉/死叉事件
    返回: [{"date","type":"golden|death","value"}, ...] 仅最近 lookback 内
    """
    events = []
    start = max(1, len(dif) - lookback)
    for i in range(start, len(dif)):
        if not (np.isfinite(dif[i]) and np.isfinite(dea[i])
                and np.isfinite(dif[i-1]) and np.isfinite(dea[i-1])):
            continue
        # 金叉: DIF 上穿 DEA
        if dif[i-1] <= dea[i-1] and dif[i] > dea[i]:
            events.append({"date": dates[i], "type": "golden",
                           "value": float(dif[i])})
        # 死叉: DIF 下穿 DEA
        if dif[i-1] >= dea[i-1] and dif[i] < dea[i]:
            events.append({"date": dates[i], "type": "death",
                           "value": float(dif[i])})
    return events


# ------------------------------------------------------------
# 汇总: 全量传统分析
# ------------------------------------------------------------
def analyze_traditional(kline=None):
    if kline is None:
        kline = fetch_index_kline("sh000001", count=500)
    close, high, low = kline["close"], kline["high"], kline["low"]

    ma5, ma10, ma20 = sma(close, 5), sma(close, 10), sma(close, 20)
    ma60 = sma(close, 60)
    dif, dea, hist = macd(close)
    rsi14 = rsi(close, 14)
    mid, up, low_b, pctb = boll(close)
    k, d, j = kdj(high, low, close)

    alert = traditional_alert(close, ma5, ma10, ma20, ma60,
                              dif, dea, hist, rsi14, pctb, k, d, j)

    # 事件检测 (BOLL 突破/跌破 + MACD 金叉/死叉)
    boll_events = detect_boll_events(kline["date"], close, up, low_b)
    macd_events = detect_macd_events(kline["date"], dif, dea)

    # 最近120日窗口 (与分形对照窗口一致)
    tail = -120
    return {
        "date": kline["date"],
        "open": kline["open"].tolist(), "close": close.tolist(),
        "high": high.tolist(), "low": low.tolist(),
        "ma5": ma5.tolist(), "ma10": ma10.tolist(), "ma20": ma20.tolist(),
        "ma60": ma60.tolist(),
        "dif": dif.tolist(), "dea": dea.tolist(), "hist": hist.tolist(),
        "rsi14": rsi14.tolist(),
        "boll_mid": mid.tolist(), "boll_up": up.tolist(), "boll_low": low_b.tolist(),
        "pctb": pctb.tolist(),
        "kdj_k": k.tolist(), "kdj_d": d.tolist(), "kdj_j": j.tolist(),
        "last_close": float(close[-1]),
        "last_ma60": float(ma60[-1]) if np.isfinite(ma60[-1]) else None,
        "last_rsi": float(rsi14[-1]),
        "last_pctb": float(pctb[-1]) if np.isfinite(pctb[-1]) else None,
        "last_j": float(j[-1]),
        "boll_events": boll_events,
        "macd_events": macd_events,
        "alert": alert,
    }


if __name__ == "__main__":
    print("传统大盘预警系统 · 自测 (上证指数)")
    try:
        res = analyze_traditional()
        print(f"最新收盘: {res['last_close']}")
        print(f"最新RSI14: {res['last_rsi']:.1f}")
        print(f"最新J值: {res['last_j']:.1f}")
        print(f"信号: {res['alert']['msg']}")
        print(f"明细: {res['alert']['signals']}")
        print("✅ 传统指标模块正常")
    except Exception as e:
        print(f"❌ 失败: {e}")
