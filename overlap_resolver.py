"""
overlap_resolver.py — 计算消除建筑物重叠的具体移动建议，并格式化为 AI-1 反馈。

核心算法（push-apart）：
  1. 对每对重叠建筑 (A, B)，根据布局风格选择推开方向，计算各自需要被推开的距离。
  2. 每对的位移由两栋建筑各承担一半。
  3. 应用上述位移后，检查移动后的建筑是否会撞到原本无重叠的建筑；
     若会，则同时给那些原本无重叠的建筑分配避让位移。
  4. 所有最终位置裁剪到地图边界（200m × 200m，即 ±100m）。
  5. 输出每栋建筑的目标新坐标和移动原因，供 AI-1 直接照做。

布局风格策略：
  orthogonal_grid / slab_row — 轴对齐推开（沿 X 轴或 Y 轴，取主要分量方向）
  radial                     — 沿各自径向射线推开（远的向外，近的向内）
  其他 / None                — 默认中心连线方向推开

对外接口：
    resolve_overlaps(scene_data, overlaps, style, ...) -> dict[int, dict]
    format_resolution_feedback(scene_data, overlaps, moves) -> str
"""

import math
import copy
from overlap_checker import building_to_polygon, _desc_building, check_overlaps


MAP_HALF_SIZE = 100.0      # 200m × 200m 场景：坐标范围 ±100m
CLEARANCE = 5.0            # 建筑物之间最小净距

# 使用轴对齐推开的风格
_AXIS_SNAP_STYLES = {"orthogonal_grid", "slab_row"}
# 使用径向推开的风格
_RADIAL_STYLES = {"radial"}


def _project_extent(poly, cx, cy, ux, uy) -> float:
    """多边形相对中心 (cx,cy) 沿单位方向 (ux,uy) 的最大半投影长度。"""
    coords = list(poly.exterior.coords)
    max_proj = 0.0
    for px, py in coords:
        proj = (px - cx) * ux + (py - cy) * uy
        if abs(proj) > max_proj:
            max_proj = abs(proj)
    return max_proj


def _compute_pair_push(
    style: "str | None",
    i: int,
    j: int,
    centers: list,
    polys: list,
    clearance: float,
) -> "tuple[float, float, float, float]":
    """
    计算一对重叠建筑 (i, j) 各自需要的位移向量。

    返回 (dx_i, dy_i, dx_j, dy_j)：
      - (dx_i, dy_i) 加到建筑 i 的累计位移
      - (dx_j, dy_j) 加到建筑 j 的累计位移
    """
    cx_i, cy_i = centers[i]
    cx_j, cy_j = centers[j]
    poly_i, poly_j = polys[i], polys[j]

    raw_dx = cx_i - cx_j
    raw_dy = cy_i - cy_j
    dist = math.sqrt(raw_dx ** 2 + raw_dy ** 2)
    if dist < 0.01:
        raw_dx, raw_dy = 1.0, 0.0
        dist = 0.01

    if style in _AXIS_SNAP_STYLES:
        # --- 轴对齐推开：沿主轴方向（X 或 Y）---
        if abs(raw_dx) >= abs(raw_dy):
            ux, uy = (1.0 if raw_dx >= 0 else -1.0), 0.0
            dist_along = abs(raw_dx)
        else:
            ux, uy = 0.0, (1.0 if raw_dy >= 0 else -1.0)
            dist_along = abs(raw_dy)

        if dist_along < 0.01:
            dist_along = 0.01

        proj_i = _project_extent(poly_i, cx_i, cy_i, ux, uy)
        proj_j = _project_extent(poly_j, cx_j, cy_j, ux, uy)
        required = proj_i + proj_j + clearance
        push = max(0.0, required - dist_along) / 2

        dx_i =  ux * push
        dy_i =  uy * push
        dx_j = -ux * push
        dy_j = -uy * push

    elif style in _RADIAL_STYLES:
        # --- 径向推开：各自沿径向射线（较远的向外，较近的向内）---
        r_i = math.sqrt(cx_i ** 2 + cy_i ** 2)
        r_j = math.sqrt(cx_j ** 2 + cy_j ** 2)
        ray_ix = cx_i / r_i if r_i > 0.01 else 1.0
        ray_iy = cy_i / r_i if r_i > 0.01 else 0.0
        ray_jx = cx_j / r_j if r_j > 0.01 else -1.0
        ray_jy = cy_j / r_j if r_j > 0.01 else 0.0

        proj_i = _project_extent(poly_i, cx_i, cy_i, ray_ix, ray_iy)
        proj_j = _project_extent(poly_j, cx_j, cy_j, ray_jx, ray_jy)
        required = proj_i + proj_j + clearance
        push = max(0.0, required - dist) / 2

        # 较远的建筑向外推，较近的向内推（朝向原点方向）
        if r_i >= r_j:
            dx_i =  ray_ix * push
            dy_i =  ray_iy * push
            dx_j = -ray_jx * push
            dy_j = -ray_jy * push
        else:
            dx_i = -ray_ix * push
            dy_i = -ray_iy * push
            dx_j =  ray_jx * push
            dy_j =  ray_jy * push

    else:
        # --- 默认：沿中心连线方向推开（point_scatter / cluster / perimeter / organic）---
        ux, uy = raw_dx / dist, raw_dy / dist
        proj_i = _project_extent(poly_i, cx_i, cy_i, ux, uy)
        proj_j = _project_extent(poly_j, cx_j, cy_j, ux, uy)
        required = proj_i + proj_j + clearance
        push = max(0.0, required - dist) / 2

        dx_i =  ux * push
        dy_i =  uy * push
        dx_j = -ux * push
        dy_j = -uy * push

    return dx_i, dy_i, dx_j, dy_j


def resolve_overlaps(
    scene_data: dict,
    overlaps: list,
    style: "str | None" = None,
    map_half: float = MAP_HALF_SIZE,
    clearance: float = CLEARANCE,
) -> dict:
    """
    返回 {building_idx: {"old_x", "old_y", "new_x", "new_y", "dx", "dy", "reason"}}
    只包含需要移动的建筑（dx 或 dy 非零）。
    """
    buildings = scene_data.get("buildings", [])
    n = len(buildings)
    if n == 0 or not overlaps:
        return {}

    # 预计算每栋建筑的多边形和中心
    polys = []
    centers = []
    for b in buildings:
        try:
            poly = building_to_polygon(b)
        except Exception:
            poly = None
        polys.append(poly)
        centers.append((float(b.get("x", 0)), float(b.get("y", 0))))

    # 标记参与重叠的建筑
    overlapping_idx = set()
    for ov in overlaps:
        if ov.get("type") == "building_building":
            overlapping_idx.add(ov["a_idx"])
            overlapping_idx.add(ov["b_idx"])

    # === 第一步：为重叠对计算推开向量（按风格选择策略）===
    moves = [[0.0, 0.0] for _ in range(n)]
    for ov in overlaps:
        if ov.get("type") != "building_building":
            continue
        i, j = ov["a_idx"], ov["b_idx"]
        if polys[i] is None or polys[j] is None:
            continue
        dx_i, dy_i, dx_j, dy_j = _compute_pair_push(
            style, i, j, centers, polys, clearance
        )
        moves[i][0] += dx_i
        moves[i][1] += dy_i
        moves[j][0] += dx_j
        moves[j][1] += dy_j

    # === 第二步：检查移动后是否会撞到原本无重叠的建筑 ===
    new_centers = [
        (centers[i][0] + moves[i][0], centers[i][1] + moves[i][1])
        for i in range(n)
    ]
    non_overlapping = set(range(n)) - overlapping_idx

    for moved_i in overlapping_idx:
        if polys[moved_i] is None:
            continue
        for static_j in non_overlapping:
            if polys[static_j] is None:
                continue
            cx_i, cy_i = new_centers[moved_i]
            cx_j = centers[static_j][0] + moves[static_j][0]
            cy_j = centers[static_j][1] + moves[static_j][1]
            dx = cx_j - cx_i
            dy = cy_j - cy_i
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.01:
                ux, uy = 1.0, 0.0
                dist = 0.01
            else:
                ux, uy = dx / dist, dy / dist
            proj_i = _project_extent(polys[moved_i], 0, 0, ux, uy)
            proj_j = _project_extent(polys[static_j], 0, 0, ux, uy)
            required = proj_i + proj_j + clearance
            if dist < required:
                # 把 static_j 沿 (ux, uy) 推开
                push = required - dist
                moves[static_j][0] += ux * push
                moves[static_j][1] += uy * push

    # === 第三步：裁剪到地图边界并整理输出 ===
    result_moves = {}
    for i in range(n):
        dx_total, dy_total = moves[i][0], moves[i][1]
        if abs(dx_total) < 0.01 and abs(dy_total) < 0.01:
            continue
        old_x, old_y = centers[i]
        nx = old_x + dx_total
        ny = old_y + dy_total
        # 裁剪到 ±map_half 内（考虑建筑的半投影长度，避免越界）
        if polys[i] is not None:
            half_w = _project_extent(polys[i], old_x, old_y, 1.0, 0.0)
            half_h = _project_extent(polys[i], old_x, old_y, 0.0, 1.0)
        else:
            half_w = half_h = 5.0
        nx = max(-map_half + half_w, min(map_half - half_w, nx))
        ny = max(-map_half + half_h, min(map_half - half_h, ny))

        if i in overlapping_idx:
            reason = "overlapping — must move to clear collision"
        else:
            reason = "make room for repositioned overlapping building(s)"

        result_moves[i] = {
            "old_x": round(old_x, 2),
            "old_y": round(old_y, 2),
            "new_x": round(nx, 2),
            "new_y": round(ny, 2),
            "dx": round(nx - old_x, 2),
            "dy": round(ny - old_y, 2),
            "reason": reason,
        }
    return result_moves


def format_resolution_feedback(
    scene_data: dict,
    overlaps: list,
    moves: dict,
    map_half: float = MAP_HALF_SIZE,
) -> str:
    """将算法计算出的移动建议格式化为发给 AI-1 的自然语言反馈。"""
    if not moves:
        return ""
    buildings = scene_data.get("buildings", [])
    lines = [
        "",
        "=== ALGORITHMIC OVERLAP RESOLUTION SUGGESTIONS ===",
        f"Map bounds: x ∈ [-{map_half:.0f}, +{map_half:.0f}] m, y ∈ [-{map_half:.0f}, +{map_half:.0f}] m.",
        f"An algorithm computed precise target positions for {len(moves)} building(s).",
        "Apply the new (x, y) values BELOW exactly as given (or stay within ±2 m of them).",
        "Keep all OTHER fields (height, width, length, rotation_deg, type, material) UNCHANGED.",
        "",
    ]
    # 先列出有重叠的建筑（必须移动）
    overlap_idx = sorted(i for i, m in moves.items() if "overlapping" in m["reason"])
    bystander_idx = sorted(i for i, m in moves.items() if i not in overlap_idx)

    if overlap_idx:
        lines.append("[Buildings that MUST move to remove overlaps]")
        for i in overlap_idx:
            m = moves[i]
            b = buildings[i] if i < len(buildings) else {}
            desc = _desc_building(i, b)
            lines.append(
                f"  - {desc}\n"
                f"      OLD (x, y) = ({m['old_x']}, {m['old_y']})\n"
                f"      NEW (x, y) = ({m['new_x']}, {m['new_y']})    [shift by Δx={m['dx']:+.2f}, Δy={m['dy']:+.2f}]"
            )
    if bystander_idx:
        lines.append("")
        lines.append("[Buildings that should ALSO move to make room (avoid creating new overlaps)]")
        for i in bystander_idx:
            m = moves[i]
            b = buildings[i] if i < len(buildings) else {}
            desc = _desc_building(i, b)
            lines.append(
                f"  - {desc}\n"
                f"      OLD (x, y) = ({m['old_x']}, {m['old_y']})\n"
                f"      NEW (x, y) = ({m['new_x']}, {m['new_y']})    [shift by Δx={m['dx']:+.2f}, Δy={m['dy']:+.2f}]"
            )
    lines += [
        "",
        f"After applying these moves, re-verify ALL pairs: every two buildings must be ≥ {CLEARANCE:.1f} m apart edge-to-edge.",
        "Do NOT change the number, type, height, dimensions or rotation of any building.",
        "Output the corrected scene JSON with the SAME ordering of buildings.",
        "=== END ALGORITHMIC SUGGESTIONS ===",
    ]
    return "\n".join(lines)


def iteratively_resolve(
    scene_data: dict,
    style: "str | None" = None,
    max_iterations: int = 100,
    map_half: float = MAP_HALF_SIZE,
    clearance: float = CLEARANCE,
    verbose: bool = True,
) -> dict:
    """
    原地修改 scene_data：反复调用 check_overlaps + resolve_overlaps，
    把算法算出的 new_x / new_y 直接写回每栋建筑的 x / y。

    终止条件：
      - 某步检测到零重叠 → 直接使用该状态（converged=True）
      - 跑满 max_iterations 步仍有重叠 → 恢复重叠数最少的那一步状态（converged=False）

    只修改每栋建筑的 x, y 字段；height / width / length / rotation_deg /
    type / material 等其他字段保持不变。

    Returns:
        {
          "converged":           bool,     # 是否真的无重叠
          "iterations":          int,      # 实际跑了几轮
          "final_overlaps":      list,     # 最终采用状态的 check_overlaps 结果
          "moved_indices":       set[int], # 本次解析中被移动过的建筑编号集合
          "best_overlap_count":  int,      # 历史最低重叠数（converged 时为 0）
        }
    """
    moved_indices: set = set()
    best_count = float("inf")     # 历史最低重叠数
    best_snapshot: "list | None" = None  # 对应的建筑列表深拷贝

    for iteration in range(1, max_iterations + 1):
        overlaps = check_overlaps(scene_data)
        n_overlaps = len(overlaps)

        # 更新最优快照
        if n_overlaps < best_count:
            best_count = n_overlaps
            best_snapshot = copy.deepcopy(scene_data.get("buildings", []))

        if n_overlaps == 0:
            if verbose:
                print(f"[resolver] converged after {iteration - 1} iteration(s).")
            return {
                "converged": True,
                "iterations": iteration - 1,
                "final_overlaps": [],
                "moved_indices": moved_indices,
                "best_overlap_count": 0,
            }

        moves = resolve_overlaps(
            scene_data, overlaps,
            style=style, map_half=map_half, clearance=clearance,
        )
        if not moves:
            if verbose:
                print(f"[resolver] iter {iteration}: {n_overlaps} overlap(s) "
                      f"but algorithm produced no moves — stopping early.")
            break

        # 把算法算出的 new_x / new_y 直接写回 scene_data
        buildings = scene_data.get("buildings", [])
        for idx, m in moves.items():
            if 0 <= idx < len(buildings):
                buildings[idx]["x"] = m["new_x"]
                buildings[idx]["y"] = m["new_y"]
                moved_indices.add(idx)

        if verbose:
            print(f"[resolver] iter {iteration}: {n_overlaps} overlap(s), "
                  f"moved {len(moves)} building(s).")

    # 未收敛 — 恢复重叠数最少的那一步快照
    if best_snapshot is not None:
        scene_data["buildings"] = best_snapshot
    final_overlaps = check_overlaps(scene_data)
    if verbose:
        print(f"[resolver] WARNING: not fully converged. "
              f"Restored best state with {len(final_overlaps)} overlap(s) "
              f"(best seen: {best_count}).")
    return {
        "converged": False,
        "iterations": max_iterations,
        "final_overlaps": final_overlaps,
        "moved_indices": moved_indices,
        "best_overlap_count": best_count,
    }
