# 螺旋管DXF生成器

**目录**: `08_dxf_spiral_toolchain/A_螺旋管DXF生成器`
**文件数**: 88 个 .py 文件

> 本目录收录 Schauberger 相关脚本，由 `E:\我创造的py文件\` 归档补充。

## 文件清单

| 文件名 | 说明 |
|--------|------|
| `1组螺线生成正+侧视图png多图2的n次曲线t=4pi为起点.py` | Function to parse a single row of user input data from the CSV |
| `5组螺线生成正+侧视图png多图ln曲线t=pi为起点.py` | 定义底部圆半径和黄金比例常数 |
| `e_spiral.py` | Function to generate Exponential spiral points |
| `e螺旋线 -可滑动.py` | Function to generate Exponential spiral points |
| `ln螺旋线3d.py` | Set range for parameter t |
| `pi_spiral.py` | Set the precision for Decimal calculations |
| `sin除t螺旋线.py` | Set range for parameter t |
| `spiral-2d -multisquare.py` | Functions for 2D spiral curve |
| `spiral-2d -multisquare特定段.py` | user_num2=(np.sqrt(5)+1)/2 |
| `spiral-2d -multisquare特定段切360份.py` | Functions for 2D spiral curve |
| `spiral-2d curve.py` | Functions for 2D spiral curve |
| `spiral-2d.py` | Functions for 2D curve |
| `spiral-3d 3 spirila.py` | Define the parametric equations |
| `spiral-3d funnel.py` | Functions for 3D curve |
| `spiral-3d tube1 -stp -new.py` | Parameters |
| `spiral-3d tube1 -stp-spring.py` | 定义 y(t) 和 z(t) 函数 |
| `spiral-3d tube1 -stp.py` | Parameters |
| `spiral-3d tube1 -stpline 3段.py` | Define constants |
| `spiral-3d tube1 -stpline test 4段 鱼形.py` | Constants |
| `spiral-3d tube1 -stpline test 4段.py` | Set the value of 'a' to 1.618 |
| `spiral-3d tube1 -stpline test 底76圈.py` | Set the value of 'a' to 1.618 |
| `spiral-3d tube1-stp-perfect.py` | 定义参数 |
| `spiral-3d tube1-stpline侧面曲线.py` | Set the value of 'a' to 1.618 |
| `spiral-3d tube1-stpline侧面直线.py` | Set the value of 'a' to 1.618 |
| `spiral-3d tube1-stp底76圈4段.py` | Define constants |
| `spiral-3d tube1.py` | Functions for 3D curve |
| `spiral-3d tube2.py` | Functions for 3D curve |
| `spiral-3d 钟 -csv数据.py` | 定义参数 |
| `spiral-3d 钟.py` | Define the parametric equations with updated a and b values |
| `spiral-3d.py` | Functions for 3D curve |
| `spiral.py` | plt.axis('equal') |
| `三组螺线生成侧视图.py` | Function to parse user input and validate the number of inputs |
| `三组螺线生成侧视图gif动图.py` | Function to parse a single row of user input data from the CSV |
| `三组螺线生成正+侧视图gif动图ln曲线t=2pi为起点.py` | Function to parse a single row of user input data from the CSV |
| `三组螺线生成正+侧视图gif动图ln曲线t=pi为起点.py` | Function to parse a single row of user input data from the CSV |
| `从外向内兜底的螺旋线.py` | Step and parameters |
| `卍spiral.py` | The points of 卍 or lotus 正旋(右旋) center: |
| `围绕中轴旋转的clothoids回旋曲线.py` | Define the curvature function |
| `多级螺旋test.py` | 更新参数并考虑新的方程 |
| `最简原始模版用于生成GL25螺纹 - dxf -完美.py` | 默认参数配置 |
| `最简原始模版用于生成斜螺锥.py` |  |
| `最简原始模版用于生成曲锥螺旋管 - 扭转exp2t.py` |  |
| `最简原始模版用于生成曲锥螺旋管.py` |  |
| `最简原始模版用于生成直锥等距螺旋管 -线性扭转- 锥角参数可调.py` |  |
| `最简原始模版用于生成直锥螺旋管 - 扭转exp -Krystal螺旋 - 2.py` |  |
| `最简原始模版用于生成直锥螺旋管 - 扭转exp -Krystal螺旋.py` |  |
| `最简原始模版用于生成直锥螺旋管 - 扭转exp.py` |  |
| `最简原始模版用于生成直锥螺旋管.py` |  |
| `最简原始模版用于生成直锥螺旋管小段往回走 - 副本.py` |  |
| `最简原始模版用于生成直锥螺旋管小段往回走 首尾曲线不一样渐变 蛋到十字.py` |  |
| `最简原始模版用于生成直锥螺旋管小段往回走 首尾曲线不一样渐变 蛋到圆.py` |  |
| `最简原始模版用于生成直锥螺旋管小段往回走 首尾曲线不一样渐变 蛋到太极旋.py` |  |
| `最简原始模版用于生成直锥螺旋管小段往回走 首尾曲线不一样渐变 蛋到扇面.py` |  |
| `最简原始模版用于生成直锥螺旋管小段往回走+波动.py` |  |
| `最简原始模版用于生成直锥非等距螺旋管-线性扭转-锥角参数可调.py` |  |
| `最简原始模版用于生成直锥非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 白银比krystal.py` |  |
| `最简原始模版用于生成直锥非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 黄金比schauberger.py` |  |
| `最简原始模版用于生成直锥非等距螺旋管-非线性扭转-锥角参数可调 管波动纹.py` |  |
| `最简原始模版用于生成直锥非等距螺旋管-非线性扭转-锥角参数可调.py` |  |
| `最简原始模版用于生成螺锥81.2° - dxf-10cm边长盒子.py` | 默认参数配置 |
| `最简原始模版用于生成螺锥88° - dxf-27cm边长盒子 -叶序.py` | 默认参数配置 |
| `最简原始模版用于生成螺锥88° - dxf-27cm边长盒子 -叶序fibonacci - 简化 - 137.5°生长.py` | 默认参数配置 |
| `最简原始模版用于生成螺锥88° - dxf-27cm边长盒子 -叶序fibonacci - 简化.py` | 默认参数配置 |
| `最简原始模版用于生成螺锥88° - dxf-27cm边长盒子.py` | 默认参数配置 - enable_circles 默认为 True |
| `椭圆偏心旋转 侧面波 单个螺旋.py` | 设置字体为 SimHei |
| `椭圆偏心旋转 侧面波.py` | 设置字体为 SimHei |
| `椭圆偏心旋转.py` | Parameters |
| `滑滑梯波.py` | 扩展时间范围以显示多个周期 |
| `生成直锥非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 黄金比schauberger-蓝线G2混接多线多规扫掠.py` |  |
| `生成直锥非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 黄金比schauberger-蓝线G4混接三轨扫掠.py` |  |
| `生成直锥非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 黄金比schauberger-蓝线G9混接多线多规扫掠.py` |  |
| `生成直锥非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 黄金比schauberger-蓝线分段.py` |  |
| `直锥非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 蓝线G9混接多线多规扫掠 - 滑滑梯波.py` | 计算φ的三次方 |
| `直锥非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 蓝线混接多线多规扫掠 - 滑滑梯波 带缝隙-曲率求导不变 -简化.py` | 黄金比例常数 |
| `直锥非线性 非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 蓝线混接多线多规扫掠 - 滑滑梯波 带缝隙-曲率求导不变 -简化 2曲线混合.py` | 黄金比例常数 |
| `直锥非线性 非等距螺旋管-非线性扭转-锥角参数可调 管波动纹 蓝线混接多线多规扫掠 - 滑滑梯波 带缝隙-曲率求导不变 -简化 3曲线混合.py` | 黄金比例常数 |
| `直锥非线性 非等距螺旋管大-非线性扭转-锥角参数可调 管波动纹 蓝线混接多线多规扫掠 - 滑滑梯波 带缝隙-曲率求导不变 -简化 3曲线混合 磁铁 备份.py` | 黄金比例常数 |
| `直锥非线性 非等距螺旋管大-非线性扭转-锥角参数可调 管波动纹 蓝线混接多线多规扫掠 - 滑滑梯波 带缝隙-曲率求导不变 -简化 3曲线混合 磁铁.py` | 黄金比例常数 |
| `直锥非线性 非等距螺旋管小-非线性扭转-锥角参数可调 管波动纹 蓝线混接多线多规扫掠 - 滑滑梯波 带孔-曲率求导不变 -简化 3曲线混合 磁铁 质心在中 单管.py` | 黄金比例常数 |
| `直锥非线性 非等距螺旋管小-非线性扭转-锥角参数可调 管波动纹 蓝线混接多线多规扫掠 - 滑滑梯波 带缝隙-曲率求导不变 -简化 3曲线混合 磁铁 质心在中 单管.py` | 黄金比例常数 |
| `直锥非线性 非等距螺旋管小-非线性扭转-锥角参数可调 管波动纹 蓝线混接多线多规扫掠 - 滑滑梯波 带缝隙-曲率求导不变 -简化 3曲线混合 磁铁.py` | 黄金比例常数 |
| `蛋偏心旋转 侧面波 单个螺旋.py` | 设置字体为 SimHei |
| `蛋偏心旋转.py` | Define t and theta ranges |
| `螺旋波3d.py` | -*- coding: utf-8 -*- |
| `螺旋蛋开口.py` | Define parameter range |
| `螺旋蛋开口nazi.py` | Define parameter range |
| `螺旋蛋开口nazi直线连接.py` | -*- coding: utf-8 -*- |
| `螺旋蛋循环.py` | Define the parameters |

## 运行环境

- 大部分需 **Rhino 3D** (`import rhinoscriptsyntax`)
- 部分可使用标准 Python (`matplotlib`, `numpy`)

*本说明由 AI 自动生成于 2026-06-15 19:52*