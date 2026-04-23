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

FREQS = [0.9, 2.4, 3.5, 6.0, 28.0, 60.0, 77.0, 100.0]

TX_LOCS = [
    "场景中心",
    "场景中心偏北", "场景中心偏南", "场景中心偏东", "场景中心偏西",
    "场景西北角", "场景东北角", "场景西南角", "场景东南角",
]

MAP_SIZES = [100, 150, 200, 250, 300]

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

    lines = [
        f"生成一个{city_str}{scene}场景{mat_str}，",
        f"包含{n_bld}栋不同高度和形状的建筑物以及{road_str}。",
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
