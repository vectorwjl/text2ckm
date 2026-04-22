"""
blender_script.py — Runs inside Blender (headless) to generate scene meshes.

Usage (called by blender_generator.py):
    blender --background --python blender_script.py -- <params_json> <mesh_dir>

Reads scene_data JSON (vertex-based format), creates meshes by polygon extrusion,
exports PLY files, writes _output.json manifest.

Building format: {"vertices": [[x1,y1],...], "height": h, "material": "concrete"}
Road format:     {"vertices": [[x1,y1],...], "height": 0.25, "material": "marble"}
"""

import sys
import json
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


def _select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _triangulate(obj):
    """Triangulate mesh in-place using bmesh."""
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
# Polygon extrusion (shared by buildings and roads)
# ---------------------------------------------------------------------------

def _make_polygon_extrusion(vertices: list, height: float, name: str = "poly"):
    """
    Extrude a 2D polygon footprint (world-space vertices) to given height.

    vertices: list of [x, y] world-space coordinates
    height:   extrusion height in metres
    """
    bm = bmesh.new()
    bm_verts = [bm.verts.new((float(v[0]), float(v[1]), 0.0)) for v in vertices]
    bm.faces.new(bm_verts)
    ret = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    top_verts = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top_verts, vec=(0.0, 0.0, float(height)))
    bm.normal_update()
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    params_path, mesh_dir = _parse_args()

    scene_data = json.loads(params_path.read_text(encoding="utf-8"))
    buildings = scene_data.get("buildings", [])
    roads = scene_data.get("roads", [])

    _clear_scene()

    output = []

    # --- Buildings ---
    for i, b in enumerate(buildings):
        _clear_scene()
        verts = b.get("vertices", [])
        height = float(b.get("height", 10))
        material = b.get("material", "concrete")

        if len(verts) < 3:
            print(f"[blender_script] building_{i}: fewer than 3 vertices, skipping.")
            continue

        try:
            obj = _make_polygon_extrusion(verts, height, name=f"building_{i}")
            _triangulate(obj)
            ply_path = str(mesh_dir / f"building_{i}.ply")
            _export_ply(obj, ply_path)
            output.append({"path": ply_path, "material": material})
            print(f"[blender_script] building_{i}.ply ({len(verts)} vertices, h={height}m) OK")
        except Exception as e:
            print(f"[blender_script] ERROR building_{i}: {e}")

    # --- Roads ---
    for i, r in enumerate(roads):
        _clear_scene()
        verts = r.get("vertices", [])
        height = float(r.get("height", 0.25))
        material = r.get("material", "marble")

        if len(verts) < 3:
            print(f"[blender_script] road_{i}: fewer than 3 vertices, skipping.")
            continue

        try:
            obj = _make_polygon_extrusion(verts, height, name=f"road_{i}")
            _triangulate(obj)
            ply_path = str(mesh_dir / f"road_{i}.ply")
            _export_ply(obj, ply_path)
            output.append({"path": ply_path, "material": material})
            print(f"[blender_script] road_{i}.ply ({len(verts)} vertices, h={height}m) OK")
        except Exception as e:
            print(f"[blender_script] ERROR road_{i}: {e}")

    # Write output manifest
    out_path = mesh_dir / "_output.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"[blender_script] Done. {len(output)} mesh(es) written to {mesh_dir}")


main()
