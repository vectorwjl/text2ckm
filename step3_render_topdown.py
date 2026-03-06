"""
Step 3: 使用 Sionna RT 渲染场景俯视图
"""

import os
import numpy as np
import matplotlib.pyplot as plt

from sionna.rt import load_scene, Camera


def render_topdown(xml_path: str, output_png: str,
                   cam_height: float = 500.0,
                   resolution: list = None,
                   num_samples: int = 256,
                   dpi: int = 150) -> None:
    """
    渲染场景正上方俯视图并保存为 PNG

    Args:
        xml_path:    场景 XML 文件路径
        output_png:  输出 PNG 文件路径
        cam_height:  相机高度（米）
        resolution:  渲染分辨率 [width, height]
        num_samples: 采样数
        dpi:         输出 DPI
    """
    if resolution is None:
        resolution = [650, 500]

    os.makedirs(os.path.dirname(output_png) or ".", exist_ok=True)

    scene = load_scene(xml_path)

    # 正上方俯视：相机在 (0, 0, cam_height)，朝向原点
    cam = Camera(position=(0.0, 0.0, float(cam_height)), look_at=(0.0, 0.0, 0.0))

    # scene.render() 返回 matplotlib Figure 对象
    fig = scene.render(
        camera=cam,
        resolution=resolution,
        num_samples=num_samples,
    )

    fig.savefig(output_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"[step3] Top-down render saved: {output_png}")
