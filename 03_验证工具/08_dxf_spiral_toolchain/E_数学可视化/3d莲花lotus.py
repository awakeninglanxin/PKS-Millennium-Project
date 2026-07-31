import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Slider

dahlia_params = {
    'phiFactor': 2.75,
    'scale': 3,
    'thetaFactor': 5000,  # 减少精度
    'thetaMultiplier': 3,  # 减少细节
    'hangDownMultiplier': 1.3,
    'rPowerFactor': 0.9,
    'petalCutConstant': 0.5
}


# 生成大丽花的图形
def dahlia(ax, phiFactor, scale, thetaFactor, thetaMultiplier, hangDownMultiplier, rPowerFactor, petalCutConstant):
    for r in np.arange(0, 1.1, 0.05):  # 更大的步长
        for theta in np.arange(0, 360 * dahlia_params['thetaMultiplier'], 5):
            phi = (360 / phiFactor) * np.exp(-theta / (66 * 180))
            petalCut = 166 + abs(np.sin(np.radians(theta * thetaMultiplier)) + petalCutConstant * np.sin(
                np.radians(theta * thetaMultiplier)))
            hangDown = hangDownMultiplier * r ** rPowerFactor * (rPowerFactor * r - 1) ** 2 * np.sin(np.radians(phi))

            if petalCut * (r * np.sin(np.radians(phi)) + hangDown * np.cos(np.radians(phi))) > 0:
                pX = scale * (1 - theta / thetaFactor) * petalCut * (
                            r * np.sin(np.radians(phi)) + hangDown * np.cos(np.radians(phi))) * np.sin(
                    np.radians(theta))
                pY = -scale * (1 - theta / thetaFactor) * petalCut * (
                            r * np.cos(np.radians(phi)) - hangDown * np.sin(np.radians(phi)))
                pZ = scale * (1 - theta / thetaFactor) * petalCut * (
                            r * np.sin(np.radians(phi)) + hangDown * np.cos(np.radians(phi))) * np.cos(
                    np.radians(theta))

                hue = (theta / (360 * thetaMultiplier)) * 360
                ax.plot([pX], [pY], [pZ], color=plt.cm.hsv(hue / 360), marker='o', markersize=1)


# 设置绘图
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 绘制初始图形
dahlia(ax, **dahlia_params)

# 设置轴范围
ax.set_xlim([-100, 100])
ax.set_ylim([-100, 100])
ax.set_zlim([-100, 100])

# 设置旋转角度
ax.view_init(elev=30, azim=45)

# 添加滑块调整功能
ax_slider_phi = plt.axes([0.85, 0.02, 0.03, 0.15], facecolor='lightgoldenrodyellow')
slider_phi = Slider(ax_slider_phi, 'Phi Factor', 1, 10, valinit=dahlia_params['phiFactor'])

ax_slider_scale = plt.axes([0.85, 0.18, 0.03, 0.15], facecolor='lightgoldenrodyellow')
slider_scale = Slider(ax_slider_scale, 'Scale', 1, 3, valinit=dahlia_params['scale'])


# 更新绘图函数
def update(val):
    # 清空当前图形
    ax.cla()

    # 获取当前滑块的值
    phiFactor = slider_phi.val
    scale = slider_scale.val

    # 重新绘制大丽花
    dahlia(ax, phiFactor, scale, dahlia_params['thetaFactor'], dahlia_params['thetaMultiplier'],
           dahlia_params['hangDownMultiplier'], dahlia_params['rPowerFactor'], dahlia_params['petalCutConstant'])

    ax.set_xlim([-100, 100])
    ax.set_ylim([-100, 100])
    ax.set_zlim([-100, 100])
    ax.view_init(elev=30, azim=45)
    plt.draw()


# 为滑块设置更新事件
slider_phi.on_changed(update)
slider_scale.on_changed(update)

plt.show()
