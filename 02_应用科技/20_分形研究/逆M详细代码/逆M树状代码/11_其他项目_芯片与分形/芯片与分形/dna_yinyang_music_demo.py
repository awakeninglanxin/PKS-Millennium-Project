# -*- coding: utf-8 -*-
"""
DNA → 正逆Mandelbrot双引擎 → 阴阳音乐
============================================
正M (阳/Yang): z → z² + c       — 标准M集, 骨架确定, 声音"实"
逆M (阴/Yin):  z → z² + 1/c     — 复反演水滴, 声音"虚"
两种算法互为阴阳, 同一DNA生成阴阳两种音乐, 可分听/可叠听
"""
import numpy as np
import wave, struct, tempfile, os, winsound, time
from datetime import datetime

# ── DNA → 复平面c值 ──
BASE_TO_COMPLEX = {
    'A': 1+0j, 'T': -1+0j, 'G': 0+1j, 'C': 0-1j,
}

def gene_to_dna(gene_name, gene_location='', chromosome=0):
    seq = []
    for ch in gene_name:
        b = ord(ch)
        for shift in [6, 4, 2, 0]:
            seq.append('ATGC'[(b >> shift) & 0b11])
    for ch in str(gene_location):
        seq.append('ATGC'[ord(ch) & 0b11])
    return ''.join(seq)

def dna_to_c_values(dna_seq, step_scale=0.03):
    z = complex(0, 0)
    points = [z]
    for base in dna_seq:
        if base in BASE_TO_COMPLEX:
            z += BASE_TO_COMPLEX[base] * step_scale
            points.append(complex(z.real, z.imag))
    return points

def dna_to_c_yin(dna_seq, step_scale=0.05):
    """逆M专用: c>4→1/c<0.25在主心形内, 长轨道收敛"""
    z = complex(4.5, 0.25)  # 远点: 1/c≈0.22在M集主心形内
    points = [z]
    for base in dna_seq:
        if base in BASE_TO_COMPLEX:
            z += BASE_TO_COMPLEX[base] * step_scale
            # 保持在c>4区域 (1/c在主心形)
            points.append(complex(max(4.0, z.real), z.imag))
    return points

# ── 复反演: c → 1/c ──
def complex_inv(c):
    """1/c = conj(c)/|c|², 原点→远点"""
    denom = c.real*c.real + c.imag*c.imag
    if denom < 1e-12:
        return complex(1e8, 0)
    return complex(c.real/denom, -c.imag/denom)

# ══════════ 阴阳双引擎 ══════════
def orbit_yang(c, max_iter=200):
    """☀ 正M (阳): z → z² + c — 标准Mandelbrot, 骨架确定"""
    z = complex(0, 0)
    orbit = [z]
    for _ in range(max_iter):
        z = z*z + c
        orbit.append(z)
        if abs(z) > 10:
            break
    return orbit

def orbit_yin(c, max_iter=200):
    """☽ 逆M (阴): z → z² + 1/c — 复反演水滴, 虚空回响"""
    c_inv = complex_inv(c)
    z = complex(0, 0)
    orbit = [z]
    for _ in range(max_iter):
        z = z*z + c_inv
        orbit.append(z)
        if abs(z) > 10:
            break
    return orbit

# ── 轨道 → 音频 (阴阳音色差异化) ──
def orbit_to_audio(orbit, mode='yang', sample_rate=48000, volume=5000, duration_per_point=0.03):
    """
    轨道 → PCM
    阳(yang): 差分向量直接映射 → 明亮实音
    阴(yin):  差分向量+低通平滑 → 柔和虚音
    """
    if len(orbit) < 2:
        return None
    samples_per_point = int(duration_per_point * sample_rate)
    pcm = bytearray()
    
    # 阴阳音色参数
    if mode == 'yang':
        harmonic = 1.0        # 基频为主
        smooth = 1.0          # 无额外平滑
    else:  # yin
        harmonic = 0.5        # 弱化, 更虚
        smooth = 0.7          # 低通柔化
    
    prev_wx, prev_wy = 0.0, 0.0
    for i in range(len(orbit) - 1):
        z0, z1 = orbit[i], orbit[i+1]
        dx, dy = z1.real - z0.real, z1.imag - z0.imag
        mag = np.sqrt(dx*dx + dy*dy + 1e-12)
        dx_n, dy_n = dx/mag, dy/mag
        
        for j in range(samples_per_point):
            t = j / samples_per_point
            w = 0.5 - 0.5 * np.cos(2 * np.pi * t)  # Hann窗
            wx = dx_n * w * harmonic
            wy = dy_n * w * harmonic
            
            # 阴模式: 一阶低通(与前值混合)
            if mode == 'yin':
                wx = smooth * wx + (1-smooth) * prev_wx
                wy = smooth * wy + (1-smooth) * prev_wy
            prev_wx, prev_wy = wx, wy
            
            sl = int(np.clip(wx * volume, -32000, 32000))
            sr = int(np.clip(wy * volume, -32000, 32000))
            pcm.extend(struct.pack('<hh', sl, sr))
    
    return bytes(pcm)

def mix_yin_yang(pcm_yang, pcm_yin, ratio=0.5):
    """阴阳叠加混音: ratio=0纯阳, 1纯阴, 0.5太极平衡"""
    n = min(len(pcm_yang), len(pcm_yin))
    n -= n % 4  # 对齐到stereo帧
    mixed = bytearray()
    for i in range(0, n, 2):
        y = struct.unpack('<h', pcm_yang[i:i+2])[0]
        yi = struct.unpack('<h', pcm_yin[i:i+2])[0]
        m = int(np.clip(y*(1-ratio) + yi*ratio, -32000, 32000))
        mixed.extend(struct.pack('<h', m))
    return bytes(mixed)

def save_wav(pcm_data, filename, sample_rate=48000):
    path = os.path.join(tempfile.gettempdir(), filename)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return path

# ══════════ 主演示 ══════════
print("=" * 64)
print("DNA → 正逆Mandelbrot双引擎 → 阴阳音乐")
print("=" * 64)

gene_name = "BRCA1"
gene_location = "17右4"
print(f"\n基因: {gene_name} @ {gene_location} (DNA损伤修复)")

# DNA → c值 (阴阳使用各自的步长策略)
dna = gene_to_dna(gene_name, gene_location)
c_yang = dna_to_c_values(dna, step_scale=0.03)   # ☀正M: 原点附近, |c|≈0.04
c_yin  = dna_to_c_yin(dna, step_scale=0.05)      # ☽逆M: 远点, 1/c在主心形
print(f"DNA: {len(dna)}碱基 → 阳{c_yang[0].real:.3f}~{c_yang[-1].real:.3f}, 阴{c_yin[0].real:.1f}~{c_yin[-1].real:.1f}")

# 取中段c值生成阴阳双音轨
seg_yang = c_yang[len(c_yang)//2 : len(c_yang)//2 + 12]
seg_yin  = c_yin[len(c_yin)//2 : len(c_yin)//2 + 12]

yang_segs, yin_segs = [], []
print(f"\n{'c_yang':<22} {'1/c_yin':<22} {'阳轨道':<8} {'阴轨道':<8}")
print("-" * 64)
for c_yan, c_yi in zip(seg_yang, seg_yin):
    orb_y = orbit_yang(c_yan, max_iter=120)
    orb_yi = orbit_yin(c_yi, max_iter=120)
    
    ay = orbit_to_audio(orb_y, mode='yang', volume=6000)
    ayi = orbit_to_audio(orb_yi, mode='yin', volume=6000)
    if ay: yang_segs.append(ay)
    if ayi: yin_segs.append(ayi)
    
    c_yi_inv = complex_inv(c_yi)
    print(f"c_y=({c_yan.real:+.3f},{c_yan.imag:+.3f}) c_yi=({c_yi.real:+.2f},{c_yi.imag:+.2f})"
          f"  {len(orb_y):>3}步  {len(orb_yi):>3}步")

# 合成三个版本
yang_pcm = b''.join(yang_segs)
yin_pcm = b''.join(yin_segs)
taiji_pcm = mix_yin_yang(yang_pcm, yin_pcm, ratio=0.5)

ts = datetime.now().strftime("%H%M%S")
p_yang = save_wav(yang_pcm, f'dna_{gene_name}_阳_{ts}.wav')
p_yin = save_wav(yin_pcm, f'dna_{gene_name}_阴_{ts}.wav')
p_taiji = save_wav(taiji_pcm, f'dna_{gene_name}_太极_{ts}.wav')

print(f"\n{'='*64}")
print("生成三个版本:")
print(f"  ☀ 阳(正M z²+c):    {p_yang}")
print(f"  ☽ 阴(逆M z²+1/c):  {p_yin}")
print(f"  ☯ 太极(阴阳50/50): {p_taiji}")

# 依次播放
print(f"\n播放顺序: 阳 → 阴 → 太极")
for label, path in [('☀阳', p_yang), ('☽阴', p_yin), ('☯太极', p_taiji)]:
    print(f"  ▶ {label}...")
    winsound.PlaySound(path, winsound.SND_FILENAME)  # 同步播放
    time.sleep(0.3)

print(f"\n✅ 阴阳双引擎验证完成!")
print(f"   正M骨架确定→声音'实', 逆M复反演→声音'虚', 太极融合两者")
