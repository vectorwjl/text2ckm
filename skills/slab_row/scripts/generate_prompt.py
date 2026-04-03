#!/usr/bin/env python3
"""
generate_prompt.py — Slab Row (行列式) prompt generator for text2ckm.

Generates Chinese-language prompts describing slab row scenes.

Usage:
    python generate_prompt.py             # generate 1 prompt
    python generate_prompt.py --count 5   # generate 5 prompts
"""

import argparse
import random

BUILDING_TYPE_NAMES = {"rectangular": "矩形建筑", "l_shaped": "L形建筑",
                       "t_shaped": "T形建筑", "u_shaped": "U形庭院建筑"}
MATERIAL_NAMES = {"concrete": "混凝土", "marble": "大理石",
                  "metal": "金属", "wood": "木材", "glass": "玻璃幕墙"}
BUILDING_MATERIAL_WEIGHTS = {"concrete": 0.45, "glass": 0.20,
                              "metal": 0.15, "marble": 0.10, "wood": 0.10}
ROAD_MATERIAL_WEIGHTS = {"marble": 0.70, "concrete": 0.20, "metal": 0.10}
FREQ_CANDIDATES = [0.9, 1.8, 2.4, 3.5, 5.8, 28.0, 39.0, 60.0]


def _r(lo: float, hi: float, decimals: int = 2) -> float:
    return round(random.uniform(lo, hi), decimals)


def _weighted_choice(d: dict) -> str:
    return random.choices(list(d.keys()), weights=list(d.values()), k=1)[0]


def generate_prompt() -> str:
    n_rows = random.randint(3, 4)
    n_per_row = random.randint(2, 3)
    row_spacing = _r(30.0, 50.0)
    bldg_gap = _r(8.0, 15.0)
    road_width = _r(7.0, 9.0)
    road_mat_cn = MATERIAL_NAMES[_weighted_choice(ROAD_MATERIAL_WEIGHTS)]
    b_mat_cn = MATERIAL_NAMES[_weighted_choice(BUILDING_MATERIAL_WEIGHTS)]

    slab_w = _r(8.0, 14.0)
    slab_l_min = round(slab_w * 3.0, 2)
    slab_l_max = round(slab_w * 5.0, 2)
    h_min = _r(10.0, 25.0)
    h_max = _r(h_min + 8.0, min(h_min + 50.0, 80.0))
    row_angle = _r(0.0, 3.0) if random.random() < 0.75 else _r(87.0, 93.0)

    tx_parts, rx_parts, rt_parts = [], [], []
    if random.random() < 0.70:
        tx_parts.append(f"频率{random.choice(FREQ_CANDIDATES)}GHz")
    if random.random() < 0.55:
        tx_parts.append(f"发射功率{_r(20.0, 46.0, 1)}dBm")
    if random.random() < 0.50:
        tx_parts.append(f"天线高度{_r(3.0, 30.0, 1)}m")
    if random.random() < 0.65:
        rx_parts.append(f"接收机高度{_r(1.0, 3.0, 1)}m")
    if random.random() < 0.60:
        rt_parts.append(f"仿真区域{random.choice([150, 200, 250, 300, 400])}m")

    lines = [
        f"请生成行列式布局场景：{n_rows}排平行板式矩形建筑，每排{n_per_row}栋，"
        f"行间距{row_spacing}m，同排建筑间距{bldg_gap}m。",
        f"每栋建筑宽度约{slab_w}m，长度在{slab_l_min}到{slab_l_max}m之间"
        f"（长宽比不低于3:1），每排建筑长度各不相同（相差≥5m）。",
        f"建筑高度{h_min}–{h_max}m，各栋高度各不相同，材质{b_mat_cn}。",
        f"所有建筑旋转角约{row_angle}度（同排一致）。",
        f"设2条与行方向平行的主道路（宽{road_width}m，{road_mat_cn}材质）"
        f"和1条垂直横道。建筑距道路边缘不少于5m。",
    ]
    if tx_parts:
        lines.append("发射机参数：" + "，".join(tx_parts) + "。")
    if rx_parts:
        lines.append("接收机参数：" + "，".join(rx_parts) + "。")
    if rt_parts:
        lines.append("射线追踪参数：" + "，".join(rt_parts) + "。")
    lines.append("请严格按JSON格式输出，所有数值精确到小数点后两位。")
    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate slab row scene prompts.")
    parser.add_argument("--count", "-n", type=int, default=1)
    args = parser.parse_args()
    for i in range(args.count):
        print(generate_prompt())
        if args.count > 1 and i < args.count - 1:
            print()


if __name__ == "__main__":
    main()
