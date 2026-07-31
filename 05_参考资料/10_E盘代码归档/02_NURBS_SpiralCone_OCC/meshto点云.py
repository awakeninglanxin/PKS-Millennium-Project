import numpy as np
import trimesh
import open3d as o3d


def mesh_to_pointcloud(mesh_path, n_points=10000, compute_normals=True):
    """
    将3D网格文件转换为点云

    参数:
        mesh_path: str, 网格文件路径(.obj, .stl等格式)
        n_points: int, 采样点的数量
        compute_normals: bool, 是否计算法向量

    返回:
        points: numpy array, 形状为(n_points, 3)的点云坐标
        normals: numpy array, 形状为(n_points, 3)的法向量(如果compute_normals=True)
    """
    # 读取网格文件
    mesh = trimesh.load_mesh(mesh_path)

    # 使用trimesh进行点采样
    points, face_indices = trimesh.sample.sample_surface(mesh, n_points)

    if compute_normals:
        # 计算法向量
        normals = mesh.face_normals[face_indices]

        # 转换为open3d点云对象以进行法向量优化
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.normals = o3d.utility.Vector3dVector(normals)

        # 估计法向量并平滑处理
        pcd.estimate_normals()
        pcd.orient_normals_consistent_tangent_plane(100)

        # 转回numpy数组
        normals = np.asarray(pcd.normals)
        return points, normals

    return points


def visualize_pointcloud(points, normals=None):
    """
    使用Open3D可视化点云

    参数:
        points: numpy array, 形状为(n_points, 3)的点云坐标
        normals: numpy array, 可选的法向量数据
    """
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    if normals is not None:
        pcd.normals = o3d.utility.Vector3dVector(normals)

    # 添加颜色使可视化效果更好
    pcd.paint_uniform_color([0.5, 0.5, 0.5])

    # 显示点云
    o3d.visualization.draw_geometries([pcd])


# 使用示例
if __name__ == "__main__":
    mesh_file = "example.obj"  # 替换为您的网格文件路径

    # 转换网格为点云
    points, normals = mesh_to_pointcloud(mesh_file, n_points=10000)

    # 可视化结果
    visualize_pointcloud(points, normals)