"""
blender_script.py — Runs inside Blender (headless) to generate scene meshes.

Usage (called by blender_generator.py):
    blender --background --python blender_script.py -- <params_json> <mesh_dir>

Reads scene_data JSON, creates meshes with bpy, exports PLY files,
writes _output.json manifest.
"""

import sys
import json
import math
from pathlib import Path

import bpy
import bmesh


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _parse_args():
    argv = sys.argv
    if "--" not in argv:
        raise SystemExit("Usage: blender --background --python blender_script.py -- <params_json> <mesh_dir>")
    args = argv[argv.index("--") + 1:]
    if len(args) < 2:
        raise SystemExit("Expected 2 arguments after --: <params_json> <mesh_dir>")
    return Path(args[0]), Path(args[1])


# ---------------------------------------------------------------------------
# Scene helpers
# ---------------------------------------------------------------------------

def _clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)


def _active_obj():
    return bpy.context.active_object


def _select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _triangulate(obj):
    """Triangulate mesh in-place using bmesh (no modifier context needed)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def _export_ply(obj, filepath: str):
    """Export a single object as ASCII PLY."""
    _select_only(obj)
    bpy.ops.wm.ply_export(
        filepath=filepath,
        ascii_format=True,
        export_normals=False,
        export_uv=False,
        export_colors='NONE',
        export_selected_objects=True,
        apply_modifiers=True,
    )


# ---------------------------------------------------------------------------
# Building generators
# ---------------------------------------------------------------------------

def _make_rectangular(x, y, width, length, height):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.transform(__import__('mathutils').Matrix.Scale(width, 4, (1, 0, 0)))
    bm.transform(__import__('mathutils').Matrix.Scale(length, 4, (0, 1, 0)))
    bm.transform(__import__('mathutils').Matrix.Scale(height, 4, (0, 0, 1)))
    # Center bottom at z=0
    bmesh.ops.translate(bm, verts=bm.verts, vec=(x, y, height / 2))
    mesh = bpy.data.meshes.new("rect")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("rect", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def _make_box_obj(cx, cy, w, l, h, name="box"):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    import mathutils
    bm.transform(mathutils.Matrix.Scale(w, 4, (1, 0, 0)))
    bm.transform(mathutils.Matrix.Scale(l, 4, (0, 1, 0)))
    bm.transform(mathutils.Matrix.Scale(h, 4, (0, 0, 1)))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, cy, h / 2))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def _join_objects(objs, name="joined"):
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    result = bpy.context.active_object
    result.name = name
    return result


def _make_l_shaped(x, y, w1, l1, w2, l2, height):
    bpy.ops.object.select_all(action='DESELECT')
    b1 = _make_box_obj(x, y, w1, l1, height, "l_main")
    b2 = _make_box_obj(x + w1 / 2 + w2 / 2, y - l1 / 2 + l2 / 2, w2, l2, height, "l_wing")
    return _join_objects([b1, b2], "l_shaped")


def _make_t_shaped(x, y, main_w, main_l, wing_w, wing_l, height):
    bpy.ops.object.select_all(action='DESELECT')
    main = _make_box_obj(x, y, main_w, main_l, height, "t_main")
    left = _make_box_obj(x - main_w / 2 - wing_w / 2, y + main_l / 2 - wing_l / 2, wing_w, wing_l, height, "t_left")
    right = _make_box_obj(x + main_w / 2 + wing_w / 2, y + main_l / 2 - wing_l / 2, wing_w, wing_l, height, "t_right")
    return _join_objects([main, left, right], "t_shaped")


def _apply_boolean(base, cutter, operation='DIFFERENCE'):
    mod = base.modifiers.new(name="Bool", type='BOOLEAN')
    mod.operation = operation
    mod.object = cutter
    mod.solver = 'EXACT'
    _select_only(base)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return base


def _make_u_shaped(x, y, outer_w, outer_l, inner_w, inner_l, height):
    outer = _make_box_obj(x, y, outer_w, outer_l, height * 1.1, "u_outer")
    inner = _make_box_obj(x, y + (outer_l - inner_l) / 2, inner_w, inner_l, height * 1.2, "u_inner")
    return _apply_boolean(outer, inner)


def _make_trapezoidal(x, y, bottom_width, top_width, length, height):
    hw_bot = bottom_width / 2
    hw_top = top_width / 2
    hl = length / 2
    verts = [
        (x - hw_bot, y - hl, 0),
        (x + hw_bot, y - hl, 0),
        (x + hw_top, y + hl, 0),
        (x - hw_top, y + hl, 0),
        (x - hw_bot, y - hl, height),
        (x + hw_bot, y - hl, height),
        (x + hw_top, y + hl, height),
        (x - hw_top, y + hl, height),
    ]
    faces = [
        (0, 1, 2, 3), (7, 6, 5, 4),
        (0, 1, 5, 4), (1, 2, 6, 5),
        (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    bm = bmesh.new()
    vl = [bm.verts.new(v) for v in verts]
    bm.verts.ensure_lookup_table()
    for f in faces:
        bm.faces.new([vl[i] for i in f])
    mesh = bpy.data.meshes.new("trapezoid")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("trapezoid", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# Road generators
# ---------------------------------------------------------------------------

def _make_straight_road(start, end, width, height=0.25):
    import mathutils
    sx, sy = float(start[0]), float(start[1])
    ex, ey = float(end[0]), float(end[1])
    dx, dy = ex - sx, ey - sy
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-6:
        return None
    cx, cy = (sx + ex) / 2, (sy + ey) / 2
    angle = math.atan2(dy, dx)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.transform(mathutils.Matrix.Scale(length, 4, (1, 0, 0)))
    bm.transform(mathutils.Matrix.Scale(width, 4, (0, 1, 0)))
    bm.transform(mathutils.Matrix.Scale(height, 4, (0, 0, 1)))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, height / 2))
    mesh = bpy.data.meshes.new("road_straight")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("road_straight", mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (cx, cy, 0)
    obj.rotation_euler = (0, 0, angle)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def _make_curved_road(points, width, height=0.25, smooth=True):
    """Build a curved road by sweeping a rectangle profile along a polyline."""
    if len(points) < 2:
        return None

    pts = [(float(p[0]), float(p[1])) for p in points]

    # Create a curve object
    curve_data = bpy.data.curves.new("road_curve", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.0

    spline = curve_data.splines.new('NURBS' if smooth else 'POLY')
    spline.points.add(len(pts) - 1)
    for i, (px, py) in enumerate(pts):
        spline.points[i].co = (px, py, 0.0, 1.0)
    if smooth:
        spline.use_endpoint_u = True
        spline.order_u = min(4, len(pts))

    # Profile: rectangle cross-section
    profile_data = bpy.data.curves.new("road_profile", type='CURVE')
    profile_data.dimensions = '2D'
    prof_spline = profile_data.splines.new('POLY')
    prof_spline.points.add(3)
    hw = width / 2
    coords = [(-hw, -height / 2), (hw, -height / 2), (hw, height / 2), (-hw, height / 2)]
    for i, (px, py) in enumerate(coords):
        prof_spline.points[i].co = (px, py, 0.0, 1.0)
    prof_spline.use_cyclic_u = True

    curve_data.bevel_mode = 'OBJECT'
    curve_data.bevel_object = bpy.data.objects.new("road_profile_obj", profile_data)
    bpy.context.collection.objects.link(curve_data.bevel_object)

    curve_obj = bpy.data.objects.new("road_curved", curve_data)
    bpy.context.collection.objects.link(curve_obj)

    # Convert to mesh
    _select_only(curve_obj)
    bpy.ops.object.convert(target='MESH')
    road_obj = bpy.context.active_object

    # Clean up profile helper
    if "road_profile_obj" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["road_profile_obj"], do_unlink=True)

    return road_obj


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    params_path, mesh_dir = _parse_args()

    scene_data = json.loads(params_path.read_text(encoding="utf-8"))
    buildings = scene_data.get("buildings", [])
    roads = scene_data.get("roads", [])
    enabled_types = scene_data.get("_enabled_building_types", ["rectangular", "trapezoidal"])

    _clear_scene()

    output = []

    # --- Buildings ---
    for i, b in enumerate(buildings):
        _clear_scene()
        btype = b.get("type", "rectangular")
        if btype not in enabled_types:
            print(f"[blender_script] Skipping building_{i} (type '{btype}' not enabled).")
            continue
        x = float(b.get("x", 0))
        y = float(b.get("y", 0))
        height = float(b.get("height", 10))
        material = b.get("material", "concrete")
        rotation_deg = float(b.get("rotation_deg", 0.0))

        try:
            if btype == "rectangular":
                w = float(b.get("width", 10))
                l = float(b.get("length", b.get("width", 10)))
                obj = _make_rectangular(x, y, w, l, height)
            elif btype == "trapezoidal":
                obj = _make_trapezoidal(x, y,
                    float(b.get("bottom_width", 12)),
                    float(b.get("top_width", 8)),
                    float(b.get("length", 10)),
                    height)
            elif btype == "l_shaped":
                obj = _make_l_shaped(x, y,
                    float(b.get("width1", 10)), float(b.get("length1", 10)),
                    float(b.get("width2", 5)),  float(b.get("length2", 5)),
                    height)
            elif btype == "t_shaped":
                obj = _make_t_shaped(x, y,
                    float(b.get("main_width", 20)), float(b.get("main_length", 30)),
                    float(b.get("wing_width", 15)), float(b.get("wing_length", 10)),
                    height)
            elif btype == "u_shaped":
                obj = _make_u_shaped(x, y,
                    float(b.get("outer_width", 40)), float(b.get("outer_length", 30)),
                    float(b.get("inner_width", 20)), float(b.get("inner_length", 20)),
                    height)
            else:
                print(f"[blender_script] Unknown building type '{btype}', skipping.")
                continue

            if abs(rotation_deg) > 0.01:
                obj.rotation_euler[2] = math.radians(rotation_deg)
                _select_only(obj)
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            _triangulate(obj)
            ply_path = str(mesh_dir / f"building_{i}.ply")
            _export_ply(obj, ply_path)
            output.append({"path": ply_path, "material": material})
            print(f"[blender_script] building_{i}.ply ({btype}) OK")

        except Exception as e:
            print(f"[blender_script] ERROR building_{i} ({btype}): {e}")

    # --- Roads ---
    for i, r in enumerate(roads):
        _clear_scene()
        rtype = r.get("type", "straight")
        width = float(r.get("width", 7))
        material = r.get("material", "marble")

        try:
            if rtype == "straight":
                obj = _make_straight_road(r.get("start", [-50, 0]), r.get("end", [50, 0]), width)
            else:
                pts = r.get("points", [])
                if len(pts) < 2:
                    pts = [r.get("start", [-50, 0]), r.get("end", [50, 0])]
                obj = _make_curved_road(pts, width, smooth=r.get("smooth", True))

            if obj is None:
                print(f"[blender_script] road_{i} skipped (degenerate geometry).")
                continue

            _triangulate(obj)
            ply_path = str(mesh_dir / f"road_{i}.ply")
            _export_ply(obj, ply_path)
            output.append({"path": ply_path, "material": material})
            print(f"[blender_script] road_{i}.ply ({rtype}) OK")

        except Exception as e:
            print(f"[blender_script] ERROR road_{i} ({rtype}): {e}")

    # Write output manifest
    out_path = mesh_dir / "_output.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[blender_script] Done. {len(output)} mesh(es) written to {mesh_dir}")


main()
