from turtle import Screen, Turtle
from time import time
import turtle
import colorsys
import math

boundary_max = 30

class VortexDrawer:
    def __init__(self):
        self.reset_screen()
        self.hue = 0  # 色调初始值
        self.scale = 1.0  # 添加缩放系数
        self.update_counter = 0  # 添加更新计数器
        self.update_frequency = 1  # 每100步更新一次屏幕

    def set_scale(self, scale: float):
        """设置缩放系数"""
        self.scale = scale

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
        rgb = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
        return tuple(int(x * 255) for x in rgb)

    def maybe_update_screen(self):
        """根据计数器决定是否更新屏幕"""
        self.update_counter += 1
        if self.update_counter >= self.update_frequency:
            self.screen.update()
            self.update_counter = 0

    def draw_vortex(self, step_size=0.5, turn_angle=10):
        """从中心向外绘制螺旋，并返回终点位置和朝向"""
        self.setup_turtle()
        self.turtle.pensize(2)
        self.turtle.penup()
        self.turtle.goto(0, 0)
        self.turtle.pendown()

        boundary = 1

        while boundary <= boundary_max:
            self.turtle.color(self.get_next_color())
            # 应用缩放系数
            scaled_step = step_size * boundary * self.scale
            self.turtle.forward(scaled_step)
            self.turtle.right(turn_angle)

            current_x, current_y = self.turtle.pos()
            distance = (current_x ** 2 + current_y ** 2) ** 0.5

            if distance >= boundary * self.scale:  # 同样缩放边界检查
                boundary += 1

            self.maybe_update_screen()

        # 确保最后一帧被绘制
        self.screen.update()
        return self.turtle.position(), self.turtle.heading()

    def draw_inward_spiral(self, step_size=0.5, turn_angle=10, start_pos=None, start_heading=None):
        """从外向内绘制螺旋"""
        self.setup_turtle()
        self.turtle.pensize(2)

        if not start_pos:
            start_radius = boundary_max * self.scale
            self.turtle.penup()
            self.turtle.goto(start_radius, 0)
            self.turtle.pendown()
        else:
            self.turtle.penup()
            self.turtle.goto(start_pos)
            self.turtle.setheading(start_heading)
            self.turtle.pendown()

        min_distance = 5 * self.scale

        current_x, current_y = self.turtle.pos()
        start_distance = (current_x ** 2 + current_y ** 2) ** 0.5
        steps_needed = int(start_distance / (step_size * self.scale))

        total_angle = 720
        steps_taken = 0

        while True:
            self.turtle.color(self.get_next_color())
            current_x, current_y = self.turtle.pos()
            distance = (current_x ** 2 + current_y ** 2) ** 0.5

            if distance < min_distance:
                break

            remaining_steps = steps_needed - steps_taken
            if remaining_steps > 0:
                current_angle = total_angle / steps_needed
            else:
                current_angle = total_angle / steps_needed * 2

            current_step = distance * 0.05 * self.scale

            self.turtle.forward(current_step)
            self.turtle.right(current_angle)

            steps_taken += 1
            self.maybe_update_screen()

        # 确保最后一帧被绘制
        self.screen.update()

    def draw_dual_spiral(self, step_size=0.5):
        """绘制双螺旋：一个向外，一个向内，使用不同的转角"""
        end_pos, end_heading = self.draw_vortex(step_size=step_size, turn_angle=10)
        self.draw_inward_spiral(step_size=step_size, turn_angle=1,
                                start_pos=end_pos, start_heading=end_heading)

    def close(self):
        try:
            turtle.bye()
        except:
            pass


def main():
    try:
        print("\nDual Spiral Pattern Generator")
        print("--------------------------------")
        step_size = 3  # 基础步长
        scale = 0.5  # 缩放系数

        drawer = VortexDrawer()
        drawer.set_scale(scale)  # 设置缩放
        drawer.draw_dual_spiral(step_size=step_size)
        drawer.screen.exitonclick()

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        drawer.close()


if __name__ == "__main__":
    main()