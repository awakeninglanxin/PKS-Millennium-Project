import numpy as np
from scipy.io import wavfile
import math

# 参数设置
A4_freq = 432.0  # A4基准频率
sample_rate = 44100
base_note_duration = 0.5  # 基础音符时长（秒）

# 正确的天空之城主题曲乐谱（久石让作曲）
castle_in_the_sky_notes = [
    # 主旋律部分 - 天空之城经典主题
    ("E", 4, 1.0, 0.8), ("G", 4, 1.0, 0.8), ("C", 5, 2.0, 0.9), ("G", 4, 1.0, 0.8),
    ("E", 4, 1.0, 0.8), ("G", 4, 1.0, 0.8), ("C", 5, 2.0, 0.9), ("G", 4, 1.0, 0.8),
    ("D", 5, 1.0, 0.8), ("C", 5, 1.0, 0.8), ("G", 4, 1.0, 0.8), ("E", 4, 2.0, 0.9),
    ("D", 4, 1.0, 0.8), ("E", 4, 1.0, 0.8), ("G", 4, 1.0, 0.8), ("E", 4, 2.0, 0.9),

    # 第二段
    ("C", 5, 1.0, 0.8), ("G", 4, 1.0, 0.8), ("E", 4, 1.0, 0.8), ("G", 4, 1.0, 0.8),
    ("C", 5, 2.0, 0.9), ("G", 4, 1.0, 0.8), ("E", 4, 1.0, 0.8), ("G", 4, 1.0, 0.8),
    ("C", 5, 2.0, 0.9), ("B", 4, 1.0, 0.8), ("G", 4, 1.0, 0.8), ("E", 4, 2.0, 0.9),

    # 高潮部分
    ("E", 5, 1.0, 1.0), ("D", 5, 0.5, 0.9), ("C", 5, 0.5, 0.9), ("B", 4, 1.0, 0.9),
    ("G", 4, 1.0, 0.8), ("E", 4, 1.0, 0.8), ("G", 4, 2.0, 0.9),
    ("C", 5, 1.0, 0.9), ("B", 4, 0.5, 0.8), ("A", 4, 0.5, 0.8), ("G", 4, 2.0, 0.9),

    # 结尾
    ("E", 4, 3.0, 1.0), ("G", 4, 3.0, 0.8), ("C", 5, 3.0, 0.8)
]

# 音符名称到半音偏移的映射
note_to_offset = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
}


def get_frequency_from_note(note_name, octave, A4_freq=432.0):
    """根据音符名称和八度计算频率"""
    A4_note = 9
    A4_octave = 4
    semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12
    return A4_freq * (2 ** (semitone_offset / 12))


def improved_linear_decay_amplitude(k, harmonic_range=4, base_amplitude=1.0):
    """改进的2^±k倍频线性衰减振幅"""
    if harmonic_range == 0:
        return base_amplitude

    # 使用平方衰减，让中心谐波更突出
    distance_factor = abs(k) / harmonic_range
    linear_factor = 1.0 - (distance_factor ** 0.7) * 0.8  # 更平缓的衰减
    return base_amplitude * max(0.2, linear_factor)  # 最小保持20%振幅


def improved_fibonacci_decay_amplitude(harmonic_num, k_factor=0.5, base_amplitude=1.0, fib_enhance=0.3):
    """改进的斐波那契谐波衰减振幅"""
    # 基础指数衰减
    exp_decay = math.exp(-abs(harmonic_num) * k_factor)

    # 添加斐波那契增强：奇数谐波稍强，模拟自然谐波特性
    if harmonic_num % 2 == 1:  # 奇数谐波
        fib_enhancement = 1.0 + fib_enhance
    else:  # 偶数谐波
        fib_enhancement = 1.0 - fib_enhance * 0.5

    return base_amplitude * exp_decay * fib_enhancement


def natural_adsr_envelope(length, sample_rate, attack=0.08, decay=0.15, sustain=0.75, release=0.4):
    """更自然的ADSR包络"""
    envelope = np.zeros(length)

    attack_samples = int(attack * sample_rate)
    decay_samples = int(decay * sample_rate)
    release_samples = int(release * sample_rate)
    sustain_samples = length - attack_samples - decay_samples - release_samples

    if sustain_samples < 0:
        # 调整参数以适应短音符
        attack_samples = int(length * 0.15)
        decay_samples = int(length * 0.25)
        release_samples = length - attack_samples - decay_samples
        sustain_samples = 0

    # 使用更平滑的曲线
    if attack_samples > 0:
        # 指数攻击，更自然
        x = np.linspace(0, 1, attack_samples)
        envelope[:attack_samples] = 1 - np.exp(-5 * x)

    if decay_samples > 0:
        # 指数衰减到持续电平
        x = np.linspace(0, 1, decay_samples)
        decay_curve = sustain + (1 - sustain) * np.exp(-3 * x)
        envelope[attack_samples:attack_samples + decay_samples] = decay_curve

    if sustain_samples > 0:
        envelope[attack_samples + decay_samples:attack_samples + decay_samples + sustain_samples] = sustain

    if release_samples > 0:
        release_start = attack_samples + decay_samples + sustain_samples
        # 指数释音
        x = np.linspace(0, 1, release_samples)
        release_curve = sustain * np.exp(-4 * x)
        envelope[release_start:release_start + release_samples] = release_curve

    return envelope


def generate_note_with_improved_harmonics(base_freq, duration, intensity=1.0, sample_rate=44100):
    """生成改进的双重谐波结构音符（无颤音版本）"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # 动态调整谐波范围，基于基频
    if base_freq < 200:  # 低音区，需要更多谐波
        octave_range = 4
        fib_range = 3
    elif base_freq > 800:  # 高音区，减少谐波避免刺耳
        octave_range = 2
        fib_range = 1
    else:  # 中音区
        octave_range = 3
        fib_range = 2

    # 第一部分：改进的2^±k倍频谐波
    octave_harmonics = []
    for k in range(-octave_range, octave_range + 1):
        harmonic_freq = base_freq * (2 ** k)
        amplitude = improved_linear_decay_amplitude(k, octave_range, base_amplitude=intensity)
        octave_harmonics.append((amplitude, harmonic_freq, k, "octave"))

    # 第二部分：改进的斐波那契谐波
    fibonacci_harmonics = []
    golden_ratio = 1.61803398875

    for h in range(-fib_range, fib_range + 1):
        if h == 0:
            harmonic_freq = base_freq
        else:
            # 使用更自然的频率比例
            if abs(h) <= 2:
                # 近基频使用较小的倍数
                freq_multiplier = 1.0 + (golden_ratio - 1) * h * 0.3
            else:
                # 远基频使用较大的倍数但限制范围
                freq_multiplier = golden_ratio ** (h * 0.3)

            harmonic_freq = base_freq * freq_multiplier

        amplitude = improved_fibonacci_decay_amplitude(h, k_factor=0.5, base_amplitude=intensity * 0.7)
        fibonacci_harmonics.append((amplitude, harmonic_freq, h, "fibonacci"))

    # 合并谐波
    composite_signal = np.zeros_like(t)

    for amplitude, harmonic_freq, harmonic_num, harmonic_type in (octave_harmonics + fibonacci_harmonics):
        if 20 <= harmonic_freq <= 20000:
            # 为不同谐波添加微小随机相位偏移，增加自然感
            phase_offset = harmonic_num * 0.1  # 基于谐波序号的相位偏移

            # 消除颤音和相位调制，使用纯净正弦波
            wave = np.sin(2 * np.pi * harmonic_freq * t + phase_offset)

            composite_signal += amplitude * wave

    # 应用改进的ADSR包络
    envelope = natural_adsr_envelope(len(t), sample_rate)
    note = composite_signal * envelope

    return note

def create_improved_castle_in_the_sky():
    """创建改进的天空之城主题曲"""
    audio_signal = np.array([], dtype=np.float32)

    print("生成改进的天空之城主题曲...")
    print("改进的双重谐波结构:")
    print("- 2^±k倍频: 改进的平方衰减，更平缓自然")
    print("- 斐波那契谐波: 奇数谐波增强，更接近自然乐器")
    print("- 动态谐波范围: 根据基频调整谐波数量")
    print("- 自然ADSR包络: 指数曲线，更平滑的过渡")

    # 生成每个音符
    for i, (note_name, octave, duration_ratio, intensity) in enumerate(castle_in_the_sky_notes):
        freq = get_frequency_from_note(note_name, octave, A4_freq)
        duration = base_note_duration * duration_ratio

        print(f"音符 {i + 1}/{len(castle_in_the_sky_notes)}: {note_name}{octave} ({freq:.2f}Hz)")

        note_audio = generate_note_with_improved_harmonics(freq, duration, intensity, sample_rate)
        audio_signal = np.concatenate((audio_signal, note_audio))

        # 音符间隙
        if i < len(castle_in_the_sky_notes) - 1:
            gap_duration = 0.02  # 20毫秒间隙
            gap = np.zeros(int(sample_rate * gap_duration))
            audio_signal = np.concatenate((audio_signal, gap))

    # 改进的淡入淡出
    fade_samples = int(0.4 * sample_rate)
    if len(audio_signal) > 2 * fade_samples:
        # 使用更平滑的S曲线淡入淡出
        fade_in = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_samples))
        fade_out = 0.5 - 0.5 * np.cos(np.linspace(np.pi, 0, fade_samples))
        audio_signal[:fade_samples] *= fade_in
        audio_signal[-fade_samples:] *= fade_out

    # 归一化
    peak = np.max(np.abs(audio_signal))
    if peak > 0:
        audio_signal = audio_signal / peak * 0.8

    return audio_signal, sample_rate


def save_audio_to_wav(audio_signal, sample_rate, filename="improved_castle_in_the_sky.wav"):
    """保存音频为WAV文件"""
    audio_int16 = (audio_signal * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, audio_int16)
    print(f"音频已保存为: {filename}")


def analyze_harmonic_structure():
    """分析谐波结构"""
    print("\n=== 改进的谐波结构分析 ===")
    print("2^±k倍频谐波 (改进线性衰减):")
    for k in range(-3, 4):
        amp = improved_linear_decay_amplitude(k, 3)
        print(f"  k={k}: 振幅 = {amp:.4f} (原线性衰减: {max(0.3, 1.0 - abs(k) / 3 * 0.7):.4f})")

    print("\n斐波那契谐波 (改进指数衰减):")
    for h in range(-2, 3):
        amp = improved_fibonacci_decay_amplitude(h, 0.5)
        print(f"  谐波指数={h}: 振幅 = {amp:.4f} (原指数衰减: {math.exp(-abs(h) * 0.5):.4f})")


def main():
    """主函数"""
    try:
        # 分析谐波结构
        analyze_harmonic_structure()

        # 生成音乐
        audio_signal, sample_rate = create_improved_castle_in_the_sky()

        # 保存为WAV文件
        filename = "improved_castle_in_the_sky.wav"
        save_audio_to_wav(audio_signal, sample_rate, filename)

        print("\n改进版天空之城生成完成！")
        print("主要改进:")
        print("1. 更自然的振幅衰减曲线")
        print("2. 动态谐波范围（基于基频）")
        print("3. 奇数谐波增强（模拟真实乐器）")
        print("4. 改进的ADSR包络")
        print("5. 添加轻微相位调制增加自然感")

    except Exception as e:
        print(f"生成音乐时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
