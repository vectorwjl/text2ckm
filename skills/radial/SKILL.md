# 技能：放射式场景生成 (Radial Layout)

## 技能名称
放射式场景生成 (Radial Layout)

## 职责
Generates scenes with roads radiating outward from the scene center (origin), with buildings arranged along each ray. The scene resembles a spoke-and-hub pattern where all roads originate from a single central point and extend outward at evenly-spaced angles, with buildings flanking each road segment.

## 触发关键词
- 放射式
- 辐射型
- radial
- 放射状
- 轮辐式

If any of these keywords appear in the user's prompt, this skill's system prompt (`assets/system_prompt.txt`) must be loaded instead of the base system prompt.

## 执行步骤

1. **确定射线数量与角度 (Determine ray count and angles)**
   - Choose number of rays N ∈ {4, 5, 6}.
   - Compute angle per ray: ray_interval = 360 / N degrees.
   - Ray angles: angle_i = i × ray_interval for i ∈ {0, 1, ..., N−1}.
   - Examples: N=4 → [0, 90, 180, 270]; N=5 → [0, 72, 144, 216, 288]; N=6 → [0, 60, 120, 180, 240, 300].

2. **生成放射道路 (Generate radial roads)**
   - For each ray at angle_i: create one straight road from [0.00, 0.00] to the computed endpoint.
   - Road endpoint: end_x = round(cos(radians(angle_i)) × span, 2), end_y = round(sin(radians(angle_i)) × span, 2).
   - span = map_size / 2 + 20 (roads extend slightly beyond the building zone).
   - Road width: 7–10 m. Material: marble (default).

3. **沿射线布置建筑 (Place buildings along each ray)**
   - Place 2–4 buildings per ray at distances 20–100 m from the origin along the ray direction.
   - Base position along ray at distance d: base_x = round(d × cos(radians(angle_i)), 2), base_y = round(d × sin(radians(angle_i)), 2).
   - Add perpendicular offset (≤ 15 m) to avoid placing buildings directly on the road centerline:
     - perp_x = round(offset × (−sin(radians(angle_i))), 2)
     - perp_y = round(offset × cos(radians(angle_i)), 2)
   - Final building position: x = base_x + perp_x, y = base_y + perp_y.
   - Alternate offset sign between buildings on the same ray (one side, then the other).

4. **分配建筑旋转角 (Assign building rotation)**
   - Each building on ray i: rotation_deg = round(angle_i, 2).
   - This ensures buildings face outward along the ray direction.
   - All buildings on the same ray share the same rotation_deg value derived from the ray angle.
   - NOTE: rotation_deg must be globally unique — for rays sharing the same numeric angle (which cannot happen in a valid N-ray layout), use small perturbations (±0.01) to distinguish if needed.

5. **可选：添加弧形连接道路 (Optional: add curved connecting roads)**
   - Optionally add 1–2 curved roads connecting buildings across adjacent rays.
   - Each curved road has 3–4 control points, arcing between two adjacent ray directions.
   - These roads provide cross-connectivity between rays.

6. **输出完整 JSON (Output complete JSON)**
   - Emit a single valid JSON object as defined in `_common/references/json_schema.md`.
   - Include all N straight radial roads and all buildings.
   - Assign unique dimensions and heights to every building.

## 输出标准

| Property              | Requirement                                                              |
|-----------------------|--------------------------------------------------------------------------|
| Road count            | Exactly N straight roads, all starting at [0.00, 0.00]                  |
| Road spacing          | Evenly spaced at 360/N degrees                                           |
| Building rotation     | rotation_deg = ray angle in degrees (0.01 precision), unique per building|
| Building position     | Along ray ±15 m perpendicular offset                                     |
| Building count        | 2–4 per ray                                                              |
| Dimension diversity   | Every building has unique dimensions (same-type vary ≥ 2 m per dimension)|
| Height diversity      | Every building has a unique height value                                 |
| Road width            | 7–10 m                                                                   |
| Precision             | All float fields: exactly 2 decimal places                               |
| Clearance             | Building-to-building ≥ 5 m; building-to-road edge ≥ 5 m                 |

## 相关文件

- `references/layout_rules.md` — Detailed spatial computation rules and formulas
- `assets/system_prompt.txt` — Full self-contained system prompt for this skill
- `assets/example_output.json` — Reference valid JSON output (6 rays, 12 buildings)
- `scripts/generate_prompt.py` — Prompt generator script

## 调用方式

Generate a single random radial layout prompt:
```
python skills/radial/scripts/generate_prompt.py --count 1
```

Generate multiple prompts (e.g., 5):
```
python skills/radial/scripts/generate_prompt.py --count 5
```

The script outputs one Chinese-language prompt per line, suitable for sending to the LLM API with `assets/system_prompt.txt` as the system prompt.
