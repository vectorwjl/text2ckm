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
# 布局风格提示词生成函数
# ---------------------------------------------------------------------------

def _generate_orthogonal_grid_prompt() -> str:
    """方格网式：轴对齐街区路网，建筑与坐标轴平行。"""
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
        f"创建虚拟场景：方格网布局，正交街区路网，"
        f"{n_long}条南北向纵向道路（间距{long_spacing}米）和{n_trans}条东西向横向道路（间距{trans_spacing}米），"
        f"道路宽{road_width}米，{road_mat_name}材质，"
        f"每个街区内放置{n_per_block}栋{type_name}（{dim_desc}，{height_desc}，{b_mat_name}材质），"
        f"建筑物朝向与坐标轴平行（旋转角为0度），同一街区内每栋尺寸各不相同，"
        f"距道路边缘至少{setback}米净距，"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


def _generate_slab_row_prompt() -> str:
    """行列式：平行板式建筑排成整齐行列。"""
    n_rows = random.randint(3, 4)
    n_per_row = random.randint(2, 3)
    row_spacing = _r(30.0, 50.0)
    bldg_gap = _r(8.0, 15.0)
    road_width = _r(7.0, 10.0)
    road_mat = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    road_mat_name = MATERIAL_NAMES[road_mat]
    b_mat = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
    b_mat_name = MATERIAL_NAMES[b_mat]

    # 板式建筑：长宽比 3:1 到 5:1
    slab_w = _r(8.0, 14.0)
    slab_l_min = round(slab_w * 3.0, 2)
    slab_l_max = round(slab_w * 5.0, 2)
    height_desc = _rand_height_desc()

    # 行方向角度：大多数与轴平行，偶尔略微旋转
    row_angle = _r(0.0, 5.0) if random.random() < 0.7 else _r(85.0, 95.0)

    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = (
        f"创建虚拟场景：行列式布局，{n_rows}排平行板式矩形建筑，"
        f"每排{n_per_row}栋，行间距{row_spacing}米，同排建筑间距{bldg_gap}米，"
        f"每栋建筑宽{slab_w}米、长度在{slab_l_min}到{slab_l_max}米之间（长宽比3:1至5:1），"
        f"{height_desc}，{b_mat_name}材质，"
        f"所有建筑朝向一致（旋转角约{row_angle}度），每栋长度各不相同，"
        f"两条与行方向平行的主要道路贯穿场景（宽{road_width}米，{road_mat_name}材质），"
        f"加一条垂直于行方向的横向道路，"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


def _generate_point_scatter_prompt() -> str:
    """点式散布：独立塔楼随机散点分布，道路稀少。"""
    n_buildings = random.randint(8, 15)
    all_types = list(BUILDING_TYPE_NAMES.keys())
    n_type_groups = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
    selected_types = random.sample(all_types, n_type_groups)

    counts = [1] * n_type_groups
    for _ in range(n_buildings - n_type_groups):
        counts[random.randint(0, n_type_groups - 1)] += 1

    group_descs = [
        _rand_building_group(btype, cnt)
        for btype, cnt in zip(selected_types, counts)
    ]
    building_part = "、".join(group_descs)

    road_width = _r(7.0, 10.0)
    road_mat = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    road_mat_name = MATERIAL_NAMES[road_mat]

    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = (
        f"创建虚拟场景：点式散布布局，{n_buildings}栋独立塔楼建筑随机散点分布，包括{building_part}，"
        f"建筑均匀散布在整个场景中，每栋旋转角度各不相同，每栋间距不小于20米，"
        f"仅设1到2条简单横纵道路（宽{road_width}米，{road_mat_name}材质），"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


def _generate_perimeter_prompt() -> str:
    """周边式：建筑沿街区周边布置，围合内庭院。"""
    n_blocks = random.randint(2, 4)
    block_size = _r(60.0, 100.0)
    road_width = _r(7.0, 10.0)
    road_mat = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    road_mat_name = MATERIAL_NAMES[road_mat]
    setback = _r(3.0, 5.0)

    # 周边式以U形和L形为主
    btypes = random.choices(["u_shaped", "l_shaped"], weights=[0.6, 0.4], k=n_blocks)
    type_names = [BUILDING_TYPE_NAMES[bt] for bt in btypes]
    height_desc = _rand_height_desc()
    b_mat = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
    b_mat_name = MATERIAL_NAMES[b_mat]

    bldg_desc = f"每个街区放置1栋{'或'.join(set(type_names))}围合建筑"

    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = (
        f"创建虚拟场景：周边式围合布局，{n_blocks}个正方形街区（每块约{block_size}米），"
        f"{bldg_desc}，建筑三面或四面围合内庭院，庭院内部留空，"
        f"{height_desc}，{b_mat_name}材质，建筑朝向与街区轴线一致，"
        f"沿街区外侧设置周边道路（宽{road_width}米，{road_mat_name}材质），"
        f"建筑距道路边缘{setback}米，"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


def _generate_radial_prompt() -> str:
    """放射式：道路从中心向四周辐射，建筑沿射线排列。"""
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
    height_desc = _rand_height_desc()
    b_mat = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
    b_mat_name = MATERIAL_NAMES[b_mat]

    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = (
        f"创建虚拟场景：放射式布局，{n_rays}条道路从场景中心向外辐射延伸"
        f"（每条间隔约{ray_interval}度），道路宽{road_width}米，{road_mat_name}材质，"
        f"沿每条射线在距中心{dist_min}到{dist_max}米范围内排列{n_per_ray}栋{type_name}，"
        f"（{dim_desc}，{height_desc}，{b_mat_name}材质），"
        f"每栋建筑旋转角度与所在射线方向一致，各栋尺寸各不相同，"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


def _generate_cluster_prompt() -> str:
    """组团式：多个独立建筑组团分散布置。"""
    n_clusters = random.choice([3, 4])
    n_per_cluster = random.randint(3, 5)
    cluster_gap = _r(10.0, 15.0)
    inter_gap = _r(50.0, 80.0)
    road_width = _r(7.0, 10.0)
    road_mat = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    road_mat_name = MATERIAL_NAMES[road_mat]
    b_mat = _weighted_choice(BUILDING_MATERIAL_WEIGHTS)
    b_mat_name = MATERIAL_NAMES[b_mat]

    # 各组团使用不同或相同建筑类型
    all_types = list(BUILDING_TYPE_NAMES.keys())
    cluster_type = random.choice(all_types)
    type_name = BUILDING_TYPE_NAMES[cluster_type]
    dim_desc = _DIM_DESC_FUNCS[cluster_type]()
    height_desc = _rand_height_desc()

    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = (
        f"创建虚拟场景：组团式布局，{n_clusters}个独立建筑组团分散分布在场景各象限，"
        f"每组团{n_per_cluster}栋{type_name}（{dim_desc}，{height_desc}，{b_mat_name}材质），"
        f"组团内建筑紧凑排列（间距{cluster_gap}米），组团间距至少{inter_gap}米，"
        f"同一组团内建筑朝向相近（旋转角相差不超过15度），各栋尺寸各不相同，"
        f"每个组团内设一条短道路（宽{road_width}米，{road_mat_name}材质），"
        f"加{n_clusters - 1}条组团间连接主道路，"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


def _generate_organic_prompt() -> str:
    """有机式：曲线道路，建筑自由不规则排列。"""
    n_buildings = random.randint(10, 15)
    all_types = list(BUILDING_TYPE_NAMES.keys())
    n_type_groups = random.choices([2, 3], weights=[0.5, 0.5])[0]
    selected_types = random.sample(all_types, n_type_groups)

    counts = [1] * n_type_groups
    for _ in range(n_buildings - n_type_groups):
        counts[random.randint(0, n_type_groups - 1)] += 1

    group_descs = [
        _rand_building_group(btype, cnt)
        for btype, cnt in zip(selected_types, counts)
    ]
    building_part = "、".join(group_descs)

    road_width = _r(6.0, 10.0)
    road_mat = _weighted_choice(ROAD_MATERIAL_WEIGHTS)
    road_mat_name = MATERIAL_NAMES[road_mat]
    n_roads = random.choice([2, 3])

    tx_part = _rand_tx_desc()
    rx_part = _rand_rx_desc()
    rt_part = _rand_rt_desc()

    prompt = (
        f"创建虚拟场景：有机自由式布局，{n_buildings}栋建筑不规则散布，包括{building_part}，"
        f"建筑位置无规律、旋转角度完全随机（各不相同），高度和尺寸变化丰富，"
        f"设置{n_roads}条蜿蜒弯曲的曲线道路（smooth曲线，每条至少3个控制点），"
        f"道路宽{road_width}米，{road_mat_name}材质，建筑松散地分布在道路两侧，"
        f"退距各不相同（5到15米随机），"
        f"{tx_part}，{rx_part}，{rt_part}"
    )
    return prompt


# ---------------------------------------------------------------------------
# 完整提示词生成
# ---------------------------------------------------------------------------

# 7种布局风格及其采样权重
_STYLE_GENERATORS = [
    (_generate_orthogonal_grid_prompt, 0.20),
    (_generate_slab_row_prompt,        0.15),
    (_generate_point_scatter_prompt,   0.15),
    (_generate_perimeter_prompt,       0.15),
    (_generate_radial_prompt,          0.10),
    (_generate_cluster_prompt,         0.15),
    (_generate_organic_prompt,         0.10),
]


def generate_random_prompt() -> str:
    """从7种布局风格中随机选取一种，生成对应的完整中文场景提示词。"""
    generators, weights = zip(*_STYLE_GENERATORS)
    chosen = random.choices(generators, weights=weights, k=1)[0]
    return chosen()


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
