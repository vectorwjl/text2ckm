"""
generate_prompt.py — 点式散布 (Point Scatter) 场景提示词生成器

Standalone script: no imports from other project files.

用法:
    python skills/point_scatter/scripts/generate_prompt.py            # 生成 1 个
    python skills/point_scatter/scripts/generate_prompt.py --count 5  # 生成 5 个
"""

import argparse
import math
import random
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# 常量映射 (self-contained, no project imports)
# ---------------------------------------------------------------------------

BUILDING_TYPE_NAMES = {
    "rectangular": "矩形建筑",
    "l_shaped":    "L形建筑",
    "t_shaped":    "T形建筑",
    "u_shaped":    "U形庭院建筑",
}

MATERIAL_NAMES = {
    "concrete": "混凝土",
    "marble":   "大理石",
    "metal":    "金属",
    "wood":     "木材",
    "glass":    "玻璃幕墙",
}

# Building material weights (biased toward concrete; glass/metal secondary)
BUILDING_MATERIAL_WEIGHTS = {
    "concrete": 0.45,
    "glass":    0.20,
    "metal":    0.15,
    "marble":   0.10,
    "wood":     0.10,
}

# Road material weights (biased toward marble)
ROAD_MATERIAL_WEIGHTS = {
    "marble":   0.70,
    "concrete": 0.20,
    "metal":    0.10,
}

# Common carrier frequency candidates (GHz)
FREQ_CANDIDATES = [0.9, 1.8, 2.4, 3.5, 5.8, 28.0, 39.0, 60.0]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _r(lo: float, hi: float, decimals: int = 2) -> float:
    """Return a random float in [lo, hi] rounded to `decimals` decimal places."""
    return round(random.uniform(lo, hi), decimals)


def _weighted_choice(d: dict):
    """Return a random key from dict `d` weighted by its values."""
    return random.choices(list(d.keys()), weights=list(d.values()), k=1)[0]


# ---------------------------------------------------------------------------
# Height / dimension description helpers
# ---------------------------------------------------------------------------

def _rand_height_desc_tall() -> str:
    """Random tall-tower height description (30–100 m range)."""
    use_range = random.random() < 0.5
    if use_range:
        h_min = _r(30.0, 60.0)
        h_max = _r(h_min + 10.0, min(h_min + 60.0, 100.0))
        return f"高度随机从{h_min}到{h_max}米"
    else:
        h = _r(30.0, 100.0)
        return f"高度{h}米"


def _dim_desc_rectangular_tower() -> str:
    """Small near-square footprint for point scatter rectangular towers."""
    # Near-square: |width - length| <= 5 m; range 10–20 m
    w = _r(10.0, 20.0)
    delta = _r(0.0, min(5.0, 20.0 - w))
    l = round(w + delta, 2)
    return f"宽{w}米、长{l}米"


def _dim_desc_l_shaped_tower() -> str:
    """Compact L-shaped tower dimensions for point scatter."""
    w1 = _r(15.0, 25.0)
    l1 = _r(15.0, 25.0)
    w2 = _r(5.0, min(w1 * 0.55, 12.0))
    l2 = _r(5.0, min(l1 * 0.55, 12.0))
    return f"主体{w1}×{l1}米，翼部{w2}×{l2}米"


def _dim_desc_u_shaped_tower() -> str:
    """U-shaped tower dimensions (compact outer shell)."""
    ow = _r(30.0, 50.0)
    ol = _r(30.0, 50.0)
    factor = _r(0.40, 0.60)
    iw = round(ow * factor, 2)
    il = round(ol * factor, 2)
    return f"外围{ow}×{ol}米，内庭{iw}×{il}米"


_TOWER_DIM_DESC_FUNCS = {
    "rectangular": _dim_desc_rectangular_tower,
    "l_shaped":    _dim_desc_l_shaped_tower,
    "u_shaped":    _dim_desc_u_shaped_tower,
}


# ---------------------------------------------------------------------------
# Building group description (one type, N buildings)
# ---------------------------------------------------------------------------

def _rand_tower_group(btype: str, count: int) -> str:
    """Generate a Chinese description fragment for one group of point-scatter towers."""
    type_name = BUILDING_TYPE_NAMES[btype]
    dim_desc = _TOWER_DIM_DESC_FUNCS[btype]()
    height_desc = _rand_height_desc_tall()
    mat = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
    mat_name = MATERIAL_NAMES[mat]
    return (
        f"{count}栋{type_name}（{dim_desc}，{height_desc}，{mat_name}材质，"
        f"每栋旋转角度完全随机（0-360度随机分布，各不相同），每栋尺寸各不相同）"
    )


# ---------------------------------------------------------------------------
# TX / RX / RT description helpers
# ---------------------------------------------------------------------------

def _rand_tx_desc() -> str:
    freq = random.choice(FREQ_CANDIDATES)
    power = random.randint(20, 50)
    z = _r(5.0, 50.0)
    return f"发射机在场景中心高度{z}米，频率{freq}GHz，功率{power}dBm"


def _rand_rx_desc() -> str:
    rx_h = _r(1.0, 3.0)
    return f"接收机高度{rx_h}米"


def _rand_rt_desc() -> str:
    map_size = random.randint(200, 400)
    return f"地图尺寸{map_size}米"


# ---------------------------------------------------------------------------
# Core prompt generator: point scatter style
# ---------------------------------------------------------------------------

def generate_prompt() -> str:
    """
    Generate one Chinese scene description prompt for the point scatter layout style.

    Rules enforced in the prompt text:
    - 8–15 buildings total, 1–3 type groups
    - Small footprint, tall towers (30–100 m)
    - Fully random rotation_deg, spread 0–360°, all unique
    - Minimum 20 m spacing between building centers
    - Buildings spread across entire map, all four quadrants
    - 1–2 straight roads only (+ or H pattern)
    - Includes TX/RX/RT parameters
    """
    # Step 1: determine building count and type mix
    n_buildings = random.randint(8, 15)
    all_scatter_types = ["rectangular", "l_shaped", "u_shaped"]
    n_type_groups = random.choices([1, 2, 3], weights=[0.35, 0.45, 0.20])[0]
    # Prefer rectangular and l_shaped; u_shaped gets lower weight in sampling
    type_pool_weights = [0.50, 0.35, 0.15]
    selected_types: list[str] = []
    for _ in range(n_type_groups):
        remaining = [t for t in all_scatter_types if t not in selected_types]
        if not remaining:
            break
        remaining_weights = [
            type_pool_weights[all_scatter_types.index(t)] for t in remaining
        ]
        chosen = random.choices(remaining, weights=remaining_weights, k=1)[0]
        selected_types.append(chosen)

    # Step 2: distribute building count across type groups
    counts: list[int] = [1] * len(selected_types)
    for _ in range(n_buildings - len(selected_types)):
        counts[random.randint(0, len(selected_types) - 1)] += 1

    # Step 3: build group descriptions
    group_descs = [
        _rand_tower_group(btype, cnt)
        for btype, cnt in zip(selected_types, counts)
    ]
    building_part = "、".join(group_descs)

    # Step 4: road configuration
    road_width = _r(7.0, 10.0)
    road_mat = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    road_mat_name = MATERIAL_NAMES[road_mat]
    road_pattern = random.choice(["十字形（一条横向+一条纵向）", "H形（两条平行横向道路）"])

    # Step 5: TX/RX/RT
    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = (
        f"创建虚拟场景：点式散布布局，{n_buildings}栋独立塔楼建筑随机散点分布，"
        f"包括{building_part}，"
        f"建筑均匀散布在整个场景的四个象限中，不能聚集在中心区域，"
        f"每栋建筑旋转角度完全随机且各不相同（0-360度均匀分布），"
        f"任意两栋建筑中心间距不小于20米，"
        f"小尺度近方形塔楼平面（矩形建筑宽度约等于长度），高度30到100米，"
        f"仅设1到2条简单{road_pattern}直线道路（宽{road_width}米，{road_mat_name}材质），"
        f"不设密集路网，"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def _next_filename(output_dir: Path, prefix: str) -> Path:
    """Return the next available sequenced filename (e.g., scene_007.txt)."""
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)\.txt$")
    max_num = 0
    for f in output_dir.glob(f"{prefix}*.txt"):
        m = pattern.match(f.name)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return output_dir / f"{prefix}{max_num + 1:03d}.txt"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="生成点式散布布局场景提示词并保存为 .txt 文件"
    )
    parser.add_argument(
        "--count", "-n", type=int, default=1,
        help="生成提示词数量（默认 1）"
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default="text_prompts",
        help="输出目录（默认 text_prompts/）"
    )
    parser.add_argument(
        "--prefix", "-p", type=str, default="point_scatter_",
        help="文件名前缀（默认 point_scatter_）"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(args.count):
        prompt = generate_prompt()
        filepath = _next_filename(output_dir, args.prefix)
        filepath.write_text(prompt + "\n", encoding="utf-8")
        print(f"[{i + 1}/{args.count}] Saved: {filepath}")
        print(f"        {prompt}\n")

    print(f"Done. {args.count} prompt(s) saved to {output_dir}/")


if __name__ == "__main__":
    main()
