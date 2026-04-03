# Orthogonal Grid Layout Rules

Detailed spatial computation rules for generating axis-aligned street grid scenes. All coordinates use 0.01 m precision.

---

## 1. Road Network Definition

### South-North Roads (vertical, aligned to Y axis)

- Count: N = 2 or 3
- Longitudinal spacing: `long_spacing` ∈ [50.00, 70.00] m
- Road x-positions: `x_k = k × long_spacing` for k = −⌊(N−1)/2⌋, ..., +⌊(N−1)/2⌋

  Examples:
  - N=2: x = −long_spacing/2, +long_spacing/2  (e.g., −30.00, +30.00 for spacing=60)
  - N=3: x = −long_spacing, 0, +long_spacing    (e.g., −60.00, 0.00, +60.00 for spacing=60)

- Road direction: south-north (start = [x, y_min], end = [x, y_max])
- Start/end Y extent: ±(map_half + 20.00), where map_half = total map extent / 2

### East-West Roads (horizontal, aligned to X axis)

- Count: M = 2 or 3
- Transverse spacing: `trans_spacing` ∈ [45.00, 65.00] m
- Road y-positions: `y_m = m × trans_spacing` for m = −⌊(M−1)/2⌋, ..., +⌊(M−1)/2⌋

  Examples:
  - M=2: y = −trans_spacing/2, +trans_spacing/2
  - M=3: y = −trans_spacing, 0, +trans_spacing

- Road direction: east-west (start = [x_min, y], end = [x_max, y])
- Start/end X extent: ±(map_half + 20.00)

### Road Width
- Uniform or per-road: `road_width` ∈ [7.00, 10.00] m
- Material: `"marble"` (default)

---

## 2. Block Identification

Total blocks = (N − 1) × (M − 1)

Each block is indexed by (k, m) and bounded by:
- x ∈ [x_k, x_{k+1}]  where x_k and x_{k+1} are adjacent south-north road centrelines
- y ∈ [y_m, y_{m+1}]  where y_m and y_{m+1} are adjacent east-west road centrelines

Block dimensions:
- block_width  = x_{k+1} − x_k = long_spacing
- block_height = y_{m+1} − y_m = trans_spacing

Block centre:
- block_cx = (x_k + x_{k+1}) / 2
- block_cy = (y_m + y_{m+1}) / 2

---

## 3. Buildable Area Within Each Block

The buildable envelope after subtracting road half-widths and setback:

- x_min_build = x_k   + road_width/2 + setback
- x_max_build = x_{k+1} − road_width/2 − setback
- y_min_build = y_m   + road_width/2 + setback
- y_max_build = y_{m+1} − road_width/2 − setback

Where `setback` = 4.00–6.00 m (distance from road edge to nearest building face).

Building placement constraint:
- bldg_x − building_width/2   ≥ x_min_build
- bldg_x + building_width/2   ≤ x_max_build
- bldg_y − building_length/2  ≥ y_min_build
- bldg_y + building_length/2  ≤ y_max_build

---

## 4. Building Arrangement Within a Block

### Option A: Row along X axis (2 buildings side by side)
```
  gap/2      bldg_A       gap      bldg_B      gap/2
|-------|[============]|-------|[============]|-------|
        x_min_build                         x_max_build
```
- bldg_A_x = x_min_build + bldg_A_width/2
- bldg_B_x = x_max_build − bldg_B_width/2
- Gap between A and B: bldg_B_x − bldg_B_width/2 − (bldg_A_x + bldg_A_width/2) ≥ 2.00 m
- Both buildings centred at block_cy in the Y direction

### Option B: 2×2 grid (4 buildings)
- 2 buildings per row, 2 rows, filling the block quadrants
- Row Y positions: block_cy ± (bldg_length/2 + gap/2)
- Column X positions: block_cx ± (bldg_width/2 + gap/2)
- Intra-block gap: 2–5 m edge-to-edge

### Option C: Single column (2–3 buildings stacked along Y)
- All buildings at block_cx
- Y positions spaced by (bldg_length + gap)

---

## 5. Building Properties

- **rotation_deg**: ALWAYS 0.00 for every building in orthogonal grid layout
- **type**: preferably `rectangular` for this style; other types permitted
- **height**: unique per building across the entire scene (vary ≥ 3 m); range 9.00–60.00 m
- **dimensions**: every building of the same type must differ by ≥ 3 m per dimension
- **material**: default `"concrete"`; may vary per block (glass, metal, etc.)

---

## 6. Coordinate Summary Example

Parameters: N=2, M=2, long_spacing=60.00, trans_spacing=50.00, road_width=8.00, setback=5.00, map_half=130.00

South-north roads:
  x = −30.00 (start=[−30.00, −150.00], end=[−30.00, 150.00])
  x = +30.00 (start=[+30.00, −150.00], end=[+30.00, 150.00])

East-west roads:
  y = −25.00 (start=[−150.00, −25.00], end=[150.00, −25.00])
  y = +25.00 (start=[−150.00, +25.00], end=[150.00, +25.00])

Block (0,0): x ∈ [−30.00, +30.00], y ∈ [−25.00, +25.00]
  block_cx = 0.00, block_cy = 0.00
  buildable x: [−30+4+5, +30−4−5] = [−21.00, +21.00]
  buildable y: [−25+4+5, +25−4−5] = [−16.00, +16.00]

---

## 7. Materials

- Roads: `"marble"` (default)
- Buildings: `"concrete"` (default); may vary by block for visual diversity
- Apply frequency fallback (all concrete) when frequency_ghz > 10

---

## 8. Validation Checklist

- [ ] All road start/end coordinates are distinct
- [ ] All buildings have rotation_deg = 0.00
- [ ] All buildings are within their block's buildable envelope
- [ ] Edge-to-edge clearance ≥ 5.00 m between all building pairs
- [ ] Edge-to-road clearance ≥ 5.00 m for all buildings
- [ ] All rotation_deg values are present (0.00 for all)
- [ ] Heights and dimensions are unique across same-type buildings
- [ ] All values have exactly 2 decimal places
