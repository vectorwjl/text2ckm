"""
to_blender.py — 将场景 JSON 导出为 Blender 可编辑脚本。

用法:
    python to_blender.py <scene_name>
    python to_blender.py text_prompt_json/scene_01.json

输出目录: blender_scenes/
    {name}_data.json     场景数据（Blender 脚本读取此文件）
    {name}_setup.py      在 Blender 中运行：导入并显示场景
    {name}_extract.py    在 Blender 中运行：导出调整后的建筑位置

完整工作流:
    1. python to_blender.py <name>
    2. blender --python blender_scenes/{name}_setup.py
       （或在 Blender GUI > Scripting 标签页中运行）
    3. 在 Blender 中手动移动建筑物（G 移动 / R 旋转 / X|Y 锁轴）
    4. 在 Blender 脚本编辑器中运行 {name}_extract.py
    5. python blender_to_json.py <name> [--render]
"""

import json
import sys
from pathlib import Path

BLENDER_SCENES_DIR = Path("blender_scenes")


# ---------------------------------------------------------------------------
# 场景加载
# ---------------------------------------------------------------------------

def _load_scene(name_or_path: str) -> tuple[str, dict, dict]:
    """返回 (name, scene_dict, full_data_dict)。"""
    p = Path(name_or_path)
    if p.suffix == ".json" and p.exists():
        full = json.loads(p.read_text(encoding="utf-8"))
        name = p.stem
    else:
        name = name_or_path
        for candidate in [
            Path("simple_scene") / name / "scene_description.json",
            Path("text_prompt_json") / f"{name}.json",
        ]:
            if candidate.exists():
                full = json.loads(candidate.read_text(encoding="utf-8"))
                break
        else:
            raise FileNotFoundError(
                f"找不到场景 '{name}' 的 JSON 文件。\n"
                f"请确认 simple_scene/{name}/scene_description.json 或 "
                f"text_prompt_json/{name}.json 存在。"
            )
    scene = full.get("scene", full)
    return name, scene, full


# ---------------------------------------------------------------------------
# 生成 Blender 导入脚本（_setup.py）
# ---------------------------------------------------------------------------

def _setup_script(name: str) -> str:
    return f'''\
"""
blender_scenes/{name}_setup.py  —  在 Blender 中运行以导入场景 "{name}"

用法（选其一）：
    blender --python blender_scenes/{name}_setup.py
    或：打开 Blender > Scripting 标签页，粘贴本文件内容并执行

编辑完成后运行：blender_scenes/{name}_extract.py
"""
import bpy, math, json
from pathlib import Path

# ── 读取场景数据 ────────────────────────────────────────────────────────────
_data_file = Path(r"blender_scenes/{name}_data.json")
if not _data_file.exists():
    raise FileNotFoundError(f"找不到 {{_data_file}}，请先运行 to_blender.py")
_sc        = json.loads(_data_file.read_text(encoding="utf-8"))
_buildings = _sc.get("buildings", [])
_roads     = _sc.get("roads", [])

# ── 清空场景 ────────────────────────────────────────────────────────────────
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for _col in list(bpy.data.collections):
    bpy.data.collections.remove(_col)

# ── 材质 ────────────────────────────────────────────────────────────────────
def _mat(n, r, g, b, a=1.0):
    m = bpy.data.materials.new(n)
    m.use_nodes = False
    m.diffuse_color = (r, g, b, a)
    return m

_M = {{
    "rectangular": _mat("rect_blue",    0.20, 0.45, 0.90),
    "trapezoidal": _mat("trap_orange",  0.90, 0.50, 0.10),
    "other":       _mat("other_purple", 0.70, 0.20, 0.80),
    "road":        _mat("road_grey",    0.40, 0.40, 0.40),
    "ground":      _mat("ground_green", 0.25, 0.60, 0.25, 0.5),
}}

# ── 地面 ────────────────────────────────────────────────────────────────────
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.01))
_g = bpy.context.active_object
_g.name = "ground"
_g.data.materials.append(_M["ground"])

# ── 建筑物 ──────────────────────────────────────────────────────────────────
# 每栋建筑以立方体近似（梯形也用最大宽度），不 apply transform，
# 保留 location / rotation_euler 供 extract 脚本读回。
for _i, _b in enumerate(_buildings):
    _btype = _b.get("type", "rectangular")
    _x     = float(_b.get("x", 0))
    _y     = float(_b.get("y", 0))
    _h     = float(_b.get("height", 10))
    _rot   = float(_b.get("rotation_deg", 0))

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    _obj = bpy.context.active_object

    if _btype == "rectangular":
        _w = float(_b.get("width",  10))
        _l = float(_b.get("length", 10))
        _obj.dimensions = (_w, _l, _h)
        _obj.data.materials.append(_M["rectangular"])
    elif _btype == "trapezoidal":
        _bw = float(_b.get("bottom_width", 12))
        _l  = float(_b.get("length",       12))
        _obj.dimensions = (_bw, _l, _h)
        _obj.data.materials.append(_M["trapezoidal"])
    else:
        _obj.dimensions = (10, 10, _h)
        _obj.data.materials.append(_M["other"])

    # 位置和旋转作为对象属性保留，不 apply
    _obj.location       = (_x, _y, _h / 2)
    _obj.rotation_euler = (0.0, 0.0, math.radians(_rot))
    _obj.name           = f"building_{{_i}}"

# ── 道路（仅可视化参考，不导出坐标）────────────────────────────────────────
for _i, _r in enumerate(_roads):
    if _r.get("type", "straight") != "straight":
        continue
    _s = _r.get("start", [0, 0])
    _e = _r.get("end",   [0, 0])
    _rw  = float(_r.get("width", 7))
    _cx, _cy = (_s[0]+_e[0])/2, (_s[1]+_e[1])/2
    _dx, _dy = _e[0]-_s[0], _e[1]-_s[1]
    _rl = (_dx**2+_dy**2)**0.5 or 1.0
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    _ro = bpy.context.active_object
    _ro.dimensions     = (_rl, _rw, 0.2)
    _ro.location       = (_cx, _cy, 0.1)
    _ro.rotation_euler = (0, 0, __import__("math").atan2(_dy, _dx))
    _ro.name           = f"road_{{_i}}"
    _ro.data.materials.append(_M["road"])

# ── 俯视正交视角 ─────────────────────────────────────────────────────────────
import mathutils
for _area in bpy.context.screen.areas:
    if _area.type == "VIEW_3D":
        _r3d = _area.spaces.active.region_3d
        _r3d.view_perspective = "ORTHO"
        _r3d.view_rotation = mathutils.Quaternion((1, 0, 0, 0))
        _r3d.view_distance = 250
        break

print(f"[setup] 场景 '{name}' 已加载：{{len(_buildings)}} 栋建筑，{{len(_roads)}} 条道路。")
print(f"[setup] 操作完成后，在脚本编辑器中运行 blender_scenes/{name}_extract.py")
'''


# ---------------------------------------------------------------------------
# 生成 Blender 导出脚本（_extract.py）
# ---------------------------------------------------------------------------

def _extract_script(name: str) -> str:
    return f'''\
"""
blender_scenes/{name}_extract.py  —  在 Blender 脚本编辑器中运行

将场景中所有 building_N 对象的位置和旋转导出为 JSON。
输出：blender_scenes/{name}_positions.json
之后运行：python blender_to_json.py {name}
"""
import bpy, math, json
from pathlib import Path

_out = {{}}
for _obj in bpy.data.objects:
    if not _obj.name.startswith("building_"):
        continue
    try:
        _idx = int(_obj.name.split("_")[1])
    except (IndexError, ValueError):
        continue
    # matrix_world 包含父对象变换（若有），更准确
    _t = _obj.matrix_world.translation
    _r = _obj.matrix_world.to_euler()[2]           # Z 轴旋转（弧度）
    _out[str(_idx)] = {{
        "x":            round(float(_t.x), 2),
        "y":            round(float(_t.y), 2),
        "rotation_deg": round(math.degrees(float(_r)) % 360, 2),
    }}

_path = Path(r"blender_scenes/{name}_positions.json")
_path.parent.mkdir(parents=True, exist_ok=True)
_path.write_text(json.dumps(_out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"[extract] {{len(_out)}} 栋建筑已导出到 {{_path}}")
print("[extract] 下一步：python blender_to_json.py {name}")
'''


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    name, scene, _ = _load_scene(sys.argv[1])
    BLENDER_SCENES_DIR.mkdir(exist_ok=True)

    # 保存场景数据 JSON（供 Blender 脚本读取）
    data_path = BLENDER_SCENES_DIR / f"{name}_data.json"
    data_path.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")

    setup_path = BLENDER_SCENES_DIR / f"{name}_setup.py"
    setup_path.write_text(_setup_script(name), encoding="utf-8")

    extract_path = BLENDER_SCENES_DIR / f"{name}_extract.py"
    extract_path.write_text(_extract_script(name), encoding="utf-8")

    n_b = len(scene.get("buildings", []))
    n_r = len(scene.get("roads", []))
    print(f"[to_blender] 场景 '{name}'：{n_b} 栋建筑 / {n_r} 条道路")
    print(f"  场景数据：{data_path}")
    print(f"  导入脚本：{setup_path}")
    print(f"  导出脚本：{extract_path}")
    print()
    print("── 操作步骤 ──────────────────────────────────────────────────────────")
    print(f"1. 运行导入脚本（选其一）：")
    print(f"     blender --python {setup_path}")
    print(f"     或在 Blender > Scripting 中粘贴 {setup_path} 内容运行")
    print(f"2. 在 Blender 中手动移动/旋转建筑物（G 移动，R 旋转，X/Y 锁轴）")
    print(f"3. 在 Blender 脚本编辑器中运行：{extract_path}")
    print(f"4. python blender_to_json.py {name}")
    print(f"   （加 --render 参数可自动重新生成俯视图）")
    print("──────────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
