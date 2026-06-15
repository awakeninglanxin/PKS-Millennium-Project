import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

n = 3
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

# --- Integrating the Lorenz Curve and Gini Coefficient Calculation ---

# Creating the sequence list based on the results
n_values = results_n
n2_values = results_n2
E_values = results_E

sequence = []
for i in range(len(E_values)):
    salary_per_person = S / n_values[i]  # 每个阶层个人的工资
    sequence.extend([salary_per_person] * n2_values[i])  # 分配工资给每个阶层的个人

sampleCount = sum(results_n2)  # 样本总数，即人数
sequence.sort()  # 从小(穷)到大(富)排序

cw = []
for i in range(sampleCount):  # 计算累积财富值
    cw.append(sum(sequence[:i + 1]))  # cw[i]表示社会最穷的i+1个人的总财富

totalWealth = cw[-1]  # 社会总财富
for i in range(len(cw)):  # 计算累积财富占比
    cw[i] = cw[i] / totalWealth  # cw[i]表示社会最穷的i+1个人的财富占比
cw = [0] + cw  # 加0: 0%的人拥有0%的财富
cp = [0] + [i / sampleCount for i in range(1, sampleCount + 1)]
B = 0  # 梯形法累加计算B区域面积
for i in range(1, sampleCount + 1):
    B = B + (cw[i] + cw[i - 1]) * (cp[i] - cp[i - 1]) / 2
A = 0.5 - B  # A+B = 0.5

# Calculate the Gini coefficient
gini_coefficient = A / (A + B)
poorest_salary = sequence[0]
richest_salary = sequence[-1]

# Create Lorenz curve plot using plotly
fig = make_subplots(rows=1, cols=2, column_widths=[0.7, 0.3], subplot_titles=("Lorenz Curve", "Distribution of Classes"))

# Lorenz curve
fig.add_trace(go.Scatter(x=cp, y=cw, mode='lines', name='Lorenz Curve', line=dict(color='blue', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=cp, y=cp, mode='lines', name='Equality Line', line=dict(color='red')), row=1, col=1)

# Adding a specific point on the Lorenz curve
middle_index = len(cp) // 2  # Get the middle index
fig.add_trace(go.Scatter(x=[cp[middle_index]], y=[cw[middle_index]], mode='markers', marker=dict(color='black', size=10), name='Middle Point'), row=1, col=1)

# Fill area A
fig.add_trace(go.Scatter(x=cp + cp[::-1], y=cw + [i for i in cp[::-1]], fill='toself', fillcolor='red', opacity=0.2, line=dict(color='rgba(255,255,255,0)'), name='Area A'), row=1, col=1)
# Fill area B
fig.add_trace(go.Scatter(x=cp, y=cw, fill='tonexty', fillcolor='green', opacity=0.2, line=dict(color='rgba(255,255,255,0)'), name='Area B'), row=1, col=1)

# Add annotations for A and B
fig.add_annotation(x=0.5, y=0.4, text="A", showarrow=False, font=dict(size=20, color="black"), row=1, col=1)
fig.add_annotation(x=0.75, y=0.1, text="B", showarrow=False, font=dict(size=20, color="black"), row=1, col=1)

fig.add_trace(go.Bar(
    x=results_n2,  # Reversing to have Class 1 at the top
    y=[f"Class {i+1}" for i in range(len(results_n2))],
    orientation='h',
    marker=dict(color='green'),
    width=0.5  # Adjust width to center the bars
), row=1, col=2)

# Update layout
fig.update_layout(
    title=dict(text=f"Gini Coefficient: {gini_coefficient:.3f}<br>Poorest Salary: {poorest_salary}<br>Richest Salary: {richest_salary}<br>Population: {sampleCount}", x=0.5, xanchor='center', font=dict(size=14)),
    xaxis_title='Cumulative Population',
    yaxis_title='Cumulative Wealth',
    xaxis=dict(tickformat=',.0%', range=[0, 1]),
    yaxis=dict(tickformat=',.0%', range=[0, 1]),
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    yaxis2=dict(title='Classes', autorange="reversed", showgrid=False),  # Reverse y-axis for classes
    xaxis2=dict(title='Number of People', showgrid=False)
)

# Show figure
fig.show()
