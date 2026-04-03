# 技能：有机式场景生成 (Organic / Freeform Layout)

## 技能名称
有机式场景生成 — Organic / Freeform Layout

---

## 职责

Generates freeform urban scenes characterized by winding curved roads and buildings placed informally alongside them with no regular pattern. This skill models organic city districts, village streets, or informal settlements where geometry is driven by topography and history rather than a planning grid. The defining feature is curved roads and completely irregular building placement/rotation.

---

## 触发关键词

- 有机式
- 有机自由式
- 自由式布局
- organic
- irregular
- freeform
- 不规则布局
- 自然生长型

---

## 执行步骤

1. **设计曲线道路 (Design curved roads)**
   - Create 2–3 curved roads using "curved" type with smooth=true.
   - Each road: 3–5 control points, each consecutive pair spaced > 20 m apart.
   - Roads should wind and curve across the scene, not run in straight lines.
   - Example 3-point road: [[-90, -20], [-20, 35], [80, 10]]
   - Example 4-point road: [[-85, 60], [-20, -10], [40, -55], [90, -30]]
   - Road width: 6–10 m. Material: marble or concrete.

2. **不规则放置建筑 (Place buildings informally)**
   - Place 10–15 buildings loosely alongside the roads.
   - Each building: choose a road to be near, pick a random point along that road, offset 8–20 m perpendicularly (either side), add ±10 m random variation.
   - No grid, no rows, no regular spacing.

3. **分配完全随机旋转角 (Assign fully random rotation_deg)**
   - Each building gets a FULLY RANDOM rotation_deg ∈ [0.00°, 359.99°].
   - All rotation_deg values must be unique across the entire scene.
   - No two buildings share the same rotation.

4. **多样化尺寸和高度 (Diversify dimensions and heights)**
   - Mix building types: use at least 2 different types.
   - Height range: 10–120 m, no two buildings with the same height.
   - Dimensions vary widely: don't repeat the same width/length across buildings.

5. **验证道路清距 (Verify road clearance)**
   - Building-road edge clearance ≥ 5 m for every building.
   - Setback = building_half_size + road_width/2 + 5 from road centerline.
   - Building-building edge distance ≥ 5 m.

---

## 输出标准

| Parameter | Requirement |
|-----------|-------------|
| Roads | 2–3 curved roads (smooth=true), 3–5 control points each |
| Control point spacing | Consecutive points > 20 m apart |
| Building count | 10–15 |
| Positions | Irregular, alongside roads, no pattern |
| rotation_deg | Fully random [0.00, 359.99], all unique |
| Building types | At least 2 different types |
| Heights | Range 10–120 m, all unique |
| Dimensions | Wide variation, no repeated values |
| Clearance | Building-road ≥ 5 m; building-building ≥ 5 m |
| Road type | curved ONLY (no straight roads) |

---

## 调用方式

```bash
python skills/organic/scripts/generate_prompt.py --count 5
```

---

## 参考文件

- `references/layout_rules.md` — Detailed rules for curved road and building placement
- `assets/system_prompt.txt` — Complete LLM system prompt for this style
- `assets/example_output.json` — Validated example JSON with 3 curved roads and 12 buildings

---

## 与其他风格的区别

| Feature | Organic | Orthogonal Grid | Slab Row | Cluster |
|---------|---------|-----------------|----------|---------|
| Road type | Curved only | Straight grid | Straight parallel | Straight internal |
| Building arrangement | Informal, alongside roads | Inside grid blocks | Parallel rows | Tight clusters |
| rotation_deg | Fully random (0–360°) | 0.00° (axis-aligned) | ~0° or ~90° | Near cluster_angle |
| Pattern | None | Regular N×M grid | Regular rows | Group-based |
| Road count | 2–3 | N+M roads | 3 roads | N+2–3 roads |
| Setback | Varies 5–15 m | Fixed 4–6 m | Uniform | 5 m minimum |
