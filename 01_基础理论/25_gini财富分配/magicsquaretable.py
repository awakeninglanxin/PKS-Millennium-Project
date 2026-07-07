import matplotlib.pyplot as plt

# 设置中文字体为SimHei
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 使用您的程序生成四个结果列表
S = 4410

def L(n):
    return 1.5 - ((n ** 2) / 2) + S / n

results_n = []
results_n2 = []
results_L = []
results_E = []

n = 1
while True:
    l_value = L(n)
    if l_value <= 0:
        break
    if l_value.is_integer():
        results_n.append(n)
        results_n2.append(n ** 2)
        results_L.append(int(l_value))
        results_E.append(n * S)
    n += 1

print('线和:',S)
print('n:',results_n,sum(results_n))
print('n^2:',results_n2,sum(results_n2))
print('Level:',results_L,sum(results_L))
print('energy:',results_E,sum(results_E))
# 创建图表
fig, axs = plt.subplots(2, 2, figsize=(14, 10))
# 绘制 results_n
left_positions_n = [(max(results_n) - d) / 2 for d in results_n]
axs[0, 0].barh(range(len(results_n), 0, -1), results_n, color='green', left=left_positions_n)
for i, v in enumerate(results_n):
    axs[0, 0].text(-0.5, len(results_n) - i, str(v), color='purple', fontweight='bold', ha='right', va='center')
axs[0, 0].set_title('n')

# 绘制 results_n2
left_positions_n2 = [(max(results_n2) - d) / 2 for d in results_n2]
axs[0, 1].barh(range(len(results_n2), 0, -1), results_n2, color='green', left=left_positions_n2)
for i, v in enumerate(results_n2):
    axs[0, 1].text(-0.5, len(results_n2) - i, str(v), color='purple', fontweight='bold', ha='right', va='center')
axs[0, 1].set_title('n^2')

# 绘制 results_L
left_positions_L = [(max(results_L) - d) / 2 for d in results_L]
axs[1, 0].barh(range(len(results_L), 0, -1), results_L, color='green', left=left_positions_L)
for i, v in enumerate(results_L):
    axs[1, 0].text(-0.5, len(results_L) - i, str(v), color='purple', fontweight='bold', ha='right', va='center')
axs[1, 0].set_title('Level')

# 绘制 results_E
left_positions_E = [(max(results_E) - d) / 2 for d in results_E]
axs[1, 1].barh(range(len(results_E), 0, -1), results_E, color='green', left=left_positions_E)
for i, v in enumerate(results_E):
    axs[1, 1].text(-0.5, len(results_E) - i, str(v), color='purple', fontweight='bold', ha='right', va='center')
axs[1, 1].set_title('Energy')

# 隐藏所有图表的y轴刻度和标签以获得更干净的外观
for ax in axs.flat:
    ax.set_yticks([])

# 调整图表布局
plt.tight_layout()

# 显示图表
plt.show()
