"""
NLS 独立诊断系统 v2.0 — 多维特征分析
从256字节响应中提取7个维度, 覆盖50+指标
"""
import serial, struct, time, math, json, numpy as np
from collections import defaultdict

COM_PORT = "COM4"
BAUD = 115200
BASE = 7.3728

# b9 → 器官 + 经络 + 五行
B9_MAP = {
    1: ("基底/地线", "—", "—"),
    2: ("极低频场", "—", "—"),
    3: ("极低频场", "—", "—"),
    4: ("极低频场", "—", "—"),
    5: ("极低频场", "—", "—"),
    6: ("极低频场", "—", "—"),
    7: ("极低频场", "—", "—"),
    8: ("极低频场", "—", "—"),
    9: ("极低频场", "—", "—"),
    10: ("极低频场", "—", "—"),
    11: ("极低频场", "—", "—"),
    12: ("极低频场", "—", "—"),
    13: ("极低频场", "—", "—"),
    14: ("骨骼/基础", "骨骼基底", "土"),
    15: ("肌肉/结缔", "脾经(肌肉)", "土"),
    16: ("皮肤/皮毛", "肺经(皮毛)", "金"),
    17: ("淋巴/免疫", "三焦(免疫)", "火"),
    18: ("消化/肠道", "大肠经", "金"),
    19: ("消化/胃部", "胃经", "土"),
    20: ("肝脏/代谢", "肝经", "木"),
    21: ("胰腺/内分泌", "脾经(胰)", "土"),
    22: ("脾脏/血液", "脾经(血)", "土"),
    23: ("肺部/呼吸", "肺经(呼吸)", "金"),
    24: ("甲状腺", "任脉(甲)", "火"),
    25: ("肾脏/肾上腺", "肾经", "水"),
    26: ("心血管", "心包经", "火"),
    27: ("心脏", "心经", "火"),
    28: ("神经系统", "督脉(神经)", "火"),
    29: ("脑/中枢", "督脉(脑)", "火"),
    30: ("下丘脑", "任脉(下丘)", "火"),
    31: ("松果体", "督脉(松)", "火"),
    32: ("超高频场", "—", "—"),
    33: ("超高频场", "—", "—"),
    34: ("超高频场", "—", "—"),
    35: ("超高频场", "—", "—"),
}

def analyze_256(raw, baseline_raw=None):
    """从256字节提取7维特征"""
    vals = np.array(list(raw), dtype=float)
    feats = {}
    
    # 1. 强度特征
    feats['avg'] = np.mean(vals)
    feats['std'] = np.std(vals)
    feats['min'] = np.min(vals)
    feats['max'] = np.max(vals)
    feats['range'] = feats['max'] - feats['min']
    feats['median'] = np.median(vals)
    
    # 2. 分布特征
    feats['skew'] = float(np.mean(((vals - feats['avg']) / (feats['std']+1))**3))
    feats['kurt'] = float(np.mean(((vals - feats['avg']) / (feats['std']+1))**4) - 3)
    
    # 3. 熵 (信号复杂度)
    hist, _ = np.histogram(vals, bins=16, range=(0,256))
    hist = hist / hist.sum()
    feats['entropy'] = float(-np.sum(hist * np.log2(hist + 1e-9)))
    
    # 4. 8组分层 (每32字节 = 一个组织层)
    groups = []
    for g in range(8):
        chunk = vals[g*32:(g+1)*32]
        groups.append({
            'avg': float(np.mean(chunk)),
            'std': float(np.std(chunk)),
            'energy': float(np.sum(chunk**2)),
        })
    feats['groups'] = groups
    
    # 5. FFT 主频
    fft = np.abs(np.fft.rfft(vals - feats['avg']))
    feats['fft_peak'] = float(np.argmax(fft[1:]) + 1)
    feats['fft_energy'] = float(np.sum(fft))
    
    # 6. 零交叉率
    centered = vals - feats['avg']
    feats['zero_cross'] = int(np.sum(np.diff(np.sign(centered)) != 0))
    
    # 7. 与基线差谱
    bl_avg = None
    if isinstance(baseline_raw, dict):
        bl_avg = baseline_raw.get('avg', None)
    elif baseline_raw is not None:
        bl_vals = np.array(list(baseline_raw), dtype=float)
        bl_avg = np.mean(bl_vals)
    
    if bl_avg is not None:
        feats['delta_avg'] = float(feats['avg'] - bl_avg)
    else:
        feats['delta_avg'] = 0
    
    return feats


def run_full_scan(baseline_data=None):
    """全频扫描 b9=1..35, 返回完整特征"""
    ser = serial.Serial(COM_PORT, BAUD, timeout=2)
    results = {}
    
    for b9 in range(1, 36):
        cmd = bytearray(128)
        cmd[9] = b9; cmd[11] = 15; cmd[13] = b9; cmd[15] = 15
        ser.reset_input_buffer()
        ser.write(bytes(cmd))
        time.sleep(0.12)
        resp = ser.read(256)
        
        bl = baseline_data.get(str(b9), None)
        feats = analyze_256(resp, bl)
        feats['freq_mhz'] = round(BASE * (2**(b9/4)) * 3, 0)
        results[b9] = feats
    
    ser.close()
    return results


def build_report(scan_data):
    """基于多维特征生成综合诊断报告"""
    lines = []
    lines.append("=" * 75)
    lines.append("  NLS 独立诊断报告 v2.0 — 多维特征分析")
    lines.append(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 75)
    
    # ── 1. 总体状态 ──
    avgs = [d['avg'] for d in scan_data.values()]
    entropies = [d['entropy'] for d in scan_data.values()]
    zc_rates = [d['zero_cross'] for d in scan_data.values()]
    fft_energies = [d['fft_energy'] for d in scan_data.values()]
    
    lines.append("")
    lines.append("┌─ 总体状态 ─────────────────────────────────")
    lines.append(f"│ 响应均值:     {np.mean(avgs):.1f}  (信号总强度)")
    lines.append(f"│ 响应方差:     {np.std(avgs):.1f}  (频段差异化)")
    lines.append(f"│ 平均熵值:     {np.mean(entropies):.2f} (信号复杂度, 3.0~4.0正常)")
    lines.append(f"│ 平均零交叉:   {np.mean(zc_rates):.0f}  (高频成分)")
    lines.append(f"│ FFT总能量:    {np.mean(fft_energies):.0f}")
    lines.append("└──────────────────────────────────────────")
    
    # ── 2. 器官系统异常 ──
    lines.append("")
    lines.append("┌─ 器官系统异常 ────────────────────────────")
    
    system_scores = defaultdict(list)
    for b9 in range(14, 32):
        d = scan_data[b9]
        organ, meridian, wuxing = B9_MAP[b9]
        # 综合评分: delta_avg + entropy + fft_energy
        score = abs(d.get('delta_avg', 0)) * 0.4 + abs(d['entropy'] - 3.5) * 2 + d['fft_energy'] / 10000
        system_scores[organ].append({
            'b9': b9, 'freq': d['freq_mhz'], 'delta': d.get('delta_avg', 0),
            'entropy': d['entropy'], 'score': score, 'meridian': meridian, 'wuxing': wuxing
        })
    
    # 排序输出
    organ_rank = []
    for organ, items in system_scores.items():
        avg_score = sum(it['score'] for it in items) / len(items)
        max_delta = max(abs(it['delta']) for it in items)
        organ_rank.append((organ, avg_score, max_delta, items))
    
    organ_rank.sort(key=lambda x: -x[2])
    
    for organ, avg_score, max_delta, items in organ_rank[:15]:
        if max_delta < 5: continue
        level = '🔵' if max_delta > 12 else ('🟡' if max_delta > 7 else '🟢')
        wu = items[0]['wuxing'] if items else '—'
        freq_str = ','.join(f"{it['freq']:.0f}" for it in items)
        lines.append(f"│ {level} {organ:<14} Δmax={max_delta:+.1f} | {wu}行 | {freq_str}MHz")
    lines.append("└──────────────────────────────────────────")
    
    # ── 3. 8层组织分析 ──
    lines.append("")
    lines.append("┌─ 8层组织分析 (每层32B = 不同组织深度) ────")
    layer_names = ["表皮", "真皮", "皮下脂肪", "浅筋膜", "肌肉", "深筋膜", "器官表膜", "器官实质"]
    layer_avgs = [0]*8
    for b9 in range(14, 32):
        groups = scan_data[b9]['groups']
        for g in range(8):
            layer_avgs[g] += groups[g]['energy']
    
    total = sum(layer_avgs) or 1
    for g in range(8):
        pct = layer_avgs[g] / total * 100
        bar = '█' * max(1, int(pct / 3))
        lines.append(f"│ L{g+1} {layer_names[g]:<10} {pct:>5.1f}% {bar}")
    lines.append("└──────────────────────────────────────────")
    
    # ── 4. 五行汇总 ──
    lines.append("")
    lines.append("┌─ 五行能量 ────────────────────────────────")
    wuxing_deltas = defaultdict(list)
    for b9 in range(14, 32):
        _, _, wu = B9_MAP[b9]
        d = scan_data[b9]
        if wu != '—':
            wuxing_deltas[wu].append(d.get('delta_avg', 0))
    
    order = ['木', '火', '土', '金', '水']
    for wu in order:
        if wu in wuxing_deltas:
            vals = wuxing_deltas[wu]
            avg_d = np.mean(vals)
            level = '偏盛' if avg_d > 3 else ('偏弱' if avg_d < -3 else '平衡')
            lines.append(f"│ {wu}行: {'+' if avg_d>0 else ''}{avg_d:.1f} [{level}] ({len(vals)}频段)")
    lines.append("└──────────────────────────────────────────")
    
    return "\n".join(lines)


if __name__ == '__main__':
    # 加载基线
    try:
        with open('NLS_扫描数据_20260630_205720.json', 'r') as f:
            baseline = json.load(f)['baseline']
        print("[OK] 已加载空扫基线")
    except:
        baseline = {}
        print("[!] 无基线, 输出绝对特征")
    
    # 扫描
    print("全频扫描 b9=1..35 (多维特征)...")
    results = run_full_scan(baseline)
    
    # 生成报告
    report = build_report(results)
    print(report)
    
    # 保存
    ts = time.strftime("%Y%m%d_%H%M%S")
    with open(f"NLS_多维诊断_{ts}.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ 已保存: NLS_多维诊断_{ts}.txt")
