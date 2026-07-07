"""PKS-CLF 选股算法 — v2.5 最终版评级引擎
======================================
基于 PKS 双锥体极化几何 (Schauberger/Pythagoras-Kepler)
四参数核心: γ(趋势方向) + h(趋势结构) + z₀(趋势空间) + c(两力耦合)
纯成长/动量池专用 · 96fen 算法天然搭档

五轮独立池回测: PKS胜 4/4 纯成长池, γ+h+z₀+c 增益 v2.4→v2.5 = +2.77%
"""

import subprocess, math

NODE = r'C:/Users/ThinkPad/.workbuddy/binaries/node/versions/22.22.2/node.exe'
WSK = r'C:/Users/ThinkPad/AppData/Local/Programs/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'

def fetch_kline(code, limit=120):
    """抓取K线 → oldest first"""
    r = subprocess.run([NODE, WSK, 'kline', code, '--period', 'day', '--limit', str(limit)],
                      capture_output=True, text=True, timeout=30)
    if r.returncode: return []
    data = []
    for l in r.stdout.strip().split('\n'):
        if not l.startswith('| ') or '---' in l: continue
        f = [x.strip() for x in l.split('|')]
        if len(f) < 9: continue
        try: data.append({'d':f[1],'o':float(f[2]),'c':float(f[3]),'h':float(f[4]),'l':float(f[5])})
        except: continue
    data.reverse(); return data

def compute_pks_v25(data_60d, pool_h_median=None, pool_z_median=None):
    """
    PKS v2.5 四参数评级
    ====================
    
    从60日K线提取 PKS 双锥体几何四参数，输出 A+~X 六级。
    使用池中位数做自适应归一化（默认值用于 stand-alone 模式）。
    
    公式链:
      r₁ = max((H-MA60)/MA60, (MA60-L)/MA60)   # 大端径向偏差
      r₂ = min((H-MA60)/MA60, (MA60-L)/MA60)   # 小端径向偏差
      γ  = atan((r₁-r₂)/(r₁+r₂))                # 趋势烈度 [0,45°]
      h  = 2·r₁·r₂/(r₁+r₂)                      # 调和平均 → 趋势结构
      u₁ = 1/r₁, u₂ = 1/r₂
      z₀ = (u₁²+u₂²)/(u₁+u₂)                    # 原著两点公式 → 趋势空间
      c  = (z₀·√2/2)·tan(2·atan(...))           # 两锥耦合
    """
    if len(data_60d) < 60: return None
    
    cls = [d['c'] for d in data_60d]
    bl = sum(cls) / len(cls)
    ph = max(d['h'] for d in data_60d)
    pl = min(d['l'] for d in data_60d)
    
    r1 = max((ph-bl)/bl, (bl-pl)/bl)
    r2 = min((ph-bl)/bl, (bl-pl)/bl)
    if r2 < 1e-8: return None
    
    # 趋势烈度 (直圆锥截面角度)
    gamma = math.degrees(math.atan((r1-r2)/(r1+r2)))
    
    # 趋势结构 (椭圆的调和平均半轴)
    h_val = 2 * r1 * r2 / (r1 + r2)
    
    # 趋势空间 (超双曲锥切割高度, 两点公式)
    u1, u2 = 1/r1, 1/r2
    z0 = (u1*u1 + u2*u2) / (u1 + u2)
    
    alpha_rad = math.atan(-u1 * u2 * (u2 - u1) / (u1 + u2))
    
    # 两力耦合 (直锥截面中心 ↔ 超双曲锥截面中心 偏移量)
    c_val = (z0 * math.sqrt(2) / 2) * math.tan(2 * alpha_rad)
    
    # 自适应阈值 (default用于standalone)
    if pool_h_median is None: pool_h_median = 0.15
    if pool_z_median is None: pool_z_median = 5.0
    
    # === v2.5 评级 ===
    # X: 极端排除 (γ>30°=抛物线临界, c 极端偏移)
    if gamma > 30 or c_val < -1 or c_val > 3:
        grade = 'X'
        reason = '极端排除'
    # A+: 三好学生 (强趋势+扎实结构+宽裕空间)
    elif gamma >= 25 and h_val >= pool_h_median and z0 >= pool_z_median:
        grade = 'A+'
        reason = 'γ强+h实+z宽'
    # A: 强趋势+扎实结构 (经典组合)
    elif gamma >= 20 and h_val >= pool_h_median and z0 >= pool_z_median:
        grade = 'A'
        reason = 'γ中+h实+z宽'
    # B: 强趋势+窄空间 (容错不足)
    elif gamma >= 25 and h_val >= pool_h_median:
        grade = 'B'
        reason = 'γ强+h实+z窄'
    # C: 中强趋势+窄空间 或 有方向但结构弱
    elif gamma >= 20:
        grade = 'C'
        reason = 'γ中'
    # D: 弱趋势
    else:
        grade = 'D'
        reason = 'γ弱'
    
    # 双薄弱标签 (纯叙事,不参与评级)
    double_fragile = (gamma >= 22.5 and gamma <= 30 and c_val >= 0)
    
    return {
        'gamma': round(gamma, 1),
        'h': round(h_val, 4),
        'z0': round(z0, 1),
        'c': round(c_val, 2),
        'grade': grade,
        'reason': reason,
        'double_fragile': double_fragile,
    }


# ====== CLI test ======
if __name__ == '__main__':
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else 'sh603259'
    data = fetch_kline(code, 120)
    if not data or len(data) < 80:
        print('数据不足')
        sys.exit(1)
    result = compute_pks_v25(data[-60:])
    if result is None:
        print('计算失败')
        sys.exit(1)
    print(f"  γ={result['gamma']}° h={result['h']:.3f} z₀={result['z0']:.1f} c={result['c']:.2f}")
    print(f"  评级: {result['grade']} ({result['reason']})")
    if result['double_fragile']:
        print(f"  ⚠️ 双薄弱: 趋势在刀尖上跳舞")
