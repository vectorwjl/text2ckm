# Slab Row Layout Rules

Detailed spatial computation rules for generating parallel slab building row scenes. All coordinates use 0.01 m precision.

---

## 1. Row Direction

The fundamental axis of the layout is the **row direction angle** (`row_angle`), measured in degrees clockwise from north (+Y axis):

| row_angle | Slab orientation          | Row runs along  | Rows separated along |
|-----------|---------------------------|-----------------|----------------------|
| 0.00°     | East-west slab (N/S faces)| X axis          | Y axis               |
| 90.00°    | North-south slab (E/W faces)| Y axis        | X axis               |
| 5.00°     | Slight diagonal           | ~X axis         | ~Y axis              |

Rules:
- All buildings within a given row share the same `rotation_deg` = `row_angle`.
- Adjacent rows **may** differ by ±5° to introduce mild visual variety (optional).
- If the user does not specify, use `row_angle = 0.00` for all rows.

---

## 2. Building Dimensions

Slab buildings use `type = "rectangular"` with a pronounced aspect ratio.

| Parameter        | Range         | Notes                                           |
|------------------|---------------|-------------------------------------------------|
| `width`          | 8.00–14.00 m  | Short dimension (perpendicular to row direction)|
| `length`         | width×3–width×5 | Long dimension (along row direction); ≥ 24 m |
| `height`         | 9.00–30.00 m  | Unique per building; vary ≥ 3 m between buildings |
| aspect ratio     | ≥ 3:1         | length / width ≥ 3.0                            |

**Dimension diversity within a row**: every building in the same row must have a **different length** (vary ≥ 5 m between any two buildings in the row). Width may be identical within a row or vary slightly (≥ 2 m).

**Dimension diversity across rows**: buildings in different rows may share similar dimensions (slab row style intentionally produces visual repetition across rows), but heights must remain unique across the **entire** scene.

---

## 3. Row Positions

Rows are centred at the scene origin. For `n_rows` rows with `row_spacing` m between adjacent row centrelines:

```
y_i = (i - (n_rows - 1) / 2.0) * row_spacing    for i = 0, 1, ..., n_rows - 1
```

This formula centres the row array at y = 0 regardless of row count.

Examples:
- n_rows=3, row_spacing=40: y = −40.00, 0.00, +40.00
- n_rows=4, row_spacing=35: y = −52.50, −17.50, +17.50, +52.50

Parameter range: `row_spacing` ∈ [30.00, 50.00] m

> When `row_angle = 90°`, the formula above applies to x rather than y.

---

## 4. Building Positions Within a Row

For `n_bldg` buildings in row i with slab length `L_j` and inter-building gap `g`:

```
total_row_length = sum(L_j for j in 0..n_bldg-1) + (n_bldg - 1) * g

x_j = -total_row_length/2 + sum(L_k for k < j) + j*g + L_j/2
```

This centres the entire row of slabs along the X axis.

Parameter range: `g` (edge-to-edge gap within row) ∈ [8.00, 15.00] m

All buildings in row i: `y = y_i`, `rotation_deg = row_angle`.

---

## 5. Road Layout

### Parallel Roads (2 roads)
- Run parallel to the row direction.
- Positioned at the midpoint between adjacent rows:
  ```
  y_road_i = (y_i + y_{i+1}) / 2    for each adjacent pair i, i+1
  ```
- For 3 rows: 2 parallel roads between rows 0-1 and rows 1-2.
- For 4 rows: 3 possible parallel roads — select the 2 that flank the central rows.
- Road extent (start/end): extends from −(scene_half + 20) to +(scene_half + 20) along X axis.

### Cross Road (1 road)
- Runs perpendicular to the row direction.
- Positioned at x = 0 (or another central position).
- Road extent: from y_0 − (max_slab_length/2 + 20) to y_{n_rows-1} + (max_slab_length/2 + 20).

### Road Parameters
- Width: 6.00–9.00 m
- Material: `"marble"` (default)
- Clearance from building edge: ≥ 5.00 m

---

## 6. Clearance Verification

For each building pair (i, j):
- Compute AABB of each building (before rotation: [x−w/2, x+w/2] × [y−l/2, y+l/2]).
- When `rotation_deg = 0.00`, AABB is exact; otherwise compute rotated corners and take hull.
- Edge-to-edge distance between AABBs ≥ 5.00 m.

For each building-road pair:
- Road edge at: road_centreline ± road_width/2
- Building face must be ≥ 5.00 m from road edge.

Row spacing of 30–50 m combined with widths of 8–14 m and heights of 9–30 m naturally satisfies the 5 m building-to-road clearance if setback is accounted for when computing road positions.

---

## 7. Coordinate Example

Parameters: n_rows=3, row_spacing=40.00, n_bldg=3, g=10.00, row_angle=0.00

Row positions: y = −40.00, 0.00, +40.00

Row 0 (y=−40.00): lengths = [30.00, 35.00, 40.00]
  total = 30+35+40 + 2*10 = 125.00
  x_0 = −62.50 + 0 + 15.00 = −47.50
  x_1 = −62.50 + 30 + 10 + 17.50 = −5.00
  x_2 = −62.50 + 30+35 + 20 + 20.00 = +42.50

Parallel roads:
  y_road_0 = (−40 + 0) / 2 = −20.00
  y_road_1 = (0 + 40) / 2  = +20.00

Cross road:
  x = 0.00, y from −80.00 to +80.00

---

## 8. Validation Checklist

- [ ] Every building has `type = "rectangular"`
- [ ] Every building has `length / width >= 3.0`
- [ ] All buildings in the same row have identical `rotation_deg`
- [ ] Heights are unique across all buildings in the scene
- [ ] Within each row, every building has a different `length` (differ ≥ 5 m)
- [ ] Row spacing is 30–50 m
- [ ] Intra-row gap is 8–15 m (edge-to-edge)
- [ ] 2 parallel roads and 1 cross road present
- [ ] All road start ≠ end
- [ ] Building-to-building clearance ≥ 5.00 m
- [ ] Building-to-road clearance ≥ 5.00 m
- [ ] All float values have exactly 2 decimal places
