# Road Parameter Reference

Roads define the navigable network in the scene. Two road subtypes are supported: `straight` and `curved`. All coordinate values use 0.01 m precision. Road thickness (the vertical extent extruded downward into the ground mesh in the Blender script) is always **0.25 m** and is hardcoded in `blender_script.py` — it must never appear in the JSON output.

---

## Common Fields (all road types)

| Field      | Type   | Unit | Description                                              |
|------------|--------|------|----------------------------------------------------------|
| `type`     | string | —    | `"straight"` or `"curved"`                              |
| `width`    | float  | m    | Carriageway width (kerb-to-kerb). Typical: 6.00–12.00 m |
| `material` | string | —    | Surface material; default `"marble"` if not specified    |

---

## Type: `straight`

A road segment defined by two endpoint coordinates. The road is rendered as a flat rectangular mesh between `start` and `end`, extruded 0.25 m into the ground.

| Field   | Type        | Unit | Description                                           |
|---------|-------------|------|-------------------------------------------------------|
| `start` | [float, float] | m | [x, y] world-space coordinate of the road start point |
| `end`   | [float, float] | m | [x, y] world-space coordinate of the road end point   |

**Validity constraint**: `start` ≠ `end` (the two points must be distinct). Recommended minimum segment length: 10.00 m.

**Example**:
```json
{
  "type": "straight",
  "start": [-120.00, 0.00],
  "end":   [ 120.00, 0.00],
  "width": 8.00,
  "material": "marble"
}
```

---

## Type: `curved`

A road segment defined by a polyline of control points. The Blender script optionally applies a Catmull-Rom spline smooth pass when `smooth` is `true`, producing a visually smooth curve through the provided waypoints.

| Field    | Type                    | Unit | Description                                                           |
|----------|-------------------------|------|-----------------------------------------------------------------------|
| `points` | [[float,float], ...]    | m    | Ordered list of [x, y] waypoints. Minimum **2 points** required.      |
| `smooth` | bool                    | —    | `true` → apply spline smoothing; `false` → piecewise-linear polyline |

**Validity constraints**:
- Must contain at least **2 points**.
- Consecutive points should be spaced **more than 20.00 m apart** to ensure the generated curve is geometrically meaningful and non-degenerate.
- For visual quality, 3–6 points are recommended for a smooth bend.

**Example**:
```json
{
  "type": "curved",
  "points": [
    [-80.00, -60.00],
    [-30.00,  10.00],
    [ 40.00,  50.00],
    [ 90.00,  30.00]
  ],
  "width": 7.00,
  "smooth": true,
  "material": "marble"
}
```

---

## Road Thickness (Blender hardcoded)

The vertical thickness of every road mesh is **0.25 m**, extruded downward from z = 0. This value is:
- Hardcoded inside `blender_script.py`.
- Identical for all road types and all materials.
- **Never included** in the JSON output — the parser in `blender_script.py` ignores any `thickness` field if accidentally present.

---

## Clearance Rules

- Road edges must maintain at least **5.00 m** clearance from the axis-aligned bounding box of every building.
- Two roads may intersect (e.g., at a junction) — intersection handling is managed by the Blender script's boolean union operation.
- A road must not pass through any building footprint.

---

## Typical Width Guidelines

| Road class              | Suggested width |
|-------------------------|-----------------|
| Residential alley       | 4.00–6.00 m     |
| Local collector road    | 6.00–8.00 m     |
| Urban arterial          | 8.00–12.00 m    |
| Dual-carriageway (each) | 10.00–14.00 m   |
