# 蛋形→Sin波进化（螺旋蛋过渡系列）

**目录**: `09_historical_evolution/C_蛋形toSin波进化`
**文件数**: 44 个 .py 文件

> 本目录收录 Schauberger 相关脚本，由 `E:\我创造的py文件\` 归档补充。

## 文件清单

| 文件名 | 说明 |
|--------|------|
| `4种波纹最佳截面曲线ln线.py` | -*- coding: utf-8 -*- |
| `aaa圆盘夹片上下曲线 原版.py` | 定义中心线函数1 |
| `aaa圆盘夹片上下曲线.py` | 定义中心线 |
| `aaa圆盘夹片上下曲线改进.py` | 定义R_up和R_down作为新函数 |
| `a乘法光的折射可视化-3组蛋t为3出gif.py` | Function to generate the cardioid set and plot it |
| `a乘法光的折射可视化-蛋-光的混色.py` | 设置参数 |
| `a乘法光的折射可视化-蛋-出gif -固定m 透明背景.py` | 设置 GIF 的帧率 |
| `a乘法光的折射可视化-蛋-出gif -固定m.py` | 固定图像的大小 |
| `a乘法光的折射可视化-蛋-出gif.py` | 固定图像的大小 |
| `a乘法光的折射可视化-蛋.py` | 设置参数 参数设置 |
| `不同n组蛋公式转成sin波 -画曲率.py` | List of 'a' values for each node |
| `不同n组蛋公式转成sin波 -等体积.py` | Function to generate nodes with 'a' value set to 1 |
| `不同n组蛋公式转成sin波 黄金比加2n次方.py` | Function to generate Fibonacci numbers starting from 5 and 8 |
| `不同n组蛋公式转成sin波.py` | List of 'a' values for each node |
| `不同蛋公式转成sin波.py` | Nodes with parameters and corresponding t ranges |
| `双曲线phi^n-螺旋蛋逐渐变圆公式转成sin波 负 -ln2开始递减 线性旋转 - 万字符 -3d.py` | -*- coding: utf-8 -*- |
| `双曲线下的分段1.618的n次每段面积代表圆盘夹层分段的体积比.py` | Define the function for the curve |
| `双曲线下的分段2的n次每段面积代表圆盘夹层分段的体积比.py` | Define the function for the curve |
| `双曲线下的分段2的n次每段面积代表圆盘夹层分段的体积比生成sin波.py` | Parameters |
| `双曲线下的分段面积代表圆盘夹层分段的体积比.py` | Define the function for the curve |
| `双曲线八度2^n+phi^n 螺旋蛋逐渐变扁公式转成sin波 负 -ln2开始递减 线性旋转 - 万字符 -3d.py` | -*- coding: utf-8 -*- |
| `双曲线八度2^n-螺旋蛋逐渐变扁公式转成sin波 负 -ln2开始递减 线性旋转 - 万字符 -3d.py` | -*- coding: utf-8 -*- |
| `双曲线阳-螺旋蛋公式转成sin波 负 -ln2开始递减 线性旋转 - 万字符 -3d.py` | 连续对数积分衰减因子 |
| `双曲线阴-螺旋蛋公式转成sin波 负 -ln2开始递减 线性旋转 - 万字符 -3d.py` | 连续对数积分衰减因子 |
| `双曲线阴阳合一-螺旋蛋逐渐变扁公式转成sin波 负 -ln2开始递减 线性旋转 - 万字符 -3d.py` | -*- coding: utf-8 -*- |
| `双波纹盘最佳截面曲线.py` | -*- coding: utf-8 -*- |
| `蛋公式转成sin波.py` | 设置参数 |
| `螺旋蛋公式转成sin波 正 -加螺旋线.py` | Parameters for the spiral |
| `螺旋蛋公式转成sin波 正 -摆线 -双曲线衰减.py` | Parameters for the spiral |
| `螺旋蛋公式转成sin波 正 -摆线.py` | Parameters for the spiral |
| `螺旋蛋公式转成sin波 正 幻方.py` | Parameters for the spiral |
| `螺旋蛋公式转成sin波 正 改.py` | Parameters for the spiral |
| `螺旋蛋公式转成sin波 正.py` | Parameters for the spiral |
| `螺旋蛋公式转成sin波 正ln线 斜心.py` | Parameters for the spiral |
| `螺旋蛋公式转成sin波 正ln线.py` | Parameters for the spiral |
| `螺旋蛋公式转成sin波 负 -ln2开始递减 - 四象限.py` | 参数设置 |
| `螺旋蛋公式转成sin波 负 -ln2开始递减 线性旋转 - 万字符.py` | 参数设置 |
| `螺旋蛋公式转成sin波 负 -ln2开始递减 线性旋转.py` | 参数设置 |
| `螺旋蛋公式转成sin波 负 -ln2开始递减.py` | 参数设置 |
| `螺旋蛋公式转成sin波 负 八度切 - 四象限.py` | 参数设置 |
| `螺旋蛋公式转成sin波 负 双曲线比切 - 四象限.py` | 参数设置 |
| `螺旋蛋公式转成sin波 负.py` | Parameters for the spiral |
| `螺旋蛋逐渐变圆公式转成sin波 负 -ln2开始递减 线性旋转 - 万字符 -3d.py` | 参数设置（按照文档1的配置） |
| `重点-螺旋蛋逐渐变圆公式转成sin波 负 -ln2开始递减 线性旋转 - 万字符.py` | 参数设置 |

## 运行环境

- 大部分需 **Rhino 3D** (`import rhinoscriptsyntax`)
- 部分可使用标准 Python (`matplotlib`, `numpy`)

*本说明由 AI 自动生成于 2026-06-15 19:52*