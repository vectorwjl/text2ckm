# 点式散布场景生成 (Point Scatter Layout)

## 技能名称

**点式散布场景生成** — Point Scatter Layout

---

## 职责

Generates scenes with isolated tower/point buildings scattered randomly across the scene, with minimal road infrastructure. Each building stands as a self-contained vertical tower element with a small footprint and tall height, distributed evenly across the full map extent without clustering. This layout models high-density urban districts of standalone skyscrapers or campus environments with widely spaced towers.

---

## 触发关键词

- 点式散布
- point scatter
- 塔楼散点
- 点式
- 独立塔楼
- 散点分布
- tower scatter

---

## 执行步骤

1. **Determine building count and type mix**
   - Total building count: 8–15 buildings
   - Type groups: choose 1–3 distinct building types from {rectangular, l_shaped, u_shaped}
   - Distribute the total count across type groups (each group gets at least 1 building)
   - For point scatter, prefer rectangular and l_shaped; u_shaped is allowed but less common

2. **Generate completely random positions**
   - Position each building independently on a 0.01 m grid
   - Spread positions across the full map bounds (typically ±80–150 m from origin)
   - Do NOT cluster buildings near the center or in one quadrant
   - Use all four quadrants of the map to ensure spatial diversity

3. **Enforce minimum spacing**
   - Minimum distance between any two building centers: ≥20 m
   - For each candidate position, check distance to all already-placed building centers
   - If distance to any existing center < 20 m, reject the position and retry
   - Allow up to 50 retries per building before relaxing constraints

4. **Assign unique rotation_deg**
   - Assign a fully random rotation to each building in range 0.00–359.99°
   - All rotation values must be unique across the entire scene
   - Distribute rotations across the full 0–360° range; avoid clustering near 0°

5. **Assign unique dimensions to each building**
   - Rectangular buildings: small footprint (width 10–20 m, length 10–20 m, near-square)
   - Tall height: 30–100 m per tower
   - l_shaped buildings: width1=length1 15–25 m, width2=length2 5–12 m
   - u_shaped buildings: outer 30–50 m, inner = outer × 0.4–0.6
   - Every building of the same type must have different dimensions (vary by ≥2 m on each dimension)

6. **Add minimal road infrastructure**
   - Add only 1–2 simple straight roads
   - Road patterns: H-shape (2 parallel roads in the same direction) OR + cross (1 horizontal + 1 vertical)
   - Road width: 7–10 m
   - Roads serve as visual reference axes, not as a dense network

7. **Verify clearance constraints**
   - For every road, verify no building center is within road_width/2 + 5 m of the road centerline within the road's extent
   - Building-to-building AABB clearance: ≥5 m edge-to-edge after rotation
   - If any building violates clearance, reposition it (retry up to 50 times)

---

## 输出标准

| Parameter | Requirement |
|-----------|-------------|
| Building count | 8–15 buildings |
| Building spacing | ≥20 m between any two building centers |
| Footprint shape | Small and roughly equal (near-square: width ≈ length for rectangular) |
| Footprint size | width/length 10–20 m for rectangular; 15–25 m for l_shaped wings |
| Height | 30–100 m (tall towers) |
| rotation_deg | Fully random, all different, spread across 0–360° |
| Road count | Maximum 2 roads, simple H or + shape only |
| Road width | 7–10 m |
| Distribution | Buildings spread across the entire map, NOT clustered |
| Material | concrete (default), glass or metal allowed |

---

## 调用方式

```bash
python skills/point_scatter/scripts/generate_prompt.py --count 5
```

This generates 5 random point-scatter-style Chinese scene description prompts, each saved as a `.txt` file in the `text_prompts/` directory.

---

## 参考文件

- `references/layout_rules.md` — Detailed spatial rules and dimension constraints
- `assets/system_prompt.txt` — Complete LLM system prompt for this layout style
- `assets/example_output.json` — Validated example JSON output

---

## 与其他风格的区别

| Feature | Point Scatter | Orthogonal Grid | Slab Row | Perimeter |
|---------|--------------|-----------------|----------|-----------|
| Building spacing | ≥20 m (wide) | 5–15 m | 8–15 m rows | 3 m setback |
| Road density | 1–2 roads only | Dense grid | 2–3 parallel | Perimeter ring |
| rotation_deg | Fully random | 0° (axis-aligned) | ~0° or ~90° | 0° or 90° |
| Footprint | Small, square-like | Varied | Long slab (3:1–5:1) | Large U/L shape |
| Height | 30–100 m (tall) | Varied | Varied | 9–30 m (low-rise) |
| Building count | 8–15 | 4–12 | 6–12 | 2–8 |
