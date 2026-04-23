"""
overlap_checker.py — 检测场景 JSON 中建筑物与道路的 2D 水平投影重叠。

新格式：建筑和道路均使用 vertices([[x,y],...]) + height 描述。

对外接口：
    building_to_polygon(b)         -> shapely Polygon
    road_to_polygon(r)             -> shapely Polygon
    check_overlaps(scene_data)     -> list[dict]
    format_overlap_feedback(overlaps) -> str
"""

from shapely.geometry import Polygon, Point
import math

try:
    from config import ENABLE_ROADS
except ImportError:
    ENABLE_ROADS = True


# ---------------------------------------------------------------------------
# 建筑 footprint 转换
# ---------------------------------------------------------------------------

def _desc_building(idx: int, b: dict) -> str:
    verts = b.get("vertices", [])
    if verts:
        cx = sum(v[0] for v in verts) / len(verts)
        cy = sum(v[1] for v in verts) / len(verts)
        return f"Building {idx} ({len(verts)}-gon centroid=({cx:.1f},{cy:.1f}))"
    return f"Building {idx} (no vertices)"


def building_to_polygon(b: dict) -> Polygon:
    """将建筑转换为 Shapely 2D 多边形（水平投影）。"""
    verts = b.get("vertices", [])
    if len(verts) >= 3:
        return Polygon([(float(v[0]), float(v[1])) for v in verts])
    raise ValueError(f"Building has fewer than 3 vertices: {b}")


# ---------------------------------------------------------------------------
# 道路 footprint 转换
# ---------------------------------------------------------------------------

def _desc_road(idx: int, r: dict) -> str:
    verts = r.get("vertices", [])
    if verts:
        cx = sum(v[0] for v in verts) / len(verts)
        cy = sum(v[1] for v in verts) / len(verts)
        return f"Road {idx} ({len(verts)}-gon centroid=({cx:.1f},{cy:.1f}))"
    return f"Road {idx} (no vertices)"


def road_to_polygon(r: dict) -> Polygon:
    """将道路转换为 Shapely 2D 多边形（水平投影）。"""
    verts = r.get("vertices", [])
    if len(verts) >= 3:
        return Polygon([(float(v[0]), float(v[1])) for v in verts])
    raise ValueError(f"Road has fewer than 3 vertices: {r}")


# ---------------------------------------------------------------------------
# 重叠检测
# ---------------------------------------------------------------------------

def _make_valid(poly):
    """Fix invalid polygon with buffer(0); return None if still invalid."""
    if poly is None:
        return None
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly if poly.is_valid and not poly.is_empty else None


def check_overlaps(scene_data: dict) -> list:
    """
    检测所有建筑-建筑、建筑-道路的 2D footprint 重叠。

    Returns:
        list of dict，每个 dict 包含：
            type: "building_building" | "building_road"
            a_idx, b_idx: 对应索引
            a_desc, b_desc: 描述字符串
            overlap_area_m2: 重叠面积（m²）
            overlap_centroid: (cx, cy) 重叠区域重心
            overlap_bounds: [minx, miny, maxx, maxy]
    """
    buildings = scene_data.get("buildings", [])
    roads = scene_data.get("roads", [])

    b_polys = []
    for i, b in enumerate(buildings):
        try:
            b_polys.append(_make_valid(building_to_polygon(b)))
        except Exception as e:
            print(f"[overlap_checker] WARNING: building {i} skipped: {e}")
            b_polys.append(None)

    r_polys = []
    if ENABLE_ROADS:
        for i, r in enumerate(roads):
            try:
                r_polys.append(_make_valid(road_to_polygon(r)))
            except Exception as e:
                print(f"[overlap_checker] WARNING: road {i} skipped: {e}")
                r_polys.append(None)

    overlaps = []

    # 建筑-建筑
    for i in range(len(buildings)):
        if b_polys[i] is None:
            continue
        for j in range(i + 1, len(buildings)):
            if b_polys[j] is None:
                continue
            try:
                inter = b_polys[i].intersection(b_polys[j])
            except Exception as e:
                print(f"[overlap_checker] WARNING: building {i} × building {j} intersection failed: {e}")
                continue
            if not inter.is_empty and inter.area > 0.01:
                c = inter.centroid
                overlaps.append({
                    "type": "building_building",
                    "a_idx": i, "b_idx": j,
                    "a_desc": _desc_building(i, buildings[i]),
                    "b_desc": _desc_building(j, buildings[j]),
                    "overlap_area_m2": round(inter.area, 4),
                    "overlap_centroid": (round(c.x, 2), round(c.y, 2)),
                    "overlap_bounds": list(inter.bounds),
                })

    # 建筑-道路
    if ENABLE_ROADS:
        for i, bp in enumerate(b_polys):
            if bp is None:
                continue
            for j, rp in enumerate(r_polys):
                if rp is None:
                    continue
                try:
                    inter = bp.intersection(rp)
                except Exception as e:
                    print(f"[overlap_checker] WARNING: building {i} × road {j} intersection failed: {e}")
                    continue
                if not inter.is_empty and inter.area > 0.01:
                    c = inter.centroid
                    overlaps.append({
                        "type": "building_road",
                        "a_idx": i, "b_idx": j,
                        "a_desc": _desc_building(i, buildings[i]),
                        "b_desc": _desc_road(j, roads[j]),
                        "overlap_area_m2": round(inter.area, 4),
                        "overlap_centroid": (round(c.x, 2), round(c.y, 2)),
                        "overlap_bounds": list(inter.bounds),
                    })

    return overlaps
