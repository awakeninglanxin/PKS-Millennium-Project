import numpy as np  # 导入NumPy库，用于数值计算
import plotly.graph_objects as go  # 导入Plotly库，用于绘制图形

# 生成从3^2开始的前10个Fibonacci数列的平方数
def fibonacci_sequence_squared(n, start=3):
    start = start  # 从3的平方开始
    fib_sequence = [start**2, (start + 2)**2]  # 3^2, (3+2)^2作为起始数列
    for i in range(2, n):
        next_fib = np.sqrt(fib_sequence[-1]) + np.sqrt(fib_sequence[-2])
        fib_sequence.append(int(next_fib**2))
    return fib_sequence

# 主程序
num_levels = 10  # 定义阶层数量为10
total_income = 500000  # 定义总收入为500000
fib_sequence = fibonacci_sequence_squared(num_levels)  # 生成前10个Fibonacci数列的平方数
print(fib_sequence)
# 计算每个阶层的个人收入
individual_group_income = total_income / num_levels  # 每个阶层的总收入
individual_incomes = [individual_group_income // num_people for num_people in fib_sequence]  # 每个人的收入

# 生成排序后的收入列表
sequence = []
for num_people, income in zip(fib_sequence, individual_incomes):
    sequence.extend([income]*int(num_people))  # 将收入加入列表

sequence.sort()  # 对收入进行排序
print(len(sequence))
# 计算累积财富占比和人群占比
sampleCount = len(sequence)  # 样本数量
cw = [sum(sequence[:i + 1]) / sum(sequence) for i in range(sampleCount)]  # 累积财富占比
cw = [0] + cw
cp = [0] + [i / sampleCount for i in range(1, sampleCount + 1)]  # 人群占比

# 计算A和B区域面积
B = sum((cw[i] + cw[i - 1]) * (cp[i] - cp[i - 1]) / 2 for i in range(1, sampleCount + 1))  # 计算区域B面积
A = 0.5 - B  # 计算区域A面积

# 使用plotly绘制图表
fig = go.Figure()

# 添加洛伦兹曲线
fig.add_trace(go.Scatter(x=cp, y=cw, mode='lines', name='洛伦兹曲线', line=dict(color='blue', dash='dash')))

# 添加完全平等线
fig.add_trace(go.Scatter(x=cp, y=cp, mode='lines', name='完全平等线', line=dict(color='red')))

# 添加洛伦兹曲线上的中点
middle_index = len(cp) // 2  # 获取中间索引
fig.add_trace(go.Scatter(x=[cp[middle_index]], y=[cw[middle_index]], mode='markers', marker=dict(color='black', size=10), name='中点'))

# 中点代表x%占了y%的财富
fig.add_annotation(x=cp[middle_index], y=cw[middle_index], text=f"{cp[middle_index]*100:.1f}%, {cw[middle_index]*100:.1f}%", showarrow=True, arrowhead=1)

# 填充区域A
fig.add_trace(go.Scatter(x=cp + cp[::-1], y=cw + [i for i in cp[::-1]], fill='toself', fillcolor='red', opacity=0.2, line=dict(color='rgba(255,255,255,0)'), name='区域A'))

# 填充区域B
fig.add_trace(go.Scatter(x=cp, y=cw, fill='tonexty', fillcolor='green', opacity=0.2, line=dict(color='rgba(255,255,255,0)'), name='区域B'))

# 添加文字标签
fig.add_annotation(x=0.5, y=0.4, text="A", showarrow=False, font=dict(size=20, color="black"))
fig.add_annotation(x=0.75, y=0.1, text="B", showarrow=False, font=dict(size=20, color="black"))

# 计算财富基尼系数
gini_coefficient = A / (A + B)
# 最穷的人的工资
poorest_salary = sequence[0]
# 最富的人的工资
richest_salary = sequence[-1]
# 定义标题，包含所有所需信息
title_text = (
    f"本财富基尼系数: {gini_coefficient:.3f}<br>"
    f"最穷的人工资: {poorest_salary}<br>"
    f"最富的人工资: {richest_salary}<br>"
    f"系统人数: {sampleCount}"
)
# 更新布局设置
fig.update_layout(
    title=dict(text=title_text, x=0.5, xanchor='center', font=dict(size=14)),
    xaxis_title='人群占比',
    yaxis_title='财富占比',
    xaxis=dict(tickformat=',.0%', range=[0, 1]),
    yaxis=dict(tickformat=',.0%', range=[0, 1]),
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)

# 显示图形
fig.show()  # 显示绘制的图形
