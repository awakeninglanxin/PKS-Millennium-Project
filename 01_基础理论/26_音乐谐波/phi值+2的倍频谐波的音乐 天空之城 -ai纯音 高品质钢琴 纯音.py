import numpy as np
from scipy.io import wavfile
import math

# 参数设置
A4_freq = 432.01  # 使用标准A4=432.01Hz
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
    if harmonic_num == 0:
        return base_amplitude * 0.8

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

    attack_time = 0.02
    decay_time = min(0.3, duration * 0.3)
    release_time = min(0.5, duration * 0.5)

    attack_samples = int(attack_time * sample_rate)
    decay_samples = int(decay_time * sample_rate)
    release_samples = int(release_time * sample_rate)
    sustain_level = 0.3
    sustain_samples = length - attack_samples - decay_samples - release_samples

    if sustain_samples < 0:
        attack_samples = int(length * 0.1)
        decay_samples = int(length * 0.4)
        release_samples = length - attack_samples - decay_samples
        sustain_samples = 0
        sustain_level = 0.2

    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    if decay_samples > 0:
        envelope[attack_samples:attack_samples + decay_samples] = np.linspace(1, sustain_level, decay_samples)

    if sustain_samples > 0:
        envelope[attack_samples + decay_samples:attack_samples + decay_samples + sustain_samples] = sustain_level

    if release_samples > 0:
        release_start = attack_samples + decay_samples + sustain_samples
        x = np.linspace(0, 1, release_samples)
        release_curve = sustain_level * np.exp(-5 * x)
        envelope[release_start:release_start + release_samples] = release_curve

    return envelope


def generate_pure_piano_note(base_freq, duration, intensity=1.0, sample_rate=44100):
    """生成纯净钢琴音色的音符，无失谐效果"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # 动态调整谐波范围
    if base_freq < 200:
        octave_range = 3
        fib_range = 4
    elif base_freq > 1000:
        octave_range = 2
        fib_range = 2
    else:
        octave_range = 3
        fib_range = 3

    # 第一部分：八度谐波
    octave_harmonics = []
    for k in range(-octave_range, octave_range + 1):
        harmonic_freq = base_freq * (2 ** k)
        amplitude = piano_like_octave_decay(k, octave_range, base_amplitude=intensity)
        octave_harmonics.append((amplitude, harmonic_freq, k, "octave"))

    # 第二部分：斐波那契谐波
    fibonacci_harmonics = []
    golden_ratio = 1.61803398875

    for h in range(-fib_range, fib_range + 1):
        if h == 0:
            harmonic_freq = base_freq
        else:
            # 使用黄金比例创建非整数倍频
            freq_multiplier = 1.0 + (golden_ratio - 1) * h * 0.15
            harmonic_freq = base_freq * freq_multiplier

        amplitude = piano_like_fibonacci_decay(h, base_amplitude=intensity * 0.6)
        fibonacci_harmonics.append((amplitude, harmonic_freq, h, "fibonacci"))

    # 合并谐波 - 移除所有失谐效果
    composite_signal = np.zeros_like(t)

    for amplitude, harmonic_freq, harmonic_num, harmonic_type in (octave_harmonics + fibonacci_harmonics):
        if 20 <= harmonic_freq <= 20000:
            # 纯净正弦波，无任何失谐或调制效果
            wave = np.sin(2 * np.pi * harmonic_freq * t)
            composite_signal += amplitude * wave

    # 应用钢琴ADSR包络
    envelope = piano_adsr_envelope(len(t), sample_rate, duration, intensity)
    note = composite_signal * envelope

    return note


def create_pure_piano_castle_in_the_sky():
    """创建纯净钢琴音色的天空之城主题曲"""
    audio_signal = np.array([], dtype=np.float32)

    print("生成纯净钢琴音色的天空之城主题曲...")
    print("优化特点:")
    print("- 移除所有失谐效果，音色更加纯净")
    print("- 保留双重谐波结构创意")
    print("- 钢琴般的谐波衰减特性")
    print("- 纯净正弦波，无任何调制效果")

    # 生成每个音符
    for i, (note_name, octave, duration_ratio, intensity) in enumerate(castle_in_the_sky_notes):
        freq = get_frequency_from_note(note_name, octave, A4_freq)
        duration = base_note_duration * duration_ratio

        print(f"音符 {i + 1}/{len(castle_in_the_sky_notes)}: {note_name}{octave} ({freq:.2f}Hz)")

        note_audio = generate_pure_piano_note(freq, duration, intensity, sample_rate)
        audio_signal = np.concatenate((audio_signal, note_audio))

        # 音符间隙
        if i < len(castle_in_the_sky_notes) - 1:
            gap_duration = 0.01
            gap = np.zeros(int(sample_rate * gap_duration))
            audio_signal = np.concatenate((audio_signal, gap))

    # 平滑淡入淡出
    fade_samples = int(0.3 * sample_rate)
    if len(audio_signal) > 2 * fade_samples:
        fade_in = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_samples))
        fade_out = 0.5 - 0.5 * np.cos(np.linspace(np.pi, 0, fade_samples))
        audio_signal[:fade_samples] *= fade_in
        audio_signal[-fade_samples:] *= fade_out

    # 归一化
    peak = np.max(np.abs(audio_signal))
    if peak > 0:
        audio_signal = audio_signal / peak * 0.8

    return audio_signal, sample_rate


def save_audio_to_wav(audio_signal, sample_rate, filename="pure_piano_castle_in_the_sky.wav"):
    """保存音频为WAV文件"""
    audio_int16 = (audio_signal * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, audio_int16)
    print(f"音频已保存为: {filename}")


def main():
    """主函数"""
    try:
        # 生成音乐
        audio_signal, sample_rate = create_pure_piano_castle_in_the_sky()

        # 保存为WAV文件
        filename = "pure_piano_castle_in_the_sky.wav"
        save_audio_to_wav(audio_signal, sample_rate, filename)

        print("\n纯净钢琴版天空之城生成完成！")
        print("主要改进:")
        print("1. 完全移除失谐效果，音色纯净")
        print("2. 使用纯净正弦波，无任何调制")
        print("3. 保留双重谐波结构创意")
        print("4. 钢琴般的谐波衰减特性")
        print("5. 标准A4=440Hz调音")

    except Exception as e:
        print(f"生成音乐时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
