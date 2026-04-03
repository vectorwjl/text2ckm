#!/usr/bin/env python3
"""
generate_prompt.py — Organic/Freeform (有机式) prompt generator for text2ckm.

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


def _rand_building_group(btype: str, count: int) -> str:
    type_name = BUILDING_TYPE_NAMES[btype]
    mat_cn = MATERIAL_NAMES[_weighted_choice(BUILDING_MATERIAL_WEIGHTS)]
    return (f"{count}栋{type_name}（{mat_cn}材质，每栋旋转角度各不相同（0-360度随机），"
            f"每栋{type_name}的外形尺寸参数各不相同）")


def generate_prompt() -> str:
    n_buildings = random.randint(10, 15)
    all_types = list(BUILDING_TYPE_NAMES.keys())
    n_types = random.choices([2, 3], weights=[0.5, 0.5])[0]
    selected = random.sample(all_types, n_types)
    counts = [1] * n_types
    for _ in range(n_buildings - n_types):
        counts[random.randint(0, n_types - 1)] += 1
    group_descs = [_rand_building_group(t, c) for t, c in zip(selected, counts)]
    building_part = "、".join(group_descs)

    n_roads = random.choice([2, 3])
    road_width = _r(6.0, 10.0)
    road_mat_cn = MATERIAL_NAMES[_weighted_choice(ROAD_MATERIAL_WEIGHTS)]
    setback_min = _r(5.0, 8.0)
    setback_max = _r(setback_min + 3.0, 15.0)
    h_min = _r(10.0, 30.0)
    h_max = _r(h_min + 20.0, min(h_min + 90.0, 120.0))

    tx_parts, rx_parts, rt_parts = [], [], []
    if random.random() < 0.70:
        tx_parts.append(f"频率{random.choice(FREQ_CANDIDATES)}GHz")
    if random.random() < 0.55:
        tx_parts.append(f"发射功率{_r(20.0, 46.0, 1)}dBm")
    if random.random() < 0.50:
        tx_parts.append(f"天线高度{_r(3.0, 40.0, 1)}m")
    if random.random() < 0.65:
        rx_parts.append(f"接收机高度{_r(1.0, 3.0, 1)}m")
    if random.random() < 0.60:
        rt_parts.append(f"仿真区域{random.choice([200, 250, 300, 350, 400])}m")

    lines = [
        f"请生成有机自由式布局场景：{n_buildings}栋建筑不规则散布，包括{building_part}，",
        f"建筑位置无规律、旋转角度完全随机（各不相同），高度{h_min}–{h_max}m，各栋高度各不相同，",
        f"设置{n_roads}条蜿蜒弯曲的曲线道路（smooth曲线，每条至少3个控制点），",
        f"道路宽{road_width}m，{road_mat_cn}材质，建筑松散地分布在道路两侧，",
        f"退距各不相同（{setback_min}到{setback_max}米随机），建筑距道路边缘不少于5m。",
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
    parser = argparse.ArgumentParser(description="Generate organic scene prompts.")
    parser.add_argument("--count", "-n", type=int, default=1)
    args = parser.parse_args()
    for i in range(args.count):
        print(generate_prompt())
        if args.count > 1 and i < args.count - 1:
            print()


if __name__ == "__main__":
    main()
