"""
to_blender.py — 将场景 JSON 导出为 Blender 可编辑脚本。

用法:
    python to_blender.py <scene_name>
    python to_blender.py text_prompt_json/scene_01.json

输出目录: blender_scenes/{name}/
    {name}_data.json     场景数据（Blender 脚本读取此文件）
    {name}_setup.py      在 Blender 中运行：导入并显示场景
    {name}_extract.py    在 Blender 中运行：导出调整后的建筑位置

完整工作流:
    1. python to_blender.py <name>
    2. blender --python blender_scenes/{name}/{name}_setup.py
       （或在 Blender GUI > Scripting 标签页中运行）
    3. 在 Blender 中手动移动建筑物（G 移动 / R 旋转 / X|Y 锁轴）
    4. 在 Blender 脚本编辑器中运行 {name}_extract.py
    5. python blender_to_json.py <name>
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
blender_scenes/{name}/{name}_setup.py  —  在 Blender 中运行以导入场景 "{name}"

用法（选其一）：
    blender --python blender_scenes/{name}/{name}_setup.py
    或：打开 Blender > Scripting 标签页，粘贴本文件内容并执行

编辑完成后运行：blender_scenes/{name}/{name}_extract.py
"""
import bpy, math, json
from pathlib import Path

# ── 定位脚本目录（兼容命令行和 Blender Scripting 标签页两种方式）──────────
def _get_script_dir():
    # 方式 1：命令行 blender --python xxx.py，__file__ 是完整路径
    try:
        p = Path(__file__).resolve()
        if p.is_file():
            return p.parent
    except NameError:
        pass
    # 方式 2：Blender Scripting 标签页，从当前打开的文本获取路径
    try:
        fp = bpy.context.space_data.text.filepath
        if fp:
            return Path(fp).resolve().parent
    except Exception:
        pass
    raise RuntimeError(
        "无法定位脚本目录。\\n"
        "请在 Blender Scripting 标签页中用 Open 打开此脚本文件后再运行。"
    )

# ── 读取场景数据 ────────────────────────────────────────────────────────────
_data_file = _get_script_dir() / "{name}_data.json"
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
import bmesh as _bmesh_mod
for _i, _b in enumerate(_buildings):
    _btype = _b.get("type", "rectangular")
    _x     = float(_b.get("x", 0))
    _y     = float(_b.get("y", 0))
    _h     = float(_b.get("height", 10))
    _rot   = float(_b.get("rotation_deg", 0))

    if _btype == "trapezoidal":
        _bw = float(_b.get("bottom_width", 12))
        _tw = float(_b.get("top_width", 8))
        _l  = float(_b.get("length", 12))
        _hw_bot, _hw_top, _hl = _bw/2, _tw/2, _l/2
        _verts = [
            (-_hw_bot, -_hl, 0),  ( _hw_bot, -_hl, 0),
            ( _hw_top,  _hl, 0),  (-_hw_top,  _hl, 0),
            (-_hw_bot, -_hl, _h), ( _hw_bot, -_hl, _h),
            ( _hw_top,  _hl, _h), (-_hw_top,  _hl, _h),
        ]
        _faces_t = [(0,1,2,3),(7,6,5,4),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        _bme = _bmesh_mod.new()
        _vl  = [_bme.verts.new(v) for v in _verts]
        _bme.verts.ensure_lookup_table()
        for _f in _faces_t: _bme.faces.new([_vl[i] for i in _f])
        _mesh_t = bpy.data.meshes.new(f"trap_mesh_{{_i}}")
        _bme.to_mesh(_mesh_t); _bme.free()
        _obj = bpy.data.objects.new(f"trap_{{_i}}", _mesh_t)
        bpy.context.collection.objects.link(_obj)
        bpy.context.view_layer.objects.active = _obj
        _obj.select_set(True)
        _obj.data.materials.append(_M["trapezoidal"])
        _obj.location       = (_x, _y, 0)   # 顶点已含 z=0..h，无需偏移
        _obj["ckm_width"]   = _bw
        _obj["ckm_length"]  = _l
    else:
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        _obj = bpy.context.active_object
        if _btype == "rectangular":
            _w = float(_b.get("width",  10))
            _l = float(_b.get("length", 10))
            _obj.dimensions = (_w, _l, _h)
            _obj.data.materials.append(_M["rectangular"])
            _obj["ckm_width"]  = _w
            _obj["ckm_length"] = _l
        else:
            _obj.dimensions = (10, 10, _h)
            _obj.data.materials.append(_M["other"])
            _obj["ckm_width"]  = 10.0
            _obj["ckm_length"] = 10.0
        _obj.location = (_x, _y, _h / 2)

    _obj.rotation_euler   = (0.0, 0.0, math.radians(_rot))
    _obj.name             = f"building_{{_i}}"
    _obj["ckm_height"]    = _h
    _obj.lock_rotation[0] = True
    _obj.lock_rotation[1] = True

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
    _ro["ckm_road_length"] = round(_rl, 2)
    _ro["ckm_road_width"]  = round(_rw, 2)
    _ro["ckm_road_cx"]     = round(_cx, 2)
    _ro["ckm_road_cy"]     = round(_cy, 2)
    _ro.lock_rotation[0]   = True
    _ro.lock_rotation[1]   = True

# ── 俯视正交视角 ─────────────────────────────────────────────────────────────
import mathutils
for _area in bpy.context.screen.areas:
    if _area.type == "VIEW_3D":
        _r3d = _area.spaces.active.region_3d
        _r3d.view_perspective = "ORTHO"
        _r3d.view_rotation = mathutils.Quaternion((1, 0, 0, 0))
        _r3d.view_distance = 250
        break

# ── 建筑物拖拽缩放算子 ──────────────────────────────────────────────────────
import gpu
from gpu_extras.batch import batch_for_shader
import blf
from bpy_extras import view3d_utils

_HANDLE_PX = 8
_MIN_DIM   = 1.0

def _get_local_dims(obj):
    return obj.scale.x * 2, obj.scale.y * 2, obj.scale.z * 2

def _edge_centers_world(obj):
    bx, by, bz = obj.location
    w, l, _ = _get_local_dims(obj)
    rot = obj.rotation_euler.z
    c, s = math.cos(rot), math.sin(rot)
    return {{
        'px': mathutils.Vector((bx + w/2*c,  by + w/2*s,  bz)),
        'nx': mathutils.Vector((bx - w/2*c,  by - w/2*s,  bz)),
        'py': mathutils.Vector((bx - l/2*s,  by + l/2*c,  bz)),
        'ny': mathutils.Vector((bx + l/2*s,  by - l/2*c,  bz)),
    }}

class CKM_OT_resize_building(bpy.types.Operator):
    bl_idname  = "object.ckm_resize_building"
    bl_label   = "拖拽调整建筑/道路尺寸"
    bl_options = {{'REGISTER', 'UNDO'}}
    _handle = None; _obj = None; _drag = None
    _start_mxy = None; _start_w = 0.0; _start_l = 0.0
    _start_loc = None; _orig_scale = None; _orig_loc = None

    def _w2s(self, ctx, pos):
        return view3d_utils.location_3d_to_region_2d(ctx.region, ctx.region_data, pos)

    def _s2w(self, ctx, mxy):
        return view3d_utils.region_2d_to_location_3d(
            ctx.region, ctx.region_data, mxy, self._obj.location)

    def _find_edge(self, ctx, mx, my):
        best, best_d = None, _HANDLE_PX * 2.5
        for eid, wpos in _edge_centers_world(self._obj).items():
            sp = self._w2s(ctx, wpos)
            if sp is None: continue
            d = ((mx - sp.x)**2 + (my - sp.y)**2) ** 0.5
            if d < best_d: best, best_d = eid, d
        return best

    def _draw_cb(self, ctx):
        if self._obj is None: return
        edges  = _edge_centers_world(self._obj)
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        gpu.state.blend_set('ALPHA')
        s = _HANDLE_PX
        for eid, wpos in edges.items():
            sp = self._w2s(ctx, wpos)
            if sp is None: continue
            sx, sy = sp.x, sp.y
            col = (1.0, 0.2, 0.2, 1.0) if eid == self._drag else (1.0, 0.9, 0.0, 1.0)
            batch = batch_for_shader(shader, 'TRI_FAN',
                {{"pos": [(sx-s,sy-s),(sx+s,sy-s),(sx+s,sy+s),(sx-s,sy+s)]}})
            shader.uniform_float("color", col)
            batch.draw(shader)
        gpu.state.blend_set('NONE')
        w, l, h = _get_local_dims(self._obj)
        blf.position(0, 15, 15, 0)
        blf.size(0, 16)
        blf.color(0, 1.0, 1.0, 1.0, 1.0)
        if self._obj.name.startswith("road_"):
            blf.draw(0, f"路长={{w:.1f}}m  路宽={{l:.1f}}m    拖拽黄点调整长宽 | D 精确输入 | ESC 取消")
        else:
            blf.draw(0, f"W={{w:.1f}}m  L={{l:.1f}}m  H={{h:.1f}}m    拖拽黄点调整长宽 | D 精确输入 | ESC 取消")

    def invoke(self, context, event):
        obj = context.active_object
        if obj is None or not (obj.name.startswith("building_") or obj.name.startswith("road_")):
            return {{'CANCELLED'}}
        self._obj        = obj
        self._orig_scale = obj.scale.copy()
        self._orig_loc   = obj.location.copy()
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_cb, (context,), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {{'RUNNING_MODAL'}}

    def modal(self, context, event):
        context.area.tag_redraw()
        mx, my = event.mouse_region_x, event.mouse_region_y
        if event.type == 'MOUSEMOVE':
            if self._drag: self._do_drag(context, mx, my)
            return {{'RUNNING_MODAL'}}
        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                eid = self._find_edge(context, mx, my)
                if eid:
                    self._drag = eid
                    self._start_mxy = (mx, my)
                    w, l, _ = _get_local_dims(self._obj)
                    self._start_w = w; self._start_l = l
                    self._start_loc = self._obj.location.copy()
                else:
                    self._finish(context); return {{'FINISHED'}}
            elif event.value == 'RELEASE':
                self._drag = None
            return {{'RUNNING_MODAL'}}
        if event.type == 'D' and event.value == 'PRESS':
            self._finish(context)
            if self._obj.name.startswith("road_"):
                bpy.ops.object.ckm_edit_road_dims('INVOKE_DEFAULT')
            else:
                bpy.ops.object.ckm_edit_dims('INVOKE_DEFAULT')
            return {{'FINISHED'}}
        if event.type in {{'RIGHTMOUSE', 'ESC'}}:
            self._obj.scale    = self._orig_scale
            self._obj.location = self._orig_loc
            self._finish(context); return {{'CANCELLED'}}
        return {{'PASS_THROUGH'}}

    def _do_drag(self, context, mx, my):
        obj = self._obj
        is_road = obj.name.startswith("road_")
        rot = obj.rotation_euler.z
        c, s = math.cos(rot), math.sin(rot)
        p0 = self._s2w(context, self._start_mxy)
        p1 = self._s2w(context, (mx, my))
        if p0 is None or p1 is None: return
        d = p1 - p0
        if self._drag in ('px', 'nx'):
            proj  = d.x * c + d.y * s
            sign  = 1 if self._drag == 'px' else -1
            new_w = max(_MIN_DIM, self._start_w + sign * proj)
            dw    = new_w - self._start_w
            obj.scale.x = new_w / 2
            obj.location.x = self._start_loc.x + (dw/2) * sign * c
            obj.location.y = self._start_loc.y + (dw/2) * sign * s
            if is_road:
                obj["ckm_road_length"] = new_w
            else:
                obj["ckm_width"] = new_w
        else:
            proj  = d.x * (-s) + d.y * c
            sign  = 1 if self._drag == 'py' else -1
            new_l = max(_MIN_DIM, self._start_l + sign * proj)
            dl    = new_l - self._start_l
            obj.scale.y = new_l / 2
            obj.location.x = self._start_loc.x + (dl/2) * sign * (-s)
            obj.location.y = self._start_loc.y + (dl/2) * sign * c
            if is_road:
                obj["ckm_road_width"] = new_l
            else:
                obj["ckm_length"] = new_l

    def _finish(self, context):
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self._handle = None
        context.area.tag_redraw()

class OBJECT_OT_ckm_edit_dims(bpy.types.Operator):
    bl_idname = "object.ckm_edit_dims"
    bl_label  = "编辑建筑尺寸（精确输入）"
    width:  bpy.props.FloatProperty(name="宽度 (m)", min=0.5, max=500.0)
    length: bpy.props.FloatProperty(name="长度 (m)", min=0.5, max=500.0)
    height: bpy.props.FloatProperty(name="高度 (m)", min=0.5, max=500.0)

    def invoke(self, context, event):
        obj = context.active_object
        if obj is None or not obj.name.startswith("building_"):
            return {{'CANCELLED'}}
        w, l, h = _get_local_dims(obj)
        self.width, self.length, self.height = w, l, h
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            return {{'CANCELLED'}}
        rot = obj.rotation_euler.copy()
        obj.rotation_euler = (0, 0, 0)
        obj.dimensions = (self.width, self.length, self.height)
        obj.rotation_euler = rot
        obj.location.z = self.height / 2
        obj["ckm_width"]  = self.width
        obj["ckm_length"] = self.length
        obj["ckm_height"] = self.height
        return {{'FINISHED'}}

class OBJECT_OT_ckm_edit_road_dims(bpy.types.Operator):
    bl_idname = "object.ckm_edit_road_dims"
    bl_label  = "编辑道路尺寸（精确输入）"
    length: bpy.props.FloatProperty(name="路长 (m)", min=0.5, max=2000.0)
    width:  bpy.props.FloatProperty(name="路宽 (m)", min=0.5, max=100.0)

    def invoke(self, context, event):
        obj = context.active_object
        if obj is None or not obj.name.startswith("road_"):
            return {{'CANCELLED'}}
        _l, _w, _ = _get_local_dims(obj)
        self.length = float(obj["ckm_road_length"]) if "ckm_road_length" in obj else _l
        self.width  = float(obj["ckm_road_width"])  if "ckm_road_width"  in obj else _w
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            return {{'CANCELLED'}}
        obj.dimensions = (self.length, self.width, 0.2)
        obj["ckm_road_length"] = self.length
        obj["ckm_road_width"]  = self.width
        return {{'FINISHED'}}

for _cls in (CKM_OT_resize_building, OBJECT_OT_ckm_edit_dims, OBJECT_OT_ckm_edit_road_dims):
    if hasattr(bpy.types, _cls.__name__):
        bpy.utils.unregister_class(getattr(bpy.types, _cls.__name__))
    bpy.utils.register_class(_cls)
_kc = bpy.context.window_manager.keyconfigs.addon
if _kc:
    _km  = _kc.keymaps.new(name="Object Mode", space_type="EMPTY")
    _kmi = _km.keymap_items.new("object.ckm_resize_building", "LEFTMOUSE", "DOUBLE_CLICK")

# ── 强制建筑/道路保持竖立（清零 X/Y 旋转，防止任何视角下操作导致倾斜）───────
_ckm_enforcing = False
def _ckm_enforce_upright(scene, depsgraph):
    global _ckm_enforcing
    if _ckm_enforcing: return
    _ckm_enforcing = True
    try:
        for _upd in depsgraph.updates:
            if not isinstance(_upd.id, bpy.types.Object): continue
            _o = _upd.id
            if not (_o.name.startswith("building_") or _o.name.startswith("road_")): continue
            if abs(_o.rotation_euler.x) > 1e-6 or abs(_o.rotation_euler.y) > 1e-6:
                _o.rotation_euler.x = 0.0
                _o.rotation_euler.y = 0.0
    finally:
        _ckm_enforcing = False

for _h in list(bpy.app.handlers.depsgraph_update_post):
    if getattr(_h, '__name__', '') == '_ckm_enforce_upright':
        bpy.app.handlers.depsgraph_update_post.remove(_h)
bpy.app.handlers.depsgraph_update_post.append(_ckm_enforce_upright)

print(f"[setup] 场景 '{name}' 已加载：{{len(_buildings)}} 栋建筑，{{len(_roads)}} 条道路。")
print(f"[setup] 操作完成后，在脚本编辑器中运行 blender_scenes/{name}/{name}_extract.py")
'''


# ---------------------------------------------------------------------------
# 生成 Blender 导出脚本（_extract.py）
# ---------------------------------------------------------------------------

def _extract_script(name: str) -> str:
    return f'''\
"""
blender_scenes/{name}/{name}_extract.py  —  在 Blender 脚本编辑器中运行

将场景中所有 building_N 对象的位置、旋转和高度导出为 JSON。
输出：blender_scenes/{name}/{name}_positions.json
之后运行：python blender_to_json.py {name}
"""
import bpy, math, json
from pathlib import Path

# ── 定位脚本目录（兼容命令行和 Blender Scripting 标签页两种方式）──────────
def _get_script_dir():
    try:
        p = Path(__file__).resolve()
        if p.is_file():
            return p.parent
    except NameError:
        pass
    try:
        fp = bpy.context.space_data.text.filepath
        if fp:
            return Path(fp).resolve().parent
    except Exception:
        pass
    raise RuntimeError(
        "无法定位脚本目录。\\n"
        "请在 Blender Scripting 标签页中用 Open 打开此脚本文件后再运行。"
    )

_buildings_out = {{}}
for _obj in bpy.data.objects:
    if not _obj.name.startswith("building_"):
        continue
    try:
        _idx = int(_obj.name.split("_")[1])
    except (IndexError, ValueError):
        continue
    _t   = _obj.matrix_world.translation
    _r   = _obj.matrix_world.to_euler()[2]
    _h_m = round(float(_obj.dimensions.z), 2)
    _w_m = round(float(_obj["ckm_width"])  if "ckm_width"  in _obj else _obj.dimensions.x, 2)
    _l_m = round(float(_obj["ckm_length"]) if "ckm_length" in _obj else _obj.dimensions.y, 2)
    _buildings_out[str(_idx)] = {{
        "x":            round(float(_t.x), 2),
        "y":            round(float(_t.y), 2),
        "rotation_deg": round(math.degrees(float(_r)) % 360, 2),
        "height_m":     _h_m,
        "width_m":      _w_m,
        "length_m":     _l_m,
    }}

_roads_out = {{}}
for _obj in bpy.data.objects:
    if not _obj.name.startswith("road_"):
        continue
    try:
        _idx = int(_obj.name.split("_")[1])
    except (IndexError, ValueError):
        continue
    _t  = _obj.matrix_world.translation
    _r  = _obj.matrix_world.to_euler()[2]
    _rl = round(float(_obj["ckm_road_length"]) if "ckm_road_length" in _obj else _obj.dimensions.x, 2)
    _rw = round(float(_obj["ckm_road_width"])  if "ckm_road_width"  in _obj else _obj.dimensions.y, 2)
    _roads_out[str(_idx)] = {{
        "cx":           round(float(_t.x), 2),
        "cy":           round(float(_t.y), 2),
        "rotation_deg": round(math.degrees(float(_r)) % 360, 2),
        "length_m":     _rl,
        "width_m":      _rw,
    }}

_out = {{"buildings": _buildings_out, "roads": _roads_out}}
_path = _get_script_dir() / "{name}_positions.json"
_path.parent.mkdir(parents=True, exist_ok=True)
_path.write_text(json.dumps(_out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"[extract] {{len(_buildings_out)}} 栋建筑、{{len(_roads_out)}} 条道路已导出到 {{_path}}")
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

    # 每个场景存入独立子目录 blender_scenes/{name}/
    scene_dir = BLENDER_SCENES_DIR / name
    scene_dir.mkdir(parents=True, exist_ok=True)

    # 保存场景数据 JSON（供 Blender 脚本读取）
    data_path = scene_dir / f"{name}_data.json"
    data_path.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")

    setup_path = scene_dir / f"{name}_setup.py"
    setup_path.write_text(_setup_script(name), encoding="utf-8")

    extract_path = scene_dir / f"{name}_extract.py"
    extract_path.write_text(_extract_script(name), encoding="utf-8")

    n_b = len(scene.get("buildings", []))
    n_r = len(scene.get("roads", []))
    print(f"[to_blender] 场景 '{name}'：{n_b} 栋建筑 / {n_r} 条道路")
    print(f"  场景数据：{data_path}")
    print(f"  导入脚本：{setup_path}")
    print(f"  导出脚本：{extract_path}")
    print()
    print("── 操作步骤 ──────────────────────────────────────────────────────────")
    print(f"1. 在 Blender 中运行导入脚本（推荐：GUI 方式）：")
    print(f"     a) 打开 Blender")
    print(f"     b) 顶部切换到 Scripting 标签页")
    print(f"     c) 点击 Open → 选择 {setup_path}")
    print(f"     d) 点击右上角 ▶ Run Script")
    print(f"")
    print(f"   命令行方式（需要知道 blender.exe 完整路径）：")
    print(f"     Windows: & \"C:\\Program Files\\Blender Foundation\\Blender X.X\\blender.exe\" --python {setup_path}")
    print(f"     Linux/Mac: blender --python {setup_path}")
    print(f"")
    print(f"2. 在 Blender 中手动调整建筑物：")
    print(f"   - G 移动，R 旋转，X/Y 锁轴（调整平面位置）")
    print(f"   - 修改高度：选中建筑 → N 键打开 Item 面板 → 修改 Dimensions Z")
    print(f"     或：选中建筑 S → Z → 输入数值 → Enter")
    print(f"   注：标注文字显示初始高度，修改后以 Dimensions Z 为准")
    print(f"3. 同样在 Blender Scripting 标签页中：Open → {extract_path} → ▶ Run Script")
    print(f"4. python blender_to_json.py {name}")
    print(f"   （位置、旋转、高度均自动写回 JSON，并重新生成 3D 场景和俯视图）")
    print("──────────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
