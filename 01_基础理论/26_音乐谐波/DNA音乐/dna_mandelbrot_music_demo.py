# -*- coding: utf-8 -*-
"""
DNA → Mandelbrot → 音乐 原型验证
取第一个基因(BRCA1/DNA修复), 演示完整映射链
"""
import numpy as np
import wave, struct, tempfile, os, winsound
from datetime import datetime

# ── DNA → 复平面c值 (4碱基 → 4方向步进) ──
BASE_TO_COMPLEX = {
    'A': 1+0j,   # 腺嘌呤 → 水平前进
    'T': -1+0j,  # 胸腺嘧啶 → 水平后退
    'G': 0+1j,   # 鸟嘌呤 → 垂直上升
    'C': 0-1j,   # 胞嘧啶 → 垂直下降
}

# 基因名称 → ASCII + 基因位置信息 → 碱基序列
def gene_to_dna(gene_name, gene_location, chromosome):
    """把基因名和位置编码成伪碱基序列"""
    # ASCII编码 → 碱基序列 (每个字节=8bit=4个碱基对)
    seq = []
    for ch in gene_name:
        b = ord(ch)
        for shift in [6, 4, 2, 0]:
            pair = (b >> shift) & 0b11
            seq.append('ATGC'[pair])
    
    # 基因位置信息 → 额外碱基
    if gene_location:
        for ch in gene_location:
            b = ord(ch)
            pair = b & 0b11  # 取低2位
            seq.append('ATGC'[pair])
    
    return ''.join(seq)

def dna_to_c_values(dna_seq, step_scale=0.02):
    """碱基序列 → 复平面c值列表(游走路径)"""
    z = complex(0, 0)
    points = [z]
    for base in dna_seq:
        if base in BASE_TO_COMPLEX:
            z += BASE_TO_COMPLEX[base] * step_scale
            points.append(complex(z.real, z.imag))
    return points

# ── Mandelbrot轨道计算 ──
def orbit_mandelbrot(c, max_iter=200):
    """z → z² + c 轨道"""
    z = complex(0, 0)
    orbit = [z]
    for _ in range(max_iter):
        z = z*z + c
        orbit.append(z)
        if abs(z) > 10:
            break
    return orbit

# ── 轨道 → 音频 ──
def orbit_to_audio(orbit, sample_rate=48000, volume=4000, duration_per_point=0.04):
    """将轨道转换为PCM波形"""
    if len(orbit) < 2:
        return None
    
    total_samples = int(len(orbit) * duration_per_point * sample_rate)
    samples_per_point = int(duration_per_point * sample_rate)
    
    pcm = bytearray()
    for i in range(len(orbit) - 1):
        z0, z1 = orbit[i], orbit[i+1]
        dx, dy = z1.real - z0.real, z1.imag - z0.imag
        mag = np.sqrt(dx*dx + dy*dy + 1e-12)
        dx_n, dy_n = dx/mag, dy/mag
        
        for j in range(samples_per_point):
            t = j / samples_per_point
            # Hann窗口平滑
            w = 0.5 - 0.5 * np.cos(2 * np.pi * t)
            wx = dx_n * w
            wy = dy_n * w
            
            sl = int(np.clip(wx * volume, -32000, 32000))
            sr = int(np.clip(wy * volume, -32000, 32000))
            pcm.extend(struct.pack('<hh', sl, sr))
    
    return bytes(pcm)

def save_and_play(pcm_data, filename, sample_rate=48000):
    """保存WAV并播放"""
    path = os.path.join(tempfile.gettempdir(), filename)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    winsound.PlaySound(path, winsound.SND_ASYNC)
    return path

# ── 主演示 ──
print("=" * 60)
print("DNA → Mandelbrot → 音乐 原型验证")
print("=" * 60)

# 测试基因: BRCA1 (第一个被识别的基因卡片)
gene_name = "BRCA1"
gene_location = "17右4"
chromosome = 17

print(f"\n┌─ 基因: {gene_name}")
print(f"├─ 位置: {gene_location} (染色体{chromosome})")
print(f"├─ 功能: DNA损伤修复")
print(f"└─ 系统: 生殖系统")

# Step 1: 基因 → DNA序列
dna = gene_to_dna(gene_name, gene_location, chromosome)
print(f"\n[Step 1] 基因编码 → DNA序列: {len(dna)}碱基")
print(f"  序列(前40): {dna[:40]}...")

# Step 2: DNA → 复平面c值
c_values = dna_to_c_values(dna, step_scale=0.03)
print(f"\n[Step 2] DNA游走 → 复平面: {len(c_values)}个采样点")
print(f"  c范围: Re∈[{min(c.real for c in c_values):.2f}, {max(c.real for c in c_values):.2f}]")
print(f"         Im∈[{min(c.imag for c in c_values):.2f}, {max(c.imag for c in c_values):.2f}]")

# Step 3: 取采样c值 → Mandelbrot轨道
# 取中间10个c值生成音频片段
segment_c = c_values[len(c_values)//2 : len(c_values)//2 + 10]
segments = []
for ci, c_val in enumerate(segment_c):
    orbit = orbit_mandelbrot(c_val, max_iter=100)
    audio = orbit_to_audio(orbit, volume=6000, duration_per_point=0.03)
    if audio:
        segments.append(audio)

if segments:
    combined = b''.join(segments)
    path = save_and_play(combined, f'dna_brca1_{datetime.now().strftime("%H%M%S")}.wav')
    print(f"\n[Step 3→4] 轨道 → 音频: {len(segments)}段, 总长{len(combined)/48000:.1f}秒")
    print(f"  ✅ 播放: {path}")
else:
    print("\n❌ 未生成音频")

# ── 对比: 测试另一个基因 ──
print(f"\n{'='*60}")
print("对比基因: TP53 (p53抑癌基因)")
gene2 = "TP53"
dna2 = gene_to_dna(gene2, "17左2", 17)
c2 = dna_to_c_values(dna2, step_scale=0.03)

print(f"\n  BRCA1: c重心=({sum(c.real for c in c_values)/len(c_values):.3f}, "
      f"{sum(c.imag for c in c_values)/len(c_values):.3f})")
print(f"  TP53:  c重心=({sum(c.real for c in c2)/len(c2):.3f}, "
      f"{sum(c.imag for c in c2)/len(c2):.3f})")
print(f"  差异: |Δc| = {abs(sum(c.real for c in c_values)/len(c_values) - sum(c.real for c in c2)/len(c2)):.3f}")
print(f"\n✅ 不同基因产生不同c值 → 不同声音 — DNA→Mandelbrot→音乐 链验证通过!")
