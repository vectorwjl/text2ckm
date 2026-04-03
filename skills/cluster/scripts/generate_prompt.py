#!/usr/bin/env python3
"""
generate_prompt.py — Cluster (组团式) prompt generator for text2ckm.

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
    n_clusters = random.choice([3, 4])
    n_per_cluster = random.randint(3, 5)
    cluster_gap = _r(10.0, 15.0)
    inter_gap = _r(50.0, 80.0)
    road_width = _r(7.0, 10.0)
    road_mat_cn = MATERIAL_NAMES[_weighted_choice(ROAD_MATERIAL_WEIGHTS)]
    b_mat_cn = MATERIAL_NAMES[_weighted_choice(BUILDING_MATERIAL_WEIGHTS)]
    btype = random.choice(list(BUILDING_TYPE_NAMES.keys()))
    type_cn = BUILDING_TYPE_NAMES[btype]
    h_min = _r(10.0, 30.0)
    h_max = _r(h_min + 10.0, min(h_min + 50.0, 80.0))
    n_connect = n_clusters - 1

    layout_desc = "分布在场景各象限" if n_clusters == 4 else "呈三角形分布"

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
        rt_parts.append(f"仿真区域{random.choice([200, 250, 300, 350, 400])}m")

    lines = [
        f"请生成组团式布局场景：{n_clusters}个独立建筑组团{layout_desc}，"
        f"每组团{n_per_cluster}栋{type_cn}，",
        f"组团内建筑紧凑排列（间距{cluster_gap}m），组团间距至少{inter_gap}m，",
        f"同一组团内建筑朝向相近（旋转角相差不超过15度），各栋尺寸各不相同，",
        f"高度{h_min}–{h_max}m，材质{b_mat_cn}。",
        f"每个组团内设一条短道路（宽{road_width}m，{road_mat_cn}材质），",
        f"加{n_connect}条组团间连接主道路。建筑距道路边缘不少于5m。",
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
    parser = argparse.ArgumentParser(description="Generate cluster scene prompts.")
    parser.add_argument("--count", "-n", type=int, default=1)
    args = parser.parse_args()
    for i in range(args.count):
        print(generate_prompt())
        if args.count > 1 and i < args.count - 1:
            print()


if __name__ == "__main__":
    main()
