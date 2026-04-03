# Perimeter/Courtyard Layout Rules — Detailed Reference

This document defines the exact spatial, dimensional, and structural rules for the Perimeter (周边式) layout style. All values use 0.01 m precision. These rules are consumed by `scripts/generate_prompt.py` and by the LLM via `assets/system_prompt.txt`.

---

## 1. Block Layout Geometry

### Row layout (2 or 3 blocks)

Block centers are positioned along the X axis:

```
block_center_x[k] = k * (block_size + road_width)
    for k = 0, 1, ..., N-1

Then shift all centers to be symmetric about origin:
offset = (N-1) * (block_size + road_width) / 2
block_center_x[k] = k * (block_size + road_width) - offset
block_center_y[k] = 0.00
```

Example with N=2, block_size=70.00, road_width=9.00:
- Block 1 center: (−39.50, 0.00)
- Block 2 center: (+39.50, 0.00)
- Shared road centerline at x = 0.00

Example with N=3, block_size=65.00, road_width=8.00:
- Block 1 center: (−73.00, 0.00)
- Block 2 center: (0.00, 0.00)
- Block 3 center: (+73.00, 0.00)

### 2×2 grid layout (4 blocks)

```
half_pitch = block_size / 2 + road_width / 2
block_centers = [
    (−half_pitch, +half_pitch),  # top-left
    (+half_pitch, +half_pitch),  # top-right
    (−half_pitch, −half_pitch),  # bottom-left
    (+half_pitch, −half_pitch),  # bottom-right
]
```

Example with block_size=80.00, road_width=9.00:
- half_pitch = 44.50
- Centers: (−44.50, +44.50), (+44.50, +44.50), (−44.50, −44.50), (+44.50, −44.50)

---

## 2. Per-Block Building Options

### Option A: u_shaped (single building, wraps three sides)

- Building position: (block_center_x, block_center_y)
- Setback from block edge to outer wall: setback = 3.00–5.00 m
- outer_width  = block_size − 2 × setback (round to 2 decimals)
- outer_length = block_size − 2 × setback (or slightly different for rectangular courtyard)
- inner_width  = outer_width  × factor,  factor ∈ [0.50, 0.65]
- inner_length = outer_length × factor
- Wall thickness constraint: (outer_width − inner_width) / 2 ≥ 2 m
- Height: unique per building; range 12.00–50.00 m
- rotation_deg: 0.00 (default; use 0.01, 0.02 … for uniqueness across multiple buildings)

Minimum clearance check:
  distance from outer wall edge to road centerline = block_size/2 − setback − outer_width/2
  This must be ≥ 0 (building does not extend to road). Verify: setback ≥ road_width/2 + 3.00.

### Option B: l_shaped combo (2 buildings per block, opposite corners)

For each pair of l_shaped buildings at opposite diagonal corners of the block:

Building 1 (e.g., top-left corner, covers top side + left side):
  x = block_center_x − (block_size/4)
  y = block_center_y + (block_size/4)
  width1 = block_size/2 − setback (covers the left wall)
  length1 = block_size − 2×setback (full block depth)
  width2 = block_size − 2×setback (covers the top wall)
  length2 = block_size/2 − setback

Building 2 (bottom-right corner, covers bottom side + right side):
  x = block_center_x + (block_size/4)
  y = block_center_y − (block_size/4)
  Dimensions mirrored; rotation_deg adjusted (e.g., 90.00 + small delta for uniqueness)

### Option C: rectangular combo (3 buildings on 3 sides, bottom open)

Left wall:
  x = block_center_x − (outer_width/2 + slab_width/2)  [outside inner courtyard]
  y = block_center_y
  width = slab_width (5–10 m)
  length = outer_length

Right wall: mirror of left wall (x offset positive)

Back wall (top):
  x = block_center_x
  y = block_center_y + (outer_length/2 + slab_width/2)
  width = outer_width + 2×slab_width
  length = slab_width

---

## 3. Road Layout

### Row layout roads (N blocks in a row)

**Transverse roads (perpendicular to row axis, i.e., north-south orientation):**
- Left outer road:  x = block_centers[0].x − block_size/2 − road_width/2, y spans ±(block_size/2 + road_width)
- Right outer road: x = block_centers[-1].x + block_size/2 + road_width/2
- Between-block roads (N−1): x = (block_centers[k].x + block_centers[k+1].x) / 2

**Longitudinal roads (parallel to row axis, i.e., east-west orientation):**
- Top road: y = block_size/2 + road_width/2
- Bottom road: y = −(block_size/2 + road_width/2)

All roads: type = "straight", width = road_width, material = "marble"

### 2×2 grid roads

- Left outer:   x = −half_pitch − block_size/2 − road_width/2
- Right outer:  x = +half_pitch + block_size/2 + road_width/2
- Center vertical: x = 0.00
- Top outer:    y = +half_pitch + block_size/2 + road_width/2
- Bottom outer: y = −half_pitch − block_size/2 − road_width/2
- Center horizontal: y = 0.00

All roads span the full cluster width/height plus road_width margin on each end.

---

## 4. Setback Calculation

Setback = minimum distance from building outer wall edge to road centerline.

For a u_shaped building at block center with outer_width = block_size − 2×s:
  building outer edge in X = block_center_x ± outer_width/2 = block_center_x ± (block_size/2 − s)
  nearest road centerline in X = block_center_x ± block_size/2 ± road_width/2 ∓ road_width/2
                                = block_center_x ± block_size/2 (block edge)
  distance from building edge to block edge = s

Minimum setback requirement: s ≥ road_width/2 + 3.00 m
  If road_width = 9.00 m → minimum s = 4.50 + 3.00 = 7.50 m
  If road_width = 7.00 m → minimum s = 3.50 + 3.00 = 6.50 m

---

## 5. Height and Dimension Uniqueness

- Each building across all blocks must have a unique height (differ by ≥ 2 m)
- Within the same building type: all geometric dimensions must differ by ≥ 2 m
- Height range guidelines:
  - Low-rise residential: 9.00–18.00 m (3–6 floors)
  - Mid-rise residential: 18.00–30.00 m (6–10 floors)
  - Commercial perimeter: 15.00–50.00 m

---

## 6. rotation_deg for Perimeter Buildings

- Perimeter buildings are axis-aligned: use 0.00° or 90.00° base rotations
- Global uniqueness rule still applies: no two buildings may share the same rotation_deg
- Strategy for uniqueness when N buildings all nominally face the same direction:
  Use small sequential offsets: 0.00, 0.01, 0.02, 0.03 …
  Or: 0.00, 90.00, 180.00, 270.00 for different block orientations

---

## 7. Clearance Summary

| Constraint | Minimum | Applies to |
|-----------|---------|------------|
| Building-to-building AABB | 5.00 m | All pairs |
| Building outer wall to road centerline | road_width/2 + 3.00 m | All perimeter buildings |
| Inner courtyard | No objects | Building void / open space |
| Road-to-road | N/A (intersections allowed) | Road network |

---

## 8. Validation Checklist (pre-output)

- [ ] Block count: 2–4
- [ ] Block size: 60.00–100.00 m per side
- [ ] Each block has buildings wrapping ≥ 3 sides
- [ ] Inner courtyard is completely empty (no buildings, no roads)
- [ ] All rotation_deg: 0.00 or 90.00 base, all globally unique
- [ ] Setback: ≥ road_width/2 + 3.00 m for all buildings
- [ ] Perimeter roads cover all outer and inter-block gaps
- [ ] All heights unique across buildings (differ by ≥ 2 m)
- [ ] All numeric fields: exactly 2 decimal places
- [ ] Materials: valid keys only
