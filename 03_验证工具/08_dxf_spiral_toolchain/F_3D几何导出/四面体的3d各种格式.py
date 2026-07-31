import numpy as np
import json
import struct
import os
from datetime import datetime


class Simple3DExporter:
    """支持多种简单3D格式的导出器"""

    def __init__(self, vertices, faces, normals=None):
        """
        初始化导出器
        vertices: 顶点坐标列表 [[x1,y1,z1], [x2,y2,z2], ...]
        faces: 面索引列表 [[v1,v2,v3], [v4,v5,v6], ...]
        normals: 法向量列表（可选）
        """
        self.vertices = np.array(vertices)
        self.faces = np.array(faces)
        self.normals = normals if normals is not None else self.calculate_normals()

    def calculate_normals(self):
        """计算面法向量"""
        normals = []
        for face in self.faces:
            if len(face) < 3:
                normals.append([0, 0, 1])
                continue

            v1 = self.vertices[face[1]] - self.vertices[face[0]]
            v2 = self.vertices[face[2]] - self.vertices[face[0]]
            normal = np.cross(v1, v2)
            length = np.linalg.norm(normal)
            if length > 0:
                normal = normal / length
            else:
                normal = [0, 0, 1]
            normals.append(normal)

        return np.array(normals)

    def export_stl_ascii(self, filename):
        """导出ASCII STL格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"solid {os.path.basename(filename)}\n")

            for i, face in enumerate(self.faces):
                normal = self.normals[i] if i < len(self.normals) else [0, 0, 1]
                f.write(f"  facet normal {normal[0]:e} {normal[1]:e} {normal[2]:e}\n")
                f.write("    outer loop\n")

                for vertex_idx in face:
                    if vertex_idx < len(self.vertices):
                        vertex = self.vertices[vertex_idx]
                        f.write(f"      vertex {vertex[0]:e} {vertex[1]:e} {vertex[2]:e}\n")

                f.write("    endloop\n")
                f.write("  endfacet\n")

            f.write(f"endsolid {os.path.basename(filename)}\n")

        print(f"已导出ASCII STL: {filename}")

    def export_stl_binary(self, filename):
        """导出二进制STL格式"""
        with open(filename, 'wb') as f:
            # 80字节头文件
            header = f"Binary STL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(80, '\0')
            f.write(header.encode('ascii'))

            # 面数（4字节无符号整数）
            f.write(struct.pack('<I', len(self.faces)))

            # 每个面的数据
            for i, face in enumerate(self.faces):
                normal = self.normals[i] if i < len(self.normals) else [0.0, 0.0, 1.0]

                # 法向量（3个32位浮点数）
                f.write(struct.pack('<3f', *normal))

                # 三个顶点
                for vertex_idx in face:
                    if vertex_idx < len(self.vertices):
                        vertex = self.vertices[vertex_idx]
                        f.write(struct.pack('<3f', *vertex))
                    else:
                        f.write(struct.pack('<3f', 0.0, 0.0, 0.0))

                # 属性字节计数（2字节）
                f.write(struct.pack('<H', 0))

        print(f"已导出二进制STL: {filename}")

    def export_obj(self, filename):
        """导出Wavefront OBJ格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# OBJ文件 - 导出时间: {datetime.now()}\n")
            f.write(f"# 顶点数: {len(self.vertices)}, 面数: {len(self.faces)}\n\n")

            # 顶点坐标
            for vertex in self.vertices:
                f.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")

            f.write("\n")

            # 法向量
            for normal in self.normals:
                f.write(f"vn {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")

            f.write("\n")

            # 面（注意OBJ索引从1开始）
            for i, face in enumerate(self.faces):
                # 格式: f v1//vn1 v2//vn2 v3//vn3
                face_str = "f"
                for vertex_idx in face:
                    if vertex_idx < len(self.vertices):
                        # 顶点索引和法向量索引（这里使用面的法向量索引）
                        face_str += f" {vertex_idx + 1}//{i + 1}"
                f.write(face_str + "\n")

        print(f"已导出OBJ: {filename}")

    def export_ply_ascii(self, filename):
        """导出ASCII PLY格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"comment 导出时间: {datetime.now()}\n")
            f.write(f"element vertex {len(self.vertices)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write(f"element face {len(self.faces)}\n")
            f.write("property list uchar int vertex_index\n")
            f.write("end_header\n")

            # 顶点数据
            for vertex in self.vertices:
                f.write(f"{vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")

            # 面数据
            for face in self.faces:
                f.write(f"{len(face)}")
                for vertex_idx in face:
                    f.write(f" {vertex_idx}")
                f.write("\n")

        print(f"已导出PLY: {filename}")

    def export_json(self, filename):
        """导出自定义JSON格式"""
        model_data = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "vertex_count": len(self.vertices),
                "face_count": len(self.faces),
                "format_version": "1.0"
            },
            "vertices": self.vertices.tolist(),
            "faces": self.faces.tolist(),
            "normals": self.normals.tolist()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2, ensure_ascii=False)

        print(f"已导出JSON: {filename}")


# 测试用例
def create_test_model():
    """创建一个简单的测试模型（四面体）"""
    # 顶点坐标
    vertices = [
        [0, 0, 0],  # 0
        [1, 0, 0],  # 1
        [0.5, 0.866, 0],  # 2
        [0.5, 0.288, 0.816]  # 3
    ]

    # 面索引
    faces = [
        [0, 1, 2],  # 底面
        [0, 1, 3],  # 侧面1
        [1, 2, 3],  # 侧面2
        [2, 0, 3]  # 侧面3
    ]

    return vertices, faces


def main():
    """主函数 - 演示各种格式导出"""
    print("=== 简单3D格式导出器演示 ===\n")

    # 创建测试模型
    vertices, faces = create_test_model()
    exporter = Simple3DExporter(vertices, faces)

    # 导出各种格式
    base_name = "test_model"

    # ASCII STL
    exporter.export_stl_ascii(f"{base_name}.stl")

    # 二进制 STL
    exporter.export_stl_binary(f"{base_name}_binary.stl")

    # OBJ
    exporter.export_obj(f"{base_name}.obj")

    # PLY
    exporter.export_ply_ascii(f"{base_name}.ply")

    # JSON
    exporter.export_json(f"{base_name}.json")

    print(f"\n所有格式导出完成！")
    print("支持的格式对比：")
    print("1. STL (ASCII) - 工业标准，广泛支持，文件较大")
    print("2. STL (二进制) - 文件小，加载快")
    print("3. OBJ - 文本格式，可读性好，支持材质")
    print("4. PLY - 灵活，支持颜色等属性")
    print("5. JSON - 易于处理，适合Web应用")


if __name__ == "__main__":
    main()
