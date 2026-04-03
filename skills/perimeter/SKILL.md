# 周边式场景生成 (Perimeter/Courtyard Layout)

## 技能名称

**周边式场景生成** — Perimeter / Courtyard Layout

---

## 职责

Generates scenes where buildings surround the perimeter of city blocks, forming enclosed courtyards with open inner spaces. Roads run along the exterior edges of each block. This layout models traditional European perimeter block urban morphology as well as modern residential compound design common in Chinese cities. The defining characteristic is the enclosed courtyard: each block has buildings on three or four sides with a completely open interior.

---

## 触发关键词

- 周边式
- 围合
- courtyard
- perimeter
- 围合式
- 内庭院
- 院落布局
- 周边围合
- 合院
- perimeter block

---

## 执行步骤

1. **Determine number of blocks and their layout arrangement**
   - Block count: 2–4 blocks
   - Layout options:
     - Row layout: blocks arranged in a single horizontal row (most common for 2–3 blocks)
     - 2×2 grid: four blocks arranged symmetrically in two rows and two columns (for 4 blocks)
   - Block size: 60–100 m per side (square or near-square blocks)
   - Road width between blocks and at outer perimeter: 7–10 m

2. **For each block: select building configuration to wrap the perimeter**
   - Option A (u_shaped): single U-shaped building wraps three sides of the block
     - outer_width ≈ block_size − 2×setback
     - outer_length ≈ block_size − 2×setback
     - inner = outer × 0.50–0.65 (open courtyard)
     - Placed at block center
   - Option B (l_shaped combo): two L-shaped buildings in opposite corners, together forming three sides
     - Each L covers two sides at a corner; together they form a U-equivalent enclosure
   - Option C (rectangular combo): three rectangular buildings on three sides (left wall, right wall, back wall)
     - Each building is a slab covering one side; bottom remains open
   - Leave the inner courtyard completely free: NO buildings, NO roads inside the courtyard void

3. **Leave inner courtyard completely open**
   - The courtyard interior (the hollow centre of the block) must contain no buildings
   - No roads, paths, or any object may be placed inside the courtyard boundary
   - The courtyard opening faces outward (typically toward the road network)

4. **Place perimeter roads around block exterior edges**
   - Roads run along the outer edges of each block
   - Between two adjacent blocks: one shared road in the gap
   - Around the outer perimeter of the entire cluster: roads on all four outer edges
   - For row layout (N blocks in a row): N+1 transverse roads and 2 longitudinal roads
   - Road pattern: all straight roads (no curves for perimeter style)

5. **Align buildings to block axes**
   - All buildings in perimeter style use axis-aligned orientations
   - rotation_deg = 0.00° for buildings facing the +Y axis
   - rotation_deg = 90.00° for buildings rotated to face the +X axis
   - No random rotations; buildings must be orthogonal to the block grid
   - Each building must still have a unique rotation_deg value: use 0.00 for most, 90.00 for those needing 90° orientation (if all must be unique, use small offsets: 0.00, 0.01, 0.02… or 90.00, 90.01…)

6. **Enforce setback from road edge**
   - Minimum setback: building center ≥ road_width/2 + 3 m from road centerline
   - For a u_shaped building at block center: auto-satisfies setback if outer dimensions match block_size − 2×setback
   - For rectangular/l_shaped perimeter buildings: explicitly verify setback ≥ 3 m

---

## 输出标准

| Parameter | Requirement |
|-----------|-------------|
| Block count | 2–4 blocks |
| Block size | 60–100 m per side |
| Primary building types | u_shaped (wraps 3 sides) or l_shaped (2 buildings per block) |
| Inner courtyard | Completely free of all buildings and roads |
| rotation_deg | 0.00 or 90.00 (axis-aligned, all unique per scene) |
| Perimeter roads | Straight only, width 7–10 m, surrounding each block exterior |
| Setback | Building center ≥ road_width/2 + 3 m from road centerline |
| Road material | marble (default) |
| Building material | concrete (default), wood or glass allowed |
| Height | Each building: unique height, typically 9–30 m (low-rise residential) or up to 50 m |

---

## 调用方式

```bash
python skills/perimeter/scripts/generate_prompt.py --count 5
```

This generates 5 random perimeter-style Chinese scene description prompts, each saved as a `.txt` file in the `text_prompts/` directory.

---

## 参考文件

- `references/layout_rules.md` — Detailed spatial rules for block placement and road layout
- `assets/system_prompt.txt` — Complete LLM system prompt for this layout style
- `assets/example_output.json` — Validated example JSON output with 2 blocks

---

## 与其他风格的区别

| Feature | Perimeter | Point Scatter | Orthogonal Grid | Slab Row |
|---------|-----------|--------------|-----------------|----------|
| Building arrangement | Wraps block perimeter | Random scatter | Free within block | Parallel rows |
| Courtyard | Yes — open inner space | No | No | No |
| rotation_deg | 0.00 or 90.00 only | Fully random (0–360°) | 0° (axis-aligned) | ~0° or ~90° |
| Building types | u_shaped, l_shaped | rectangular, l_shaped | Any | rectangular (slabs) |
| Road density | Perimeter ring roads | 1–2 roads max | Dense grid | 2–3 parallel |
| Height | 9–50 m (low-to-mid rise) | 30–100 m (towers) | Varied | Varied |
| Enclosure | Strong (3–4 sides wrapped) | None | Loose | None |
