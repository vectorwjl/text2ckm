"""
overlap_checker.py — 检测场景 JSON 中建筑物与道路的 2D 水平投影重叠。

对外接口：
    building_to_polygon(b)         -> shapely Polygon
    road_to_polygon(r)             -> shapely Polygon
    check_overlaps(scene_data)     -> list[dict]
    format_overlap_feedback(overlaps) -> str
"""

from shapely.geometry import box, Point, LineString, Polygon
from shapely.geometry import JOIN_STYLE
from shapely import affinity
import math


# ---------------------------------------------------------------------------
# 建筑 footprint 转换
# ---------------------------------------------------------------------------

def _desc_building(idx: int, b: dict) -> str:
    btype = b.get("type", "rectangular")
    x = float(b.get("x", 0))
    y = float(b.get("y", 0))
    if btype == "rectangular":
        w = float(b.get("width", 10))
        l = float(b.get("length", w))
        return f"Building {idx} (rectangular at ({x:.2f}, {y:.2f}), {w:.2f}×{l:.2f}m)"
    elif btype == "l_shaped":
        return f"Building {idx} (l_shaped at ({x:.2f}, {y:.2f}))"
    elif btype == "t_shaped":
        return f"Building {idx} (t_shaped at ({x:.2f}, {y:.2f}))"
    elif btype == "u_shaped":
        return f"Building {idx} (u_shaped at ({x:.2f}, {y:.2f}))"
    return f"Building {idx} ({btype} at ({x:.2f}, {y:.2f}))"


def building_to_polygon(b: dict) -> Polygon:
    """将任意建筑类型转换为 Shapely 2D 多边形（水平投影，含旋转）。"""
    btype = b.get("type", "rectangular")
    x = float(b.get("x", 0))
    y = float(b.get("y", 0))

    if btype == "rectangular":
        w = float(b.get("width", 10))
        l = float(b.get("length", b.get("width", 10)))
        poly = box(x - w / 2, y - l / 2, x + w / 2, y + l / 2)

    elif btype == "l_shaped":
        w1 = float(b.get("width1", 10))
        l1 = float(b.get("length1", 10))
        w2 = float(b.get("width2", 5))
        l2 = float(b.get("length2", 5))
        main = box(x - w1 / 2, y - l1 / 2, x + w1 / 2, y + l1 / 2)
        wing_cx = x + w1 / 2 + w2 / 2
        wing_cy = y - l1 / 2 + l2 / 2
        wing = box(wing_cx - w2 / 2, wing_cy - l2 / 2, wing_cx + w2 / 2, wing_cy + l2 / 2)
        poly = main.union(wing)

    elif btype == "t_shaped":
        mw = float(b.get("main_width", 20))
        ml = float(b.get("main_length", 30))
        ww = float(b.get("wing_width", 15))
        wl = float(b.get("wing_length", 10))
        main = box(x - mw / 2, y - ml / 2, x + mw / 2, y + ml / 2)
        left_cx = x - mw / 2 - ww / 2
        left_cy = y + ml / 2 - wl / 2
        left = box(left_cx - ww / 2, left_cy - wl / 2, left_cx + ww / 2, left_cy + wl / 2)
        right_cx = x + mw / 2 + ww / 2
        right_cy = y + ml / 2 - wl / 2
        right = box(right_cx - ww / 2, right_cy - wl / 2, right_cx + ww / 2, right_cy + wl / 2)
        poly = main.union(left).union(right)

    elif btype == "u_shaped":
        ow = float(b.get("outer_width", 40))
        ol = float(b.get("outer_length", 30))
        iw = float(b.get("inner_width", 20))
        il = float(b.get("inner_length", 15))
        outer = box(x - ow / 2, y - ol / 2, x + ow / 2, y + ol / 2)
        inner_cy = y + (ol - il) / 2
        inner = box(x - iw / 2, inner_cy - il / 2, x + iw / 2, inner_cy + il / 2)
        result = outer.difference(inner)
        poly = result if not result.is_empty else outer

    else:
        poly = Point(x, y).buffer(10.0, resolution=16)

    rotation_deg = float(b.get("rotation_deg", 0.0))
    if abs(rotation_deg) > 0.01:
        poly = affinity.rotate(poly, rotation_deg, origin=(x, y))
    return poly


# ---------------------------------------------------------------------------
# 道路 footprint 转换
# ---------------------------------------------------------------------------

def _desc_road(idx: int, r: dict) -> str:
    rtype = r.get("type", "straight")
    w = float(r.get("width", 7))
    if rtype == "straight":
        s = r.get("start", [0, 0])
        e = r.get("end", [0, 0])
        return f"Road {idx} (straight from [{s[0]:.2f}, {s[1]:.2f}] to [{e[0]:.2f}, {e[1]:.2f}], width={w:.2f}m)"
    else:
        pts = r.get("points", [])
        return f"Road {idx} (curved, {len(pts)} points, width={w:.2f}m)"


def road_to_polygon(r: dict) -> Polygon:
    """将道路转换为 Shapely 2D 多边形（水平投影）。"""
    rtype = r.get("type", "straight")
    width = float(r.get("width", 7))

    if rtype == "straight":
        start = r.get("start", [0, 0])
        end = r.get("end", [0, 0])
        sx, sy = float(start[0]), float(start[1])
        ex, ey = float(end[0]), float(end[1])
        dx, dy = ex - sx, ey - sy
        if math.sqrt(dx * dx + dy * dy) < 1e-6:
            return Point(sx, sy).buffer(width / 2)
        line = LineString([(sx, sy), (ex, ey)])
    else:
        pts = r.get("points", [])
        if len(pts) < 2:
            start = r.get("start", [0, 0])
            end = r.get("end", [0, 0])
            pts = [start, end]
        coords = [(float(p[0]), float(p[1])) for p in pts]
        line = LineString(coords)

    return line.buffer(width / 2, cap_style=2)  # cap_style=2 → flat ends


# ---------------------------------------------------------------------------
# 重叠检测
# ---------------------------------------------------------------------------

def check_overlaps(scene_data: dict) -> list:
    """
    检测所有建筑-建筑、建筑-道路、道路-道路的 2D footprint 重叠。

    Returns:
        list of dict，每个 dict 包含：
            type: "building_building" | "building_road" | "road_road"
            a_idx, b_idx: 对应索引
            a_desc, b_desc: 描述字符串
            overlap_area_m2: 重叠面积（m²）
    """
    buildings = scene_data.get("buildings", [])
    roads = scene_data.get("roads", [])

    b_polys = []
    for i, b in enumerate(buildings):
        try:
            poly = building_to_polygon(b)
            b_polys.append((i, b, poly))
        except Exception as e:
            print(f"[overlap_checker] WARNING: failed to convert building {i}: {e}")

    r_polys = []
    for i, r in enumerate(roads):
        try:
            poly = road_to_polygon(r)
            r_polys.append((i, r, poly))
        except Exception as e:
            print(f"[overlap_checker] WARNING: failed to convert road {i}: {e}")

    overlaps = []

    # 建筑 vs 建筑
    for ai in range(len(b_polys)):
        for bi in range(ai + 1, len(b_polys)):
            i, b_a, poly_a = b_polys[ai]
            j, b_b, poly_b = b_polys[bi]
            intersection = poly_a.intersection(poly_b)
            area = intersection.area
            if area > 0.01:  # 忽略 < 0.01 m² 的数值误差
                cx = round(intersection.centroid.x, 2)
                cy = round(intersection.centroid.y, 2)
                bounds = [round(v, 2) for v in intersection.bounds]
                overlaps.append({
                    "type": "building_building",
                    "a_idx": i,
                    "b_idx": j,
                    "a_desc": _desc_building(i, b_a),
                    "b_desc": _desc_building(j, b_b),
                    "overlap_area_m2": round(area, 4),
                    "overlap_centroid": (cx, cy),
                    "overlap_bounds": bounds,
                })

    # 建筑 vs 道路
    for i, b, poly_b in b_polys:
        for j, r, poly_r in r_polys:
            intersection = poly_b.intersection(poly_r)
            area = intersection.area
            if area > 0.01:
                cx = round(intersection.centroid.x, 2)
                cy = round(intersection.centroid.y, 2)
                bounds = [round(v, 2) for v in intersection.bounds]
                overlaps.append({
                    "type": "building_road",
                    "a_idx": i,
                    "b_idx": j,
                    "a_desc": _desc_building(i, b),
                    "b_desc": _desc_road(j, r),
                    "overlap_area_m2": round(area, 4),
                    "overlap_centroid": (cx, cy),
                    "overlap_bounds": bounds,
                })

    # 道路 vs 道路
    for ai in range(len(r_polys)):
        for bi in range(ai + 1, len(r_polys)):
            i, r_a, poly_a = r_polys[ai]
            j, r_b, poly_b = r_polys[bi]
            intersection = poly_a.intersection(poly_b)
            area = intersection.area
            if area > 0.01:
                cx = round(intersection.centroid.x, 2)
                cy = round(intersection.centroid.y, 2)
                bounds = [round(v, 2) for v in intersection.bounds]
                overlaps.append({
                    "type": "road_road",
                    "a_idx": i,
                    "b_idx": j,
                    "a_desc": _desc_road(i, r_a),
                    "b_desc": _desc_road(j, r_b),
                    "overlap_area_m2": round(area, 4),
                    "overlap_centroid": (cx, cy),
                    "overlap_bounds": bounds,
                })

    return overlaps


# ---------------------------------------------------------------------------
# 反馈文本生成
# ---------------------------------------------------------------------------

def format_overlap_feedback(overlaps: list) -> str:
    """将重叠列表格式化为发给 AI 的自然语言反馈。"""
    if not overlaps:
        return ""

    lines = [
        f"OVERLAP ERRORS detected in your scene — please fix all {len(overlaps)} issue(s):",
    ]
    for idx, ov in enumerate(overlaps, 1):
        cx, cy = ov["overlap_centroid"]
        bnd = ov["overlap_bounds"]  # [minx, miny, maxx, maxy]
        lines.append(
            f"{idx}. {ov['a_desc']} overlaps with {ov['b_desc']}. "
            f"Overlap area: {ov['overlap_area_m2']:.2f} m². "
            f"Overlap centroid: ({cx}, {cy}). "
            f"Overlap bounding box: x=[{bnd[0]}, {bnd[2]}], y=[{bnd[1]}, {bnd[3]}]."
        )

    lines += [
        "",
        "Please regenerate the scene JSON with the SAME number of buildings and roads.",
        "Reposition buildings (and/or roads) to eliminate ALL overlaps. Ensure:",
        "- Minimum clearance between any two building footprints: >= 5.0m",
        "- Minimum clearance between building footprint and road edge: >= 5.0m",
        "All coordinates must remain within the original map bounds.",
        "Use 0.01m precision for all coordinates and dimensions.",
    ]
    return "\n".join(lines)
