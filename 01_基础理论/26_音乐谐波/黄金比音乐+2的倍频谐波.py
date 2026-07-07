import numpy as np
from scipy.io import wavfile
import math

# 参数设置
note_duration = 1.45 / 2  # 每个音符1.45秒/2
A4_freq = 432.0
fibonacci_count = 144
sample_rate = 44100


def generate_fibonacci_sequence(count=fibonacci_count):
    """生成Fibonacci数列"""
    fibonacci = [1, 1]
    for i in range(2, count):
        fibonacci.append(fibonacci[i - 1] + fibonacci[i - 2])
    return fibonacci


def calculate_frequency_from_semitone(semitone_offset, A4_freq=432.0):
    """根据半音偏移量计算频率"""
    A0_freq = A4_freq / 16
    return A0_freq * (2 ** (semitone_offset / 12.0))


def adsr_envelope(length, sample_rate, attack=0.02, decay=0.2, sustain=0.6, release=0.8):
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
        envelope[:attack_samples] = 1 - np.exp(-5 * np.linspace(0, 1, attack_samples))

    # 衰减阶段
    if decay_samples > 0:
        decay_curve = 1 - (1 - sustain) * (1 - np.exp(-3 * np.linspace(0, 1, decay_samples)))
        envelope[attack_samples:attack_samples + decay_samples] = decay_curve

    # 持续阶段
    if sustain_samples > 0:
        envelope[attack_samples + decay_samples:attack_samples + decay_samples + sustain_samples] = sustain

    # 释音阶段
    if release_samples > 0:
        release_start = attack_samples + decay_samples + sustain_samples
        release_curve = sustain * np.exp(-5 * np.linspace(0, 1, release_samples))
        envelope[release_start:release_start + release_samples] = release_curve

    return envelope


def linear_decay_amplitude(k, harmonic_range=4, base_amplitude=1.0):
    """2^±k倍频的线性衰减振幅"""
    # 线性衰减: 距离基频越远的谐波振幅越小
    # 中心(k=0)振幅最大，向两边线性减小
    if harmonic_range == 0:
        return base_amplitude

    linear_factor = 1.0 - (abs(k) / harmonic_range) * 0.7  # 最大衰减到30%
    return base_amplitude * max(0.3, linear_factor)  # 确保不小于30%


def fibonacci_exp_decay_amplitude(fib_num, harmonic_num, k_factor=0.5, base_amplitude=1.0):
    """斐波那契谐波的指数衰减振幅（k因子=0.5）"""
    # 使用斐波那契数的特性来影响衰减
    fib_factor = math.log(fib_num + 1) / math.log(144)  # 归一化到0-1范围

    # 指数衰减公式: A = base_amplitude * exp(-|harmonic_num| * k_factor)
    exp_decay = math.exp(-abs(harmonic_num) * k_factor)

    # 结合斐波那契因子，使大数产生更丰富的谐波
    fibonacci_enhancement = 1.0 + fib_factor * 0.5  # 增强0%-50%

    return base_amplitude * exp_decay * fibonacci_enhancement


def generate_note_with_dual_harmonics(base_freq, fib_num, duration, sample_rate=44100,
                                      octave_range=4, fib_harmonic_range=4):
    """生成带有双重谐波结构的音符"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # 第一部分：2^±k倍频谐波（线性衰减）
    octave_harmonics = []
    octave_count = 2 * octave_range + 1

    for k in range(-octave_range, octave_range + 1):
        harmonic_freq = base_freq * (2 ** k)
        amplitude = linear_decay_amplitude(k, octave_range)
        octave_harmonics.append((amplitude, harmonic_freq, k, "octave"))

    # 第二部分：斐波那契谐波（指数衰减，k因子=0.5）
    fibonacci_harmonics = []

    # 生成基于斐波那契数的谐波系列
    # 使用斐波那契数本身来生成谐波频率偏移
    fib_factor = (fib_num % 12) / 12.0  # 使用模12得到半音偏移因子

    for h in range(-fib_harmonic_range, fib_harmonic_range + 1):
        if h == 0:
            # 基频保持不变
            harmonic_freq = base_freq
        else:
            # 创建基于斐波那契数的频率偏移
            # 使用黄金比例和斐波那契数来创建独特的谐波关系
            golden_ratio = 1.61803398875
            fib_ratio = (fib_num % 8 + 1) / 8.0  # 归一化到0.125-1.0

            # 谐波频率 = 基频 * (黄金比例^h) * 斐波那契因子
            freq_multiplier = (golden_ratio ** h) * (1.0 + fib_ratio * 0.5)
            harmonic_freq = base_freq * freq_multiplier

        amplitude = fibonacci_exp_decay_amplitude(fib_num, h, k_factor=0.5)
        fibonacci_harmonics.append((amplitude, harmonic_freq, h, "fibonacci"))

    # 合并所有谐波
    all_harmonics = octave_harmonics + fibonacci_harmonics

    # 生成合成信号
    composite_signal = np.zeros_like(t)
    harmonic_info = []

    for amplitude, harmonic_freq, harmonic_num, harmonic_type in all_harmonics:
        # 只添加频率在可听范围内的谐波
        if 20 <= harmonic_freq <= 20000:
            # 为不同类型的谐波添加不同的音色特性
            if harmonic_type == "octave":
                # 八度谐波使用纯净正弦波
                harmonic_wave = np.sin(2 * np.pi * harmonic_freq * t)
            else:
                # 斐波那契谐波添加轻微失真，创造更丰富的音色
                raw_wave = np.sin(2 * np.pi * harmonic_freq * t)
                # 添加轻微的过驱动效果
                harmonic_wave = np.tanh(raw_wave * 1.5) * 0.8

            composite_signal += amplitude * harmonic_wave
            harmonic_info.append((harmonic_num, harmonic_freq, amplitude, harmonic_type))

    # 应用ADSR包络
    envelope = adsr_envelope(len(t), sample_rate)
    note = composite_signal * envelope

    return note, harmonic_info


def create_fibonacci_music_with_dual_harmonics():
    """创建带有双重谐波结构的Fibonacci音乐"""
    # 生成Fibonacci数列
    fibonacci_sequence = generate_fibonacci_sequence(fibonacci_count)

    # 计算每个Fibonacci数字对应的频率
    frequencies = []
    for num in fibonacci_sequence:
        semitone_offset = num % 144
        freq = calculate_frequency_from_semitone(semitone_offset, A4_freq)
        frequencies.append(freq)

    # 生成音频信号
    audio_signal = np.array([], dtype=np.float32)
    all_harmonic_info = []

    print("生成带有双重谐波的Fibonacci音乐...")
    print("2^±k倍频: 线性衰减")
    print("斐波那契谐波: 指数衰减 (k因子=0.5)")

    for i, (freq, fib_num) in enumerate(zip(frequencies, fibonacci_sequence)):
        print(f"进度: {i + 1}/{len(frequencies)}, 基频: {freq:.2f} Hz, Fibonacci数: {fib_num}")

        # 生成音符（带有双重谐波结构）
        note, harmonic_info = generate_note_with_dual_harmonics(freq, fib_num, note_duration, sample_rate)
        audio_signal = np.concatenate((audio_signal, note))
        all_harmonic_info.append(harmonic_info)

    # 添加淡入淡出效果
    fade_samples = int(0.1 * sample_rate)
    if len(audio_signal) > 2 * fade_samples:
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        audio_signal[:fade_samples] *= fade_in
        audio_signal[-fade_samples:] *= fade_out

    # 归一化音频信号
    peak = np.max(np.abs(audio_signal))
    if peak > 0:
        audio_signal = audio_signal / peak

    return audio_signal, sample_rate, frequencies, all_harmonic_info, fibonacci_sequence


def save_audio_to_wav(audio_signal, sample_rate, filename="fibonacci_dual_harmonics.wav"):
    """保存音频为WAV文件"""
    audio_int16 = (audio_signal * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, audio_int16)
    print(f"音频已保存为: {filename}")


def print_harmonic_info(harmonic_info, base_freq, fib_num, note_index):
    """打印谐波信息"""
    print(f"\n音符 {note_index + 1} (基频: {base_freq:.2f} Hz, Fibonacci数: {fib_num})")
    print("类型\t谐波索引\t频率(Hz)\t振幅")
    print("-" * 60)

    octave_harmonics = [h for h in harmonic_info if h[3] == "octave"]
    fibonacci_harmonics = [h for h in harmonic_info if h[3] == "fibonacci"]

    print("八度谐波 (线性衰减):")
    for h_num, freq, amp, h_type in sorted(octave_harmonics, key=lambda x: x[0]):
        print(f"  {h_type}\t{h_num}\t\t{freq:.2f}\t\t{amp:.4f}")

    print("斐波那契谐波 (指数衰减, k=0.5):")
    for h_num, freq, amp, h_type in sorted(fibonacci_harmonics, key=lambda x: x[0]):
        print(f"  {h_type}\t{h_num}\t\t{freq:.2f}\t\t{amp:.4f}")


def test_decay_functions():
    """测试衰减函数"""
    print("线性衰减测试 (八度谐波):")
    for k in range(-4, 5):
        amp = linear_decay_amplitude(k, 4)
        print(f"  k={k}: 振幅 = {amp:.4f}")

    print("\n指数衰减测试 (斐波那契谐波, k因子=0.5):")
    fib_num = 89  # 示例斐波那契数
    for h in range(-4, 5):
        amp = fibonacci_exp_decay_amplitude(fib_num, h, 0.5)
        print(f"  谐波指数={h}: 振幅 = {amp:.4f}")


def main():
    """主函数"""
    try:
        # 测试衰减函数
        test_decay_functions()

        # 生成音乐
        audio_signal, sample_rate, frequencies, all_harmonic_info, fibonacci_sequence = create_fibonacci_music_with_dual_harmonics()

        # 显示前3个音符的谐波信息
        for i in range(min(3, len(all_harmonic_info))):
            print_harmonic_info(all_harmonic_info[i], frequencies[i], fibonacci_sequence[i], i)

        # 保存为WAV文件
        filename = "黄金比phi+2^k_dual_harmonics .wav"
        save_audio_to_wav(audio_signal, sample_rate, filename)

        print("\n音乐生成完成！")
        print("特点:")
        print("- 2^±k倍频采用线性衰减，产生平衡的八度和声")
        print("- 斐波那契谐波采用指数衰减(k因子=0.5)，产生丰富的音色变化")
        print("- 两种谐波系列同时存在，创造立体声场效果")

    except Exception as e:
        print(f"生成音乐时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()