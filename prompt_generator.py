"""
prompt_generator.py — 批量生成场景描述 .txt 文件，放入 text_prompts/ 目录。

用法:
    python prompt_generator.py           # 生成 10 个（默认）
    python prompt_generator.py 50        # 生成 50 个
    python prompt_generator.py 20 --seed 42   # 固定随机种子（可复现）
"""

import argparse
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# 参数选项池
# ---------------------------------------------------------------------------

SCENE_TYPES = [
    "城市街区", "商业区", "工业园区", "住宅小区", "校园", "开阔地带",
    "科技园区", "历史街区", "滨海商务区", "城市综合体",
]

ROAD_FORMS = ["平行", "交叉", "L形", "环形"]

FREQS = [3.5, 28.0]

TX_LOCS = [
    "场景中心",
    "场景中心偏北", "场景中心偏南", "场景中心偏东", "场景中心偏西",
    "场景西北角", "场景东北角", "场景西南角", "场景东南角",
]

MAP_SIZES = [200]

CITIES = ["北京", "上海", "深圳", "广州", "成都", "武汉", "杭州", "南京", ""]  # ""=不指定

MATERIAL_HINTS = [
    "以混凝土结构为主",
    "以玻璃幕墙建筑为主",
    "砖混结构为主",
    "",  # 不指定材质
    "",
    "",  # 多放几个空，降低材质描述出现频率
]

TX_HEIGHT_RANGES = [(5, 15), (10, 25), (20, 35)]  # (min, max) 分段采样

# 建筑高度分布模式（权重之和为 1.0）
HEIGHT_PATTERNS = [
    ("highly_varied", 0.15),   # 高度差异很大
    ("uniform",       0.15),   # 高度基本一致
    ("moderate",      0.70),   # 高度有差异但差距不大
]

# 建筑形状概率表（权重之和为 1.0）
BUILDING_SHAPES = {
    "矩形":         0.30,
    "梯形":         0.20,
    "L形":          0.20,
    "T形":          0.15,
    "正六边形":     0.10,
    "不规则多边形": 0.05,
}


# ---------------------------------------------------------------------------
# 形状采样
# ---------------------------------------------------------------------------

def _sample_height_desc(rng: random.Random) -> str:
    """按概率采样建筑高度分布模式，返回中文描述字符串。"""
    patterns = [p[0] for p in HEIGHT_PATTERNS]
    weights  = [p[1] for p in HEIGHT_PATTERNS]
    pattern  = rng.choices(patterns, weights=weights, k=1)[0]

    if pattern == "highly_varied":
        h_min = rng.randint(5, 15)
        h_max = rng.randint(60, 120)
        return f"建筑物高度差异显著，各栋高度各不相同（高度从约{h_min}m到约{h_max}m不等）"
    elif pattern == "uniform":
        base_h = rng.randint(15, 50)
        return f"建筑物高度基本一致（各栋高度约{base_h}m，相互之间误差不超过5m）"
    else:  # moderate
        h_min = rng.randint(10, 25)
        h_max = h_min + rng.randint(15, 35)
        return f"建筑物高度有一定差异但差距不大（高度约在{h_min}m至{h_max}m范围内）"


def _sample_shape_counts(rng: random.Random, n_bld: int) -> dict:
    """按概率为 n_bld 栋建筑各选一种形状，返回 {形状: 数量} 字典。"""
    shapes  = list(BUILDING_SHAPES.keys())
    weights = list(BUILDING_SHAPES.values())
    picks   = rng.choices(shapes, weights=weights, k=n_bld)
    counts: dict = {}
    for s in picks:
        counts[s] = counts.get(s, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# 核心生成函数
# ---------------------------------------------------------------------------

def make_prompt(rng: random.Random) -> str:
    scene    = rng.choice(SCENE_TYPES)
    n_bld    = rng.randint(4, 8)
    n_road   = rng.randint(1, 3)
    road_f   = rng.choice(ROAD_FORMS)
    freq     = rng.choice(FREQS)
    tx_loc   = rng.choice(TX_LOCS)
    tx_h_min, tx_h_max = rng.choice(TX_HEIGHT_RANGES)
    tx_h     = rng.randint(tx_h_min, tx_h_max)
    mapsize  = rng.choice(MAP_SIZES)
    city     = rng.choice(CITIES)
    mat_hint = rng.choice(MATERIAL_HINTS)

    city_str = f"模拟{city}" if city else "虚拟"

    if n_road == 1:
        road_str = "1条主干道"
    else:
        road_str = f"{n_road}条{road_f}道路"

    mat_str = f"，建筑{mat_hint}" if mat_hint else ""

    # 按概率采样各形状数量和高度分布，写入 prompt
    shape_counts = _sample_shape_counts(rng, n_bld)
    shape_str    = "、".join(f"{v}栋{k}建筑" for k, v in shape_counts.items())
    height_desc  = _sample_height_desc(rng)

    lines = [
        f"生成一个{city_str}{scene}场景{mat_str}，",
        f"包含{shape_str}以及{road_str}，每种形状各自保持独特外观。",
        f"{height_desc}。",
        f"发射机频率{freq}GHz，天线位于{tx_loc}，高度约{tx_h}m。",
        f"场景范围约{mapsize}m×{mapsize}m。",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 文件命名：scene_NNNN.txt，从当前最大编号 +1 开始
# ---------------------------------------------------------------------------

def _next_index(out_dir: Path) -> int:
    existing = [
        int(p.stem.split("_")[-1])
        for p in out_dir.glob("scene_*.txt")
        if p.stem.split("_")[-1].isdigit()
    ]
    return max(existing, default=0) + 1


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="批量生成场景描述 txt 文件")
    parser.add_argument("count", nargs="?", type=int, default=10,
                        help="生成数量（默认 10）")
    parser.add_argument("--seed", type=int, default=None,
                        help="随机种子（固定后结果可复现）")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    out_dir = Path("text_prompts")
    out_dir.mkdir(exist_ok=True)

    start_idx = _next_index(out_dir)
    generated = []

    for i in range(args.count):
        idx = start_idx + i
        prompt = make_prompt(rng)
        filename = out_dir / f"scene_{idx:04d}.txt"
        filename.write_text(prompt, encoding="utf-8")
        generated.append(filename)
        print(f"  {filename.name}: {prompt.splitlines()[0]}")

    print(f"\n[prompt_generator] 已生成 {len(generated)} 个 prompt 文件 → {out_dir}/")


if __name__ == "__main__":
    main()
