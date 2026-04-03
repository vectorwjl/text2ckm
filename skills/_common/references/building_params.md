# Building Parameter Reference

All building objects share common positional and material fields, then carry type-specific geometry fields. Every numeric field must be expressed to exactly 2 decimal places (0.01 m resolution). The `rotation_deg` field is mandatory for every building and must be unique across all buildings in the scene.

---

## Common Fields (all building types)

| Field          | Type   | Unit | Description                                                   |
|----------------|--------|------|---------------------------------------------------------------|
| `type`         | string | —    | One of: `rectangular`, `l_shaped`, `t_shaped`, `u_shaped`    |
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

## Type: `l_shaped`

An L-shaped footprint formed by two rectangular wings joined at one corner.

| Field     | Type  | Unit | Description                                         |
|-----------|-------|------|-----------------------------------------------------|
| `width1`  | float | m    | Width of the primary (longer) wing                  |
| `length1` | float | m    | Length of the primary wing                          |
| `width2`  | float | m    | Width of the secondary wing (the short leg of the L)|
| `length2` | float | m    | Length of the secondary wing                        |

Geometric interpretation: the primary wing runs along the local Y axis. The secondary wing branches off one end of the primary wing along the local X axis, creating the characteristic L shape. The origin (x, y) is placed at the inner corner of the L. Constraint: `width2 < length1` and `length2 < width1` are recommended for a visually correct L shape.

---

## Type: `t_shaped`

A T-shaped footprint formed by a main stem and a perpendicular wing (the top bar of the T).

| Field         | Type  | Unit | Description                                              |
|---------------|-------|------|----------------------------------------------------------|
| `main_width`  | float | m    | Width of the main stem (runs along local Y axis)         |
| `main_length` | float | m    | Length of the main stem                                  |
| `wing_width`  | float | m    | Depth (local Y extent) of the perpendicular wing         |
| `wing_length` | float | m    | Span (local X extent) of the perpendicular wing          |

Geometric interpretation: the main stem is centred on the local Y axis. The wing is attached to one end of the stem and extends symmetrically left and right. The origin (x, y) is at the geometric centre of the combined T footprint. Constraint: `wing_length > main_width` for a proper T shape.

---

## Type: `u_shaped`

A U-shaped (courtyard) footprint formed by a rectangular outer shell with a rectangular void cut from one face.

| Field          | Type  | Unit | Description                                          |
|----------------|-------|------|------------------------------------------------------|
| `outer_width`  | float | m    | Overall width of the outer rectangle                 |
| `outer_length` | float | m    | Overall length (depth) of the outer rectangle        |
| `inner_width`  | float | m    | Width of the courtyard void                          |
| `inner_length` | float | m    | Depth of the courtyard void (open toward one face)   |

Geometric interpretation: the outer rectangle is centred at (x, y). The courtyard void is centred on the open face of the U, leaving three walls of thickness (outer_width − inner_width)/2 on the sides and (outer_length − inner_length) at the closed end. Constraints: `inner_width < outer_width`, `inner_length < outer_length`, and wall thickness ≥ 2 m on each side.

---

## Notes for All Types

1. **Precision**: all float fields must be formatted to exactly 2 decimal places, e.g. `12.50` not `12.5` or `12`.
2. **Height range**: residential 9–30 m (3–10 floors at 3 m/floor); commercial 15–80 m; landmark 80–200 m.
3. **Minimum footprint**: width/length (or equivalent dimension) ≥ 6.00 m for any wing or side.
4. **Clearance**: the axis-aligned bounding box (AABB) of any building — after applying rotation — must maintain at least 5.00 m clearance from every other building AABB and from every road edge.
5. **Same-type diversity**: when multiple buildings of the same type appear in a scene, every building must have individually different geometric dimensions, varying by at least ±2 m on each dimension.
