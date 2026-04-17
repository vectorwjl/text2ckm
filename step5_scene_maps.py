"""
step5_scene_maps.py — 根据场景描述生成四通道场景地图

用法:
    python step5_scene_maps.py <scene_name>
    python step5_scene_maps.py simple_scene/scene_001/scene_description.json

输出目录: scene_maps/{name}/
    {name}_maps.npy              四通道地图，shape (40, 40, 4)，float32
    {name}_material_props.json   材质电磁属性及归一化参数（供后续反归一化使用）
    {name}_height.png            通道0：建筑物高度图（归一化，灰度）
    {name}_material_eps.png      通道1：归一化相对介电常数图
    {name}_material_sigma.png    通道2：归一化电导率图
    {name}_distance.png          通道3：距离地图（每栅格中心到 TX 的欧几里得距离，归一化）

通道说明:
    通道0 — 高度图：每格最高建筑物的高度，归一化到 [0, 1]
    通道1 — 归一化相对介电常数（ε_r_norm）：
            按 ITU-R P.2040 公式 ε_r = a·f^b 在场景频率下计算，min-max 归一化
    通道2 — 归一化电导率（σ_norm）：
            按 ITU-R P.2040 公式 σ = c·f^d 在场景频率下计算，对数归一化
    通道3 — 距离图：每栅格点中心到 TX 的欧几里得距离，归一化到 [0, 1]

    背景（无建筑格点）使用地面材质 wet_ground 的归一化属性。

地图参数:
    分辨率：40 × 40
    格点尺寸：5.0 m × 5.0 m（与 path_gain cell_size 一致）
    地图范围：200 m × 200 m，坐标 x,y ∈ [-100, +100] m
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
# 地图几何常量
# ---------------------------------------------------------------------------

RESOLUTION = 200
MAP_SIZE_M = 200.0
HALF       = MAP_SIZE_M / 2.0          # 100.0 m
CELL_SIZE  = MAP_SIZE_M / RESOLUTION   # 5.0 m

_COORDS = np.linspace(
    -HALF + CELL_SIZE / 2,
    HALF  - CELL_SIZE / 2,
    RESOLUTION,
    dtype=np.float32,
)

# ---------------------------------------------------------------------------
# ITU-R P.2040 材质参数: {材质名: (a, b, c, d)}
#   ε_r = a × f_GHz^b
#   σ   = c × f_GHz^d
# 对有多频率行（glass / ceiling_board）的材质使用 1–100 GHz 行
# ---------------------------------------------------------------------------

MATERIAL_ITU: dict = {
    "vacuum":            (1.0,    0.0,   0.0,      0.0   ),
    "concrete":          (5.24,   0.0,   0.0462,   0.7822),
    "brick":             (3.91,   0.0,   0.0238,   0.16  ),
    "plasterboard":      (2.73,   0.0,   0.0085,   0.9395),
    "wood":              (1.99,   0.0,   0.0047,   1.0718),
    "glass":             (6.31,   0.0,   0.0036,   1.3394),
    "ceiling_board":     (1.48,   0.0,   0.0011,   1.0750),
    "chipboard":         (2.58,   0.0,   0.0217,   0.7800),
    "plywood":           (2.71,   0.0,   0.33,     0.0   ),
    "marble":            (7.074,  0.0,   0.0055,   0.9262),
    "floorboard":        (3.66,   0.0,   0.0044,   1.3515),
    "metal":             (1.0,    0.0,   1e7,      0.0   ),
    "very_dry_ground":   (3.0,    0.0,   0.00015,  2.52  ),
    "medium_dry_ground": (15.0,  -0.1,   0.035,    1.63  ),
    "wet_ground":        (30.0,  -0.4,   0.15,     1.30  ),
}

_DEFAULT_GROUND = "wet_ground"   # 背景（无建筑格点）默认使用的地面材质


# ---------------------------------------------------------------------------
# 材质电磁属性计算与归一化
# ---------------------------------------------------------------------------

def compute_material_props(freq_ghz: float) -> dict:
    """
    按 ITU-R P.2040 公式计算每种材质在给定频率下的原始 (ε_r, σ)。

    Returns:
        {材质名: {"eps_r": float, "sigma": float}}
    """
    result = {}
    for mat, (a, b, c, d) in MATERIAL_ITU.items():
        eps_r = a * (freq_ghz ** b)
        sigma = c * (freq_ghz ** d) if c > 0 else 0.0
        result[mat] = {"eps_r": float(eps_r), "sigma": float(sigma)}
    return result


def compute_normalized_props(freq_ghz: float) -> tuple:
    """
    计算并归一化所有材质在给定频率下的电磁属性。

    ε_r  — min-max 归一化：eps_r_norm = (ε_r - ε_min) / (ε_max - ε_min)
    σ    — 对数归一化：sigma_norm = log(σ + 1) / log(σ_max + 1)
             （解决 metal σ=10^7 与其他材质量级差距悬殊的问题，σ=0 自然映射到 0）

    Returns:
        normalized:  {材质名 → {"eps_r", "sigma", "eps_r_norm", "sigma_norm"}}
        norm_params: 归一化参数（含 eps_min/max、sigma_max、log_sigma_max）
    """
    props = compute_material_props(freq_ghz)

    eps_vals   = [v["eps_r"] for v in props.values()]
    sigma_vals = [v["sigma"] for v in props.values()]

    eps_min, eps_max = min(eps_vals), max(eps_vals)
    sigma_max        = max(sigma_vals)                    # 对数归一化只需要最大值
    log_sigma_max    = math.log(sigma_max + 1) if sigma_max > 0 else 1.0

    normalized = {}
    for mat, p in props.items():
        eps_norm = (
            (p["eps_r"] - eps_min) / (eps_max - eps_min)
            if eps_max > eps_min else 0.0
        )
        sigma_norm = math.log(p["sigma"] + 1) / log_sigma_max
        normalized[mat] = {
            "eps_r":      p["eps_r"],
            "sigma":      p["sigma"],
            "eps_r_norm": float(eps_norm),
            "sigma_norm": float(sigma_norm),
        }

    norm_params = {
        "freq_ghz":     freq_ghz,
        "eps_min":      eps_min,      "eps_max":      eps_max,
        "sigma_max":    sigma_max,    "log_sigma_max": log_sigma_max,
        "sigma_method": "log(sigma+1)/log(sigma_max+1)",
    }
    return normalized, norm_params


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _world_to_grid(wx: float, wy: float) -> tuple:
    col = int((wx + HALF) / CELL_SIZE)
    row = int((wy + HALF) / CELL_SIZE)
    return max(0, min(RESOLUTION - 1, col)), max(0, min(RESOLUTION - 1, row))


def _bresenham_path(x0: int, y0: int, x1: int, y1: int) -> list:
    pts = []
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x1 > x0 else -1), (1 if y1 > y0 else -1)
    err = dx - dy
    x, y = x0, y0
    while (x, y) != (x1, y1):
        pts.append((x, y))
        e2 = 2 * err
        if e2 > -dy: err -= dy; x += sx
        if e2 <  dx: err += dx; y += sy
    return pts


# ---------------------------------------------------------------------------
# 核心计算
# ---------------------------------------------------------------------------

def _compute_height_material(
    buildings: list,
    mat_norm: dict,
    ground_mat: str = _DEFAULT_GROUND,
) -> tuple:
    """
    光栅化建筑物，返回高度图与两张材质图（ε_r_norm、σ_norm）。

    背景格点（无建筑覆盖）填充地面材质的归一化属性。

    Returns:
        height_raw (40,40) float32  — 原始高度（米），地面=0
        eps_r_map  (40,40) float32  — 归一化 ε_r
        sigma_map  (40,40) float32  — 归一化 σ
    """
    g_key = ground_mat if ground_mat in mat_norm else _DEFAULT_GROUND
    g_eps = float(mat_norm[g_key]["eps_r_norm"])
    g_sig = float(mat_norm[g_key]["sigma_norm"])

    height_raw = np.zeros((RESOLUTION, RESOLUTION), dtype=np.float32)
    eps_r_map  = np.full((RESOLUTION, RESOLUTION), g_eps, dtype=np.float32)
    sigma_map  = np.full((RESOLUTION, RESOLUTION), g_sig, dtype=np.float32)

    footprints = []
    for b in buildings:
        try:
            fp    = building_to_polygon(b)
            bh    = float(b.get("height", 0))
            mkey  = (b.get("material") or "concrete").lower().strip()
            m     = mat_norm.get(mkey, mat_norm["concrete"])
            footprints.append((fp, bh, float(m["eps_r_norm"]), float(m["sigma_norm"])))
        except Exception as e:
            print(f"[step5] WARNING: 跳过建筑物（无法生成 footprint）：{e}")

    for j, ry in enumerate(_COORDS):
        for i, rx in enumerate(_COORDS):
            p = Point(float(rx), float(ry))
            for fp, bh, eps_n, sig_n in footprints:
                if bh > height_raw[j, i] and fp.contains(p):
                    height_raw[j, i] = bh
                    eps_r_map[j, i]  = eps_n
                    sigma_map[j, i]  = sig_n

    return height_raw, eps_r_map, sigma_map


def _compute_distance(
    tx_x: float, tx_y: float, tx_z: float, rx_height: float
) -> np.ndarray:
    """
    计算每个栅格点中心（高度=rx_height）到 TX（高度=tx_z）的三维欧几里得距离，
    归一化到 [0, 1]。

    归一化基准：网格内距 TX 最远的栅格点距离（场景内最大值）。
    """
    XX, YY = np.meshgrid(_COORDS, _COORDS)          # (40, 40)
    dz = rx_height - tx_z
    dist = np.sqrt((XX - tx_x) ** 2 + (YY - tx_y) ** 2 + dz ** 2).astype(np.float32)
    max_dist = float(dist.max())
    return (dist / max_dist).astype(np.float32) if max_dist > 0 else dist


# ---------------------------------------------------------------------------
# 可视化保存
# ---------------------------------------------------------------------------

def _save_height_png(height_norm: np.ndarray, path: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(height_norm, cmap="gray", vmin=0, vmax=1,
                   origin="lower", extent=[-HALF, HALF, -HALF, HALF])
    ax.set_title("Height Map (normalized)")
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    plt.colorbar(im, ax=ax, label="normalized height")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_material_eps_png(eps_map: np.ndarray, path: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(eps_map, cmap="plasma", vmin=0, vmax=1,
                   origin="lower", extent=[-HALF, HALF, -HALF, HALF])
    ax.set_title("Material Map — ε_r (normalized)")
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    plt.colorbar(im, ax=ax, label="normalized permittivity ε_r")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_material_sigma_png(sigma_map: np.ndarray, path: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(sigma_map, cmap="inferno", vmin=0, vmax=1,
                   origin="lower", extent=[-HALF, HALF, -HALF, HALF])
    ax.set_title("Material Map — σ (normalized)")
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    plt.colorbar(im, ax=ax, label="normalized conductivity σ")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_distance_png(dist_map: np.ndarray, path: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(dist_map, cmap="viridis_r", vmin=0, vmax=1,
                   origin="lower", extent=[-HALF, HALF, -HALF, HALF])
    ax.set_title("Distance Map to TX (normalized, dark=near)")
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    plt.colorbar(im, ax=ax, label="normalized distance to TX")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 主接口
# ---------------------------------------------------------------------------

def generate_scene_maps(
    scene_desc_path: str,
    output_dir: str,
    resolution: int = 40,
) -> str:
    """
    根据 scene_description.json 生成四通道场景地图。

    通道: [height_norm, eps_r_norm, sigma_norm, dist_norm]  shape (40, 40, 4)

    Args:
        scene_desc_path: simple_scene/{name}/scene_description.json 的路径
        output_dir:      输出目录（如 scene_maps/{name}/）
        resolution:      暂仅支持默认值 40（cell_size=5m）

    Returns:
        npy_path: 保存的 .npy 文件路径
    """
    if resolution != RESOLUTION:
        print(f"[step5] WARNING: resolution={resolution} ignored，固定为 {RESOLUTION}")

    desc_path = Path(scene_desc_path)
    if not desc_path.exists():
        raise FileNotFoundError(f"[step5] 找不到场景描述文件：{desc_path}")

    full = json.loads(desc_path.read_text(encoding="utf-8"))
    name      = full.get("location_name") or desc_path.parent.name
    scene     = full.get("scene", full)
    buildings = scene.get("buildings", [])

    tx        = full.get("tx", {})
    rx        = full.get("rx", {})
    tx_x      = float(tx.get("x", 0.0))
    tx_y      = float(tx.get("y", 0.0))
    tx_z      = float(tx.get("z", 20.0))
    rx_height = float(rx.get("rx_height", 1.5))
    freq_ghz  = float(tx.get("frequency_ghz", 28.0))

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[step5] 场景 '{name}'：{len(buildings)} 栋建筑，频率={freq_ghz} GHz")
    print(f"[step5] TX=({tx_x:.1f},{tx_y:.1f},{tx_z:.1f})m  RX高度={rx_height:.1f}m")

    # ── 计算材质电磁属性及归一化 ─────────────────────────────────────────────
    mat_norm, norm_params = compute_normalized_props(freq_ghz)
    print(f"[step5] ε_r 范围：[{norm_params['eps_min']:.4f}, {norm_params['eps_max']:.4f}]")
    print(f"[step5] σ   范围：[0, {norm_params['sigma_max']:.4e}] S/m（对数归一化）")

    # 保存材质属性 JSON（含原始值和归一化值，供后续反归一化）
    props_path = out_dir / f"{name}_material_props.json"
    props_path.write_text(
        json.dumps({"norm_params": norm_params, "materials": mat_norm},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[step5] 材质属性已保存：{props_path}")

    # ── 通道 0/1/2：高度图 & 材质图（ε_r、σ） ────────────────────────────────
    print(f"[step5] 计算高度图和材质图…")
    height_raw, eps_r_map, sigma_map = _compute_height_material(buildings, mat_norm)

    max_h = float(height_raw.max())
    height_norm = (height_raw / max_h).astype(np.float32) if max_h > 0 else height_raw.copy()
    print(f"[step5] 建筑物最大高度：{max_h:.1f} m")

    # ── 通道 3：距离图 ────────────────────────────────────────────────────────
    dist_map = _compute_distance(tx_x, tx_y, tx_z, rx_height)
    print(f"[step5] 距离图完成（TX=({tx_x:.1f},{tx_y:.1f})m，最大距离={dist_map.max() * dist_map.max():.0f}m²）")

    # ── 拼合四通道 (40, 40, 4) ────────────────────────────────────────────────
    maps = np.stack([height_norm, eps_r_map, sigma_map, dist_map], axis=-1)

    # ── 保存 .npy ─────────────────────────────────────────────────────────────
    npy_path = out_dir / f"{name}_maps.npy"
    np.save(str(npy_path), maps)
    print(f"[step5] 地图已保存：{npy_path}  shape={maps.shape} dtype={maps.dtype}")

    # ── 保存四张 PNG ──────────────────────────────────────────────────────────
    _save_height_png(height_norm,      str(out_dir / f"{name}_height.png"))
    _save_material_eps_png(eps_r_map,  str(out_dir / f"{name}_material_eps.png"))
    _save_material_sigma_png(sigma_map, str(out_dir / f"{name}_material_sigma.png"))
    _save_distance_png(dist_map,       str(out_dir / f"{name}_distance.png"))
    print(f"[step5] PNG 已保存至：{out_dir}")

    return str(npy_path)


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------

def _resolve_scene_desc(arg: str) -> str:
    p = Path(arg)
    if p.suffix == ".json" and p.exists():
        return str(p)
    for c in [
        Path("simple_scene") / arg / "scene_description.json",
        Path(arg) / "scene_description.json",
    ]:
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
    generate_scene_maps(desc_path, str(Path("scene_maps") / name))


if __name__ == "__main__":
    main()
