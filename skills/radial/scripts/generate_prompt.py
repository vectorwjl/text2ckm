"""
generate_prompt.py — Generates random Chinese-language scene prompts for the
radial (放射式) layout style.

Usage:
    python skills/radial/scripts/generate_prompt.py --count 1
    python skills/radial/scripts/generate_prompt.py --count 5
"""

import argparse
import random

# ---------------------------------------------------------------------------
# Constants
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
# Utility helpers
# ---------------------------------------------------------------------------

def _r(lo: float, hi: float, decimals: int = 2) -> float:
    """Return a random float in [lo, hi] rounded to `decimals` places."""
    return round(random.uniform(lo, hi), decimals)


def _weighted_choice(weight_dict: dict):
    keys = list(weight_dict.keys())
    weights = list(weight_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Dimension description helpers (per building type)
# ---------------------------------------------------------------------------

def _dim_desc_rectangular() -> str:
    use_range = random.random() < 0.5
    if use_range:
        w_min = _r(8.0, 20.0)
        w_max = _r(w_min + 3.0, 30.0)
        l_min = _r(8.0, 25.0)
        l_max = _r(l_min + 3.0, 40.0)
        return f"宽度随机从{w_min}到{w_max}米，长度随机从{l_min}到{l_max}米"
    else:
        w = _r(8.0, 30.0)
        l = _r(8.0, 40.0)
        return f"宽{w}米、长{l}米"


def _dim_desc_l_shaped() -> str:
    w1 = _r(15.0, 35.0)
    l1 = _r(15.0, 35.0)
    w2 = _r(5.0, min(w1 * 0.7, 20.0))
    l2 = _r(5.0, min(l1 * 0.7, 20.0))
    return f"主体{w1}×{l1}米，翼部{w2}×{l2}米"


def _dim_desc_t_shaped() -> str:
    mw = _r(20.0, 50.0)
    ml = _r(15.0, 35.0)
    ww = _r(8.0, min(mw * 0.5, 20.0))
    wl = _r(6.0, min(ml * 0.5, 15.0))
    return f"主体{mw}×{ml}米，侧翼{ww}×{wl}米"


def _dim_desc_u_shaped() -> str:
    ow = _r(30.0, 60.0)
    ol = _r(30.0, 60.0)
    factor = _r(0.4, 0.7)
    iw = round(ow * factor, 2)
    il = round(ol * factor, 2)
    return f"外围{ow}×{ol}米，内庭{iw}×{il}米"


_DIM_DESC_FUNCS = {
    "rectangular": _dim_desc_rectangular,
    "l_shaped":    _dim_desc_l_shaped,
    "t_shaped":    _dim_desc_t_shaped,
    "u_shaped":    _dim_desc_u_shaped,
}


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
    map_size = random.randint(150, 400)
    return f"地图尺寸{map_size}米"


# ---------------------------------------------------------------------------
# Core radial prompt generator
# ---------------------------------------------------------------------------

def generate_prompt() -> str:
    """Generate a single random Chinese-language radial layout scene prompt.

    Matches the style and parameters of _generate_radial_prompt() in
    prompt_generator.py:
      - 4–6 rays at evenly-spaced angles
      - 2–4 buildings per ray
      - ray_interval = 360 / n_rays degrees
      - buildings at dist_min to dist_max from origin
      - single building type per scene
      - TX, RX, RT parameters appended
    """
    n_rays = random.choice([4, 5, 6])
    n_per_ray = random.randint(2, 4)
    ray_interval = round(360.0 / n_rays, 2)
    dist_min = _r(20.0, 35.0)
    dist_max = _r(60.0, 100.0)
    road_width = _r(7.0, 10.0)
    road_mat = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    road_mat_name = MATERIAL_NAMES[road_mat]

    btype = random.choice(list(BUILDING_TYPE_NAMES.keys()))
    type_name = BUILDING_TYPE_NAMES[btype]
    dim_desc = _DIM_DESC_FUNCS[btype]()
    height_desc_lo = _r(10.0, 40.0)
    height_desc_hi = _r(height_desc_lo + 15.0, min(height_desc_lo + 80.0, 120.0))
    b_mat = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
    b_mat_name = MATERIAL_NAMES[b_mat]

    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = (
        f"创建虚拟场景：放射式布局，{n_rays}条道路从场景中心向外辐射延伸"
        f"（每条间隔约{ray_interval}度），道路宽{road_width}米，{road_mat_name}材质，"
        f"沿每条射线在距中心{dist_min}到{dist_max}米范围内排列{n_per_ray}栋{type_name}，"
        f"（{dim_desc}，高度从{height_desc_lo}到{height_desc_hi}米随机，{b_mat_name}材质），"
        f"每栋建筑旋转角度与所在射线方向一致，各栋尺寸各不相同，"
        f"同一射线上的建筑旋转角度相差0.01度以保证唯一性，"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate random Chinese radial layout scene prompts."
    )
    parser.add_argument(
        "--count", "-n", type=int, default=1,
        help="Number of prompts to generate (default: 1)"
    )
    args = parser.parse_args()

    for i in range(args.count):
        prompt = generate_prompt()
        print(f"[{i + 1}/{args.count}] {prompt}\n")


if __name__ == "__main__":
    main()
