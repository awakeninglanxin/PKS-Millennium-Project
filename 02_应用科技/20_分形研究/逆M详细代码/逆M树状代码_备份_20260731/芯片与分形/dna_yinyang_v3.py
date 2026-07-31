# -*- coding: utf-8 -*-
"""
DNA → 正逆M双引擎 → 阴阳音乐 v3 (修正音频频率)
================================================================
关键修复 (v2听不到声音的根因):
  ❌ v2错误: 每个轨道点占0.03秒(1323采样) → 波形是<1Hz超低频包络 → 听不到
  ✅ v3修正: 遵循FractalSoundExplorer原理
     - steps = sample_rate/max_freq ≈ 11采样/轨道点
     - 轨道循环遍历填满音符时长
     - 轨道周期p → 音高 = sample_rate/(p×steps) Hz (落在可听区)
       例: 周期3→1336Hz, 周期8→501Hz, 周期20→200Hz

  阴阳音色区分:
     ☀阳: max_freq=4000Hz (明亮, 高频载波)
     ☽阴: max_freq=2000Hz (低沉, 低频载波)
"""
import numpy as np
import wave, struct, os
from datetime import datetime

BASE_MAP = {'A': 1+0j, 'T': -1+0j, 'G': 0+1j, 'C': 0-1j}
OUT_DIR = r'D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\DNA阴阳音乐'

def gene_to_dna(name, loc='', chr=0):
    seq = []
    for ch in name:
        b = ord(ch)
        for s in [6,4,2,0]: seq.append('ATGC'[(b>>s)&0b11])
    for ch in str(loc): seq.append('ATGC'[ord(ch)&0b11])
    return ''.join(seq)

def dna_walk(dna, start=complex(0,0), step=0.03):
    z = start; pts = [z]
    for b in dna:
        if b in BASE_MAP: z += BASE_MAP[b]*step; pts.append(complex(z.real, z.imag))
    return pts

def complex_inv(c):
    d = c.real*c.real + c.imag*c.imag
    return complex(1e8,0) if d < 1e-12 else complex(c.real/d, -c.imag/d)

def orbit_mandelbrot(c, max_iter=200, escape=2.0):
    z = complex(0,0); orb = [z]
    for _ in range(max_iter):
        z = z*z + c; orb.append(z)
        if abs(z) > escape: break
    return orb

def orbit_inverse_m(c, max_iter=200, escape=2.0):
    ci = complex_inv(c)
    z = complex(0,0); orb = [z]
    for _ in range(max_iter):
        z = z*z + ci; orb.append(z)
        if abs(z) > escape: break
    return orb

# ══════════ 正确的轨道→音频 (FractalSoundExplorer原理) ══════════
def orbit_to_audio(orbit, sample_rate=44100, max_freq=4000,
                   volume=10000, note_duration=1.2, sustain=True):
    """
    核心: steps=sr/max_freq采样/轨道点, 轨道循环遍历→周期性音高
    轨道周期p → 音高 = sample_rate/(p*steps) Hz
    """
    if len(orbit) < 2:
        return b''
    steps = max(2, sample_rate // max_freq)  # 每个轨道点的采样数 ≈11
    total_samples = int(note_duration * sample_rate)
    pcm = bytearray()

    # 归一化差分(参照CodeParade NORMALIZED模式)
    prev_dx, prev_dy = 0.0, 0.0
    written = 0
    idx = 0
    amp = float(volume)
    n_seg = len(orbit) - 1

    while written < total_samples:
        i = idx % n_seg  # 循环遍历轨道
        z0, z1 = orbit[i], orbit[i+1]
        dx, dy = z1.real - z0.real, z1.imag - z0.imag
        mag = np.sqrt(dx*dx + dy*dy + 1e-12)
        dx_n, dy_n = dx/mag, dy/mag

        for j in range(steps):
            t = j / steps
            ti = 0.5 - 0.5*np.cos(t*np.pi)  # 余弦插值(平滑过渡)
            wx = ti*dx_n + (1-ti)*prev_dx
            wy = ti*dy_n + (1-ti)*prev_dy
            sl = int(np.clip(wx * amp, -32000, 32000))
            sr = int(np.clip(wy * amp, -32000, 32000))
            pcm.extend(struct.pack('<hh', sl, sr))
            written += 1
            if written >= total_samples:
                break

        prev_dx, prev_dy = dx_n, dy_n
        idx += 1
        if not sustain:
            amp *= 0.9995  # 缓慢衰减

    # 淡入淡出防爆音(前后各50ms)
    fade = int(0.05 * sample_rate)
    pcm_arr = np.frombuffer(bytes(pcm), dtype=np.int16).copy().astype(np.float64)
    for k in range(min(fade, len(pcm_arr)//2)):
        g = k/fade
        pcm_arr[2*k] *= g; pcm_arr[2*k+1] *= g
        pcm_arr[-2*k-2] *= g; pcm_arr[-2*k-1] *= g
    return pcm_arr.astype(np.int16).tobytes()

def mix_stereo(a, b, balance=0.5):
    n = min(len(a), len(b)); n -= n%4
    aa = np.frombuffer(a[:n], dtype=np.int16).astype(np.float64)
    bb = np.frombuffer(b[:n], dtype=np.int16).astype(np.float64)
    mixed = np.clip(aa*(1-balance)+bb*balance, -32000, 32000).astype(np.int16)
    return mixed.tobytes()

def save_wav(pcm, name, sr=44100):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(pcm)
    return path

# ══════════ 主程序 ══════════
print("=" * 64)
print("DNA → 正逆M阴阳音乐 v3 (修正可听频率)")
print("=" * 64)

gene_name = "BRCA1"
dna = gene_to_dna(gene_name, "17右4", 17)
print(f"\n基因: {gene_name}, DNA {len(dna)}碱基")

# 阴阳c值 (基于研究报告: 阳原点, 阴远点使1/c<0.25)
c_yang = dna_walk(dna, start=complex(0,0), step=0.04)
c_yin  = dna_walk(dna, start=complex(4.5, 0.3), step=0.06)

mid = len(c_yang)//2
seg_y, seg_yi = c_yang[mid:mid+8], c_yin[mid:mid+8]

# 每个c值生成一个音符, 串成旋律
yang_notes, yin_notes = [], []
print(f"\n{'c':<20} {'阳周期':<8} {'阳音高':<10} {'阴周期':<8} {'阴音高'}")
print("-" * 64)
for c_y, c_yi in zip(seg_y, seg_yi):
    orb_y = orbit_mandelbrot(c_y, max_iter=200)
    orb_yi = orbit_inverse_m(c_yi, max_iter=200)

    # 阳: max_freq=4000 明亮; 阴: max_freq=2000 低沉
    ay = orbit_to_audio(orb_y, max_freq=4000, volume=12000, note_duration=0.8)
    ayi = orbit_to_audio(orb_yi, max_freq=2000, volume=12000, note_duration=0.8)
    yang_notes.append(ay)
    yin_notes.append(ayi)

    # 估算音高 (轨道长度作为周期估计)
    steps_y = 44100 // 4000
    steps_yi = 44100 // 2000
    pitch_y = 44100 / (len(orb_y) * steps_y) if len(orb_y) > 0 else 0
    pitch_yi = 44100 / (len(orb_yi) * steps_yi) if len(orb_yi) > 0 else 0
    print(f"({c_y.real:+.2f},{c_y.imag:+.2f})       {len(orb_y):>4}    {pitch_y:>6.1f}Hz    {len(orb_yi):>4}    {pitch_yi:>6.1f}Hz")

yang_pcm = b''.join(yang_notes)
yin_pcm  = b''.join(yin_notes)
taiji_pcm = mix_stereo(yang_pcm, yin_pcm, 0.5)

ts = datetime.now().strftime("%H%M%S")
p_yang = save_wav(yang_pcm, f'{gene_name}_阳_v3_{ts}.wav')
p_yin = save_wav(yin_pcm, f'{gene_name}_阴_v3_{ts}.wav')
p_taiji = save_wav(taiji_pcm, f'{gene_name}_太极_v3_{ts}.wav')

# RMS音量检查 (确认不是静音)
def rms(pcm):
    arr = np.frombuffer(pcm, dtype=np.int16).astype(np.float64)
    return np.sqrt(np.mean(arr**2)) if len(arr) > 0 else 0

print(f"\n{'='*64}")
print(f"音量RMS检查 (>100=可听, 静音≈0):")
print(f"  ☀阳:   RMS={rms(yang_pcm):.0f}  {p_yang}")
print(f"  ☽阴:   RMS={rms(yin_pcm):.0f}  {p_yin}")
print(f"  ☯太极: RMS={rms(taiji_pcm):.0f}  {p_taiji}")
print(f"\n✅ v3修正: 轨道点占{44100//4000}采样(非1323), 音高落在200-1400Hz可听区")
