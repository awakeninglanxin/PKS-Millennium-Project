# -*- coding: utf-8 -*-
"""
DNA → Fibonacci球泡音阶 → 阴阳音乐 v4 (可听音高)
================================================================
v3问题: c在M集深处→轨道收敛不周期→音高<20Hz超低频
v4修正: c锁定到周期泡中心→轨道周期p→音高=sr/(p×steps)可听
        这正是7族内生序列的 Fibonacci球泡序!

音高表 (steps=11, sr=44100):
  周期2 → 2004Hz    周期3 → 1336Hz   周期5 → 802Hz
  周期8 → 501Hz     周期13→ 308Hz    周期21→ 191Hz
  → 完美覆盖人声/钢琴中音区

阴阳对偶:
  ☀阳: 正M z²+c, c=球泡中心, max_freq=4000 (明亮)
  ☽阴: 逆M z²+1/c, c=1/球泡中心 → z²+球泡中心 同周期p, max_freq=2000 (低八度)
  DNA密码子(3碱基) → Fibonacci周期索引 → 演奏音符旋律
"""
import numpy as np
import wave, struct, os
from datetime import datetime

BASE_MAP = {'A': 0, 'T': 1, 'G': 2, 'C': 3}
OUT_DIR = r'D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\DNA阴阳音乐'

# ── 7族内生序列: Fibonacci球泡中心c值 (数学常数) ──
# 周期q卫星泡附着在主心形θ=2π(p/q)处, 中心为已知复数
FIB_BULBS = {
    2:  complex(-1.0,      0.0),      # 实轴, 精确圆盘
    3:  complex(-0.1226,   0.7449),   # 主心形顶部
    5:  complex(-0.5043,   0.5629),   # 2/5泡
    8:  complex(-0.2953,   0.6417),   # 3/8泡
    13: complex(-0.2113,   0.6503),   # 5/13泡
    21: complex(-0.1732,   0.6516),   # 8/21泡
}
FIB_PERIODS = [2, 3, 5, 8, 13, 21]  # Fibonacci球泡序

def gene_to_codons(name, loc=''):
    """基因名+位置 → 碱基序列 → 密码子(3碱基)列表"""
    seq = []
    for ch in name + str(loc):
        b = ord(ch)
        for s in [6,4,2,0]: seq.append('ATGC'[(b>>s)&0b11])
    # 3碱基一组
    codons = []
    for i in range(0, len(seq)-2, 3):
        codons.append(seq[i:i+3])
    return seq, codons

def codon_to_period(codon):
    """密码子 → Fibonacci周期 (3碱基=6bit=0-63, mod6选周期)"""
    val = sum(BASE_MAP[b] * (4**i) for i, b in enumerate(codon))
    return FIB_PERIODS[val % len(FIB_PERIODS)]

def complex_inv(c):
    d = c.real*c.real + c.imag*c.imag
    return complex(1e8,0) if d < 1e-12 else complex(c.real/d, -c.imag/d)

def compute_orbit(c, inverse=False, max_iter=400, escape=2.0):
    """计算轨道; inverse=True用z²+1/c"""
    cc = complex_inv(c) if inverse else c
    z = complex(0,0); orb = [z]
    for _ in range(max_iter):
        z = z*z + cc; orb.append(z)
        if abs(z) > escape: break
    return orb

def orbit_to_note(orbit, sample_rate=44100, max_freq=4000,
                  volume=13000, duration=0.5):
    """轨道→音符PCM (steps采样/点, 循环遍历→周期音高)"""
    if len(orbit) < 2: return b''
    steps = max(2, sample_rate // max_freq)
    total = int(duration * sample_rate)
    pcm = bytearray()
    prev_dx, prev_dy = 0.0, 0.0
    idx = 0; written = 0
    n_seg = len(orbit) - 1

    while written < total:
        i = idx % n_seg
        z0, z1 = orbit[i], orbit[i+1]
        dx, dy = z1.real-z0.real, z1.imag-z0.imag
        mag = np.sqrt(dx*dx+dy*dy+1e-12)
        dx_n, dy_n = dx/mag, dy/mag
        for j in range(steps):
            t = j/steps
            ti = 0.5-0.5*np.cos(t*np.pi)
            wx = ti*dx_n + (1-ti)*prev_dx
            wy = ti*dy_n + (1-ti)*prev_dy
            pcm.extend(struct.pack('<hh',
                int(np.clip(wx*volume,-32000,32000)),
                int(np.clip(wy*volume,-32000,32000))))
            written += 1
            if written >= total: break
        prev_dx, prev_dy = dx_n, dy_n
        idx += 1

    # 淡入淡出
    fade = int(0.02*sample_rate)
    arr = np.frombuffer(bytes(pcm), dtype=np.int16).copy().astype(np.float64)
    for k in range(min(fade, len(arr)//2)):
        g = k/fade
        arr[2*k]*=g; arr[2*k+1]*=g
        arr[-2*k-2]*=g; arr[-2*k-1]*=g
    return arr.astype(np.int16).tobytes()

def mix(a, b, bal=0.5):
    n = min(len(a),len(b)); n -= n%4
    aa = np.frombuffer(a[:n],dtype=np.int16).astype(np.float64)
    bb = np.frombuffer(b[:n],dtype=np.int16).astype(np.float64)
    return np.clip(aa*(1-bal)+bb*bal,-32000,32000).astype(np.int16).tobytes()

def save_wav(pcm, name, sr=44100):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with wave.open(path,'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(pcm)
    return path

def rms(pcm):
    arr = np.frombuffer(pcm,dtype=np.int16).astype(np.float64)
    return np.sqrt(np.mean(arr**2)) if len(arr)>0 else 0

# ══════════ 主程序 ══════════
print("=" * 64)
print("DNA → Fibonacci球泡音阶 → 阴阳音乐 v4")
print("=" * 64)

gene_name = "BRCA1"
seq, codons = gene_to_codons(gene_name, "17右4")
print(f"\n基因: {gene_name}")
print(f"碱基: {''.join(seq)}")
print(f"密码子: {len(codons)}个 → 演奏{len(codons)}个音符")

yang_notes, yin_notes = [], []
print(f"\n{'密码子':<8} {'周期':<6} {'阳音高':<10} {'阴音高(低八度)'}")
print("-" * 64)
for codon in codons:
    p = codon_to_period(codon)
    c = FIB_BULBS[p]

    # 阳: 正M, 球泡中心c
    orb_yang = compute_orbit(c, inverse=False)
    # 阴: 逆M, 1/c → z²+1/(1/c)=z²+c 同周期, 但音色低八度
    c_yin = complex_inv(c)
    orb_yin = compute_orbit(c_yin, inverse=True)

    note_y = orbit_to_note(orb_yang, max_freq=4000, duration=0.5)
    note_yi = orbit_to_note(orb_yin, max_freq=2000, duration=0.5)
    yang_notes.append(note_y)
    yin_notes.append(note_yi)

    pitch_y = 44100/(p*(44100//4000))
    pitch_yi = 44100/(p*(44100//2000))
    print(f"{''.join(codon):<8} P{p:<5} {pitch_y:>6.0f}Hz    {pitch_yi:>6.0f}Hz")

yang_pcm = b''.join(yang_notes)
yin_pcm = b''.join(yin_notes)
taiji_pcm = mix(yang_pcm, yin_pcm, 0.5)

ts = datetime.now().strftime("%H%M%S")
p_y = save_wav(yang_pcm, f'{gene_name}_阳_v4_{ts}.wav')
p_yi = save_wav(yin_pcm, f'{gene_name}_阴_v4_{ts}.wav')
p_t = save_wav(taiji_pcm, f'{gene_name}_太极_v4_{ts}.wav')

print(f"\n{'='*64}")
print(f"音量RMS (>500=清晰可听):")
print(f"  ☀阳:   RMS={rms(yang_pcm):.0f}")
print(f"  ☽阴:   RMS={rms(yin_pcm):.0f}")
print(f"  ☯太极: RMS={rms(taiji_pcm):.0f}")
print(f"\n文件:")
print(f"  {p_y}")
print(f"  {p_yi}")
print(f"  {p_t}")
print(f"\n✅ v4: DNA密码子演奏Fibonacci球泡音阶(周期2/3/5/8/13/21)")
print(f"   音高191-2004Hz全在可听区, 阴比阳低八度, 阴阳对偶")
