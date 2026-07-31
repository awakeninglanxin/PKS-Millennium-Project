"""
NLS 独立探针诊断系统 v1.0
─────────────────────────────
绕过 MetaHunter.exe，通过 COM4 直驱手环，
全频扫描 b9=1~35 (26MHz~9.5GHz)，生成第一份独立诊断报告。

使用方法:
  python nls_independent_scanner.py
  → 先做空扫基线（传感器悬空）
  → 再做接触扫描（手腕/手心）
  → 输出对比诊断报告
"""
import serial, struct, time, math, json, os
from collections import defaultdict

# ========== 配置 ==========
COM_PORT = "COM4"
BAUD = 115200
BASE_FREQ = 7.3728  # MHz 晶振

# b9 → 器官系统映射（基于PCAP验证）
B9_ORGAN = {
    14: ("骨骼/基础组织", "骨骼系统"),
    15: ("肌肉/结缔", "肌肉系统"),
    16: ("皮肤/表皮", "皮肤系统"),
    17: ("淋巴/免疫", "免疫系统"),
    18: ("消化/肠道", "消化系统"),
    19: ("消化/胃部", "消化系统"),
    20: ("肝脏/代谢", "肝胆系统"),
    21: ("胰腺/内分泌", "内分泌系统"),
    22: ("脾脏/血液", "血液系统"),
    23: ("肺部/呼吸", "呼吸系统"),
    24: ("甲状腺", "内分泌系统"),
    25: ("肾上腺", "泌尿系统"),
    26: ("心血管", "心血管系统"),
    27: ("心脏", "心血管系统"),
    28: ("神经系统", "神经系统"),
    29: ("脑/中枢", "神经系统"),
    30: ("下丘脑", "神经内分泌"),
    31: ("松果体", "神经内分泌"),
}

# 经络映射
B9_MERIDIAN = {
    14: "骨骼(基底)", 15: "脾经(肌肉)", 16: "肺经(皮毛)",
    17: "三焦(免疫)", 18: "大肠经", 19: "胃经", 20: "肝经",
    21: "脾经(胰)", 22: "脾经(血)", 23: "肺经(呼吸)",
    24: "任脉(甲状腺)", 25: "肾经(肾上腺)", 26: "心包经",
    27: "心经", 28: "督脉(神经)", 29: "督脉(脑)",
    30: "任脉(下丘脑)", 31: "督脉(松果体)",
}


class NLSScanner:
    def __init__(self):
        self.ser = None
        self.baseline = {}   # {b9: stats}
        self.measurement = {}  # {b9: stats}
        
    def connect(self):
        """打开 COM4"""
        try:
            self.ser = serial.Serial(COM_PORT, BAUD, timeout=2)
            print(f"[OK] COM4 已连接")
            return True
        except Exception as e:
            print(f"[FAIL] COM4 连接失败: {e}")
            return False
    
    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.ser = None
    
    def freq(self, b9):
        return BASE_FREQ * (2 ** (b9 / 4)) * 3
    
    def probe_once(self, b9, b11=15):
        """发送单次探针，返回256字节响应"""
        cmd = bytearray(128)
        cmd[9] = b9
        cmd[11] = b11
        cmd[13] = b9
        cmd[15] = b11
        
        self.ser.reset_input_buffer()
        self.ser.write(bytes(cmd))
        time.sleep(0.12)
        return self.ser.read(256)
    
    def scan(self, label, b9_range=None):
        """全频扫描，返回统计结果"""
        if b9_range is None:
            b9_range = range(1, 36)  # b9=1..35
        
        results = {}
        n = len(list(b9_range))
        
        print(f"\n{'='*55}")
        print(f"  {'空扫基线' if 'air' in label.lower() else '接触扫描'}: {label}")
        print(f"  b9=1~35 (35个频段, 26MHz~9.5GHz)")
        print(f"{'='*55}")
        
        for i, b9 in enumerate(b9_range):
            resp = self.probe_once(b9)
            f = self.freq(b9)
            
            if len(resp) == 256:
                vals = list(resp)
                avg = sum(vals) / 256
                std = math.sqrt(sum((v - avg) ** 2 for v in vals) / 256)
                
                # 分组分析（每组32字节 ≈ 8组）
                groups = []
                for g in range(8):
                    chunk = vals[g*32:(g+1)*32]
                    groups.append(sum(chunk) / 32)
                
                results[b9] = {
                    'freq_mhz': round(f, 0),
                    'avg': round(avg, 1),
                    'std': round(std, 1),
                    'min': min(vals),
                    'max': max(vals),
                    'groups': [round(g, 1) for g in groups],
                    'raw_head': vals[:8],
                }
                
                bar = '█' * min(20, int(avg / 10))
                organ = B9_ORGAN.get(b9, ('?', '?'))[0]
                prog = f"{i+1}/{n}"
                print(f"  [{prog}] b9={b9:2d} {f:>5.0f}MHz {organ:<12} avg={avg:>6.1f} {bar}")
            else:
                print(f"  [{i+1}/{n}] b9={b9:2d} {f:>5.0f}MHz → {len(resp)}B (异常)")
        
        return results
    
    def compare(self, baseline, measurement):
        """对比基线和测量，生成诊断报告"""
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("  NLS 独立诊断报告")
        report_lines.append(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 70)
        report_lines.append("")
        report_lines.append(f"{'b9':<4} {'频率':<8} {'器官系统':<16} {'基线':>7} {'实测':>7} {'偏差':>7} {'状态'}")
        report_lines.append("-" * 70)
        
        findings = []
        for b9 in sorted(baseline.keys() & measurement.keys()):
            bl = baseline[b9]
            ms = measurement[b9]
            delta = ms['avg'] - bl['avg']
            
            # 判定异常等级
            if abs(delta) < 3:
                status = "🟢 正常"
                level = 0
            elif abs(delta) < 7:
                status = "🟡 轻度"
                level = 1
            elif abs(delta) < 12:
                status = "🔵 中度"
                level = 2
            elif abs(delta) < 20:
                status = "🔷 明显"
                level = 3
            else:
                status = "🟣 严重"
                level = 4
            
            organ, system = B9_ORGAN.get(b9, ('?', '?'))
            meridian = B9_MERIDIAN.get(b9, '')
            
            line = (f"{b9:<4} {ms['freq_mhz']:>5.0f}MHz "
                   f"{organ:<16} {bl['avg']:>6.1f} {ms['avg']:>6.1f} {delta:>+6.1f}  {status}")
            report_lines.append(line)
            
            if level >= 2:  # 中度及以上记录
                findings.append({
                    'b9': b9, 'organ': organ, 'system': system,
                    'meridian': meridian, 'delta': delta, 'level': level,
                    'freq': ms['freq_mhz']
                })
        
        # 系统汇总
        report_lines.append("")
        report_lines.append("=" * 70)
        report_lines.append("  系统汇总")
        report_lines.append("=" * 70)
        
        system_deltas = defaultdict(list)
        for f in findings:
            system_deltas[f['system']].append(f)
        
        for system in sorted(system_deltas.keys()):
            items = system_deltas[system]
            avg_delta = sum(it['delta'] for it in items) / len(items)
            max_level = max(it['level'] for it in items)
            level_names = ['', '', '', '', '']
            level_icon = {0:'🟢', 1:'🟡', 2:'🔵', 3:'🔷', 4:'🟣'}[max_level]
            report_lines.append(f"  {level_icon} {system:<12} {len(items)}项异常 | 均Δ={avg_delta:+.1f} | 最重={max_level}")
        
        # 经络
        report_lines.append("")
        report_lines.append("=" * 70)
        report_lines.append("  经络关注")
        report_lines.append("=" * 70)
        for f in sorted(findings, key=lambda x: -abs(x['delta']))[:10]:
            report_lines.append(f"  b9={f['b9']:2d} {f['meridian']:<16} {f['organ']:<16} Δ={f['delta']:+.1f} → {f['system']}")
        
        return "\n".join(report_lines), findings


def main():
    scanner = NLSScanner()
    
    print("╔══════════════════════════════════════════════╗")
    print("║   NLS 独立探针诊断系统 v1.0                 ║")
    print("║   绕过 MetaHunter.exe，COM4 直驱手环        ║")
    print("╚══════════════════════════════════════════════╝")
    
    if not scanner.connect():
        return
    
    try:
        # ── 第1步: 空扫基线 ──
        input("\n[步骤1] 传感器悬空（不接触皮肤），按 Enter 开始空扫基线...")
        baseline = scanner.scan("空扫基线")
        
        # ── 第2步: 接触扫描 ──
        input("\n[步骤2] 将传感器贴手腕/手心，按 Enter 开始扫描...")
        measurement = scanner.scan("手腕接触")
        
        # ── 第3步: 生成报告 ──
        print("\n[步骤3] 生成诊断报告...")
        report, findings = scanner.compare(baseline, measurement)
        
        print(report)
        
        # ── 保存 ──
        ts = time.strftime("%Y%m%d_%H%M%S")
        report_path = f"NLS_独立诊断_{ts}.txt"
        data_path = f"NLS_扫描数据_{ts}.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump({
                'baseline': {str(k): v for k, v in baseline.items()},
                'measurement': {str(k): v for k, v in measurement.items()},
                'findings': findings,
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 报告已保存: {report_path}")
        print(f"✅ 数据已保存: {data_path}")
        
    finally:
        scanner.disconnect()


if __name__ == '__main__':
    main()
