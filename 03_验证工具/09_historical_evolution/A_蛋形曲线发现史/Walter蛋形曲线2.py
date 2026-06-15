import numpy as np
import matplotlib.pyplot as plt

# 设置字体为 SimHei
plt.rcParams['font.sans-serif'] = ['SimHei']
# 设置正常显示负号
plt.rcParams['axes.unicode_minus'] = False

# 参数设置
b = 5 / 3  # 固定参数
f = np.arctan(2 / 3)  # 固定角度
t_positive = np.linspace(-np.pi / 2, np.pi / 2, 300)  # 正半部分的 t 范围
t_negative = np.linspace(np.pi / 2, -np.pi / 2, 300)  # 负半部分的 t 范围

# 初始化无效点记录
invalid_point_pos_saved = False
invalid_point_neg_saved = False

# 计算正半部分
x_pos = []
y_pos = []
for t in t_positive:
    value = 1 / (b + t * np.sin(f)) ** 2 - (t * np.cos(f)) ** 2
    if value >= 0:
        x_pos.append(t)
        y_pos.append(np.sqrt(value))
    else:
        if not invalid_point_pos_saved:
            invalid_point_pos_saved = True  # 设置标志为已保存
        continue

# 计算负半部分
x_neg = []
y_neg = []
for t in t_negative:
    value = 1 / (b + t * np.sin(f)) ** 2 - (t * np.cos(f)) ** 2
    if value >= 0:
        x_neg.append(t)
        y_neg.append(-np.sqrt(value))
    else:
        if not invalid_point_neg_saved:
            invalid_point_neg_saved = True  # 设置标志为已保存
        continue

# 创建图形
plt.figure(figsize=(6, 6))

# 将实部曲线的每一段单独绘制以实现颜色渐变
colors_pos = plt.cm.hsv(np.linspace(0, 1, len(x_pos)))  # 正半部分颜色渐变
colors_neg = plt.cm.hsv(np.linspace(0, 1, len(x_neg)))  # 负半部分颜色渐变

# 绘制正半部分的实部连线
for i in range(1, len(x_pos)):
    plt.plot(x_pos[i-1:i+1], y_pos[i-1:i+1], color=colors_pos[i])

# 绘制负半部分的实部连线
for i in range(1, len(x_neg)):
    plt.plot(x_neg[i-1:i+1], y_neg[i-1:i+1], color=colors_neg[i])

# 添加标签和标题
plt.xlabel('X')
plt.ylabel('Y')
plt.title('完整蛋形曲线')

# 显示网格和图例
plt.grid(True)
plt.legend(['正半部分', '负半部分'])

# 设置轴的比例一致
plt.axis('equal')

# 显示图形
plt.show()
