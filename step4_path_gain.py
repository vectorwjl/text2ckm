"""
Step 4: 使用 Sionna RadioMapSolver 生成 path_gain 图片和原始数据，
        并额外跑一次 max_depth=0 求解得到精确 LOS 图。
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import mitsuba as mi

from sionna.rt import load_scene, Transmitter, PlanarArray, RadioMapSolver


def generate_path_gain(
    xml_path: str,
    photo_path: str,
    npz_path: str,
    tx_params: dict = None,
    rx_params: dict = None,
    rt_params: dict = None,
) -> np.ndarray:
    """
    生成 path_gain 热力图（PNG）和原始数据（NPZ），并计算 LOS 图。

    Args:
        xml_path:    场景 XML 文件路径
        photo_path:  输出热力图 PNG 路径
        npz_path:    输出原始数据 NPZ 路径
        tx_params:   发射机参数字典
        rx_params:   接收机参数字典
        rt_params:   射线追踪参数字典

    Returns:
        los_map: shape (H, W) float32，1.0=LOS，0.0=NLOS
                 H = W = map_size_m / cell_size_m（默认 40×40）
    """
    tx_params = tx_params or {}
    rx_params = rx_params or {}
    rt_params = rt_params or {}

    # TX 参数
    tx_power_dbm = float(tx_params.get("power_dbm", 44.0))
    tx_frequency_ghz = float(tx_params.get("frequency_ghz", 28.0))
    tx_x = float(tx_params.get("x", 0.0))
    tx_y = float(tx_params.get("y", 0.0))
    tx_z = float(tx_params.get("z", 20.0))
    tx_array_cfg = tx_params.get("array", {}) or {}

    # RX 参数
    rx_array_cfg = rx_params.get("array", {}) or {}

    # RT 参数
    map_size = float(rt_params.get("map_size_m", 200.0))
    max_depth = int(rt_params.get("max_depth", 5))
    samples_per_tx = int(rt_params.get("samples_per_tx", 10_000_000))
    cell_size = float(rt_params.get("cell_size_m", 1.0))

    os.makedirs(os.path.dirname(photo_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(npz_path) or ".", exist_ok=True)

    def build_array(cfg: dict) -> PlanarArray:
        return PlanarArray(
            num_rows=int(cfg.get("num_rows", 1)),
            num_cols=int(cfg.get("num_cols", 1)),
            vertical_spacing=float(cfg.get("vertical_spacing", 0.5)),
            horizontal_spacing=float(cfg.get("horizontal_spacing", 0.5)),
            pattern=str(cfg.get("pattern", "iso")),
            polarization=str(cfg.get("polarization", "V")),
        )

    # 公共参数
    _rm_kwargs = dict(
        cell_size=mi.Point2f(cell_size, cell_size),
        center=mi.Point3f(0, 0, 0),
        size=mi.Point2f(map_size, map_size),
        orientation=mi.Point3f(0, 0, 0),
        samples_per_tx=samples_per_tx,
    )

    # 加载场景
    scene = load_scene(xml_path)
    scene.frequency = tx_frequency_ghz * 1e9
    scene.tx_array = build_array(tx_array_cfg)
    scene.rx_array = build_array(rx_array_cfg)
    scene.add(Transmitter(
        name="tx0",
        position=mi.Point3f(tx_x, tx_y, tx_z),
        orientation=mi.Point3f(0, 0, 0),
        power_dbm=tx_power_dbm,
    ))

    rm_solver = RadioMapSolver()

    # ── 完整 path gain（含反射/绕射）────────────────────────────────────────────
    rm = rm_solver(scene, max_depth=max_depth, **_rm_kwargs)

    rm.show(metric="path_gain")
    plt.savefig(photo_path, dpi=250, bbox_inches="tight")
    plt.close()
    print(f"[step4] Path gain photo saved: {photo_path}")

    path_gain_np = rm.path_gain.numpy()  # shape: [num_tx, H, W]
    np.savez_compressed(npz_path, path_gain_linear=path_gain_np)
    print(f"[step4] Path gain raw data saved: {npz_path}")

    # ── LOS 图（max_depth=0，仅直射路径）────────────────────────────────────────
    print(f"[step4] 计算 LOS 图（max_depth=0）…")
    rm_los = rm_solver(scene, max_depth=0, **_rm_kwargs)
    los_map = (rm_los.path_gain.numpy()[0] > 0).astype(np.float32)  # (H, W)
    los_ratio = los_map.mean() * 100
    print(f"[step4] LOS 覆盖率：{los_ratio:.1f}%  shape={los_map.shape}")

    return los_map

