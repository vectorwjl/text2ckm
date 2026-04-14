"""
main.py — 批量处理 text_prompts/ 下所有 .txt 文件，生成场景、俯视图和 path_gain
"""

import json
from pathlib import Path

from step1_text_to_json import text_to_scene_json, detect_style, SKILLS_DIR
from step2_json_to_scene import generate_scene
from step3_render_topdown import render_topdown
from step4_path_gain import generate_path_gain
from overlap_resolver import iteratively_resolve

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

        # Step 1: text → JSON（AI-1 只调用一次，后续由算法直接修改场景）
        text = txt_file.read_text(encoding="utf-8")
        style = detect_style(text)
        print(f"[main] Calling DeepSeek API (single-shot)...")
        result = text_to_scene_json(text)
        scene_for_resolver = result.get("scene", {})

        # 算法直接修改 scene_data 的建筑 x, y，直至无重叠
        resolve_report = iteratively_resolve(scene_for_resolver, style=style)
        if resolve_report["converged"]:
            if resolve_report["iterations"] == 0:
                print("[main] No overlaps detected.")
            else:
                print(
                    f"[main] Overlaps resolved by algorithm in "
                    f"{resolve_report['iterations']} iteration(s); "
                    f"{len(resolve_report['moved_indices'])} building(s) moved."
                )
        else:
            print(
                f"[main] WARNING: {len(resolve_report['final_overlaps'])} "
                f"overlap(s) remain after {resolve_report['iterations']} iterations."
            )
            print(f"[main] 提示：可在 Blender 中手动调整建筑位置：")
            print(f"[main]   python to_blender.py {name}")
            print(f"[main]   （详见 to_blender.py 文件头部的工作流说明）")

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

        # 只有完全无重叠时才保存至示例目录
        if resolve_report["converged"]:
            EXAMPLE_JSON_DIR.mkdir(exist_ok=True)
            example_path = EXAMPLE_JSON_DIR / f"{name}.json"
            example_path.write_text(
                json.dumps(result_with_material, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"[main] No overlaps — JSON saved to example_json: {example_path}")
        else:
            print(f"[main] Skipping example_json (residual overlaps remain).")

        scene_data = result.get("scene", {"buildings": [], "roads": []})
        tx_params = result.get("tx", {})
        rx_params = result.get("rx", {})
        rt_params = result.get("rt", {})

        # Step 2: JSON → PLY + XML
        scene_dir = str(Path("simple_scene") / name)
        Path(scene_dir).mkdir(parents=True, exist_ok=True)

        # 保存完整参数到场景目录（材质补全默认值）
        scene_desc_path = Path(scene_dir) / "scene_description.json"
        scene_data_with_material = {
            "buildings": [
                {**b, "material": b.get("material", "concrete")}
                for b in scene_data.get("buildings", [])
            ],
            "roads": [
                {**r, "material": r.get("material", "marble")}
                for r in scene_data.get("roads", [])
            ],
        }
        full_params = {
            "location_name": name,
            "scene": scene_data_with_material,
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

        # Step 4: path_gain
        photo_path = str(Path("path_gain/path_gain_photo") / f"{name}.png")
        npz_path = str(Path("path_gain/path_gain_raw_data") / f"{name}.npz")
        try:
            generate_path_gain(
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

        print(f"[main] Done: {name}")

    print(f"\n[main] All {len(txt_files)} file(s) processed.")


if __name__ == "__main__":
    main()
