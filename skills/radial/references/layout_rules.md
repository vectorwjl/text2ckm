# Radial Layout — Detailed Spatial Rules

## 1. Ray Angle Tables

For N rays, the evenly-spaced angles are:

| N | Angles (degrees)                          |
|---|-------------------------------------------|
| 4 | 0, 90, 180, 270                           |
| 5 | 0, 72, 144, 216, 288                      |
| 6 | 0, 60, 120, 180, 240, 300                 |

Formula: `angle_i = i * (360 / N)` for `i ∈ {0, 1, ..., N−1}`

---

## 2. Road Endpoint Computation

Each radial road is a **straight** road from the origin to the computed endpoint.

```
span = map_size / 2 + 20

road_end_x = round(cos(radians(angle_i)) * span, 2)
road_end_y = round(sin(radians(angle_i)) * span, 2)

road = {
  "type": "straight",
  "start": [0.00, 0.00],
  "end": [road_end_x, road_end_y],
  "width": <7.0–10.0>,
  "material": "marble"
}
```

**Pre-computed endpoints for span=120 m (N=6):**

| Angle | end_x   | end_y   |
|-------|---------|---------|
| 0°    | 120.00  | 0.00    |
| 60°   | 60.00   | 103.92  |
| 120°  | -60.00  | 103.92  |
| 180°  | -120.00 | 0.00    |
| 240°  | -60.00  | -103.92 |
| 300°  | 60.00   | -103.92 |

---

## 3. Building Position Along Ray

For a building on ray at angle `a` (degrees), at distance `d` from origin, with perpendicular offset `offset` metres:

```
rad = radians(a)

# Along-ray base position
base_x = round(d * cos(rad), 2)
base_y = round(d * sin(rad), 2)

# Perpendicular direction (rotate ray direction by +90°)
perp_x = round(offset * (-sin(rad)), 2)
perp_y = round(offset *   cos(rad),  2)

# Final building position
x = base_x + perp_x
y = base_y + perp_y
```

- `offset` range: −15 m to +15 m (positive = left of ray direction, negative = right).
- Alternate offset sign between consecutive buildings on the same ray.

---

## 4. Building Rotation

```
rotation_deg = round(angle_i, 2)
```

All buildings on ray `i` use `rotation_deg = angle_i`. Because each ray has a distinct angle, buildings on different rays automatically have different rotation values. Buildings on the **same ray** must be given slightly different rotation values (e.g., vary by ±0.01° increments) so that the global uniqueness constraint is satisfied.

---

## 5. Distance Distribution Along Ray

For `k` buildings on a ray, distribute distances evenly between `dist_min` and `dist_max`:

```
if k == 1:  distances = [dist_min]
if k == 2:  distances = [dist_min, dist_max]
if k == 3:  distances = [dist_min, (dist_min + dist_max) / 2, dist_max]
if k == 4:  distances = [dist_min,
                          dist_min + (dist_max - dist_min) / 3,
                          dist_min + 2 * (dist_max - dist_min) / 3,
                          dist_max]
```

Round each distance to 2 decimal places.

Typical range: `dist_min = 20–35 m`, `dist_max = 60–100 m`.

---

## 6. Clearance Verification

### Building-to-road clearance
For a building on ray `a` at perpendicular offset `offset`:
- The building's distance from the road centerline ≈ `abs(offset)`.
- Required: `abs(offset) > building_half_size + road_width / 2 + 5`
- Where `building_half_size = max(width, length) / 2` for rectangular type.
- Minimum viable offset for a 14 m wide building on a 8.5 m road: `7 + 4.25 + 5 = 16.25 m` → use offset ≥ 17 m, OR use smaller buildings.
- For buildings with width/length ≤ 12 m on roads ≤ 9 m: offset of 12–15 m is typically sufficient.

### Building-to-building clearance
Buildings on the same ray at adjacent distances must have edge-to-edge gap ≥ 5 m:
```
gap = dist_next - dist_prev - (length_prev / 2) - (length_next / 2) >= 5.0
```

Buildings on different rays must also maintain ≥ 5 m edge-to-edge clearance (use AABB after rotation to check).

---

## 7. Optional Curved Connecting Roads

To add cross-connectivity between adjacent rays:
1. Select two adjacent rays i and i+1.
2. Create a curved road with 3–4 control points that arcs between them.
3. Example for rays at 0° and 60° (span=120 m):
   - Points: [[40.00, 0.00], [35.00, 35.00], [30.00, 52.00]]
4. Ensure consecutive points are > 20 m apart.
5. Use `smooth: true`.

---

## 8. Scene Coordinate System

- Origin (0, 0) is the scene center and the hub of all radial roads.
- X-axis: east direction (angle = 0°).
- Y-axis: north direction (angle = 90°).
- Angles increase counter-clockwise.
- All positions in metres, all values to exactly 2 decimal places.
