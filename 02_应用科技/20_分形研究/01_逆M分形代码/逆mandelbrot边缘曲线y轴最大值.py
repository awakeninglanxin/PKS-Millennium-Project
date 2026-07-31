import numpy as np
import matplotlib.pyplot as plt
from mpmath import mp
from multiprocessing import Pool

# 使用高精度的复数运算
mp.dps = 30  # 设置30位精度以提高计算速度

# 定义逆Mandelbrot集的迭代函数
def mandelbrot_iteration(C, max_iter=500):
    z = 0
    for i in range(max_iter):
        z = z ** 2 + 1 / C
        if abs(z) > 1000:
            return i
    return max_iter

# 牛顿法迭代，寻找接近边界的点
def newton_method(C, max_iter=500, threshold=950):
    z = 0
    for i in range(max_iter):
        f = z ** 2 + 1 / C - z
        f_prime = 2 * z - 1 / C
        z = z - f / f_prime
        if abs(f) < threshold:
            return z
    return None

# 计算接近水滴边缘的点，进行牛顿法细化搜索
def find_bifurcation_edge_segment(x_range, y_range, max_iter=500, threshold=950):
    edge_points = []
    for y in np.linspace(y_range[0], y_range[1], 50):  # 使用较大步长
        for x in np.linspace(x_range[0], x_range[1], 50):  # 使用较大步长
            C = mp.mpc(x, y)
            iterations = mandelbrot_iteration(C, max_iter)
            if iterations > threshold:
                refined_point = newton_method(C, max_iter, threshold)
                if refined_point is not None:
                    edge_points.append((refined_point.real, refined_point.imag))
    return edge_points

# 并行计算多个区段
def parallel_find_bifurcation_edge(x_range, y_range, num_segments=4):
    # 将y范围分割为多个区段并并行处理
    segment_ranges = np.linspace(y_range[0], y_range[1], num_segments + 1)
    with Pool(processes=num_segments) as pool:
        results = pool.starmap(find_bifurcation_edge_segment,
                              [(x_range, (segment_ranges[i], segment_ranges[i+1])) for i in range(num_segments)])
    edge_points = [point for result in results for point in result]
    return edge_points

# 主程序入口
if __name__ == '__main__':
    # 设置搜索范围
    x_range = (0.4, 0.6)
    y_range = (1.618, 1.626)  # 注意的y范围

    # 寻找分岔边界
    max_iter = 500  # 降低max_iter
    edge_points = parallel_find_bifurcation_edge(x_range, y_range, num_segments=4)

    # 可视化
    plt.figure(figsize=(8, 8))
    for point in edge_points:
        plt.plot(point[0], point[1], 'ro', markersize=1)

    plt.title("Bifurcation edge points in the inverse Mandelbrot set using Newton's method")
    plt.xlabel("Real part of C")
    plt.ylabel("Imaginary part of C")
    plt.show()
