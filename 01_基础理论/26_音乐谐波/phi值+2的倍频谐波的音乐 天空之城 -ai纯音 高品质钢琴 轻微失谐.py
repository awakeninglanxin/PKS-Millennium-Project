import numpy as np
from scipy.io import wavfile
import math

# 参数设置
A4_freq =432.01  # 使用标准A4=432.01Hz，更符合钢琴调音
sample_rate = 44100
base_note_duration = 0.5  # 基础音符时长（秒）

# 天空之城主题曲乐谱
castle_in_the_sky_notes = [
    # 主旋律部分
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


def get_frequency_from_note(note_name, octave, A4_freq=440.0):
    """根据音符名称和八度计算频率"""
    A4_note = 9
    A4_octave = 4
    semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12
    return A4_freq * (2 ** (semitone_offset / 12))


def piano_like_octave_decay(k, harmonic_range=4, base_amplitude=1.0):
    """钢琴般的八度谐波衰减"""
    if harmonic_range == 0:
        return base_amplitude

    # 钢琴音色特点：低次谐波强，高次谐波快速衰减
    if k == 0:  # 基频最强
        return base_amplitude
    elif abs(k) == 1:  # 第一八度较强
        return base_amplitude * 0.7
    elif abs(k) == 2:  # 第二八度中等
        return base_amplitude * 0.4
    else:  # 更高八度快速衰减
        return base_amplitude * 0.2


def piano_like_fibonacci_decay(harmonic_num, base_amplitude=1.0):
    """钢琴般的斐波那契谐波衰减"""
    # 钢琴音色特点：奇数谐波较强，偶数谐波较弱
    if harmonic_num == 0:
        return base_amplitude * 0.8  # 基频稍弱于八度谐波的基频

    # 钢琴的谐波衰减模式：前几个谐波较强，之后快速衰减
    if abs(harmonic_num) == 1:
        return base_amplitude * 0.6
    elif abs(harmonic_num) == 2:
        return base_amplitude * 0.4
    elif abs(harmonic_num) == 3:
        return base_amplitude * 0.25
    else:
        return base_amplitude * 0.15


def piano_adsr_envelope(length, sample_rate, duration, intensity=1.0):
    """钢琴般的ADSR包络"""
    envelope = np.zeros(length)

    # 钢琴包络特点：快速起音，中等衰减，较长释音
    attack_time = 0.02  # 非常快的起音
    decay_time = min(0.3, duration * 0.3)  # 衰减时间与音符时长相关
    release_time = min(0.5, duration * 0.5)  # 释音时间

    attack_samples = int(attack_time * sample_rate)
    decay_samples = int(decay_time * sample_rate)
    release_samples = int(release_time * sample_rate)
    sustain_level = 0.3  # 较低的持续电平，模拟钢琴快速衰减
    sustain_samples = length - attack_samples - decay_samples - release_samples

    if sustain_samples < 0:
        # 调整参数以适应短音符
        attack_samples = int(length * 0.1)
        decay_samples = int(length * 0.4)
        release_samples = length - attack_samples - decay_samples
        sustain_samples = 0
        sustain_level = 0.2

    # 起音阶段 - 非常快速
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    # 衰减阶段 - 快速衰减到持续电平
    if decay_samples > 0:
        envelope[attack_samples:attack_samples + decay_samples] = np.linspace(1, sustain_level, decay_samples)

    # 持续阶段
    if sustain_samples > 0:
        envelope[attack_samples + decay_samples:attack_samples + decay_samples + sustain_samples] = sustain_level

    # 释音阶段 - 指数衰减
    if release_samples > 0:
        release_start = attack_samples + decay_samples + sustain_samples
        # 使用指数衰减模拟钢琴弦振动衰减
        x = np.linspace(0, 1, release_samples)
        release_curve = sustain_level * np.exp(-5 * x)
        envelope[release_start:release_start + release_samples] = release_curve

    return envelope


def generate_piano_like_note(base_freq, duration, intensity=1.0, sample_rate=44100):
    """生成钢琴般的音符，保留双重谐波结构"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # 动态调整谐波范围，基于基频
    if base_freq < 200:  # 低音区，需要更多谐波
        octave_range = 3
        fib_range = 4
    elif base_freq > 1000:  # 高音区，减少谐波避免刺耳
        octave_range = 2
        fib_range = 2
    else:  # 中音区
        octave_range = 3
        fib_range = 3

    # 第一部分：钢琴般的八度谐波
    octave_harmonics = []
    for k in range(-octave_range, octave_range + 1):
        harmonic_freq = base_freq * (2 ** k)
        amplitude = piano_like_octave_decay(k, octave_range, base_amplitude=intensity)
        octave_harmonics.append((amplitude, harmonic_freq, k, "octave"))

    # 第二部分：钢琴般的斐波那契谐波
    fibonacci_harmonics = []
    golden_ratio = 1.61803398875

    for h in range(-fib_range, fib_range + 1):
        if h == 0:
            harmonic_freq = base_freq
        else:
            # 使用黄金比例创建非整数倍频，模拟钢琴的非谐波成分
            # 钢琴的非整数倍谐波通常与琴弦刚度和边界条件有关
            freq_multiplier = 1.0 + (golden_ratio - 1) * h * 0.15
            harmonic_freq = base_freq * freq_multiplier

        amplitude = piano_like_fibonacci_decay(h, base_amplitude=intensity * 0.6)
        fibonacci_harmonics.append((amplitude, harmonic_freq, h, "fibonacci"))

    # 合并谐波
    composite_signal = np.zeros_like(t)

    # 添加微小的失谐效果，模拟真实钢琴的多弦共鸣
    detune_amount = 0.001  # 0.1%的失谐

    for amplitude, harmonic_freq, harmonic_num, harmonic_type in (octave_harmonics + fibonacci_harmonics):
        if 20 <= harmonic_freq <= 20000:
            # 为不同谐波添加微小失谐，增加丰富度
            detuned_freq = harmonic_freq * (1 + detune_amount * harmonic_num)

            # 纯净正弦波，无颤音
            wave = np.sin(2 * np.pi * detuned_freq * t)

            composite_signal += amplitude * wave

    # 应用钢琴般的ADSR包络
    envelope = piano_adsr_envelope(len(t), sample_rate, duration, intensity)
    note = composite_signal * envelope

    return note


def create_piano_like_castle_in_the_sky():
    """创建钢琴般的天空之城主题曲"""
    audio_signal = np.array([], dtype=np.float32)

    print("生成钢琴般的天空之城主题曲...")
    print("优化的双重谐波结构:")
    print("- 八度谐波: 钢琴般的衰减特性")
    print("- 斐波那契谐波: 模拟钢琴非整数倍谐波")
    print("- 钢琴ADSR包络: 快速起音，快速衰减")
    print("- 轻微失谐: 模拟多弦共鸣效果")

    # 生成每个音符
    for i, (note_name, octave, duration_ratio, intensity) in enumerate(castle_in_the_sky_notes):
        freq = get_frequency_from_note(note_name, octave, A4_freq)
        duration = base_note_duration * duration_ratio

        print(f"音符 {i + 1}/{len(castle_in_the_sky_notes)}: {note_name}{octave} ({freq:.2f}Hz)")

        note_audio = generate_piano_like_note(freq, duration, intensity, sample_rate)
        audio_signal = np.concatenate((audio_signal, note_audio))

        # 音符间隙 - 钢琴音符间有短暂重叠
        if i < len(castle_in_the_sky_notes) - 1:
            gap_duration = 0.01  # 10毫秒短间隙，模拟连奏效果
            gap = np.zeros(int(sample_rate * gap_duration))
            audio_signal = np.concatenate((audio_signal, gap))

    # 添加平滑的淡入淡出
    fade_samples = int(0.3 * sample_rate)
    if len(audio_signal) > 2 * fade_samples:
        # 使用余弦曲线平滑淡入淡出
        fade_in = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_samples))
        fade_out = 0.5 - 0.5 * np.cos(np.linspace(np.pi, 0, fade_samples))
        audio_signal[:fade_samples] *= fade_in
        audio_signal[-fade_samples:] *= fade_out

    # 添加轻微的整体混响效果（卷积模拟）
    reverb_samples = int(0.1 * sample_rate)  # 100ms混响
    reverb_env = np.exp(-np.linspace(0, 5, reverb_samples))  # 指数衰减
    reverb_signal = np.convolve(audio_signal, reverb_env, mode='same') * 0.3
    audio_signal = audio_signal + reverb_signal

    # 归一化
    peak = np.max(np.abs(audio_signal))
    if peak > 0:
        audio_signal = audio_signal / peak * 0.8

    return audio_signal, sample_rate


def save_audio_to_wav(audio_signal, sample_rate, filename="piano_like_castle_in_the_sky.wav"):
    """保存音频为WAV文件"""
    audio_int16 = (audio_signal * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, audio_int16)
    print(f"音频已保存为: {filename}")


def analyze_piano_characteristics():
    """分析钢琴音色特性"""
    print("\n=== 钢琴音色特性分析 ===")
    print("八度谐波衰减模式 (模拟钢琴):")
    for k in range(-3, 4):
        amp = piano_like_octave_decay(k, 3)
        print(f"  k={k}: 振幅 = {amp:.4f}")

    print("\n斐波那契谐波衰减模式 (模拟钢琴非整数倍谐波):")
    for h in range(-3, 4):
        amp = piano_like_fibonacci_decay(h)
        print(f"  谐波指数={h}: 振幅 = {amp:.4f}")


def main():
    """主函数"""
    try:
        # 分析钢琴音色特性
        analyze_piano_characteristics()

        # 生成音乐
        audio_signal, sample_rate = create_piano_like_castle_in_the_sky()

        # 保存为WAV文件
        filename = "piano_like_castle_in_the_sky.wav"
        save_audio_to_wav(audio_signal, sample_rate, filename)

        print("\n钢琴版天空之城生成完成！")
        print("钢琴音色优化:")
        print("1. 钢琴般的谐波衰减特性")
        print("2. 快速起音、快速衰减的ADSR包络")
        print("3. 轻微失谐模拟多弦共鸣")
        print("4. 简单位置模拟混响效果")
        print("5. 保留双重谐波结构创意")

    except Exception as e:
        print(f"生成音乐时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()