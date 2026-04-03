#!/usr/bin/env python3
"""
generate_prompt.py — Perimeter/Courtyard (周边式) prompt generator for text2ckm.

Usage:
    python generate_prompt.py             # generate 1 prompt
    python generate_prompt.py --count 5   # generate 5 prompts
"""

import argparse
import random

MATERIAL_NAMES = {"concrete": "混凝土", "marble": "大理石",
                  "metal": "金属", "wood": "木材", "glass": "玻璃幕墙"}
BUILDING_MATERIAL_WEIGHTS = {"concrete": 0.50, "glass": 0.20,
                              "metal": 0.10, "marble": 0.10, "wood": 0.10}
ROAD_MATERIAL_WEIGHTS = {"marble": 0.70, "concrete": 0.20, "metal": 0.10}
FREQ_CANDIDATES = [0.9, 1.8, 2.4, 3.5, 5.8, 28.0, 39.0, 60.0]
BLDG_OPTIONS = ["u_shaped", "l_shaped", "rectangular"]
BLDG_OPTION_NAMES = {
    "u_shaped":    "U形庭院建筑（单栋三面围合）",
    "l_shaped":    "L形建筑（两栋组合围合）",
    "rectangular": "矩形板式建筑（三栋围三面）",
}


def _r(lo: float, hi: float, decimals: int = 2) -> float:
    return round(random.uniform(lo, hi), decimals)


def _weighted_choice(d: dict) -> str:
    return random.choices(list(d.keys()), weights=list(d.values()), k=1)[0]


def generate_prompt() -> str:
    n_blocks = random.randint(2, 4)
    block_size = _r(60.0, 100.0)
    road_width = _r(7.0, 10.0)
    setback = _r(3.0, 5.0)
    bldg_opt = random.choices(BLDG_OPTIONS, weights=[0.6, 0.25, 0.15])[0]
    bldg_opt_cn = BLDG_OPTION_NAMES[bldg_opt]
    b_mat_cn = MATERIAL_NAMES[_weighted_choice(BUILDING_MATERIAL_WEIGHTS)]
    road_mat_cn = MATERIAL_NAMES[_weighted_choice(ROAD_MATERIAL_WEIGHTS)]
    h_min = _r(9.0, 20.0)
    h_max = _r(h_min + 5.0, min(h_min + 40.0, 50.0))
    layout = "行排列" if n_blocks <= 3 else "2×2网格排列"

    tx_parts, rx_parts, rt_parts = [], [], []
    if random.random() < 0.70:
        tx_parts.append(f"频率{random.choice(FREQ_CANDIDATES)}GHz")
    if random.random() < 0.55:
        tx_parts.append(f"发射功率{_r(20.0, 46.0, 1)}dBm")
    if random.random() < 0.50:
        tx_parts.append(f"天线高度{_r(3.0, 25.0, 1)}m")
    if random.random() < 0.65:
        rx_parts.append(f"接收机高度{_r(1.0, 3.0, 1)}m")
    if random.random() < 0.60:
        rt_parts.append(f"仿真区域{random.choice([150, 200, 250, 300])}m")

    lines = [
        f"请生成周边式围合布局场景：{n_blocks}个正方形街区（每块约{block_size}m），{layout}。",
        f"每个街区用{bldg_opt_cn}三面或四面围合内庭院，庭院内部留空，不放置任何建筑或道路。",
        f"建筑材质{b_mat_cn}，高度{h_min}–{h_max}m，各栋高度各不相同。",
        f"建筑朝向与街区轴线对齐（旋转角0度或90度），退道路红线{setback}m。",
        f"沿街区外侧设置周边直线道路（宽{road_width}m，{road_mat_cn}材质），建筑距道路边缘不少于5m。",
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
    parser = argparse.ArgumentParser(description="Generate perimeter scene prompts.")
    parser.add_argument("--count", "-n", type=int, default=1)
    args = parser.parse_args()
    for i in range(args.count):
        print(generate_prompt())
        if args.count > 1 and i < args.count - 1:
            print()


if __name__ == "__main__":
    main()
