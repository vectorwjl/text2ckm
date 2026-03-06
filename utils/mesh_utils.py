"""Mesh utility functions for saving PyVista meshes."""
import meshio
import numpy as np


def save_mesh_as_ply(polydata, output_path: str, binary: bool = False):
    """统一的mesh保存函数

    Args:
        polydata: PyVista PolyData对象
        output_path: 输出文件路径
        binary: 是否使用二进制格式
    """
    points = polydata.points.astype(np.float32)
    faces = polydata.faces.reshape(-1, 4)[:, 1:].astype(np.int32)
    cells = [("triangle", faces)]
    mesh = meshio.Mesh(points, cells)
    meshio.write(output_path, mesh, binary=binary)
