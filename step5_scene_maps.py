"""
step5_scene_maps.py — 根据场景描述生成三通道场景地图

用法:
    python step5_scene_maps.py <scene_name>
    python step5_scene_maps.py simple_scene/scene_001/scene_description.json

输出目录: scene_maps/{name}/
    {name}_maps.npy        三通道地图，shape (128, 128, 3)，float32
    {name}_height.png      通道0：建筑物高度图（归一化，灰度）
    {name}_material.png    通道1：材质图（0–5 整数编码）
    {name}_los.png         通道2：LOS 图（1=直视，0=遮挡）

通道说明:
    通道0 — 高度图：每格最高建筑物的高度，归一化到 [0, 1]
    通道1 — 材质图：0=地面, 1=concrete, 2=marble, 3=metal, 4=wood, 5=glass（归一化到 [0, 1]）
    通道2 — LOS图：从发射机(TX)到该格点的直视路径，1.0=直视，0.0=遮挡

地图参数:
    分辨率：128 × 128
    地图范围：200 m × 200 m，坐标 x,y ∈ [-100, +100] m
    格点中心：-100 + (i + 0.5) × (200/128) m
"""

import json
import sys
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from shapely.geometry import Point

from overlap_checker import building_to_polygon

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

RESOLUTION = 128
MAP_SIZE_M = 200.0
HALF = MAP_SIZE_M / 2.0          # 100.0 m
CELL_SIZE = MAP_SIZE_M / RESOLUTION  # ≈ 1.5625 m

# 格点中心坐标（1D，共 128 个）
_COORDS = np.linspace(
    -HALF + CELL_SIZE / 2,
    HALF - CELL_SIZE / 2,
    RESOLUTION,
    dtype=np.float32,
)

# 材质名称 → 整数编码（0 保留给无建筑的地面）
MATERIAL_ENCODING = {
    "ground":   0,
    "concrete": 1,
    "marble":   2,
    "metal":    3,
    "wood":     4,
    "glass":    5,
}
MATERIAL_MAX = 5  # 用于归一化

# 可视化色板
_HEIGHT_CMAP = "gray"
_MATERIAL_COLORS = ["#888888",  # 0: ground — 灰色
                    "#B0B0B0",  # 1: concrete — 浅灰
                    "#C8A96E",  # 2: marble — 米黄
                    "#5A8FC3",  # 3: metal — 钢蓝
                    "#8B5E3C",  # 4: wood — 木棕
                    "#7EC8D6"]  # 5: glass — 冰蓝
_MATERIAL_CMAP = mcolors.ListedColormap(_MATERIAL_COLORS)
_LOS_CMAP = mcolors.ListedColormap(["#D63031", "#00B894"])  # 红=遮挡, 绿=直视


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _encode_material(mat_str: str) -> int:
    """将建筑物材质字符串映射为整数编码。"""
    key = mat_str.lower().strip() if mat_str else "concrete"
    return MATERIAL_ENCODING.get(key, 1)  # 未知材质默认 concrete=1


def _world_to_grid(wx: float, wy: float) -> tuple[int, int]:
    """将世界坐标 (wx, wy) 转换为格点索引 (col, row)，不超出 [0, RESOLUTION-1]。"""
    col = int((wx + HALF) / CELL_SIZE)
    row = int((wy + HALF) / CELL_SIZE)
    col = max(0, min(RESOLUTION - 1, col))
    row = max(0, min(RESOLUTION - 1, row))
    return col, row


def _bresenham_path(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """
    返回从 (x0, y0) 到 (x1, y1) 之间的所有中间格点（不含终点 (x1,y1)）。
    使用 Bresenham 直线算法。
    """
    pts = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy
    x, y = x0, y0
    while (x, y) != (x1, y1):
        pts.append((x, y))
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return pts  # 不含终点


# ---------------------------------------------------------------------------
# 核心计算
# ---------------------------------------------------------------------------

def _compute_height_material(buildings: list) -> tuple[np.ndarray, np.ndarray]:
    """
    遍历所有建筑物，将其 footprint 光栅化到 128×128 网格。

    Returns:
        height_raw   (128, 128) float32  — 原始高度（米），地面=0
        material_map (128, 128) float32  — 材质整数编码 / MATERIAL_MAX
    """
    height_raw = np.zeros((RESOLUTION, RESOLUTION), dtype=np.float32)
    material_raw = np.zeros((RESOLUTION, RESOLUTION), dtype=np.int32)

    # 预构建 footprint
    footprints = []
    for b in buildings:
        try:
            fp = building_to_polygon(b)
            bh = float(b.get("height", 0))
            mat = _encode_material(b.get("material", "concrete"))
            footprints.append((fp, bh, mat))
        except Exception as e:
            print(f"[step5] WARNING: 跳过建筑物（无法生成 footprint）：{e}")

    if not footprints:
        return height_raw, material_raw.astype(np.float32) / MATERIAL_MAX

    for j, ry in enumerate(_COORDS):         # row ↔ y
        for i, rx in enumerate(_COORDS):     # col ↔ x
            p = Point(float(rx), float(ry))
            for fp, bh, mat in footprints:
                if bh > height_raw[j, i] and fp.contains(p):
                    height_raw[j, i] = bh
                    material_raw[j, i] = mat

    material_map = material_raw.astype(np.float32) / MATERIAL_MAX
    return height_raw, material_map


def _compute_los(
    height_raw: np.ndarray,
    tx_x: float, tx_y: float, tx_z: float,
    rx_height: float,
) -> np.ndarray:
    """
    通过高度场射线投影计算 LOS 图。

    对每个格点 (col, row)，用 Bresenham 算法沿射线从 TX 格点遍历到该格点，
    在每个中间格点处检查射线高度是否被建筑遮挡。

    Returns:
        los_map (128, 128) float32  — 1.0=直视，0.0=遮挡
    """
    los_map = np.ones((RESOLUTION, RESOLUTION), dtype=np.float32)

    # TX 格点索引
    tx_col, tx_row = _world_to_grid(tx_x, tx_y)

    for row in range(RESOLUTION):
        for col in range(RESOLUTION):
            path = _bresenham_path(tx_col, tx_row, col, row)
            if not path:
                continue  # TX 与 RX 在同一格点，直视

            total_dist = math.sqrt((col - tx_col) ** 2 + (row - tx_row) ** 2)

            for (mc, mr) in path:
                d = math.sqrt((mc - tx_col) ** 2 + (mr - tx_row) ** 2)
                t = d / total_dist if total_dist > 0 else 0.0
                # 射线在中间格点处的高度
                ray_h = tx_z + t * (rx_height - tx_z)
                bld_h = height_raw[mr, mc]
                if bld_h > 0 and ray_h <= bld_h:
                    los_map[row, col] = 0.0
                    break

    return los_map


# ---------------------------------------------------------------------------
# 可视化保存
# ---------------------------------------------------------------------------

def _save_height_png(height_norm: np.ndarray, path: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(height_norm, cmap=_HEIGHT_CMAP, vmin=0, vmax=1,
                   origin="lower", extent=[-HALF, HALF, -HALF, HALF])
    ax.set_title("Height Map (normalized)")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    plt.colorbar(im, ax=ax, label="normalized height")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_material_png(material_raw_int: np.ndarray, path: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(material_raw_int, cmap=_MATERIAL_CMAP,
                   vmin=-0.5, vmax=MATERIAL_MAX + 0.5,
                   origin="lower", extent=[-HALF, HALF, -HALF, HALF])
    ax.set_title("Material Map")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    cbar = plt.colorbar(im, ax=ax, ticks=list(range(MATERIAL_MAX + 1)))
    cbar.ax.set_yticklabels(
        ["ground", "concrete", "marble", "metal", "wood", "glass"]
    )
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_los_png(los_map: np.ndarray, path: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(los_map, cmap=_LOS_CMAP, vmin=0, vmax=1,
                   origin="lower", extent=[-HALF, HALF, -HALF, HALF])
    ax.set_title("LOS Map (green=LOS, red=NLOS)")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    plt.colorbar(im, ax=ax, label="LOS (1=visible)")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 主接口
# ---------------------------------------------------------------------------

def generate_scene_maps(
    scene_desc_path: str,
    output_dir: str,
    resolution: int = 128,
) -> str:
    """
    根据 scene_description.json 生成三通道场景地图。

    Args:
        scene_desc_path: simple_scene/{name}/scene_description.json 的路径
        output_dir:      输出目录（如 scene_maps/{name}/）
        resolution:      暂仅支持默认值 128

    Returns:
        npy_path: 保存的 .npy 文件路径
    """
    if resolution != RESOLUTION:
        print(f"[step5] WARNING: resolution={resolution} ignored，当前固定为 {RESOLUTION}")

    desc_path = Path(scene_desc_path)
    if not desc_path.exists():
        raise FileNotFoundError(f"[step5] 找不到场景描述文件：{desc_path}")

    full = json.loads(desc_path.read_text(encoding="utf-8"))
    name = full.get("location_name") or desc_path.parent.name
    scene = full.get("scene", full)
    buildings = scene.get("buildings", [])

    tx = full.get("tx", {})
    rx = full.get("rx", {})
    tx_x = float(tx.get("x", 0.0))
    tx_y = float(tx.get("y", 0.0))
    tx_z = float(tx.get("z", 20.0))
    rx_height = float(rx.get("rx_height", 1.5))

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[step5] 场景 '{name}'：{len(buildings)} 栋建筑")
    print(f"[step5] TX=({tx_x:.1f}, {tx_y:.1f}, {tx_z:.1f})m  RX高度={rx_height:.1f}m")

    # ── 通道 0 + 1：高度图 & 材质图 ──────────────────────────────────────────
    print(f"[step5] 计算高度图和材质图…")
    height_raw, material_map = _compute_height_material(buildings)

    max_h = float(height_raw.max())
    height_norm = (height_raw / max_h).astype(np.float32) if max_h > 0 else height_raw.copy()
    print(f"[step5] 建筑物最大高度：{max_h:.1f} m")

    # 材质图整数版本（用于可视化）
    material_int = np.round(material_map * MATERIAL_MAX).astype(np.int32)

    # ── 通道 2：LOS 图 ────────────────────────────────────────────────────────
    print(f"[step5] 计算 LOS 图（128×128 射线投影）…")
    los_map = _compute_los(height_raw, tx_x, tx_y, tx_z, rx_height)
    los_ratio = los_map.mean() * 100
    print(f"[step5] LOS 覆盖率：{los_ratio:.1f}%")

    # ── 拼合三通道 ─────────────────────────────────────────────────────────────
    maps = np.stack([height_norm, material_map, los_map], axis=-1)  # (128, 128, 3)

    # ── 保存 .npy ─────────────────────────────────────────────────────────────
    npy_path = out_dir / f"{name}_maps.npy"
    np.save(str(npy_path), maps)
    print(f"[step5] 地图已保存：{npy_path}  shape={maps.shape} dtype={maps.dtype}")

    # ── 保存三张 PNG ──────────────────────────────────────────────────────────
    _save_height_png(height_norm,  str(out_dir / f"{name}_height.png"))
    _save_material_png(material_int, str(out_dir / f"{name}_material.png"))
    _save_los_png(los_map,         str(out_dir / f"{name}_los.png"))
    print(f"[step5] PNG 已保存：{out_dir / name}_{{height,material,los}}.png")

    return str(npy_path)


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------

def _resolve_scene_desc(arg: str) -> str:
    """接受场景名称或 JSON 文件路径，返回 scene_description.json 的路径。"""
    p = Path(arg)
    if p.suffix == ".json" and p.exists():
        return str(p)
    # 按场景名称查找
    candidates = [
        Path("simple_scene") / arg / "scene_description.json",
        Path(arg) / "scene_description.json",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    raise FileNotFoundError(
        f"找不到场景 '{arg}' 的 scene_description.json。\n"
        f"请先运行 main.py 生成场景，或直接传入 JSON 文件路径。"
    )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]
    try:
        desc_path = _resolve_scene_desc(arg)
    except FileNotFoundError as e:
        print(f"[step5] 错误：{e}")
        sys.exit(1)

    name = Path(desc_path).parent.name
    out_dir = str(Path("scene_maps") / name)
    generate_scene_maps(desc_path, out_dir)


if __name__ == "__main__":
    main()
