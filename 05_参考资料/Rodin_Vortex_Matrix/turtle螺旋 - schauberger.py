from turtle import Screen, Turtle
from time import time
import turtle
import colorsys
import math


class VortexDrawer:
    def __init__(self):
        self.reset_screen()
        self.hue = 0  # 色调初始值

    def reset_screen(self):
        try:
            turtle.TurtleScreen._RUNNING = True
            self.screen = Screen()
            self.screen.clear()
            self.screen.colormode(255)  # 设置颜色模式为RGB
            self.turtle = Turtle()
            self.turtle.reset()
            self.screen.delay(0)
        except Exception as e:
            print(f"Reset screen warning: {str(e)}")
            turtle.TurtleScreen._RUNNING = True
            self.screen = Screen()
            self.turtle = Turtle()

    def setup_turtle(self):
        self.screen.bgcolor("#000000")
        self.turtle.hideturtle()
        self.turtle.speed(0)
        self.screen.tracer(0)

    def get_next_color(self):
        """生成下一个彩虹颜色"""
        self.hue += 0.01  # 色调递增
        if self.hue > 1.0:
            self.hue = 0
        # 将HSV颜色转换为RGB
        rgb = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
        # 将0-1的RGB值转换为0-255
        return tuple(int(x * 255) for x in rgb)

    def calculate_digital_root(self, num: int) -> int:
        """计算数根：将数字各位相加，直到得到一位数"""
        if num == 0:
            return 0
        return (num - 1) % 9 + 1

    def draw_vortex(self, coefficient):
        self.setup_turtle()
        self.turtle.pensize(2)
        self.turtle.penup()
        self.turtle.goto(0, 0)
        self.turtle.pendown()
        self.turtle.setheading(60)
        step = 3  # 步进值，从3开始
        n = 4  # 多边形边数，从3开始
        boundary = 3  # 当前边界值

        while boundary <= 30:  # 边界值到300为止

            # 更新颜色
            self.turtle.color(self.get_next_color())

            # 计算到下一个边界的步长
            current_x, current_y = self.turtle.pos()

            # 计算当前海龟前进方向的角度（弧度）
            heading_rad = self.turtle.heading() * math.pi / 180

            # 获取海龟当前方向的单位向量
            direction_x = math.cos(heading_rad)
            direction_y = math.sin(heading_rad)

            # 计算到达下一个边界所需的步长
            # 使用二次方程求解：(x + t*dx)^2 + (y + t*dy)^2 = (boundary * coefficient)^2
            # 其中 t 是我们要求的步长，系数coefficient用来整体放大图形
            a = direction_x ** 2 + direction_y ** 2  # 应该等于1
            b = 2 * (current_x * direction_x + current_y * direction_y)
            c = current_x ** 2 + current_y ** 2 - ((boundary + 1) * coefficient) ** 2  # 边界也要乘以系数

            # 解二次方程
            discriminant = b ** 2 - 4 * a * c
            if discriminant >= 0:
                # 我们要得到正的解
                step_length = (-b + math.sqrt(discriminant)) / (2 * a)
            else:
                # 如果没有解（这种情况理论上不应该发生），使用一个默认步长
                step_length = coefficient  # 默认步长也要乘以系数

            # 前进计算出的步长
            self.turtle.forward(step_length)

            # 检查新位置是否达到边界
            current_x, current_y = self.turtle.pos()
            distance = (current_x ** 2 + current_y ** 2) ** 0.5

            print(f"Step: {step}, Distance: {distance:.2f}, Boundary: {boundary}, Polygon: {n}")

            # 如果到达当前边界
            if distance >= boundary:
                print(f"Reached boundary {boundary}, turning...")
                # 计算相对于原点的角度
                absolute_angle = (n - 2) * 180 / n  # 计算正n边形内角
                # 设置绝对角度
                self.turtle.setheading(absolute_angle)
                boundary += 1  # 增加边界值
                n += 1  # 增加多边形边数

            step += 1

            # 立即更新显示
            self.screen.update()

        print("Pattern completed")

    def close(self):
        try:
            turtle.bye()
        except:
            pass


def main():
    drawer = VortexDrawer()

    try:
        print("\nRainbow Vortex Pattern Generator")
        print("--------------------------------")
        coef = 10
        drawer.draw_vortex(coef)

        # 保持窗口打开直到关闭
        drawer.screen.mainloop()

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        drawer.close()


if __name__ == "__main__":
    main()