import ezdxf
import math


class RippleSpiralPipe:
    def __init__(self, bands=5, radius=100, height=200, spiral_turns=3):
        self.bands = bands
        self.radius = radius
        self.height = height
        self.spiral_turns = spiral_turns
        self.doc = ezdxf.new('R2010')
        self.msp = self.doc.modelspace()

    def generate_spiral_points(self, points_per_turn=100):
        """生成螺旋线点"""
        total_points = points_per_turn * self.spiral_turns
        points = []

        for i in range(total_points + 1):
            t = i / points_per_turn * 2 * math.pi * self.spiral_turns
            # 螺旋线参数方程
            x = self.radius * math.cos(t)
            y = self.radius * math.sin(t)
            z = (i / total_points) * self.height

            # 添加波纹效果
            ripple = math.sin(t * self.bands) * 5
            x += ripple * math.cos(t)
            y += ripple * math.sin(t)

            points.append((x, y, z))

        return points

    def generate_pipe(self):
        """生成波纹螺旋锥管"""
        # 生成螺旋线
        spiral_points = self.generate_spiral_points()

        # 绘制螺旋线
        self.msp.add_lwpolyline(spiral_points)

        # 添加波纹标记
        for i in range(self.bands):
            angle = i * (2 * math.pi / self.bands)
            x = self.radius * math.cos(angle)
            y = self.radius * math.sin(angle)

            # 添加波纹标记点
            self.msp.add_circle((x, y, 0), radius=2)

            # 修正：正确设置文本位置
            text = self.msp.add_text(f'波段{i + 1}', dxfattribs={
                'height': 8
            })
            # 使用正确的属性设置文本位置
            text.dxf.insert = (x + 5, y + 5)

    def save_to_dxf(self, filename=None):
        """保存为DXF文件"""
        if filename is None:
            # 使用f-string正确格式化文件名
            filename = f'波纹螺旋锥管_{self.bands}段波.dxf'

        self.generate_pipe()
        self.doc.saveas(filename)
        print(f"文件已保存为: {filename}")


# 测试代码
if __name__ == "__main__":
    # 创建波纹螺旋锥管实例
    pipe = RippleSpiralPipe(bands=5, radius=50, height=150, spiral_turns=2)

    # 方法1：使用默认文件名
    pipe.save_to_dxf()

    # 方法2：自定义文件名
    pipe.save_to_dxf('自定义波纹管.dxf')

    # 创建不同波段的实例
    pipe_8_bands = RippleSpiralPipe(bands=8, radius=60, height=180, spiral_turns=3)
    pipe_8_bands.save_to_dxf()
