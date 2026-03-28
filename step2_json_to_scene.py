"""
Step 2: 根据场景 JSON 生成 PLY mesh 文件 + Sionna XML
"""

import os
import numpy as np
import pyvista as pv
import xml.etree.ElementTree as ET
import xml.dom.minidom

from blender_generator import generate_scene_from_description
from utils.mesh_utils import save_mesh_as_ply
from utils.material_utils import get_all_material_properties, select_ground_material, normalize_material_name


def xml_mesh_ref(abs_path: str) -> str:
    filename = os.path.basename(abs_path)
    return f"mesh/{filename}".replace("\\", "/")


def create_scene_xml() -> ET.Element:
    scene = ET.Element("scene", version="3.0.0")
    materials = get_all_material_properties()
    for mat_id, props in materials.items():
        bsdf = ET.SubElement(scene, "bsdf", type="itu", id=mat_id)
        for key, value in props.items():
            if key == "color":
                ET.SubElement(bsdf, "rgb", name="diffuse_reflectance", value=value)
            else:
                ET.SubElement(bsdf, "float", name=key, value=value)
    integrator = ET.SubElement(scene, "integrator", type="path")
    ET.SubElement(integrator, "integer", name="max_depth", value="3")
    return scene


def create_ground_mesh(scene_dir: str, size: float = 300.0) -> str:
    mesh_dir = os.path.join(scene_dir, "mesh")
    os.makedirs(mesh_dir, exist_ok=True)
    half = size / 2
    corners = np.array([
        [-half, -half, 0],
        [half, -half, 0],
        [half, half, 0],
        [-half, half, 0],
    ])
    points = pv.PolyData(corners)
    ground_mesh = points.delaunay_2d()
    ground_path = os.path.join(mesh_dir, "ground.ply")
    save_mesh_as_ply(ground_mesh, ground_path)
    return ground_path


def save_scene_xml(scene: ET.Element, scene_dir: str) -> str:
    xml_string = ET.tostring(scene, encoding="utf-8")
    dom = xml.dom.minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")
    xml_path = os.path.join(scene_dir, "simple_OSM_scene.xml")
    with open(xml_path, "wb") as f:
        f.write(pretty_xml)
    return xml_path


def generate_scene(scene_data: dict, scene_dir: str, rt_params: dict = None) -> str:
    """
    生成 PLY mesh + XML，返回 XML 文件路径

    Args:
        scene_data: {"buildings": [...], "roads": [...]}
        scene_dir:  输出目录（如 simple_scene/scene_01）
        rt_params:  可选，用于获取 map_size_m 和 frequency_ghz

    Returns:
        xml_path: 生成的 XML 文件路径
    """
    rt_params = rt_params or {}
    map_size = float(rt_params.get("map_size_m", 200.0))
    tx_frequency_ghz = float(rt_params.get("frequency_ghz", 28.0))

    os.makedirs(scene_dir, exist_ok=True)

    # 生成建筑/道路 PLY
    mesh_results = generate_scene_from_description(scene_data, scene_dir)

    # 生成地面
    ground_path = create_ground_mesh(scene_dir, size=map_size * 1.5)

    # 构建 XML
    scene_xml = create_scene_xml()

    for idx, (ply_path, material) in enumerate(mesh_results):
        shape = ET.SubElement(scene_xml, "shape", type="ply", id=f"mesh-obj-{idx}")
        ET.SubElement(shape, "string", name="filename", value=xml_mesh_ref(ply_path))
        ET.SubElement(shape, "ref", id=normalize_material_name(material), name="bsdf")
        ET.SubElement(shape, "boolean", name="face_normals", value="true")

    ground_material = select_ground_material(tx_frequency_ghz, "wet_ground")
    ground_shape = ET.SubElement(scene_xml, "shape", type="ply", id="mesh-ground")
    ET.SubElement(ground_shape, "string", name="filename", value=xml_mesh_ref(ground_path))
    ET.SubElement(ground_shape, "ref", id=ground_material, name="bsdf")
    ET.SubElement(ground_shape, "boolean", name="face_normals", value="true")

    xml_path = save_scene_xml(scene_xml, scene_dir)
    print(f"[step2] Scene XML saved: {xml_path}")
    return xml_path
