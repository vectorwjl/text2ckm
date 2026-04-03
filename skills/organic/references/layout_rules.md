# Organic Layout — Detailed Spatial Rules

## Curved Road Design

### Control Point Rules
- Each curved road: 3–5 control points.
- Consecutive control points must be spaced > 20 m apart (for smooth curvature).
- Roads should start and end near or outside the scene edge (|x| or |y| ≥ 60 m).
- Roads wind across the scene — avoid straight-line point sequences.

### Typical Point Patterns
```
3-point road:  [[-85, -25], [-10, 40], [80,  5]]
4-point road:  [[-80,  50], [-30, -20], [30, 55], [85, -15]]
5-point road:  [[-90, 10], [-50, -40], [0, 20], [50, -30], [90, 15]]
```

### Road Width and Material
- Width: 6.00–10.00 m (0.01 precision).
- Material: "marble" (default) or "concrete".
- smooth: true (always for organic style).

---

## Building Placement

### Near-Road Placement
For each building, select a road and compute position:
1. Pick a control point P_k on the chosen road.
2. Compute tangent direction at P_k (approximate from P_{k-1} to P_{k+1}).
3. Perpendicular direction = rotate tangent 90°.
4. Building base position = P_k + rand(8, 20) * perpendicular ± rand(-10, 10) * tangent.
5. Round to 0.01 m precision.

Alternatively: pick any position spread across the scene in an irregular pattern without any formula — the key is NO regular grid and NO regular spacing.

### Building Spacing
- Minimum edge-to-edge distance between any two buildings: ≥ 5.00 m.
- No maximum distance enforced (organic layouts have variable spacing).

---

## Rotation Assignment
- Each building: `rotation_deg = round(random.uniform(0.0, 359.99), 2)`.
- Must be globally unique — check all existing rotation_deg values.
- If collision, add 0.01 until unique.

---

## Height and Dimension Rules
- Heights: pick from [10, 120] m, all unique (differ ≥ 3 m).
- Type mix: at least 2 different building types in the scene.
- Rectangular: width 10–30 m, length 10–40 m (no aspect ratio constraint).
- l_shaped: width1=length1=12–30 m, width2=length2=5–15 m.
- t_shaped: main 15–30 m, wing 8–20 m.
- u_shaped: outer 25–50 m, inner = outer × 0.5–0.6.
- All dimensions unique per building.

---

## Clearance Enforcement
For building at (bx, by) and road with control points:
```
For each road segment between point_k and point_{k+1}:
  distance_to_segment = point_to_segment_distance(bx, by, point_k, point_{k+1})
  required_clearance  = building_half_size + road_width/2 + 5.0
  ASSERT distance_to_segment >= required_clearance
```
Where `building_half_size = max(width, length) / 2` for rectangular.

---

## Example Building Count Distribution
| Total buildings | Type A | Type B | Type C |
|----------------|--------|--------|--------|
| 10             | 5      | 5      | —      |
| 12             | 5      | 4      | 3      |
| 15             | 6      | 5      | 4      |
