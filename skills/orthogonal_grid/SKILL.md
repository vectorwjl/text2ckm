# 技能：方格网式场景生成 (Orthogonal Grid Layout)

## 技能名称
方格网式场景生成 (Orthogonal Grid Layout)

## 职责
Generates axis-aligned street grid urban scenes with buildings placed inside rectangular city blocks. The scene resembles a classic Manhattan-style grid where all roads are either north-south or east-west, and buildings are aligned with the street grid (rotation_deg = 0.00 for all buildings).

## 触发关键词
- 方格网布局
- 正交网格
- orthogonal grid
- 方格网式
- 棋盘式路网
- 直角网格

If any of these keywords appear in the user's prompt, this skill's system prompt (`assets/system_prompt.txt`) must be loaded instead of the base system prompt.

## 执行步骤

1. **确定路网规模 (Determine road network dimensions)**
   - Decide N south-north roads (N = 2 or 3) and M east-west roads (M = 2 or 3).
   - Choose longitudinal spacing (between south-north roads): 50–70 m.
   - Choose transverse spacing (between east-west roads): 45–65 m.
   - Choose road width: 7–10 m (consistent for all roads, or vary slightly per road class).

2. **计算路网坐标 (Compute road positions)**
   - South-north roads: x = k × long_spacing, for k ∈ {−⌊(N−1)/2⌋, ..., +⌊(N−1)/2⌋}. All aligned to the Y axis.
   - East-west roads: y = m × trans_spacing, for m ∈ {−⌊(M−1)/2⌋, ..., +⌊(M−1)/2⌋}. All aligned to the X axis.
   - Road start/end coordinates: extend to ±(max_road_span/2 + 20) to ensure roads reach beyond the building zone.

3. **识别街区中心 (Identify block centers)**
   - Each block is bounded by adjacent road pairs: x ∈ [x_k, x_{k+1}], y ∈ [y_m, y_{m+1}].
   - Block centre: ((x_k + x_{k+1}) / 2, (y_m + y_{m+1}) / 2).
   - Total blocks = (N − 1) × (M − 1).

4. **填充街区建筑 (Fill each block with buildings)**
   - Place 2–4 buildings per block arranged in a row or 2×2 grid within the block interior.
   - All buildings: rotation_deg = 0.00 (axis-aligned with the grid).
   - Enforce setback: building centre must satisfy:
     x_k + road_width/2 + setback + building_width/2  ≤  bldg_x  ≤  x_{k+1} − road_width/2 − setback − building_width/2
     (and identically for y with building_length).
   - Default setback = 4–6 m from road edge to building face.
   - Building gap within block (edge-to-edge between buildings in the same block): 2–5 m.

5. **分配唯一高度与尺寸 (Assign unique heights and dimensions)**
   - Every building must have a unique height (vary by ≥ 3 m between all buildings in the scene).
   - Every building of the same type must have unique dimensions (vary by ≥ 3–8 m per dimension from others of the same type).
   - All values formatted to exactly 2 decimal places.

6. **输出完整 JSON (Output complete JSON)**
   - Emit a single valid JSON object as defined in `_common/references/json_schema.md`.
   - Include all buildings (rotation_deg = 0.00) and all road objects.
   - Include tx/rx/rt only if explicitly mentioned by the user.

## 输出标准

| Property              | Requirement                                           |
|-----------------------|-------------------------------------------------------|
| Building rotation     | rotation_deg = 0.00 for ALL buildings                 |
| Road alignment        | All roads axis-aligned (horizontal or vertical only)  |
| Longitudinal spacing  | 50–70 m (between south-north roads)                   |
| Transverse spacing    | 45–65 m (between east-west roads)                     |
| Setback               | Building face ≥ road_width/2 + 4 m from road centreline |
| Building gap in block | 2–5 m edge-to-edge between buildings within same block|
| Dimension diversity   | Every building has unique dimensions (vary ±3–8 m from others in same block) |
| Height diversity      | Every building has unique height                      |
| Road width            | 7–10 m per road                                       |
| Precision             | All float fields: exactly 2 decimal places            |

## 调用方式

Generate a single random orthogonal grid prompt:
```
python skills/orthogonal_grid/scripts/generate_prompt.py --count 1
```

Generate multiple prompts (e.g., 5):
```
python skills/orthogonal_grid/scripts/generate_prompt.py --count 5
```

The script outputs one Chinese-language prompt per line, suitable for sending to the LLM API with `assets/system_prompt.txt` as the system prompt.

## 相关文件

- `references/layout_rules.md` — Detailed spatial computation rules
- `assets/system_prompt.txt` — Full system prompt for this skill
- `assets/example_output.json` — Reference valid JSON output
- `scripts/generate_prompt.py` — Prompt generator script
