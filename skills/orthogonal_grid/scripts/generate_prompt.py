#!/usr/bin/env python3
"""
generate_prompt.py — Orthogonal Grid prompt generator for text2ckm.

Generates Chinese-language natural-language prompts describing orthogonal
grid (方格网式) urban scenes for use with the orthogonal_grid skill.

Usage:
    python generate_prompt.py             # generate 1 prompt
    python generate_prompt.py --count 5   # generate 5 prompts
    python generate_prompt.py -n 3        # generate 3 prompts
"""

import argparse
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants (self-contained — no imports from other project files)
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

BUILDING_MATERIAL_WEIGHTS = {
    "concrete": 0.45,
    "glass":    0.20,
    "metal":    0.15,
    "marble":   0.10,
    "wood":     0.10,
}

ROAD_MATERIAL_WEIGHTS = {
    "marble":   0.70,
    "concrete": 0.20,
    "metal":    0.10,
}

FREQ_CANDIDATES = [0.9, 1.8, 2.4, 3.5, 5.8, 28.0, 39.0, 60.0]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _r(lo: float, hi: float, decimals: int = 2) -> float:
    """Return a random float in [lo, hi] rounded to `decimals` places."""
    return round(random.uniform(lo, hi), decimals)


def _weighted_choice(d: dict) -> str:
    """Return a key from dict d sampled proportional to its value weights."""
    return random.choices(list(d.keys()), weights=list(d.values()), k=1)[0]


def _unique_floats(lo: float, hi: float, n: int, min_gap: float = 3.0,
                   decimals: int = 2) -> list:
    """Generate n unique floats in [lo, hi] each at least min_gap apart."""
    results = []
    attempts = 0
    while len(results) < n and attempts < 10000:
        candidate = round(random.uniform(lo, hi), decimals)
        if all(abs(candidate - v) >= min_gap for v in results):
            results.append(candidate)
        attempts += 1
    # Fallback: evenly spaced if random sampling fails
    if len(results) < n:
        step = (hi - lo) / (n + 1)
        results = [round(lo + step * (i + 1), decimals) for i in range(n)]
    return results


# ---------------------------------------------------------------------------
# Building dimension generators
# ---------------------------------------------------------------------------

def _gen_rectangular_dims(n: int) -> list:
    """Generate n rectangular buildings with unique dimensions."""
    buildings = []
    widths  = _unique_floats(8.0, 22.0, n, min_gap=3.0)
    lengths = _unique_floats(10.0, 30.0, n, min_gap=3.0)
    heights = _unique_floats(9.0, 50.0, n, min_gap=3.0)
    for i in range(n):
        buildings.append({
            "type":   "rectangular",
            "width":  widths[i],
            "length": lengths[i],
            "height": heights[i],
        })
    return buildings


def _gen_l_shaped_dims(n: int) -> list:
    buildings = []
    w1s = _unique_floats(10.0, 20.0, n, min_gap=3.0)
    l1s = _unique_floats(14.0, 28.0, n, min_gap=3.0)
    w2s = _unique_floats(6.0,  12.0, n, min_gap=3.0)
    l2s = _unique_floats(8.0,  16.0, n, min_gap=3.0)
    heights = _unique_floats(12.0, 45.0, n, min_gap=3.0)
    for i in range(n):
        buildings.append({
            "type":    "l_shaped",
            "width1":  w1s[i],
            "length1": l1s[i],
            "width2":  w2s[i],
            "length2": l2s[i],
            "height":  heights[i],
        })
    return buildings


def _gen_t_shaped_dims(n: int) -> list:
    buildings = []
    mws = _unique_floats(8.0,  16.0, n, min_gap=3.0)
    mls = _unique_floats(12.0, 24.0, n, min_gap=3.0)
    wws = _unique_floats(6.0,  12.0, n, min_gap=3.0)
    wls = _unique_floats(20.0, 36.0, n, min_gap=3.0)
    heights = _unique_floats(12.0, 50.0, n, min_gap=3.0)
    for i in range(n):
        buildings.append({
            "type":        "t_shaped",
            "main_width":  mws[i],
            "main_length": mls[i],
            "wing_width":  wws[i],
            "wing_length": wls[i],
            "height":      heights[i],
        })
    return buildings


def _gen_u_shaped_dims(n: int) -> list:
    buildings = []
    ows = _unique_floats(16.0, 30.0, n, min_gap=3.0)
    ols = _unique_floats(16.0, 30.0, n, min_gap=3.0)
    heights = _unique_floats(12.0, 40.0, n, min_gap=3.0)
    for i in range(n):
        iw = round(ows[i] - random.uniform(5.0, 8.0), 2)
        il = round(ols[i] - random.uniform(4.0, 7.0), 2)
        buildings.append({
            "type":         "u_shaped",
            "outer_width":  ows[i],
            "outer_length": ols[i],
            "inner_width":  max(iw, 6.0),
            "inner_length": max(il, 6.0),
            "height":       heights[i],
        })
    return buildings


# ---------------------------------------------------------------------------
# Main prompt generator
# ---------------------------------------------------------------------------

def generate_prompt() -> str:
    """
    Generate a single Chinese natural-language prompt describing an
    orthogonal grid urban scene.

    Returns a string suitable for sending to the LLM API.
    """
    # --- Road network parameters ---
    n_long      = random.randint(2, 3)    # number of south-north roads
    n_trans     = random.randint(2, 3)    # number of east-west roads
    long_spacing  = _r(50.0, 70.0)       # spacing between S-N roads (m)
    trans_spacing = _r(45.0, 65.0)       # spacing between E-W roads (m)
    road_width    = _r(7.0, 10.0)        # road width (m)
    road_mat      = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    road_mat_cn   = MATERIAL_NAMES[road_mat]

    # --- Building parameters ---
    n_blocks    = (n_long - 1) * (n_trans - 1)
    n_per_block = random.randint(2, 4)
    total_bldgs = n_blocks * n_per_block
    setback     = _r(4.0, 6.0)

    bldg_type   = random.choice(list(BUILDING_TYPE_NAMES.keys()))
    bldg_type_cn = BUILDING_TYPE_NAMES[bldg_type]
    bldg_mat    = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
    bldg_mat_cn = MATERIAL_NAMES[bldg_mat]

    # Generate building dimension descriptions
    dim_generators = {
        "rectangular": _gen_rectangular_dims,
        "l_shaped":    _gen_l_shaped_dims,
        "t_shaped":    _gen_t_shaped_dims,
        "u_shaped":    _gen_u_shaped_dims,
    }
    bldg_dims = dim_generators[bldg_type](total_bldgs)

    # Describe heights range
    heights = [b["height"] for b in bldg_dims]
    h_min, h_max = round(min(heights), 2), round(max(heights), 2)

    # --- TX parameters (randomly include or omit) ---
    tx_parts = []
    if random.random() < 0.70:
        freq = random.choice(FREQ_CANDIDATES)
        tx_parts.append(f"频率{freq}GHz")
    if random.random() < 0.55:
        power = round(random.uniform(20.0, 46.0), 1)
        tx_parts.append(f"发射功率{power}dBm")
    if random.random() < 0.50:
        tx_z = round(random.uniform(3.0, 30.0), 1)
        tx_parts.append(f"天线高度{tx_z}m")
    if random.random() < 0.35:
        rows = random.choice([1, 2, 4, 8])
        cols = random.choice([1, 2, 4, 8])
        tx_parts.append(f"{rows}×{cols}天线阵列")

    # --- RX parameters ---
    rx_parts = []
    if random.random() < 0.65:
        rx_h = round(random.uniform(1.0, 3.0), 1)
        rx_parts.append(f"接收机高度{rx_h}m")

    # --- RT parameters ---
    rt_parts = []
    if random.random() < 0.60:
        map_sz = round(random.choice([150.0, 200.0, 250.0, 300.0, 400.0]), 1)
        rt_parts.append(f"仿真区域{map_sz}m")
    if random.random() < 0.40:
        aoi = round(random.uniform(60.0, 150.0), 1)
        rt_parts.append(f"AOI半径{aoi}m")

    # --- Location (occasionally) ---
    locations = [
        "北京市朝阳区", "上海市浦东新区", "深圳市南山区",
        "广州市天河区", "成都市武侯区", "杭州市滨江区",
        "南京市江宁区", "武汉市洪山区", "西安市雁塔区",
        "某城市中心区域",
    ]
    loc_str = ""
    if random.random() < 0.45:
        loc_str = f"位于{random.choice(locations)}，"

    # --- Assemble prompt ---
    lines = []

    # Opening: scene type and location
    lines.append(
        f"请生成一个{loc_str}方格网布局的城市场景，"
        f"包含{n_long}条南北向道路和{n_trans}条东西向道路。"
    )

    # Road details
    lines.append(
        f"南北向道路间距约{long_spacing}m，东西向道路间距约{trans_spacing}m，"
        f"道路宽度{road_width}m，道路材质为{road_mat_cn}。"
    )

    # Building details
    lines.append(
        f"每个街区布置{n_per_block}栋{bldg_mat_cn}{bldg_type_cn}，"
        f"建筑退道路红线{setback}m，"
        f"建筑高度范围{h_min}–{h_max}m，所有建筑旋转角度为0度。"
    )

    # Clearance reminder
    lines.append("建筑间距不少于5m，建筑距道路边缘不少于5m。")

    # TX
    if tx_parts:
        lines.append("发射机参数：" + "，".join(tx_parts) + "。")

    # RX
    if rx_parts:
        lines.append("接收机参数：" + "，".join(rx_parts) + "。")

    # RT
    if rt_parts:
        lines.append("射线追踪参数：" + "，".join(rt_parts) + "。")

    # Output format reminder
    lines.append("请严格按照JSON格式输出，所有数值精确到小数点后两位。")

    return "".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate orthogonal grid scene prompts for text2ckm.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=1,
        help="Number of prompts to generate (default: 1)",
    )
    args = parser.parse_args()

    for i in range(args.count):
        prompt = generate_prompt()
        print(prompt)
        if args.count > 1 and i < args.count - 1:
            print()  # blank line separator between multiple prompts


if __name__ == "__main__":
    main()
