"""
blender_generator.py — Scene mesh generation via Blender Python API.

Delegates all mesh creation to blender_script.py running inside a headless
Blender process. Output PLY files are compatible with Sionna RT.

Public interface (unchanged):
    generate_scene_from_description(scene_data, scene_dir) -> list[(ply_path, material)]
"""

import json
import subprocess
from pathlib import Path

try:
    from config import BLENDER_EXECUTABLE, BLENDER_TIMEOUT
except ImportError:
    BLENDER_EXECUTABLE = "F:/Blender/blender.exe"
    BLENDER_TIMEOUT = 120


def generate_scene_from_description(scene_data: dict, scene_dir: str) -> list:
    """
    Generate PLY mesh files for all buildings and roads in scene_data.

    Args:
        scene_data: dict with 'buildings' and 'roads' lists
        scene_dir:  output directory (mesh/ subdirectory will be created)

    Returns:
        list of (ply_path: str, material: str) tuples
    """
    mesh_dir = Path(scene_dir) / "mesh"
    mesh_dir.mkdir(parents=True, exist_ok=True)

    # Write scene parameters for the Blender script to read
    params_path = mesh_dir / "_scene_params.json"
    params_path.write_text(
        json.dumps(scene_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Locate blender_script.py next to this file
    script_path = Path(__file__).parent / "blender_script.py"
    if not script_path.exists():
        raise FileNotFoundError(f"blender_script.py not found at {script_path}")

    blender_exe = Path(BLENDER_EXECUTABLE)
    if not blender_exe.exists():
        raise FileNotFoundError(
            f"Blender executable not found: {BLENDER_EXECUTABLE}\n"
            "Update BLENDER_EXECUTABLE in config.py."
        )

    cmd = [
        str(blender_exe),
        "--background",
        "--python", str(script_path),
        "--",
        str(params_path),
        str(mesh_dir),
    ]

    print(f"[blender_generator] Running Blender for scene: {Path(scene_dir).name}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=BLENDER_TIMEOUT,
    )

    # Print relevant lines from Blender stdout
    for line in result.stdout.splitlines():
        if line.startswith("[blender_script]") or "Error" in line:
            print(f"  {line}")

    if result.returncode != 0:
        print("[blender_generator] Blender stderr (last 2000 chars):")
        print(result.stderr[-2000:])
        raise RuntimeError(
            f"Blender exited with code {result.returncode}."
        )

    # Read the output manifest written by blender_script.py
    output_path = mesh_dir / "_output.json"
    if not output_path.exists():
        raise RuntimeError(
            "_output.json not found after Blender run — script may have crashed."
        )

    output = json.loads(output_path.read_text(encoding="utf-8"))
    mesh_list = [(item["path"], item["material"]) for item in output]
    print(f"[blender_generator] {len(mesh_list)} mesh(es) generated in {mesh_dir}")
    return mesh_list
