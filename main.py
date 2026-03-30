"""
main.py — 批量处理 text_prompts/ 下所有 .txt 文件，生成场景、俯视图和 path_gain
"""

import json
import os
from pathlib import Path

from step1_text_to_json import text_to_scene_json
from step2_json_to_scene import generate_scene
from step3_render_topdown import render_topdown
from step4_path_gain import generate_path_gain
from overlap_checker import check_overlaps, format_overlap_feedback

MAX_OVERLAP_RETRIES = 3


def main():
    txt_files = sorted(Path("text_prompts").glob("*.txt"))
    if not txt_files:
        print("[main] No .txt files found in text_prompts/")
        return

    for txt_file in txt_files:
        name = txt_file.stem
        print(f"\n{'='*50}")
        print(f"[main] Processing: {name}")
        print(f"{'='*50}")

        # Step 1: text → JSON（含重叠检测重试）
        text = txt_file.read_text(encoding="utf-8")
        retry_text = text
        result = None
        for attempt in range(MAX_OVERLAP_RETRIES + 1):
            print(f"[main] Calling DeepSeek API (attempt {attempt + 1}/{MAX_OVERLAP_RETRIES + 1})...")
            result = text_to_scene_json(retry_text)
            scene_check = result.get("scene", {})
            overlaps = check_overlaps(scene_check)
            if not overlaps:
                if attempt > 0:
                    print(f"[main] Overlaps resolved on attempt {attempt + 1}.")
                else:
                    print(f"[main] No overlaps detected.")
                break
            if attempt < MAX_OVERLAP_RETRIES:
                feedback = format_overlap_feedback(overlaps)
                print(f"[main] {len(overlaps)} overlap(s) detected. Retrying with feedback...")
                retry_text = text + "\n\n" + feedback
            else:
                print(f"[main] WARNING: {len(overlaps)} overlap(s) remain after {MAX_OVERLAP_RETRIES} retries. Proceeding anyway.")

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
