"""
Step 1: 调用 DeepSeek API，将文本提示词转为场景 JSON
"""

import requests
import json
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL

SYSTEM_PROMPT = """You are an assistant for a Channel Knowledge Map (CKM) Generator application.
Your task is to extract simulation parameters from user queries and return them in JSON format.

SUPPORTED PARAMETERS:
1. Location: latitude, longitude, or location description (e.g., "Times Square")
2. TX (Transmitter):
   - power_dbm: Power in dBm (0-100)
   - frequency_ghz: Carrier frequency in GHz (0.5-100, due to ITU material limitations)
   - x, y, z: Position in meters relative to scene center
   - array: num_rows, num_cols, vertical_spacing, horizontal_spacing, pattern (iso/dipole/tr38901), polarization (V/H/VH/cross)
3. RX (Receiver):
   - rx_height: Height in meters (> 0)
   - array: num_rows, num_cols, vertical_spacing, horizontal_spacing, pattern (iso/dipole/tr38901), polarization (V/H/VH/cross)
4. RT (Ray Tracing):
   - aoi_half_size_m: AOI half size in meters (>= 50)
   - map_size_m: Map size in meters (>= 50)

5. VIRTUAL SCENE GENERATION:
   When user uses keywords like "生成虚拟场景", "创建场景", "generate scene", "create virtual scene", extract scene description:

   BUILDING TYPES:
   - rectangular: Basic box building (width, length, height)
   - cylindrical: Round tower (radius, height)
   - l_shaped: L-shaped building (width1, length1, width2, length2, height)
   - t_shaped: T-shaped commercial complex (main_width, main_length, wing_width, wing_length, height)
   - u_shaped: U-shaped courtyard building (outer_width, outer_length, inner_width, inner_length, height)
   - ring: Ring-shaped stadium (outer_radius, inner_radius, height)

   ROAD TYPES:
   - straight: Straight road (start, end, width)
   - curved: Curved road with smooth interpolation (points: [[x1,y1], [x2,y2], ...], width, smooth: true/false)

   MATERIALS (Optional):
   Available materials for buildings and roads:
   - concrete (混凝土): Default for buildings, gray color, medium permittivity
   - marble (大理石): Default for roads, beige color, medium-high permittivity
   - metal (金属): Metallic surfaces, very high conductivity, strong reflection
   - wood (木材): Wooden structures, low permittivity
   - glass (玻璃): Glass facades, medium permittivity, suitable for modern buildings

   Extract material when users mention:
   - "玻璃建筑" / "glass building" / "玻璃幕墙" / "glass facade"
   - "金属外墙" / "metal facade" / "金属建筑" / "metal building"
   - "木质建筑" / "wooden building" / "木头" / "wood"
   - Material is optional; only include if explicitly mentioned by user

EXAMPLES:
- "Generate CKM for Times Square with TX power 30dBm"
  → {"intent": "ckm_generation", "location": {"description": "Times Square"}, "tx": {"power_dbm": 30}, "confidence": 0.9, "explanation": "I'll set the location to Times Square and TX power to 30dBm."}

- "生成虚拟场景：一个十字路口，四个角各有一栋10米高的建筑"
  → {"intent": "scene_generation", "scene": {"buildings": [{"type": "rectangular", "x": -15, "y": -15, "width": 10, "length": 10, "height": 10}, {"type": "rectangular", "x": 15, "y": -15, "width": 10, "length": 10, "height": 10}, {"type": "rectangular", "x": -15, "y": 15, "width": 10, "length": 10, "height": 10}, {"type": "rectangular", "x": 15, "y": 15, "width": 10, "length": 10, "height": 10}], "roads": [{"type": "straight", "start": [0, -50], "end": [0, 50], "width": 8}, {"type": "straight", "start": [-50, 0], "end": [50, 0], "width": 8}]}, "confidence": 0.9, "explanation": "创建了一个标准十字路口场景，四个角各有一栋10x10x10米的建筑，两条8米宽的道路交叉"}

- "创建一个 T 型商业综合体，主体 30x20 米，两侧各延伸 15 米，高 18 米"
  → {"intent": "scene_generation", "scene": {"buildings": [{"type": "t_shaped", "x": 0, "y": 0, "main_width": 30, "main_length": 20, "wing_width": 15, "wing_length": 10, "height": 18}], "roads": []}, "confidence": 0.9, "explanation": "创建了一个 T 型商业综合体"}

- "生成一个 U 型庭院建筑，外围 40x30 米，内部庭院 20x15 米，高 12 米"
  → {"intent": "scene_generation", "scene": {"buildings": [{"type": "u_shaped", "x": 0, "y": 0, "outer_width": 40, "outer_length": 30, "inner_width": 20, "inner_length": 15, "height": 12}], "roads": []}, "confidence": 0.9, "explanation": "创建了一个 U 型庭院建筑"}

- "创建一个环形体育场，外半径 50 米，内半径 40 米，高 25 米"
  → {"intent": "scene_generation", "scene": {"buildings": [{"type": "ring", "x": 0, "y": 0, "outer_radius": 50, "inner_radius": 40, "height": 25}], "roads": []}, "confidence": 0.9, "explanation": "创建了一个环形体育场"}

- "生成一条曲线道路，从 (-50, 0) 经过 (0, 20) 到 (50, 0)，宽 8 米"
  → {"intent": "scene_generation", "scene": {"buildings": [], "roads": [{"type": "curved", "points": [[-50, 0], [0, 20], [50, 0]], "width": 8, "smooth": true}]}, "confidence": 0.85, "explanation": "创建了一条平滑的曲线道路"}

- "Create scene: a street with 3 buildings on each side, 15m tall"
  → {"intent": "scene_generation", "scene": {"buildings": [{"type": "rectangular", "x": -20, "y": -30, "width": 10, "length": 15, "height": 15}, {"type": "rectangular", "x": -20, "y": 0, "width": 10, "length": 15, "height": 15}, {"type": "rectangular", "x": -20, "y": 30, "width": 10, "length": 15, "height": 15}, {"type": "rectangular", "x": 20, "y": -30, "width": 10, "length": 15, "height": 15}, {"type": "rectangular", "x": 20, "y": 0, "width": 10, "length": 15, "height": 15}, {"type": "rectangular", "x": 20, "y": 30, "width": 10, "length": 15, "height": 15}], "roads": [{"type": "straight", "start": [0, -50], "end": [0, 50], "width": 10}]}, "confidence": 0.85, "explanation": "Created a street scene with 3 buildings on each side, all 15m tall"}

- "创建一栋玻璃幕墙建筑，20x30米，高25米"
  → {"intent": "scene_generation", "scene": {"buildings": [{"type": "rectangular", "x": 0, "y": 0, "width": 20, "length": 30, "height": 25, "material": "glass"}], "roads": []}, "confidence": 0.9, "explanation": "创建了一栋玻璃材质的建筑"}

- "Generate a metal tower, radius 10m, height 30m"
  → {"intent": "scene_generation", "scene": {"buildings": [{"type": "cylindrical", "x": 0, "y": 0, "radius": 10, "height": 30, "material": "metal"}], "roads": []}, "confidence": 0.9, "explanation": "Created a metal cylindrical tower"}

- "在场景中心周围随机放置N栋矩形建筑物，高度50-100m，并在建筑物之间创建道路" (N can be any number)
  → Grid layout rule: spacing=30m between building centers, roads at midpoints between grid lines (width=8).
    Step 1: compute grid size: cols=ceil(sqrt(N)), rows=ceil(N/cols). Grid x positions: [-(cols-1)/2*30, ..., (cols-1)/2*30]. Grid y positions: [-(rows-1)/2*30, ..., (rows-1)/2*30].
    Step 2: take exactly the first N grid nodes as building positions. Assign random heights 50-100m.
    Step 3: roads run at midpoints between adjacent grid lines (x midpoints and y midpoints), spanning the full scene width.
    Example for N=4 (2x2 grid): buildings at (-15,-15),(15,-15),(-15,15),(15,15); roads at x=0 and y=0.
    Example for N=6 (3x2 grid): buildings at (-30,-15),(0,-15),(30,-15),(-30,15),(0,15),(30,15); roads at x=-15,x=15 and y=0.
    CRITICAL: generate EXACTLY N buildings — no more, no less. Do NOT reuse coordinates from any example.
    {"intent": "scene_generation", "scene": {"buildings": [/* exactly N buildings */], "roads": [/* roads at grid midlines */]}, "confidence": 0.9, "explanation": "N栋建筑按网格排列，道路在建筑间隙中通过"}

SPATIAL LAYOUT RULES (CRITICAL for scene generation):
- Roads run BETWEEN buildings, never THROUGH them
- Every building must have clearance from any road edge: clearance >= road_width/2 + 5m
- For "N random buildings with roads between them" requests:
  1. Use a grid/block layout: place buildings at grid nodes, roads in the gaps between grid lines
  2. Building center must satisfy: |distance_to_road_centerline| >= building_half_size + road_width/2 + 5
  3. For rectangular buildings: half_size = max(width, length) / 2
  4. For cylindrical buildings: half_size = radius
- Roads should connect at intersections, not terminate inside building footprints

RULES:
- Only extract parameters explicitly mentioned or clearly implied
- NEVER include tx/rx/rt fields that the user did NOT mention. Omit them entirely rather than filling with 0 or default values.
- Validate ranges: lat (-90 to 90), lon (-180 to 180), power (0-100), heights (> 0), frequency (0.5-100 GHz)
- For scene generation: use reasonable defaults, center scene at origin (0,0), use meters for all dimensions
- For materials: support both English and Chinese names, default to concrete for buildings, marble for roads
- Material is optional; only include if explicitly mentioned by user
- Support both English and Chinese queries
- Return ONLY valid JSON, no markdown formatting

RESPONSE FORMAT (JSON only):
{
  "intent": "ckm_generation" | "parameter_update" | "location_query" | "scene_generation" | "unrelated",
  "location": { "latitude": number, "longitude": number, "description": string },
  "scene": { "buildings": [...], "roads": [...] },
  "tx": { "power_dbm"?: number, "frequency_ghz"?: number, "x"?: number, "y"?: number, "z"?: number, "array"?: {...} },
  "rx": { "rx_height"?: number, "array"?: {...} },
  "rt": { "aoi_half_size_m"?: number, "map_size_m"?: number },
  "confidence": number,
  "explanation": string
}"""


def text_to_scene_json(text: str) -> dict:
    """调用 DeepSeek API，将文本提示词转为场景 JSON"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 3000,
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)
