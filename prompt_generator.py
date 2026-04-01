"""
prompt_generator.py — 随机生成中文场景描述提示词，保存为 .txt 文件供 main.py 消费。

用法：
    python prompt_generator.py                         # 生成 1 个提示词到 text_prompts/
    python prompt_generator.py --count 10              # 生成 10 个
    python prompt_generator.py --count 5 --output-dir text_prompts/ --prefix scene_
"""

import argparse
import random
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# 常量映射
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

# 建筑材质权重（偏向混凝土，玻璃/金属次之）
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

# 常用频段（GHz）
FREQ_CANDIDATES = [0.9, 1.8, 2.4, 3.5, 5.8, 28.0, 39.0, 60.0]


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _r(lo: float, hi: float, decimals: int = 2) -> float:
    """在 [lo, hi] 范围内生成指定小数位的随机浮点数。"""
    val = random.uniform(lo, hi)
    return round(val, decimals)


def _weighted_choice(weight_dict: dict):
    keys = list(weight_dict.keys())
    weights = list(weight_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# 高度描述
# ---------------------------------------------------------------------------

def _rand_height_desc() -> str:
    """随机生成高度描述：固定值或范围。"""
    use_range = random.random() < 0.5
    if use_range:
        h_min = _r(5.0, 60.0)
        h_max = _r(h_min + 10.0, min(h_min + 80.0, 150.0))
        return f"高度随机从{h_min}到{h_max}米"
    else:
        h = _r(5.0, 120.0)
        return f"高度{h}米"


# ---------------------------------------------------------------------------
# 各建筑类型的尺寸描述
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
# 建筑组描述
# ---------------------------------------------------------------------------

def _rand_building_group(btype: str, count: int) -> str:
    """生成一组同类型建筑的完整中文描述片段（含旋转和尺寸差异要求）。"""
    type_name = BUILDING_TYPE_NAMES[btype]
    dim_desc = _DIM_DESC_FUNCS[btype]()
    height_desc = _rand_height_desc()
    mat = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
    mat_name = MATERIAL_NAMES[mat]
    return (
        f"{count}栋{type_name}（{dim_desc}，{height_desc}，{mat_name}材质，"
        f"每栋旋转角度各不相同（0-360度随机），每栋{type_name}的外形尺寸参数各不相同）"
    )


# ---------------------------------------------------------------------------
# 道路描述（8 种路网模板）
# ---------------------------------------------------------------------------

def _rand_road_desc(_ignored: int = 0) -> str:
    """从 8 种复杂路网模板中随机选取一种生成道路描述。"""
    width = _r(6.0, 12.0)
    mat = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    mat_name = MATERIAL_NAMES[mat]
    w = width
    m = mat_name

    templates = [
        # 0: 错位双十字网格
        f"两条东西向横道（Y轴偏移不同，间距随机）加两条南北向纵道（X轴偏移不同），共4条直线道路，宽{w}米，形成错位网格路网，{m}材质",
        # 1: 斜向+正交混合
        f"一条水平直道、一条纵向直道加一条约45度斜向道路，共3条，宽{w}米，{m}材质",
        # 2: 放射状四叉
        f"从场景中心向4个不同方向（约0°/50°/100°/160°）放射延伸的4条直道，宽{w}米，{m}材质",
        # 3: 城市街区网格
        f"城市街区路网：3条东西向横道（间距不等）加2条南北向纵道（间距不等），共5条直线道路，宽{w}米，{m}材质",
        # 4: Y形三叉
        f"Y形三叉路口：3条直道以约120度夹角从中心延伸至场景边缘，宽{w}米，{m}材质",
        # 5: 弧形+直道组合
        f"一条弧形曲线道路绕过建筑群一侧（smooth曲线，3个控制点），加两条相互错开的直线干道，共3段道路，宽{w}米，{m}材质",
        # 6: 折线+直道混合
        f"两条含转折点的折线道路（各含2个弯角，角度约30-60度）加一条横贯场景的直道，共3段，宽{w}米，{m}材质",
        # 7: 菱形对角网格
        f"两条平行斜向道路（约30度倾斜）加两条水平直道，共4条，形成菱形路网，宽{w}米，{m}材质",
    ]
    return random.choice(templates)


# ---------------------------------------------------------------------------
# TX / RX / RT 描述
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
# 城市街区布局提示词生成
# ---------------------------------------------------------------------------

def _generate_urban_block_prompt() -> str:
    """生成触发城市街区布局规则的中文提示词。"""
    theta = _r(15.0, 50.0)
    n_long = random.choice([2, 3])
    n_trans = random.choice([2, 3])
    long_spacing = _r(50.0, 70.0)
    trans_spacing = _r(45.0, 65.0)
    road_width = _r(7.0, 10.0)
    road_mat = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    road_mat_name = MATERIAL_NAMES[road_mat]
    n_per_block = random.randint(2, 4)
    setback = _r(4.0, 6.0)

    btype = random.choice(list(BUILDING_TYPE_NAMES.keys()))
    type_name = BUILDING_TYPE_NAMES[btype]
    dim_desc = _DIM_DESC_FUNCS[btype]()
    height_desc = _rand_height_desc()
    b_mat = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
    b_mat_name = MATERIAL_NAMES[b_mat]

    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = (
        f"创建虚拟场景：按城市街区排列，道路网格整体旋转{theta}度，"
        f"{n_long}条纵向道路（间距{long_spacing}米）和{n_trans}条横向道路（间距{trans_spacing}米），"
        f"道路宽{road_width}米，{road_mat_name}材质，"
        f"每个街区内随机放置{n_per_block}栋{type_name}（{dim_desc}，{height_desc}，{b_mat_name}材质），"
        f"建筑物朝向与道路一致（旋转角均为{theta}度），同一街区内每栋尺寸各不相同，"
        f"距道路边缘至少{setback}米净距，"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


# ---------------------------------------------------------------------------
# 完整提示词生成
# ---------------------------------------------------------------------------

def generate_random_prompt() -> str:
    """生成一条完整的随机中文场景提示词（40% 概率为城市街区布局）。"""
    if random.random() < 0.40:
        return _generate_urban_block_prompt()

    all_types = list(BUILDING_TYPE_NAMES.keys())

    # 决定类型组合数量
    n_type_groups = random.choices([1, 2, 3], weights=[0.50, 0.35, 0.15])[0]
    selected_types = random.sample(all_types, n_type_groups)

    # 决定总建筑数，并分配到各类型
    total_buildings = random.randint(3, 15)
    if n_type_groups == 1:
        counts = [total_buildings]
    else:
        # 保证每组至少 1 栋
        counts = [1] * n_type_groups
        remaining = total_buildings - n_type_groups
        for i in range(remaining):
            counts[random.randint(0, n_type_groups - 1)] += 1

    # 道路数量
    n_roads = random.randint(1, 3)

    # 组装建筑描述
    if n_type_groups == 1:
        btype = selected_types[0]
        type_name = BUILDING_TYPE_NAMES[btype]
        dim_desc = _DIM_DESC_FUNCS[btype]()
        height_desc = _rand_height_desc()
        mat = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
        mat_name = MATERIAL_NAMES[mat]
        building_part = (
            f"在场景中心周围随机放置{total_buildings}栋{type_name}，"
            f"{dim_desc}，{height_desc}，材质为{mat_name}，"
            f"每栋旋转角度各不相同（0-360度随机），每栋{type_name}的外形尺寸参数各不相同"
        )
    else:
        group_descs = [
            _rand_building_group(btype, cnt)
            for btype, cnt in zip(selected_types, counts)
        ]
        building_part = (
            f"在场景中心周围随机放置{total_buildings}栋建筑，包括"
            + "、".join(group_descs)
        )

    road_part = f"在建筑间创建{_rand_road_desc(n_roads)}"
    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = f"创建虚拟场景：{building_part}，{road_part}，{tx_part}，{rx_part}，{rt_part}"
    return prompt


# ---------------------------------------------------------------------------
# 文件保存
# ---------------------------------------------------------------------------

def _next_filename(output_dir: Path, prefix: str) -> Path:
    """扫描已有同前缀文件，返回下一个可用文件名（如 scene_007.txt）。"""
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)\.txt$")
    max_num = 0
    for f in output_dir.glob(f"{prefix}*.txt"):
        m = pattern.match(f.name)
        if m:
            max_num = max(max_num, int(m.group(1)))
    next_num = max_num + 1
    return output_dir / f"{prefix}{next_num:03d}.txt"


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="随机生成中文场景提示词并保存为 .txt 文件"
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
        "--prefix", "-p", type=str, default="scene_",
        help="文件名前缀（默认 scene_）"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(args.count):
        prompt = generate_random_prompt()
        filepath = _next_filename(output_dir, args.prefix)
        filepath.write_text(prompt + "\n", encoding="utf-8")
        print(f"[{i+1}/{args.count}] Saved: {filepath}")
        print(f"        {prompt}\n")

    print(f"Done. {args.count} prompt(s) saved to {output_dir}/")


if __name__ == "__main__":
    main()
