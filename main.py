"""
main.py — 批量处理 text_prompts/ 下所有 .txt 文件，生成场景、俯视图和 path_gain
"""

import json
from pathlib import Path

from step1_text_to_json import text_to_scene_json
from step2_json_to_scene import generate_scene
from step3_render_topdown import render_topdown
from step4_path_gain import generate_path_gain
from step5_scene_maps import generate_scene_maps
from overlap_checker import check_overlaps
import to_blender as _to_blender

EXAMPLE_JSON_DIR = Path("example_json")


def main():
    txt_files = sorted(Path("text_prompts").glob("*.txt"))
    if not txt_files:
        print("[main] No .txt files found in text_prompts/")
        return

    for txt_file in txt_files:
        name = txt_file.stem

        # 检查该场景的所有输出文件是否都已存在，若是则跳过
        _expected = [
            Path("text_prompt_json") / f"{name}.json",
            Path("simple_scene") / name / "scene_description.json",
            Path("3D_scene") / f"{name}.png",
            Path("path_gain/path_gain_photo") / f"{name}.png",
            Path("path_gain/path_gain_raw_data") / f"{name}.npz",
        ]
        if all(p.exists() for p in _expected):
            print(f"[main] Skipping '{name}' — all output files already exist.")
            continue

        print(f"\n{'='*50}")
        print(f"[main] Processing: {name}")
        print(f"{'='*50}")

        # Step 1: text → JSON（AI-1 单次调用）
        text = txt_file.read_text(encoding="utf-8")
        print(f"[main] Calling DeepSeek API...")
        result = text_to_scene_json(text)

        # 保存 JSON（含材质默认值）
        json_path = Path("text_prompt_json") / f"{name}.json"
        json_path.parent.mkdir(exist_ok=True)
        result_with_material = {
            **result,
            "scene": {
                "buildings": [
                    {**b, "material": b.get("material", "concrete")}
                    for b in result.get("scene", {}).get("buildings", [])
                ],
                "roads": [
                    {**r, "material": r.get("material", "marble")}
                    for r in result.get("scene", {}).get("roads", [])
                ],
            },
        } if result.get("scene") else result
        json_path.write_text(json.dumps(result_with_material, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[main] JSON saved: {json_path}")

        # 检测建筑物重叠
        scene_data = result_with_material.get("scene", {"buildings": [], "roads": []})
        overlaps = check_overlaps(scene_data)

        if overlaps:
            print(f"[main] ⚠ 检测到 {len(overlaps)} 处建筑物重叠，需要在 Blender 中手动调整：")
            for ov in overlaps:
                print(f"  {ov['a_desc']}  ×  {ov['b_desc']}  "
                      f"({ov['overlap_area_m2']:.2f} m²，重心 {ov['overlap_centroid']})")

            # 写入 scene_description.json（blender_to_json.py 需要此文件）
            _scene_dir = Path("simple_scene") / name
            _scene_dir.mkdir(parents=True, exist_ok=True)
            _scene_desc_path = _scene_dir / "scene_description.json"
            _scene_desc_path.write_text(
                json.dumps(
                    {"location_name": name, "scene": scene_data,
                     "tx": result.get("tx", {}), "rx": result.get("rx", {}),
                     "rt": result.get("rt", {})},
                    ensure_ascii=False, indent=2,
                ),
                encoding="utf-8",
            )
            print(f"[main] Scene description saved: {_scene_desc_path}")

            # 自动生成 Blender 脚本文件（存入 blender_scenes/{name}/ 子目录）
            _blender_scene_dir = _to_blender.BLENDER_SCENES_DIR / name
            _blender_scene_dir.mkdir(parents=True, exist_ok=True)
            (_blender_scene_dir / f"{name}_data.json").write_text(
                json.dumps(scene_data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            setup_path = _blender_scene_dir / f"{name}_setup.py"
            setup_path.write_text(_to_blender._setup_script(name), encoding="utf-8")
            extract_path = _blender_scene_dir / f"{name}_extract.py"
            extract_path.write_text(_to_blender._extract_script(name), encoding="utf-8")

            print(f"[main] Blender 脚本已生成，请按以下步骤手动调整后继续：")
            print(f"  1. 打开 Blender > Scripting 标签页")
            print(f"  2. Open → {setup_path} → ▶ Run Script")
            print(f"  3. 手动移动建筑物（G 移动，R Z 旋转，N → Dimensions Z 改高度）")
            print(f"  4. Open → {extract_path} → ▶ Run Script")
            print(f"  5. python blender_to_json.py {name}")
            continue  # 等用户在 Blender 中调整完再运行 blender_to_json.py

        # 无重叠：保存到 example_json 并继续流程
        print(f"[main] No overlaps detected.")
        EXAMPLE_JSON_DIR.mkdir(exist_ok=True)
        example_path = EXAMPLE_JSON_DIR / f"{name}.json"
        example_path.write_text(
            json.dumps(result_with_material, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[main] JSON saved to example_json: {example_path}")

        tx_params = result.get("tx", {})
        rx_params = result.get("rx", {})
        rt_params = result.get("rt", {})

        # Step 2: JSON → PLY + XML
        scene_dir = str(Path("simple_scene") / name)
        Path(scene_dir).mkdir(parents=True, exist_ok=True)

        scene_desc_path = Path(scene_dir) / "scene_description.json"
        full_params = {
            "location_name": name,
            "scene": scene_data,
            "tx": tx_params,
            "rx": rx_params,
            "rt": rt_params,
        }
        scene_desc_path.write_text(json.dumps(full_params, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[main] Scene description saved: {scene_desc_path}")

        xml_path = generate_scene(scene_data, scene_dir, {**rt_params, "frequency_ghz": tx_params.get("frequency_ghz", 28.0)})

        # Step 3: 俯视图
        topdown_png = str(Path("3D_scene") / f"{name}.png")
        map_size = float(rt_params.get("map_size_m", 200.0))
        try:
            render_topdown(
                xml_path=xml_path,
                output_png=topdown_png,
                cam_height=max(map_size * 2.5, 500.0),
            )
        except Exception as e:
            print(f"[main] WARNING: Top-down render failed: {e}")

        # Step 4: path_gain + LOS 图（Sionna RT max_depth=0）
        photo_path = str(Path("path_gain/path_gain_photo") / f"{name}.png")
        npz_path = str(Path("path_gain/path_gain_raw_data") / f"{name}.npz")
        los_map = None
        try:
            los_map = generate_path_gain(
                xml_path=xml_path,
                photo_path=photo_path,
                npz_path=npz_path,
                tx_params=tx_params,
                rx_params=rx_params,
                rt_params=rt_params,
            )
        except Exception as e:
            print(f"[main] ERROR: Path gain generation failed: {e}")
            raise

        # Step 5: 多通道场景地图（高度图/材质图/LOS图）
        maps_dir = str(Path("scene_maps") / name)
        try:
            generate_scene_maps(str(scene_desc_path), maps_dir, los_map=los_map)
        except Exception as e:
            print(f"[main] WARNING: Scene maps generation failed: {e}")

        print(f"[main] Done: {name}")

    print(f"\n[main] All {len(txt_files)} file(s) processed.")


if __name__ == "__main__":
    main()

