# Point Scatter Layout Rules — Detailed Reference

This document defines the exact spatial, dimensional, and structural rules that govern the Point Scatter (点式散布) layout style. All values use 0.01 m precision. These rules are consumed by `scripts/generate_prompt.py` and by the LLM via `assets/system_prompt.txt`.

---

## 1. Map Bounds

- Scene origin: (0.00, 0.00)
- Typical map bounds: ±80 m to ±150 m from origin in both X and Y
- Default for point scatter scenes: ±120 m (total 240 m × 240 m)
- Building positions must stay within bounds so that the building footprint AABB does not extend beyond the map edge
- Allow a margin of at least half the building's largest dimension from the map boundary

---

## 2. Position Generation Algorithm

For each building i (i = 0, 1, …, N−1):

```
max_retries = 50
for attempt in range(max_retries):
    x = random.uniform(-bound + margin, bound - margin)
    y = random.uniform(-bound + margin, bound - margin)
    x = round(x, 2)
    y = round(y, 2)
    min_dist = min(distance(x, y, bj.x, bj.y) for all previously placed buildings bj)
    if min_dist >= 20.00 (or no buildings placed yet):
        accept (x, y) and continue to next building
reject if all retries exhausted → relax bound to ±150 m and retry
```

- Distance metric: Euclidean distance between building centers
- All four map quadrants must be used; after placing 4 buildings, ensure at least one in each quadrant
- Buildings should be spread across the full spatial extent, NOT concentrated in the center

---

## 3. Building Dimensions by Type

### 3a. rectangular (preferred for point scatter)

| Parameter | Range | Notes |
|-----------|-------|-------|
| width | 10.00–20.00 m | Near-square footprint |
| length | 10.00–20.00 m | Near-square: |width − length| ≤ 5 m preferred |
| height | 30.00–100.00 m | Tall tower characteristic |
| material | concrete (default), glass, metal | |

Uniqueness: every rectangular building must have a distinct (width, length, height) triple. Width and length must differ by ≥2 m from every other rectangular building.

### 3b. l_shaped

| Parameter | Range | Notes |
|-----------|-------|-------|
| width1 | 15.00–25.00 m | Primary wing width |
| length1 | 15.00–25.00 m | Primary wing length (near-square wing) |
| width2 | 5.00–12.00 m | Secondary wing width (short leg) |
| length2 | 5.00–12.00 m | Secondary wing length |
| height | 30.00–90.00 m | Tall |
| material | concrete (default), glass, metal | |

Constraints: width2 < length1 and length2 < width1 (structural validity).
Uniqueness: all four dimension parameters must differ by ≥2 m across l_shaped buildings.

### 3c. u_shaped (optional, less common in point scatter)

| Parameter | Range | Notes |
|-----------|-------|-------|
| outer_width | 30.00–50.00 m | |
| outer_length | 30.00–50.00 m | |
| inner_width | outer_width × 0.40–0.60 | Must satisfy inner_width < outer_width |
| inner_length | outer_length × 0.40–0.60 | Must satisfy inner_length < outer_length |
| height | 30.00–80.00 m | |
| material | concrete (default) | |

Wall thickness constraint: (outer_width − inner_width) / 2 ≥ 2 m and (outer_length − inner_length) ≥ 2 m.

---

## 4. Rotation Assignment

- Range: 0.00–359.99° (clockwise from +Y axis)
- All rotation_deg values must be globally unique across the entire scene
- Distribution strategy: divide the 0–360° range into N equal slots, then add a small random offset within each slot

  ```
  slot_size = 360.0 / N
  for i in range(N):
      base = i * slot_size
      offset = random.uniform(0, slot_size - 0.01)
      rotation = round((base + offset) % 360.0, 2)
  ```

- This ensures rotations are spread across the full circle, not clustered near 0°
- Shuffle the resulting list before assigning to buildings to avoid positional bias

---

## 5. Road Layout

Point scatter uses minimal roads. Only 1–2 straight roads are permitted.

### Pattern A: + Cross (十字形)
- 1 horizontal road: start = (−bound, 0.00), end = (bound, 0.00), passes through origin
- 1 vertical road: start = (0.00, −bound), end = (0.00, bound), passes through origin
- Two roads intersect at the origin

### Pattern B: H-Shape (H形, 2 parallel roads)
- Road 1: start = (−bound, y_offset), end = (bound, y_offset) for some y_offset ≠ 0
- Road 2: start = (−bound, −y_offset), end = (bound, −y_offset)
- Both roads are horizontal and parallel, symmetric about y = 0
- y_offset: typically 30–60 m

### Road parameters
| Parameter | Value |
|-----------|-------|
| Road count | 1–2 |
| Width | 7.00–10.00 m |
| Material | marble (default) |
| Type | straight only |

---

## 6. Road-Building Clearance Check

For each straight road with centerline from `start` to `end` and half-width `w/2`:

For each building at position (bx, by) with footprint radius `r` (= half of max(width, length)):

1. Project (bx, by) onto the road centerline segment
2. If the projected point lies within the segment extent:
   - perpendicular_distance = distance from (bx, by) to centerline
   - required_clearance = w/2 + 5.00 m
   - If perpendicular_distance < required_clearance + r: VIOLATION → reposition building
3. If the projection falls outside the segment extent, check distance to nearest endpoint instead

Simplified approximation (acceptable for generation): treat building as a point and require:
```
distance_to_road_centerline ≥ road_width / 2 + 5.00 + building_half_footprint
```
where `building_half_footprint = max(width, length) / 2` for rectangular.

---

## 7. Global Rules (apply to all scene types)

1. All numeric values: exactly 2 decimal places (e.g., `15.00`, not `15` or `15.0`)
2. rotation_deg: present for every building, unique across all buildings
3. Same-type buildings: dimension differences ≥ 2 m on each geometric parameter
4. Building-to-building AABB clearance: ≥ 5.00 m edge-to-edge after rotation
5. Building-to-road clearance: ≥ 5.00 m from any building edge to nearest road edge
6. Material values: exactly one of {concrete, marble, metal, wood, glass}
7. Straight road endpoints: start ≠ end; minimum length 10.00 m

---

## 8. Validation Checklist (pre-output)

- [ ] Building count: 8–15
- [ ] All building centers at unique (x, y) positions with ≥20 m spacing
- [ ] All positions within map bounds (±120 m or configured bound)
- [ ] All rotation_deg values unique and spread across 0–360°
- [ ] All buildings of the same type have different dimensions (≥2 m variation)
- [ ] Road count: ≤ 2 straight roads
- [ ] Road pattern: + or H only
- [ ] All buildings have clearance ≥5 m from road edges
- [ ] All numeric fields: exactly 2 decimal places
- [ ] Materials: valid keys only
