import math
import matplotlib.pyplot as plt
import numpy as np


def spring_decay_amplitude(k, k_factor=1.0, base_amplitude=1.0):
    """
    弹簧式指数衰减振幅计算
    参数:
    k: 谐波序号，0表示基频，正数表示倍频，负数表示分频
    k_factor: 衰减因子，控制衰减速度
    base_amplitude: 基频振幅
    """
    return base_amplitude * math.exp(-abs(k) * k_factor)


def demonstrate_spring_decay():
    """演示弹簧衰减算法"""
    # 测试不同的衰减因子
    k_factors = [0.3, 0.7, 1.2, 2.0]
    k_values = list(range(-4, 5))  # k从-4到4

    plt.figure(figsize=(12, 8))

    for i, k_factor in enumerate(k_factors):
        amplitudes = [spring_decay_amplitude(k, k_factor) for k in k_values]

        plt.subplot(2, 2, i + 1)
        plt.plot(k_values, amplitudes, 'o-', linewidth=2, markersize=8)
        plt.title(f'弹簧衰减 (k_factor = {k_factor})')
        plt.xlabel('谐波序号 k')
        plt.ylabel('振幅')
        plt.grid(True, alpha=0.3)

        # 标注关键点
        for k, amp in zip(k_values, amplitudes):
            plt.annotate(f'{amp:.3f}', (k, amp), textcoords="offset points",
                         xytext=(0, 10), ha='center', fontsize=9)

    plt.tight_layout()
    plt.show()


def calculate_frequency_ratio(k, base_freq):
    """计算谐波频率相对于基频的比率"""
    return 2 ** k  # 频率比率为2的k次方


def analyze_harmonic_relationships():
    """分析谐波关系"""
    base_freq = 440  # 以A4=440Hz为例

    print("谐波关系分析 (基频 = 440Hz):")
    print("k值\t频率比\t频率(Hz)\t相对于基频的距离\t振幅衰减")
    print("-" * 80)

    k_factors = [0.5, 1.0, 1.5]

    for k in range(-4, 5):
        freq_ratio = calculate_frequency_ratio(k, base_freq)
        freq = base_freq * freq_ratio
        distance_from_base = abs(k)  # 距离基频的"步数"

        print(f"\nk={k}:")
        print(f"  频率比率: {freq_ratio:.3f}x")
        print(f"  频率: {freq:.1f} Hz")
        print(f"  距离基频: {distance_from_base} 个八度")

        for k_factor in k_factors:
            amp = spring_decay_amplitude(k, k_factor)
            print(
                f"  k_factor={k_factor}: 振幅 = {amp:.4f} (衰减到基波的 {amp / spring_decay_amplitude(0, k_factor):.2%})")


def mathematical_analysis():
    """数学分析"""
    print("\n数学分析:")
    print("衰减函数: A(k) = exp(-|k| × k_factor)")
    print("其中:")
    print("  - k: 谐波序号 (0=基频, ±1=相邻八度, ±2=相隔两个八度, 等等)")
    print("  - k_factor: 衰减因子，控制衰减速度")
    print("  - |k|: 谐波与基频的绝对距离")

    print("\n关键特性:")
    print("1. 对称性: A(k) = A(-k)，分频和倍频对称衰减")
    print("2. 单调性: |k|越大，A(k)越小")
    print("3. 连续性: 函数在k=0处连续但不可导")
    print("4. 衰减速率: k_factor控制衰减快慢")

    print("\n衰减示例 (k_factor=1.0时):")
    for k in [0, 1, 2, 3, 4]:
        amp_ratio = spring_decay_amplitude(k, 1.0) / spring_decay_amplitude(0, 1.0)
        print(f"  距离基频{k}个八度: 振幅衰减到 {amp_ratio:.2%}")


def compare_decay_patterns():
    """比较不同衰减模式"""
    k_values = list(range(0, 5))  # 只看正半轴

    print("\n不同衰减模式比较:")
    print("距离基频的八度数 | 弹簧衰减 | 线性衰减 | 平方衰减")
    print("-" * 50)

    for k in k_values:
        spring_amp = spring_decay_amplitude(k, 1.0)
        linear_amp = 1.0 / (1 + k)  # 线性衰减
        square_amp = 1.0 / (1 + k ** 2)  # 平方衰减

        print(f"{k:^18} | {spring_amp:^8.3f} | {linear_amp:^8.3f} | {square_amp:^8.3f}")


if __name__ == "__main__":
    print("弹簧衰减振幅算法分析")
    print("=" * 50)

    # 分析谐波关系
    analyze_harmonic_relationships()

    # 数学分析
    mathematical_analysis()

    # 比较衰减模式
    compare_decay_patterns()

    # 如果需要绘图，取消注释下一行
    demonstrate_spring_decay()