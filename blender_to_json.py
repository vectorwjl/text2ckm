"""
blender_to_json.py — 将 Blender 导出的建筑物位置写回场景 JSON。

用法:
    python blender_to_json.py <scene_name>

前置条件:
    先在 Blender 中运行 blender_scenes/{name}_extract.py，
    生成 blender_scenes/{name}_positions.json。

读取:
    blender_scenes/{name}_positions.json        由 Blender 导出脚本生成
    simple_scene/{name}/scene_description.json  原始场景（回退到 text_prompt_json/）

输出:
    simple_scene/{name}/scene_description.json  原地更新建筑坐标
    text_prompt_json/{name}.json                覆盖原 JSON
    example_json/{name}.json                    仅当无重叠时覆盖
    3D_scene/{name}.png                         覆盖俯视图
"""

import json
import sys
from pathlib import Path

from overlap_checker import check_overlaps


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _load_full(name: str) -> tuple[dict, Path]:
    """读取原始场景 JSON，返回 (full_data, source_path)。"""
    candidates = [
        Path("simple_scene") / name / "scene_description.json",
        Path("text_prompt_json") / f"{name}.json",
    ]
    for p in candidates:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8")), p
    raise FileNotFoundError(
        f"找不到场景 '{name}' 的 JSON 文件。\n"
        f"请先运行 main.py 生成场景，或确认文件路径正确。"
    )


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    name = sys.argv[1]

    # ── 读取 Blender 导出的位置 ──────────────────────────────────────────────
    pos_path = Path("blender_scenes") / f"{name}_positions.json"
    if not pos_path.exists():
        print(f"[blender_to_json] 错误：找不到 {pos_path}")
        print("请先在 Blender 脚本编辑器中运行对应的 _extract.py 脚本。")
        sys.exit(1)
    positions = json.loads(pos_path.read_text(encoding="utf-8"))

    # ── 读取原始场景 JSON ────────────────────────────────────────────────────
    full, src_path = _load_full(name)
    scene     = full.get("scene", full)
    buildings = scene.get("buildings", [])

    # ── 应用 Blender 中的位置更新 ────────────────────────────────────────────
    print(f"[blender_to_json] 更新场景 '{name}'…")
    moved = 0
    for idx_str, pos in positions.items():
        idx = int(idx_str)
        if not (0 <= idx < len(buildings)):
            print(f"  警告：building_{idx} 超出范围，跳过。")
            continue
        b = buildings[idx]
        old_x = float(b.get("x", 0))
        old_y = float(b.get("y", 0))
        new_x = round(float(pos["x"]), 2)
        new_y = round(float(pos["y"]), 2)
        b["x"] = new_x
        b["y"] = new_y
        if "rotation_deg" in pos:
            b["rotation_deg"] = round(float(pos["rotation_deg"]) % 360, 2)
        if "height_m" in pos:
            old_h = float(b.get("height", 0))
            new_h = round(float(pos["height_m"]), 2)
            b["height"] = new_h
            if abs(new_h - old_h) > 0.01:
                print(f"  building_{idx}: height {old_h:.2f} → {new_h:.2f} m")
        dx, dy = new_x - old_x, new_y - old_y
        if abs(dx) > 0.01 or abs(dy) > 0.01:
            print(f"  building_{idx}: ({old_x:.2f}, {old_y:.2f}) → "
                  f"({new_x:.2f}, {new_y:.2f})  Δ=({dx:+.2f}, {dy:+.2f})")
            moved += 1

    print(f"[blender_to_json] {moved}/{len(positions)} 栋建筑位置已更改。")

    # ── 重叠检测 ──────────────────────────────────────────────────────────────
    overlaps = check_overlaps(scene)
    if overlaps:
        print(f"[blender_to_json] ⚠ 仍有 {len(overlaps)} 处重叠：")
        for ov in overlaps:
            print(f"    {ov['a_desc']}  ×  {ov['b_desc']}  "
                  f"({ov['overlap_area_m2']:.2f} m²，"
                  f"重心 {ov['overlap_centroid']})")
        print("  可在 Blender 中继续调整，再次运行 _extract.py 和本脚本。")
    else:
        print("[blender_to_json] ✓ 无重叠检测到。")

    # ── 写回 scene_description.json ──────────────────────────────────────────
    if "scene" in full:
        full["scene"] = scene
    src_path.write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[blender_to_json] 已更新：{src_path}")

    # ── 保存到 text_prompt_json/（覆盖原文件）────────────────────────────────
    out_path = Path("text_prompt_json") / f"{name}.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[blender_to_json] 已保存：{out_path}")

    # ── 无重叠时保存到 example_json/（覆盖原文件）────────────────────────────
    if not overlaps:
        ex_path = Path("example_json") / f"{name}.json"
        ex_path.parent.mkdir(exist_ok=True)
        ex_path.write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[blender_to_json] 无重叠 JSON 已保存：{ex_path}")

    # ── 重新生成 3D 场景 ──────────────────────────────────────────────────────
    print("\n[blender_to_json] 重新生成 3D 场景…")
    try:
        from step2_json_to_scene import generate_scene
        from step3_render_topdown import render_topdown

        scene_dir = str(Path("simple_scene") / name)
        rt_params = {
            **full.get("rt", {}),
            "frequency_ghz": full.get("tx", {}).get("frequency_ghz", 28.0),
        }
        xml_path = generate_scene(scene, scene_dir, rt_params)
        print(f"[blender_to_json] 3D 场景 XML 已生成：{xml_path}")

        topdown_png = str(Path("3D_scene") / f"{name}.png")
        map_size = float(full.get("rt", {}).get("map_size_m", 200.0))
        render_topdown(
            xml_path=xml_path,
            output_png=topdown_png,
            cam_height=max(map_size * 2.5, 500.0),
        )
        print(f"[blender_to_json] 俯视图已保存：{topdown_png}")
    except Exception as e:
        print(f"[blender_to_json] 渲染失败（可手动运行 main.py）：{e}")


if __name__ == "__main__":
    main()
