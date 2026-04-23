"""
overlap_resolver.py — Jacobi-style push-apart 消除建筑物重叠。

新格式：建筑和道路均使用 vertices([[x,y],...]) + height 描述。
道路固定不动，只移动建筑的顶点坐标。

对外接口：
    resolve_overlaps_auto(scene_data, ...) -> (modified_scene_data, converged: bool)
"""

import math
import copy
from overlap_checker import check_overlaps

MAP_HALF_SIZE = 100.0
CLEARANCE = 5.0


def _normalize(dx: float, dy: float) -> tuple:
    d = math.hypot(dx, dy)
    return (dx / d, dy / d) if d > 1e-9 else (1.0, 0.0)


def _centroid(verts: list) -> tuple:
    n = len(verts)
    return (
        sum(float(v[0]) for v in verts) / n,
        sum(float(v[1]) for v in verts) / n,
    )


def _translate_verts(verts: list, dx: float, dy: float) -> list:
    return [
        [round(max(-95.0, min(95.0, float(v[0]) + dx)), 1),
         round(max(-95.0, min(95.0, float(v[1]) + dy)), 1)]
        for v in verts
    ]


def resolve_overlaps_auto(
    scene_data: dict,
    max_iter: int = 150,
    alpha: float = 0.8,
    beta: float = 0.03,
) -> "tuple[dict, bool]":
    """
    Jacobi-style push-apart with elastic restoring force.

    道路固定不动，只移动建筑的 vertices。每轮先对所有建筑累积推力向量
    再同步应用（Jacobi），避免 Gauss-Seidel 的顺序依赖振荡。
    弹性回弹力（beta * (orig_centroid - current_centroid)）防止建筑无限漂移。

    Returns:
        (modified_scene_data, converged: bool)
        若未完全收敛，返回迭代过程中总重叠面积最小的历史快照。
    """
    scene = copy.deepcopy(scene_data)
    buildings = scene["buildings"]

    # 记录原始质心（用于弹性回弹）
    orig_pos = [_centroid(b["vertices"]) for b in buildings]

    best_scene = copy.deepcopy(scene)
    best_area = float("inf")

    for iteration in range(max_iter):
        overlaps = check_overlaps(scene)
        total_area = sum(o["overlap_area_m2"] for o in overlaps)

        if total_area < best_area:
            best_area = total_area
            best_scene = copy.deepcopy(scene)

        if not overlaps:
            return scene, True

        # Jacobi 阶段：先累积所有力向量，不立即应用
        delta = [[0.0, 0.0] for _ in buildings]

        for ov in overlaps:
            cx, cy = ov["overlap_centroid"]
            push = math.sqrt(ov["overlap_area_m2"]) + 0.5

            if ov["type"] == "building_building":
                i, j = ov["a_idx"], ov["b_idx"]
                xi, yi = _centroid(buildings[i]["vertices"])
                xj, yj = _centroid(buildings[j]["vertices"])
                dxi, dyi = _normalize(xi - cx, yi - cy)
                dxj, dyj = _normalize(xj - cx, yj - cy)
                delta[i][0] += dxi * push * alpha
                delta[i][1] += dyi * push * alpha
                delta[j][0] += dxj * push * alpha
                delta[j][1] += dyj * push * alpha

            elif ov["type"] == "building_road":
                i = ov["a_idx"]
                xi, yi = _centroid(buildings[i]["vertices"])
                dxi, dyi = _normalize(xi - cx, yi - cy)
                delta[i][0] += dxi * push * alpha
                delta[i][1] += dyi * push * alpha

        # 同步应用 + 弹性回弹（基于质心偏移量）
        for i, b in enumerate(buildings):
            ox, oy = orig_pos[i]
            cx, cy = _centroid(b["vertices"])
            dx = delta[i][0] + beta * (ox - cx)
            dy = delta[i][1] + beta * (oy - cy)
            b["vertices"] = _translate_verts(b["vertices"], dx, dy)

        if iteration > 0 and iteration % 50 == 0:
            print(f"[resolver] iter {iteration}: {len(overlaps)} overlap(s), "
                  f"total_area={total_area:.1f} m²")

    return best_scene, False
