"""
Blender场景生成器模块

使用PyVista直接生成PLY文件，不依赖Blender
这样可以避免bpy安装的复杂性，同时保持与现有代码的一致性

支持的功能：
1. 生成建筑物mesh（长方体、圆柱体、L型、T型、U型、圆环）
2. 生成道路mesh（直线、曲线）
3. 导出为PLY格式，兼容Sionna RT
"""

import os
import numpy as np
import pyvista as pv
from typing import Dict, List, Tuple
from utils.mesh_utils import save_mesh_as_ply
from utils.material_utils import normalize_material_name, validate_material


def create_rectangular_building(
    x: float,
    y: float,
    width: float,
    length: float,
    height: float
) -> pv.PolyData:
    """
    创建长方体建筑物

    Args:
        x: 中心X坐标（米）
        y: 中心Y坐标（米）
        width: 宽度（X方向，米）
        length: 长度（Y方向，米）
        height: 高度（Z方向，米）

    Returns:
        PyVista PolyData对象
    """
    # 创建长方体
    box = pv.Box(
        bounds=[
            x - width/2, x + width/2,
            y - length/2, y + length/2,
            0, height
        ]
    )

    # 三角化面片
    triangulated = box.triangulate()

    return triangulated


def create_cylindrical_building(
    x: float,
    y: float,
    radius: float,
    height: float,
    resolution: int = 32
) -> pv.PolyData:
    """
    创建圆柱体建筑物

    Args:
        x: 中心X坐标（米）
        y: 中心Y坐标（米）
        radius: 半径（米）
        height: 高度（米）
        resolution: 圆周分辨率（顶点数）

    Returns:
        PyVista PolyData对象
    """
    # 创建圆柱体
    cylinder = pv.Cylinder(
        center=(x, y, height/2),
        direction=(0, 0, 1),
        radius=radius,
        height=height,
        resolution=resolution
    )

    # 三角化面片
    triangulated = cylinder.triangulate()

    return triangulated


def create_l_shaped_building(
    x: float,
    y: float,
    width1: float,
    length1: float,
    width2: float,
    length2: float,
    height: float
) -> pv.PolyData:
    """
    创建L型建筑物

    Args:
        x: 中心X坐标（米）
        y: 中心Y坐标（米）
        width1: 第一部分宽度（米）
        length1: 第一部分长度（米）
        width2: 第二部分宽度（米）
        length2: 第二部分长度（米）
        height: 高度（米）

    Returns:
        PyVista PolyData对象
    """
    # 创建两个长方体并合并
    box1 = pv.Box(
        bounds=[
            x - width1/2, x + width1/2,
            y - length1/2, y + length1/2,
            0, height
        ]
    )

    box2 = pv.Box(
        bounds=[
            x + width1/2, x + width1/2 + width2,
            y - length1/2, y - length1/2 + length2,
            0, height
        ]
    )

    # 合并两个box
    combined = box1 + box2

    # 三角化
    triangulated = combined.triangulate()

    return triangulated


def create_t_shaped_building(
    x: float,
    y: float,
    main_width: float,
    main_length: float,
    wing_width: float,
    wing_length: float,
    height: float
) -> pv.PolyData:
    """
    创建T型建筑物（商业综合体）

    Args:
        x: 中心X坐标（米）
        y: 中心Y坐标（米）
        main_width: 主体部分宽度（X方向，米）
        main_length: 主体部分长度（Y方向，米）
        wing_width: 横向翼部宽度（米）
        wing_length: 横向翼部长度（米）
        height: 高度（米）

    Returns:
        PyVista PolyData对象
    """
    # 创建主体长方体（竖直部分）
    main_box = pv.Box(
        bounds=[
            x - main_width/2, x + main_width/2,
            y - main_length/2, y + main_length/2,
            0, height
        ]
    )

    # 创建左侧翼
    left_wing = pv.Box(
        bounds=[
            x - main_width/2 - wing_width, x - main_width/2,
            y + main_length/2 - wing_length, y + main_length/2,
            0, height
        ]
    )

    # 创建右侧翼
    right_wing = pv.Box(
        bounds=[
            x + main_width/2, x + main_width/2 + wing_width,
            y + main_length/2 - wing_length, y + main_length/2,
            0, height
        ]
    )

    # 合并三个部分
    combined = main_box + left_wing + right_wing

    # 三角化
    triangulated = combined.triangulate()

    return triangulated


def create_u_shaped_building(
    x: float,
    y: float,
    outer_width: float,
    outer_length: float,
    inner_width: float,
    inner_length: float,
    height: float
) -> pv.PolyData:
    """
    创建U型建筑物（庭院式建筑）

    Args:
        x: 中心X坐标（米）
        y: 中心Y坐标（米）
        outer_width: 外围宽度（X方向，米）
        outer_length: 外围长度（Y方向，米）
        inner_width: 内部庭院宽度（米）
        inner_length: 内部庭院长度（米）
        height: 高度（米）

    Returns:
        PyVista PolyData对象
    """
    # 创建外部大长方体
    outer_box = pv.Box(
        bounds=[
            x - outer_width/2, x + outer_width/2,
            y - outer_length/2, y + outer_length/2,
            0, height
        ]
    )

    # 创建内部庭院（需要挖空的部分，位于上方）
    inner_box = pv.Box(
        bounds=[
            x - inner_width/2, x + inner_width/2,
            y, y + outer_length/2,
            -0.1, height + 0.1  # 稍微扩展以确保布尔运算成功
        ]
    )

    # 使用布尔差运算
    try:
        u_shaped = outer_box.boolean_difference(inner_box)
        triangulated = u_shaped.triangulate()
    except Exception as e:
        print(f"Warning: Boolean operation failed, using fallback method: {e}")
        # 备用方案：手动创建三个长方体组成U型
        left_part = pv.Box(
            bounds=[
                x - outer_width/2, x - inner_width/2,
                y - outer_length/2, y + outer_length/2,
                0, height
            ]
        )
        right_part = pv.Box(
            bounds=[
                x + inner_width/2, x + outer_width/2,
                y - outer_length/2, y + outer_length/2,
                0, height
            ]
        )
        bottom_part = pv.Box(
            bounds=[
                x - outer_width/2, x + outer_width/2,
                y - outer_length/2, y,
                0, height
            ]
        )
        combined = left_part + right_part + bottom_part
        triangulated = combined.triangulate()

    return triangulated


def create_ring_building(
    x: float,
    y: float,
    outer_radius: float,
    inner_radius: float,
    height: float,
    resolution: int = 32
) -> pv.PolyData:
    """
    创建圆环建筑物（体育场）

    Args:
        x: 中心X坐标（米）
        y: 中心Y坐标（米）
        outer_radius: 外半径（米）
        inner_radius: 内半径（米）
        height: 高度（米）
        resolution: 圆周分辨率（顶点数）

    Returns:
        PyVista PolyData对象
    """
    # 创建外圆柱
    outer_cylinder = pv.Cylinder(
        center=(x, y, height/2),
        direction=(0, 0, 1),
        radius=outer_radius,
        height=height,
        resolution=resolution
    )

    # 创建内圆柱（用于挖空）
    inner_cylinder = pv.Cylinder(
        center=(x, y, height/2),
        direction=(0, 0, 1),
        radius=inner_radius,
        height=height + 0.2,  # 稍微高一点以确保布尔运算成功
        resolution=resolution
    )

    # 使用布尔差运算
    try:
        ring = outer_cylinder.boolean_difference(inner_cylinder)
        triangulated = ring.triangulate()
    except Exception as e:
        print(f"Warning: Boolean operation failed for ring building: {e}")
        # 备用方案：使用参数化方法手动创建圆环
        triangulated = _create_ring_fallback(x, y, outer_radius, inner_radius, height, resolution)

    return triangulated


def _create_ring_fallback(
    x: float,
    y: float,
    outer_radius: float,
    inner_radius: float,
    height: float,
    resolution: int
) -> pv.PolyData:
    """圆环建筑的备用实现方法"""
    theta = np.linspace(0, 2*np.pi, resolution, endpoint=False)

    # 创建顶点
    vertices = []
    # 底部外圈
    for t in theta:
        vertices.append([x + outer_radius * np.cos(t), y + outer_radius * np.sin(t), 0])
    # 底部内圈
    for t in theta:
        vertices.append([x + inner_radius * np.cos(t), y + inner_radius * np.sin(t), 0])
    # 顶部外圈
    for t in theta:
        vertices.append([x + outer_radius * np.cos(t), y + outer_radius * np.sin(t), height])
    # 顶部内圈
    for t in theta:
        vertices.append([x + inner_radius * np.cos(t), y + inner_radius * np.sin(t), height])

    vertices = np.array(vertices)

    # 创建面
    faces = []
    n = resolution
    # 外侧面
    for i in range(n):
        next_i = (i + 1) % n
        faces.extend([[3, i, next_i, next_i + 2*n], [3, i, next_i + 2*n, i + 2*n]])
    # 内侧面
    for i in range(n):
        next_i = (i + 1) % n
        faces.extend([[3, i + n, i + 3*n, next_i + 3*n], [3, i + n, next_i + 3*n, next_i + n]])
    # 底面
    for i in range(n):
        next_i = (i + 1) % n
        faces.extend([[3, i, i + n, next_i + n], [3, i, next_i + n, next_i]])
    # 顶面
    for i in range(n):
        next_i = (i + 1) % n
        faces.extend([[3, i + 2*n, next_i + 2*n, next_i + 3*n], [3, i + 2*n, next_i + 3*n, i + 3*n]])

    faces = np.array(faces)
    ring_mesh = pv.PolyData(vertices, faces)
    return ring_mesh.triangulate()


def create_curved_road(
    points: List[Tuple[float, float]],
    width: float,
    height: float = 0.25,
    smooth: bool = True
) -> pv.PolyData:
    """
    创建曲线道路

    Args:
        points: 控制点列表 [(x1, y1), (x2, y2), ...]
        width: 道路宽度（米）
        height: 道路高度（米，默认0.25）
        smooth: 是否使用样条插值平滑（默认True）

    Returns:
        PyVista PolyData对象
    """
    if len(points) < 2:
        raise ValueError("Curved road requires at least 2 points")

    points_array = np.array(points)

    # 如果需要平滑，使用样条插值
    if smooth and len(points) > 2:
        from scipy.interpolate import splprep, splev
        # 参数化样条插值
        tck, u = splprep([points_array[:, 0], points_array[:, 1]], s=0, k=min(3, len(points)-1))
        # 生成更多插值点
        u_fine = np.linspace(0, 1, len(points) * 20)
        x_fine, y_fine = splev(u_fine, tck)
        path_points = np.column_stack([x_fine, y_fine])
    else:
        path_points = points_array

    # 沿路径生成道路mesh
    half_width = width / 2
    num_points = len(path_points)

    # 计算每个点的切线方向
    tangents = np.zeros((num_points, 2))
    for i in range(num_points):
        if i == 0:
            tangents[i] = path_points[1] - path_points[0]
        elif i == num_points - 1:
            tangents[i] = path_points[i] - path_points[i-1]
        else:
            tangents[i] = path_points[i+1] - path_points[i-1]

        # 归一化
        norm = np.linalg.norm(tangents[i])
        if norm > 0:
            tangents[i] /= norm

    # 计算垂直方向（用于道路宽度）
    normals = np.column_stack([-tangents[:, 1], tangents[:, 0]])

    # 生成道路边缘顶点
    vertices = []
    # 底部左边缘
    for i in range(num_points):
        p = path_points[i] + normals[i] * half_width
        vertices.append([p[0], p[1], 0])
    # 底部右边缘
    for i in range(num_points):
        p = path_points[i] - normals[i] * half_width
        vertices.append([p[0], p[1], 0])
    # 顶部左边缘
    for i in range(num_points):
        p = path_points[i] + normals[i] * half_width
        vertices.append([p[0], p[1], height])
    # 顶部右边缘
    for i in range(num_points):
        p = path_points[i] - normals[i] * half_width
        vertices.append([p[0], p[1], height])

    vertices = np.array(vertices)

    # 创建面
    faces = []
    for i in range(num_points - 1):
        # 底面
        faces.extend([[3, i, i+1, i+1+num_points], [3, i, i+1+num_points, i+num_points]])
        # 顶面
        faces.extend([[3, i+2*num_points, i+1+3*num_points, i+1+2*num_points],
                     [3, i+2*num_points, i+3*num_points, i+1+3*num_points]])
        # 左侧面
        faces.extend([[3, i, i+2*num_points, i+1+2*num_points], [3, i, i+1+2*num_points, i+1]])
        # 右侧面
        faces.extend([[3, i+num_points, i+1+num_points, i+1+3*num_points],
                     [3, i+num_points, i+1+3*num_points, i+3*num_points]])

    # 封闭起点和终点
    # 起点
    faces.extend([[3, 0, num_points, 2*num_points], [3, num_points, 3*num_points, 2*num_points]])
    # 终点
    last = num_points - 1
    faces.extend([[3, last, last+2*num_points, last+3*num_points],
                 [3, last, last+3*num_points, last+num_points]])

    faces = np.array(faces)
    road_mesh = pv.PolyData(vertices, faces)

    return road_mesh.triangulate()


def _get_building_aabb(b: dict) -> tuple:
    """返回建筑物2D占地的轴对齐包围盒 (x_min, x_max, y_min, y_max)"""
    btype = b.get("type", "rectangular")
    x = float(b.get("x", 0))
    y = float(b.get("y", 0))
    if btype == "cylindrical":
        r = float(b.get("radius", 5))
        return (x - r, x + r, y - r, y + r)
    elif btype == "l_shaped":
        w = max(float(b.get("width1", 10)), float(b.get("width2", 5)))
        l = float(b.get("length1", 10)) + float(b.get("length2", 5))
        return (x - w/2, x + w/2, y - l/2, y + l/2)
    elif btype == "t_shaped":
        w = max(float(b.get("main_width", 20)), float(b.get("wing_width", 15)))
        l = float(b.get("main_length", 30)) + float(b.get("wing_length", 10))
        return (x - w/2, x + w/2, y - l/2, y + l/2)
    elif btype == "u_shaped":
        w = float(b.get("outer_width", 40))
        l = float(b.get("outer_length", 30))
        return (x - w/2, x + w/2, y - l/2, y + l/2)
    elif btype == "ring":
        r = float(b.get("outer_radius", 50))
        return (x - r, x + r, y - r, y + r)
    else:  # rectangular
        w = float(b.get("width", 10))
        l = float(b.get("length", b.get("width", 10)))
        return (x - w/2, x + w/2, y - l/2, y + l/2)


def _road_overlaps_building(r: dict, aabb: tuple) -> bool:
    """用SAT检测直线道路矩形与建筑AABB是否重叠，曲线道路跳过"""
    if r.get("type", "straight") != "straight":
        return False
    x1, y1 = r.get("start", [-50, 0])
    x2, y2 = r.get("end", [50, 0])
    half_w = float(r.get("width", 7)) / 2
    dx, dy = x2 - x1, y2 - y1
    road_len = np.sqrt(dx*dx + dy*dy)
    if road_len < 1e-6:
        return False
    ux, uy = dx / road_len, dy / road_len
    px, py = -uy, ux
    road_corners = np.array([
        [x1 + px*half_w, y1 + py*half_w],
        [x1 - px*half_w, y1 - py*half_w],
        [x2 - px*half_w, y2 - py*half_w],
        [x2 + px*half_w, y2 + py*half_w],
    ])
    bx0, bx1, by0, by1 = aabb
    bld_corners = np.array([[bx0, by0], [bx1, by0], [bx1, by1], [bx0, by1]])
    for ax, ay in [(ux, uy), (px, py), (1.0, 0.0), (0.0, 1.0)]:
        axis = np.array([ax, ay])
        rp = road_corners @ axis
        bp = bld_corners @ axis
        if rp.max() < bp.min() or bp.max() < rp.min():
            return False
    return True


def _shift_building_off_road(b: dict, r: dict, margin: float = 5.0) -> dict:
    """将建筑沿道路法线方向移出道路，保留足够间距"""
    x1, y1 = r.get("start", [-50, 0])
    x2, y2 = r.get("end", [50, 0])
    road_width = float(r.get("width", 7))
    dx, dy = x2 - x1, y2 - y1
    road_len = np.sqrt(dx*dx + dy*dy)
    if road_len < 1e-6:
        return b
    px, py = -dy / road_len, dx / road_len
    bx = float(b.get("x", 0))
    by = float(b.get("y", 0))
    signed_dist = (bx - x1) * px + (by - y1) * py
    aabb = _get_building_aabb(b)
    bx0, bx1, by0, by1 = aabb
    half_size = max(bx1 - bx, bx - bx0, by1 - by, by - by0)
    required = road_width / 2 + half_size + margin
    if abs(signed_dist) < required:
        direction = 1.0 if signed_dist >= 0 else -1.0
        shift = required * direction - signed_dist
        b = dict(b)
        b["x"] = bx + px * shift
        b["y"] = by + py * shift
    return b


def resolve_building_road_collisions(
    buildings: list,
    roads: list,
    margin: float = 5.0,
    max_iterations: int = 3,
) -> list:
    """迭代检测并修正建筑与道路的碰撞，通过移动建筑来消除重叠"""
    adjusted = [dict(b) for b in buildings]
    for _ in range(max_iterations):
        collision_found = False
        for i, b in enumerate(adjusted):
            for r in roads:
                if r.get("type", "straight") != "straight":
                    continue
                if _road_overlaps_building(r, _get_building_aabb(b)):
                    adjusted[i] = _shift_building_off_road(b, r, margin)
                    b = adjusted[i]
                    collision_found = True
        if not collision_found:
            break
    return adjusted


def generate_scene_from_description(
    scene_data: dict,
    scene_dir: str,
) -> list:
    """
    根据场景描述生成所有mesh文件，返回 (ply_path, material) 元组列表

    Args:
        scene_data: 包含 buildings 和 roads 的场景描述 dict
        scene_dir: 场景目录路径

    Returns:
        list of (ply_path: str, material: str)
    """
    mesh_dir = os.path.join(scene_dir, "mesh")
    os.makedirs(mesh_dir, exist_ok=True)

    results = []
    buildings = scene_data.get("buildings", [])
    roads = scene_data.get("roads", [])

    # 解决建筑与道路的碰撞，移动建筑使其不与道路重叠
    if buildings and roads:
        buildings = resolve_building_road_collisions(buildings, roads)

    for i, b in enumerate(buildings):
        btype = b.get("type", "rectangular")
        x = float(b.get("x", 0))
        y = float(b.get("y", 0))
        height = float(b.get("height", 10))

        if btype == "cylindrical":
            radius = float(b.get("radius", 5))
            mesh = create_cylindrical_building(x, y, radius, height)
        elif btype == "l_shaped":
            mesh = create_l_shaped_building(
                x, y,
                float(b.get("width1", 10)), float(b.get("length1", 10)),
                float(b.get("width2", 5)), float(b.get("length2", 5)),
                height
            )
        elif btype == "t_shaped":
            mesh = create_t_shaped_building(
                x, y,
                float(b.get("main_width", 20)), float(b.get("main_length", 30)),
                float(b.get("wing_width", 15)), float(b.get("wing_length", 10)),
                height
            )
        elif btype == "u_shaped":
            mesh = create_u_shaped_building(
                x, y,
                float(b.get("outer_width", 40)), float(b.get("outer_length", 30)),
                float(b.get("inner_width", 20)), float(b.get("inner_length", 15)),
                height
            )
        elif btype == "ring":
            mesh = create_ring_building(
                x, y,
                float(b.get("outer_radius", 50)), float(b.get("inner_radius", 40)),
                height
            )
        else:
            width = float(b.get("width", 10))
            length = float(b.get("length", b.get("width", 10)))
            mesh = create_rectangular_building(x, y, width, length, height)

        ply_path = os.path.join(mesh_dir, f"building_{i}.ply")
        save_mesh_as_ply(mesh, ply_path)

        # 获取建筑材质（支持用户指定，默认为concrete）
        material = validate_material(
            normalize_material_name(b.get("material", "concrete")),
            object_type="building"
        )
        results.append((ply_path, material))

    for i, r in enumerate(roads):
        rtype = r.get("type", "straight")
        width = float(r.get("width", 7))

        if rtype == "straight":
            start = tuple(r.get("start", [-50, 0]))
            end = tuple(r.get("end", [50, 0]))
            mesh = create_straight_road(start, end, width)
        elif rtype == "curved":
            points = r.get("points", [[-50, 0], [0, 20], [50, 0]])
            smooth = r.get("smooth", True)
            mesh = create_curved_road(points, width, smooth=smooth)
        else:
            # 默认使用直线道路
            start = tuple(r.get("start", [-50, 0]))
            end = tuple(r.get("end", [50, 0]))
            mesh = create_straight_road(start, end, width)

        ply_path = os.path.join(mesh_dir, f"road_{i}.ply")
        save_mesh_as_ply(mesh, ply_path)

        # 获取道路材质（支持用户指定，默认为marble）
        material = validate_material(
            normalize_material_name(r.get("material", "marble")),
            object_type="road"
        )
        results.append((ply_path, material))

    return results


def create_straight_road(
    start: Tuple[float, float],
    end: Tuple[float, float],
    width: float,
    height: float = 0.25
) -> pv.PolyData:
    """
    创建直线道路

    Args:
        start: 起点坐标 (x, y)
        end: 终点坐标 (x, y)
        width: 道路宽度（米）
        height: 道路高度（米，默认0.25）

    Returns:
        PyVista PolyData对象
    """
    x1, y1 = start
    x2, y2 = end

    # 计算道路方向向量
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx**2 + dy**2)

    # 归一化方向向量
    if length > 0:
        dx /= length
        dy /= length

    # 计算垂直方向（用于宽度）
    perp_x = -dy
    perp_y = dx

    # 计算四个角点
    half_width = width / 2
    corners = np.array([
        [x1 + perp_x * half_width, y1 + perp_y * half_width, 0],
        [x1 - perp_x * half_width, y1 - perp_y * half_width, 0],
        [x2 - perp_x * half_width, y2 - perp_y * half_width, 0],
        [x2 + perp_x * half_width, y2 + perp_y * half_width, 0],
        [x1 + perp_x * half_width, y1 + perp_y * half_width, height],
        [x1 - perp_x * half_width, y1 - perp_y * half_width, height],
        [x2 - perp_x * half_width, y2 - perp_y * half_width, height],
        [x2 + perp_x * half_width, y2 + perp_y * half_width, height],
    ])

    # 定义面（使用三角形）
    faces = np.array([
        # 底面
        [3, 0, 1, 2],
        [3, 0, 2, 3],
        # 顶面
        [3, 4, 6, 5],
        [3, 4, 7, 6],
        # 侧面
        [3, 0, 4, 5], [3, 0, 5, 1],
        [3, 1, 5, 6], [3, 1, 6, 2],
        [3, 2, 6, 7], [3, 2, 7, 3],
        [3, 3, 7, 4], [3, 3, 4, 0],
    ])

    # 创建PolyData
    road_mesh = pv.PolyData(corners, faces)

    # 三角化
    triangulated = road_mesh.triangulate()

    return triangulated
