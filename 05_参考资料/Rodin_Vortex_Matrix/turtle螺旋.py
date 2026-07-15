from turtle import Screen, Turtle
from time import time
import turtle
import colorsys


class NumberProcessor:
    @staticmethod
    def calculate_digital_root(num: str) -> int:
        if not num.isdigit():
            raise ValueError("Input must be a digit string")

        while len(num) > 1:
            num = str(sum(int(d) for d in num))
        return int(num)


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

    def draw_vortex(self, start: int = 3, step: int = 3, coefficient: int = 3):
        self.setup_turtle()
        self.turtle.pensize(2)
        self.turtle.penup()
        self.turtle.goto(0, 0)
        self.turtle.pendown()

        size_factor = 0.8  # 增大图案尺寸
        turn = 1
        dpd_sum = 0

        while True:
            current = start

            while True:
                dpd = NumberProcessor.calculate_digital_root(str(current))

                # 更新颜色
                self.turtle.color(self.get_next_color())

                self.turtle.forward(dpd * coefficient * 4 * size_factor)
                self.turtle.right(dpd * coefficient)
                current += step

                if abs(self.turtle.pos()) < 0.00001:
                    self.turtle.right(dpd)
                    dpd_sum += dpd
                    break

            print(f'Turn {turn} completed')
            turn += 1

            if dpd_sum >= 360:
                break

        # 完成后一次性更新
        self.screen.update()

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
        start = int(input("Enter starting number (recommended 3): "))
        step = int(input("Enter step size (recommended 3): "))
        coef = int(input("Enter coefficient (recommended 3): "))
        drawer.draw_vortex(start, step, coef)

        # 保持窗口打开直到关闭
        drawer.screen.mainloop()

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        drawer.close()


if __name__ == "__main__":
    main()