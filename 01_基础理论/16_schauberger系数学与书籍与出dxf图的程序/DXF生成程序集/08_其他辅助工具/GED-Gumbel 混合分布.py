import numpy as np
from scipy.special import gamma
import matplotlib.pyplot as plt

# 使用英文标签以避免字体警告
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Bitstream Vera Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


def ged_gumbel_pdf(x, mu=-1, a=1, b=1, p=2, beta=0.5, alpha=1, mixture_param=0.5):
    """
    GED-Gumbel混合分布的概率密度函数
    参数:
    x: 随机变量值或数组
    mu: GED部分的位置参数
    a, b: GED部分的尺度参数
    p: GED部分的形状参数
    alpha: Gumbel部分的尺度参数(控制分布的宽度)
    beta: Gumbel部分的位置参数(控制分布的中心)
    mixture_param: 混合参数(0-1)，控制GED和Gumbel的混合比例
                   mixture_param=0: 纯Gumbel分布
                   mixture_param=1: 纯GED分布

    返回:
    混合分布的概率密度值
    """
    # 计算GED部分的概率密度
    scale_factor = a * b
    ged_normalization = p / (2 * scale_factor * gamma(1 / p))
    ged_exponent = - (np.abs(x - mu) / scale_factor) ** p
    ged_pdf = ged_normalization * np.exp(ged_exponent)

    # 计算Gumbel部分的概率密度
    z = (x - beta) / alpha
    gumbel_pdf = (1 / alpha) * np.exp(-(z + np.exp(-z)))

    # 混合两部分
    return mixture_param * ged_pdf + (1 - mixture_param) * gumbel_pdf


# 示例使用
if __name__ == "__main__":
    # 生成x值范围
    x = np.linspace(-5, 10, 1000)

    # 默认参数值
    mu_default, a_default, b_default, p_default = -1, 1, 1, 2
    beta_default, alpha_default, mixture_default =-1, 1, 0.5

    # 构建参数信息字符串
    param_info = f"Parameters: μ={mu_default}, a={a_default}, b={b_default}, p={p_default}, β={beta_default}, α={alpha_default}"

    # 绘制不同混合参数的GED-Gumbel混合分布
    plt.figure(figsize=(12, 8))

    # 纯GED分布 (mixture_param=1)
    plt.plot(x, ged_gumbel_pdf(x, mixture_param=1), 'g-', linewidth=2, label='Pure GED (mixture=1.0)')

    # 纯Gumbel分布 (mixture_param=0)
    plt.plot(x, ged_gumbel_pdf(x, mixture_param=0), 'b-', linewidth=2, label='Pure Gumbel (mixture=0.0)')

    # 不同混合比例
    plt.plot(x, ged_gumbel_pdf(x, mixture_param=0.3), 'r--', linewidth=2, label='GED-Gumbel Mix (mixture=0.3)')
    plt.plot(x, ged_gumbel_pdf(x, mixture_param=0.7), 'm-.', linewidth=2, label='GED-Gumbel Mix (mixture=0.7)')

    # 调整GED参数的特殊情况
    plt.plot(x, ged_gumbel_pdf(x, p=0.5, mixture_param=0.5), 'c:', linewidth=3,
             label='GED(p=0.5)-Gumbel Mix (mixture=0.5)')

    plt.title(f'GED-Gumbel Mixture Distribution PDF\n{param_info}', fontsize=14)
    plt.xlabel('x')
    plt.ylabel('Probability Density f(x)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 保存图像
    plt.savefig('GED_Gumbel_mixture_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()

    # 计算并显示一些统计特性
    print("GED-Gumbel Mixture Distribution Characteristics:")
    print("- Combines the flexible shape characteristics of GED and extreme value characteristics of Gumbel")
    print("- Suitable for scenarios requiring handling of both regular data and extreme values")
    print("- Mixture parameter controls the weights of the two distributions")
    print("- Has applications in finance, climatology, and reliability engineering")
    print("\nParameter Explanation:")
    print(f"- GED component: μ={mu_default}(location), a={a_default}, b={b_default}(scale), p={p_default}(shape)")
    print(f"- Gumbel component: β={beta_default}(location), α={alpha_default}(scale)")
    print("- Mixture parameter: Controls the mixing ratio of GED and Gumbel")