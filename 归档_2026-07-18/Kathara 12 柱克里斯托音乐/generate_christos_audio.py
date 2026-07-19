#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kathara 12 柱克里斯托祈祷 · 光声音频生成器
============================================================
依据元宝对话「还原 Kathara 12 柱克里斯托祈祷」的参数还原实现:

  A) 12 柱标准元音序列 (音高 131Hz~392Hz, 元音 A/Sh/E/L)
  B) Christos 祈祷 Mandelbrot 轨道 Pad 底乐
     - Mandelbrot 轨道: c 从 -1.755 -> 0.25 (Feigenbaum 减速)
     - 双载波: 432Hz (左声道/EirA 银光阴脉) + 528Hz (右声道/ManA 金光阳脉)
  C) 每柱切换"叮"提示音; 7柱(心轮)停留8秒, 12柱(顶轮)停留12秒

生成三个 WAV:
  1. christos_prayer_pad.wav    纯 Pad 底乐 (自己唱诵叠上去)
  2. christos_prayer_full.wav   Pad + 12柱元音引导 + 叮提示 (完整版)
  3. kathara_12_tones.wav       纯 12 柱音高序列 (一轮, 学唱用)

用法:  python generate_christos_audio.py [分钟数(默认11)]
"""

import numpy as np
import wave, os, sys

SR = 44100                       # 采样率
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

# ── 12 柱数据: (频率Hz, 元音, 停留秒, 身体地标, 意图语) ──
PILLARS = [
    (131.0, 'A',  4, '尾骨尖',        '我锚定于此身'),
    (147.0, 'A',  4, '骶骨',          '我打开情绪体'),
    (165.0, 'A',  4, '腰椎3',         '我认领力量'),
    (185.0, 'Sh', 4, '心门(腰椎1)',   '我打开心门'),
    (196.0, 'A',  4, '肚脐',          '我表达真实'),
    (220.0, 'E',  4, '太阳神经丛',    '我选择我的路'),
    (247.0, 'E',  8, '心轮(胸骨柄)',  '我的心与源合一'),     # ★停留加倍
    (262.0, 'L',  4, '喉底',          '我的声音是真理'),
    (294.0, 'A',  4, '眉心',          '我看见更高视野'),
    (330.0, 'Sh', 4, '顶轮内',        '我接收指引'),
    (349.0, 'A',  4, '顶轮外一指',    '我与万物合一'),
    (392.0, 'L', 12, '头顶上一掌',    '我是，我永远是'),     # ★停留最长
]

# ── 元音谐波权重 (共振峰近似, 模拟人声音色) ──
VOWEL_HARM = {
    'A':  {1: 1.00, 2: 0.55, 3: 0.42, 4: 0.22, 5: 0.12},   # 开元音"啊", 明亮
    'E':  {1: 1.00, 2: 0.32, 3: 0.50, 4: 0.30, 5: 0.10},   # "诶", 前共振峰高
    'L':  {1: 1.00, 2: 0.60, 3: 0.22, 4: 0.10},            # 浊音"勒", 低沉
    'Sh': {1: 0.30, 2: 0.20, 3: 0.15},                     # 齿擦音, 主要靠噪声
}


def write_wav(path, stereo):
    """stereo: (N,2) float in [-1,1] -> 16bit PCM WAV"""
    data = np.clip(stereo, -1.0, 1.0)
    pcm = (data * 32767.0).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    mb = os.path.getsize(path) / 1024 / 1024
    print(f'  [写出] {os.path.basename(path)}  ({mb:.1f} MB)')


def smoothstep(x):
    return x * x * (3.0 - 2.0 * x)


def make_pad(dur):
    """Mandelbrot 轨道调制的双载波 Pad 底乐 (立体声: 左432 / 右528)"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    prog = t / dur

    # c(t): -1.755 -> 0.25, Feigenbaum 减速 (smoothstep 缓入缓出)
    ease = smoothstep(prog)
    c_t = -1.755 + (0.25 - (-1.755)) * ease

    # 控制率轨道特征 (200Hz), 再上采样, 避免逐样本迭代
    cr = 200
    nc = max(16, int(dur * cr))
    p = np.linspace(0.0, 1.0, nc)
    cc = -1.755 + (0.25 - (-1.755)) * smoothstep(p)
    zz = np.zeros(nc, dtype=np.complex128)
    orbit = np.zeros(nc)
    for _ in range(14):                       # 迭代取有界轨道特征
        zz = zz * zz + cc
        orbit += np.tanh(np.abs(zz))
    orbit /= 14.0
    k = np.ones(21) / 21.0
    orbit = np.convolve(orbit, k, mode='same')          # 平滑
    orbit = (orbit - orbit.min()) / (np.ptp(orbit) + 1e-9)
    mod = np.interp(np.linspace(0, nc - 1, n), np.arange(nc), orbit)

    # 慢颤音 + 轨道微失谐
    vib = 1.0 + 0.004 * np.sin(2 * np.pi * 0.12 * t)
    detune = 1.0 + 0.0035 * mod

    def carrier(base):
        inst_f = base * detune * vib
        phase = 2 * np.pi * np.cumsum(inst_f) / SR
        sig = np.zeros(n)
        for h, a in [(1, 1.0), (2, 0.32), (3, 0.16), (4, 0.07)]:
            sig += a * np.sin(h * phase)
        return sig

    left = carrier(432.0)      # EirA 银光 / 阴脉
    right = carrier(528.0)     # ManA 金光 / 阳脉

    # 轨道驱动的呼吸振幅 + 全局淡入淡出 (10秒)
    breath = 0.55 + 0.45 * mod
    fade = np.ones(n)
    fl = min(int(10 * SR), n // 2)
    fade[:fl] = np.linspace(0, 1, fl)
    fade[-fl:] = np.linspace(1, 0, fl)
    amp = breath * fade

    left *= amp
    right *= amp
    peak = max(np.abs(left).max(), np.abs(right).max(), 1e-9)
    scale = 0.5 / peak                        # 留 headroom
    return np.stack([left * scale, right * scale], axis=1)


def adsr(n, atk, dec, sus, rel):
    env = np.ones(n)
    a = int(atk * SR); d = int(dec * SR); r = int(rel * SR)
    a = min(a, n); 
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if d > 0 and a + d <= n:
        env[a:a + d] = np.linspace(1, sus, d)
    if a + d < n - r:
        env[a + d:n - r] = sus
    if r > 0:
        env[n - r:] = np.linspace(env[n - r - 1] if n - r - 1 >= 0 else sus, 0, r)
    return env


def tone_segment(freq, vowel, dur, prev_freq=None):
    """单柱元音音: 基频+共振峰谐波, 柱间大二度滑音, ADSR 包络"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = np.full(n, freq)
    if prev_freq is not None:
        gl = min(int(0.3 * SR), n)
        f[:gl] = np.linspace(prev_freq, freq, gl)      # 0.3秒滑音
    phase = 2 * np.pi * np.cumsum(f) / SR

    sig = np.zeros(n)
    for h, a in VOWEL_HARM[vowel].items():
        sig += a * np.sin(h * phase)

    if vowel == 'Sh':                                  # 齿擦: 叠高频带噪
        noise = np.random.randn(n)
        # 简单高通: 一阶差分近似
        noise = np.concatenate([[0], np.diff(noise)])
        sig += 0.5 * noise

    env = adsr(n, atk=0.15, dec=0.1, sus=0.82, rel=min(0.5, dur * 0.3))
    return sig * env


def ding(dur=0.6):
    """柱切换提示音: 高频钟声, 快速衰减"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = 1568.0                                        # G6
    sig = np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 2.01 * t)
    sig *= np.exp(-t * 6.0)
    return sig * 0.35


def make_guide_round(with_ding=True):
    """一轮 12 柱引导 (单声道信号), 返回 float 数组"""
    parts = []
    prev = None
    for freq, vowel, hold, _land, _intent in PILLARS:
        if with_ding:
            parts.append(ding(0.5))                    # 每柱前"叮"
        parts.append(tone_segment(freq, vowel, hold, prev))
        prev = freq
    return np.concatenate(parts)


def tile_to_length(sig, n):
    """把信号循环/裁剪到 n 长度"""
    if len(sig) >= n:
        return sig[:n]
    reps = int(np.ceil(n / len(sig)))
    return np.tile(sig, reps)[:n]


def main():
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 11.0
    dur = minutes * 60.0
    print(f'== Kathara 12柱克里斯托音频生成 ==  时长 {minutes:.1f} 分钟, SR={SR}')
    print(f'输出目录: {SCRIPT_DIR}')

    # 1) Pad 底乐
    print('[1/3] 生成 Mandelbrot 轨道 Pad 底乐 ...')
    pad = make_pad(dur)
    write_wav(os.path.join(SCRIPT_DIR, 'christos_prayer_pad.wav'), pad)

    # 2) 纯 12 柱音序 (一轮)
    print('[2/3] 生成 12 柱音高序列 (一轮, 学唱用) ...')
    one = make_guide_round(with_ding=True)
    one_st = np.stack([one, one], axis=1)
    peak = max(np.abs(one).max(), 1e-9)
    write_wav(os.path.join(SCRIPT_DIR, 'kathara_12_tones.wav'), one_st * (0.7 / peak))

    # 3) 完整版: Pad + 12柱引导循环 + 叮
    print('[3/3] 生成完整版 (Pad + 12柱引导 + 叮) ...')
    n = pad.shape[0]
    guide = tile_to_length(make_guide_round(with_ding=True), n)
    gp = max(np.abs(guide).max(), 1e-9)
    guide = guide * (0.6 / gp)                         # 引导音相对 Pad 的比例
    full = pad.copy()
    full[:, 0] += guide                                # 引导居中(双声道等量)
    full[:, 1] += guide
    peak = max(np.abs(full).max(), 1e-9)
    if peak > 0.98:
        full *= (0.98 / peak)                          # 防削波
    write_wav(os.path.join(SCRIPT_DIR, 'christos_prayer_full.wav'), full)

    print('== 完成! 3 个 WAV 已生成 ==')


if __name__ == '__main__':
    main()
