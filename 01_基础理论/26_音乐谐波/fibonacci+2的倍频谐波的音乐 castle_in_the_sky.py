import numpy as np
from scipy.io import wavfile
import math

# 参数设置
A4_freq = 432.0  # A4基准频率
sample_rate = 44100
base_note_duration = 0.6  # 基础音符时长（秒）

# 天空之城更完整的简谱 (覆盖多个八度)
# 格式: (音符名称, 八度, 时长比例, 强度)
castle_in_the_sky_notes = [
    # 第一段
    ("A", 3, 1.5, 0.8), ("B", 3, 0.5, 0.8), ("C", 4, 0.5, 0.8), ("B", 3, 0.5, 0.8),
    ("C", 4, 0.5, 0.8), ("B", 3, 0.5, 0.8), ("E", 4, 1.5, 0.9), ("C", 4, 0.5, 0.8),
    ("B", 3, 0.5, 0.8), ("C", 4, 0.5, 0.8), ("B", 3, 0.5, 0.8), ("C", 4, 0.5, 0.8),
    ("G", 4, 0.5, 0.8), ("F", 4, 0.5, 0.8), ("E", 4, 0.5, 0.8), ("D", 4, 0.5, 0.8),
    ("C", 4, 0.5, 0.8), ("B", 3, 0.5, 0.8), ("A", 3, 2.0, 1.0),

    # 第二段 (高八度)
    ("A", 4, 1.5, 0.8), ("B", 4, 0.5, 0.8), ("C", 5, 0.5, 0.8), ("B", 4, 0.5, 0.8),
    ("C", 5, 0.5, 0.8), ("B", 4, 0.5, 0.8), ("E", 5, 1.5, 0.9), ("C", 5, 0.5, 0.8),
    ("B", 4, 0.5, 0.8), ("C", 5, 0.5, 0.8), ("B", 4, 0.5, 0.8), ("C", 5, 0.5, 0.8),
    ("G", 5, 0.5, 0.8), ("F", 5, 0.5, 0.8), ("E", 5, 0.5, 0.8), ("D", 5, 0.5, 0.8),
    ("C", 5, 0.5, 0.8), ("B", 4, 0.5, 0.8), ("A", 4, 2.0, 1.0),

    # 第三段 (低音部分)
    ("A", 2, 1.0, 0.7), ("E", 3, 1.0, 0.7), ("A", 3, 1.0, 0.7), ("C", 4, 1.0, 0.7),
    ("E", 4, 1.0, 0.7), ("A", 4, 1.0, 0.7), ("C", 5, 1.0, 0.7), ("E", 5, 1.0, 0.7),

    # 第四段 (回到主旋律，添加和声)
    ("A", 3, 0.75, 0.8), ("C", 4, 0.75, 0.7), ("E", 4, 0.75, 0.7),  # A小调和弦
    ("A", 3, 0.75, 0.8), ("C", 4, 0.75, 0.7), ("E", 4, 0.75, 0.7),
    ("G", 3, 0.75, 0.8), ("B", 3, 0.75, 0.7), ("D", 4, 0.75, 0.7),  # G大调和弦
    ("G", 3, 0.75, 0.8), ("B", 3, 0.75, 0.7), ("D", 4, 0.75, 0.7),
    ("F", 3, 0.75, 0.8), ("A", 3, 0.75, 0.7), ("C", 4, 0.75, 0.7),  # F大调和弦
    ("F", 3, 0.75, 0.8), ("A", 3, 0.75, 0.7), ("C", 4, 0.75, 0.7),
    ("E", 3, 0.75, 0.8), ("G", 3, 0.75, 0.7), ("B", 3, 0.75, 0.7),  # E小调和弦
    ("E", 3, 0.75, 0.8), ("G", 3, 0.75, 0.7), ("B", 3, 0.75, 0.7),

    # 结尾
    ("A", 3, 3.0, 1.0), ("C", 4, 3.0, 0.7), ("E", 4, 3.0, 0.7)  # 长音结尾
]

# 音符名称到半音偏移的映射
note_to_offset = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
}


def get_frequency_from_note(note_name, octave, A4_freq=432.0):
    """根据音符名称和八度计算频率"""
    # A4是第9个音符，在八度4
    A4_note = 9
    A4_octave = 4

    # 计算相对于A4的半音偏移
    semitone_offset = (note_to_offset[note_name] - A4_note) + (octave - A4_octave) * 12

    # 计算频率
    return A4_freq * (2 ** (semitone_offset / 12))


def linear_decay_amplitude(k, harmonic_range=4, base_amplitude=1.0):
    """2^±k倍频的线性衰减振幅"""
    if harmonic_range == 0:
        return base_amplitude

    linear_factor = 1.0 - (abs(k) / harmonic_range) * 0.7
    return base_amplitude * max(0.3, linear_factor)


def fibonacci_exp_decay_amplitude(harmonic_num, k_factor=0.5, base_amplitude=1.0):
    """斐波那契谐波的指数衰减振幅（k因子=0.5）"""
    return base_amplitude * math.exp(-abs(harmonic_num) * k_factor)


def adsr_envelope(length, sample_rate, attack=0.1, decay=0.2, sustain=0.7, release=0.5):
    """生成ADSR包络"""
    envelope = np.zeros(length)

    attack_samples = int(attack * sample_rate)
    decay_samples = int(decay * sample_rate)
    release_samples = int(release * sample_rate)
    sustain_samples = length - attack_samples - decay_samples - release_samples

    if sustain_samples < 0:
        attack_samples = int(length * 0.1)
        decay_samples = int(length * 0.3)
        release_samples = length - attack_samples - decay_samples
        sustain_samples = 0

    # 起音阶段
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    # 衰减阶段
    if decay_samples > 0:
        envelope[attack_samples:attack_samples + decay_samples] = np.linspace(1, sustain, decay_samples)

    # 持续阶段
    if sustain_samples > 0:
        envelope[attack_samples + decay_samples:attack_samples + decay_samples + sustain_samples] = sustain

    # 释音阶段
    if release_samples > 0:
        release_start = attack_samples + decay_samples + sustain_samples
        envelope[release_start:release_start + release_samples] = np.linspace(sustain, 0, release_samples)

    return envelope


def generate_note_with_dual_harmonics(base_freq, duration, intensity=1.0, sample_rate=44100,
                                      octave_range=3, fib_harmonic_range=2):
    """生成带有双重谐波结构的音符"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # 第一部分：2^±k倍频谐波（线性衰减）
    octave_harmonics = []

    for k in range(-octave_range, octave_range + 1):
        harmonic_freq = base_freq * (2 ** k)
        amplitude = linear_decay_amplitude(k, octave_range, base_amplitude=intensity)
        octave_harmonics.append((amplitude, harmonic_freq, k, "octave"))

    # 第二部分：斐波那契谐波（指数衰减，k因子=0.5）
    fibonacci_harmonics = []

    # 使用黄金比例创建斐波那契相关的谐波
    golden_ratio = 1.61803398875

    for h in range(-fib_harmonic_range, fib_harmonic_range + 1):
        if h == 0:
            harmonic_freq = base_freq
        else:
            # 使用黄金比例的非整数倍频
            freq_multiplier = golden_ratio ** (h * 0.5)
            harmonic_freq = base_freq * freq_multiplier

        amplitude = fibonacci_exp_decay_amplitude(h, k_factor=0.5, base_amplitude=intensity * 0.8)
        fibonacci_harmonics.append((amplitude, harmonic_freq, h, "fibonacci"))

    # 合并所有谐波
    all_harmonics = octave_harmonics + fibonacci_harmonics

    # 生成合成信号
    composite_signal = np.zeros_like(t)
    harmonic_info = []

    for amplitude, harmonic_freq, harmonic_num, harmonic_type in all_harmonics:
        # 只添加频率在可听范围内的谐波
        if 20 <= harmonic_freq <= 20000:
            if harmonic_type == "octave":
                # 八度谐波使用纯净正弦波
                harmonic_wave = np.sin(2 * np.pi * harmonic_freq * t)
            else:
                # 斐波那契谐波添加轻微相位调制
                phase_mod = 0.1 * np.sin(2 * np.pi * 5 * t)
                harmonic_wave = np.sin(2 * np.pi * harmonic_freq * t + phase_mod)

            composite_signal += amplitude * harmonic_wave
            harmonic_info.append((harmonic_num, harmonic_freq, amplitude, harmonic_type))

    # 应用ADSR包络
    envelope = adsr_envelope(len(t), sample_rate)
    note = composite_signal * envelope

    return note, harmonic_info


def create_castle_in_the_sky():
    """创建更完整的天空之城音乐"""
    # 生成音频信号
    audio_signal = np.array([], dtype=np.float32)

    print("生成完整的天空之城音乐...")
    print("使用双重谐波结构:")
    print("- 2^±k倍频: 线性衰减")
    print("- 斐波那契谐波: 指数衰减 (k因子=0.5)")

    # 计算总时长
    total_duration = 0
    for note_name, octave, duration_ratio, intensity in castle_in_the_sky_notes:
        total_duration += base_note_duration * duration_ratio

    print(f"预计总时长: {total_duration:.2f}秒")

    # 生成每个音符
    for i, (note_name, octave, duration_ratio, intensity) in enumerate(castle_in_the_sky_notes):
        # 计算频率
        freq = get_frequency_from_note(note_name, octave, A4_freq)
        duration = base_note_duration * duration_ratio

        print(
            f"音符 {i + 1}/{len(castle_in_the_sky_notes)}: {note_name}{octave} ({freq:.2f}Hz), 时长: {duration:.2f}秒, 强度: {intensity}")

        # 生成音符
        note_audio, harmonic_info = generate_note_with_dual_harmonics(freq, duration, intensity, sample_rate)
        audio_signal = np.concatenate((audio_signal, note_audio))

        # 添加音符间的小间隙（除了和弦音符之间）
        if i < len(castle_in_the_sky_notes) - 1:
            next_note = castle_in_the_sky_notes[i + 1]
            # 如果是和弦的一部分，间隙更短
            if duration_ratio == next_note[2]:  # 相同时长可能是和弦
                gap_duration = 0.01  # 10毫秒短间隙
            else:
                gap_duration = 0.05  # 50毫秒正常间隙

            gap = np.zeros(int(sample_rate * gap_duration))
            audio_signal = np.concatenate((audio_signal, gap))

    # 添加淡入淡出效果
    fade_samples = int(0.5 * sample_rate)  # 更长的淡入淡出
    if len(audio_signal) > 2 * fade_samples:
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        audio_signal[:fade_samples] *= fade_in
        audio_signal[-fade_samples:] *= fade_out

    # 归一化音频信号
    peak = np.max(np.abs(audio_signal))
    if peak > 0:
        audio_signal = audio_signal / peak * 0.8  # 留一些动态余量

    return audio_signal, sample_rate


def save_audio_to_wav(audio_signal, sample_rate, filename="castle_in_the_sky_full.wav"):
    """保存音频为WAV文件"""
    audio_int16 = (audio_signal * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, audio_int16)
    print(f"音频已保存为: {filename}")


def print_music_info():
    """打印音乐信息"""
    print("\n=== 完整的天空之城音乐信息 ===")
    print(f"A4基准频率: {A4_freq}Hz")
    print(f"采样率: {sample_rate}Hz")
    print(f"音符数量: {len(castle_in_the_sky_notes)}")

    # 计算音域范围
    min_octave = min(note[1] for note in castle_in_the_sky_notes)
    max_octave = max(note[1] for note in castle_in_the_sky_notes)
    print(f"音域范围: 八度{min_octave}到八度{max_octave}")

    total_duration = 0
    for _, _, duration_ratio, _ in castle_in_the_sky_notes:
        total_duration += base_note_duration * duration_ratio

    print(f"总时长: {total_duration:.2f}秒")
    print("音乐结构:")
    print("- 第一段: 主旋律 (八度3-4)")
    print("- 第二段: 高音变奏 (八度4-5)")
    print("- 第三段: 低音进行 (八度2-5)")
    print("- 第四段: 和声进行 (和弦)")
    print("- 结尾: 长音结束")


def main():
    """主函数"""
    try:
        # 打印音乐信息
        print_music_info()

        # 生成音乐
        audio_signal, sample_rate = create_castle_in_the_sky()

        # 保存为WAV文件
        filename = "castle_in_the_sky_full_dual_harmonics.wav"
        save_audio_to_wav(audio_signal, sample_rate, filename)

        print("\n完整的天空之城音乐生成完成！")
        print("特点:")
        print("- 覆盖从八度2到八度5的广阔音域")
        print("- 包含主旋律、高音变奏、低音进行和和声部分")
        print("- 2^±k倍频采用线性衰减，产生清晰的和声")
        print("- 斐波那契谐波采用指数衰减(k因子=0.5)，创造丰富的音色")
        print("- 基于A4=432Hz的纯净调音")

    except Exception as e:
        print(f"生成音乐时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()