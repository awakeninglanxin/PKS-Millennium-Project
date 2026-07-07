import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


def analyze_market_fluctuations(prices, window_size=20):
    """
    分析市场波动的统计特性
    prices: 股票价格序列
    window_size: 滑动窗口大小
    """
    # 计算对数收益率
    returns = np.diff(np.log(prices))

    # 计算波动率
    volatility = np.array([np.std(returns[i:i + window_size])
                           for i in range(len(returns) - window_size)])

    # 计算间隔分布
    sorted_vols = np.sort(volatility)
    level_spacings = np.diff(sorted_vols)
    normalized_spacings = level_spacings / np.mean(level_spacings)

    # GUE理论分布
    def gue_distribution(s):
        return (32 / np.pi ** 2) * s ** 2 * np.exp(-4 * s ** 2 / np.pi)

    # 绘制结果
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # 波动率分布
    ax1.hist(volatility, bins=50, density=True, alpha=0.6, label='Observed')
    ax1.set_title('Volatility Distribution')
    ax1.set_xlabel('Volatility')
    ax1.set_ylabel('Density')
    ax1.grid(True)

    # 间隔分布与GUE对比
    s = np.linspace(0, 3, 100)
    gue = gue_distribution(s)

    ax2.hist(normalized_spacings, bins=50, density=True, alpha=0.6, label='Market Data')
    ax2.plot(s, gue, 'r-', label='GUE Distribution')
    ax2.set_title('Level Spacing Distribution vs GUE')
    ax2.set_xlabel('Normalized Spacing')
    ax2.set_ylabel('Density')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.show()

    # 计算Hurst指数
    def hurst_exponent(ts):
        lags = range(2, 20)
        tau = [np.std(np.subtract(ts[lag:], ts[:-lag])) for lag in lags]
        reg = np.polyfit(np.log(lags), np.log(tau), 1)
        return reg[0] / 2.0

    h = hurst_exponent(returns)
    print(f"Hurst Exponent: {h:.3f}")

    return volatility, normalized_spacings


# 生成示例数据（可以替换为实际股票数据）
np.random.seed(42)
n_days = 1000
prices = np.exp(np.random.randn(n_days).cumsum() * 0.02 + 4.5)

# 运行分析
volatility, spacings = analyze_market_fluctuations(prices)