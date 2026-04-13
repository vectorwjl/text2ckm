# Building Parameter Reference

All building objects share common positional and material fields, then carry type-specific geometry fields. Every numeric field must be expressed to exactly 2 decimal places (0.01 m resolution). The `rotation_deg` field is mandatory for every building and must be unique across all buildings in the scene.

---

## Common Fields (all building types)

| Field          | Type   | Unit | Description                                                   |
|----------------|--------|------|---------------------------------------------------------------|
| `type`         | string | —    | One of: `rectangular`, `trapezoidal`                         |
| `x`            | float  | m    | World-space X coordinate of the building origin (centroid)    |
| `y`            | float  | m    | World-space Y coordinate of the building origin (centroid)    |
| `height`       | float  | m    | Total vertical height of the building above ground (z=0)      |
| `material`     | string | —    | Surface material; default `"concrete"` if not specified       |
| `rotation_deg` | float  | °    | Clockwise rotation around the vertical axis (Z). Range 0.00–359.99. Must be unique across the entire scene. |

---

## Type: `rectangular`

A simple box-shaped building with a rectangular footprint.

| Field    | Type  | Unit | Description                              |
|----------|-------|------|------------------------------------------|
| `width`  | float | m    | Footprint dimension along the local X axis before rotation |
| `length` | float | m    | Footprint dimension along the local Y axis before rotation |

Geometric interpretation: the footprint occupies [x − width/2, x + width/2] × [y − length/2, y + length/2] in local space before `rotation_deg` is applied. After rotation the bounding box expands accordingly — clearance checks must use the rotated envelope.

---

## Type: `trapezoidal`

A trapezoid footprint with two parallel sides of different lengths.

| Field          | Type  | Unit | Description                                                        |
|----------------|-------|------|--------------------------------------------------------------------|
| `bottom_width` | float | m    | Width of the wider (bottom) edge, centred at y − length/2          |
| `top_width`    | float | m    | Width of the narrower (top) edge, centred at y + length/2          |
| `length`       | float | m    | Depth along the local Y axis                                       |

Geometric interpretation: the four footprint vertices (before rotation) are
`(±bottom_width/2, −length/2)` and `(±top_width/2, +length/2)`.
The origin (x, y) is at the centroid of the trapezoid.
Constraints: `bottom_width >= top_width >= 6.00 m`; typical ratio `top_width / bottom_width` in [0.4, 0.85].

---

## Notes for All Types

1. **Precision**: all float fields must be formatted to exactly 2 decimal places, e.g. `12.50` not `12.5` or `12`.
2. **Height range**: residential 9–30 m (3–10 floors at 3 m/floor); commercial 15–80 m; landmark 80–200 m.
3. **Minimum footprint**: width/length (or equivalent dimension) ≥ 6.00 m for any wing or side.
4. **Clearance**: the axis-aligned bounding box (AABB) of any building — after applying rotation — must maintain at least 5.00 m clearance from every other building AABB and from every road edge.
5. **Same-type diversity**: when multiple buildings of the same type appear in a scene, every building must have individually different geometric dimensions, varying by at least ±2 m on each dimension.
