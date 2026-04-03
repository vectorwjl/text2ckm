# Global Scene Generation Rules

These rules apply to every scene regardless of layout style. The AI must follow all of them without exception.

---

## 1. Numeric Precision

**All** coordinate, dimension, and rotation values must be formatted to exactly **2 decimal places** (0.01 m resolution).

- Correct: `12.50`, `0.00`, `359.99`, `-47.30`
- Wrong: `12.5`, `12`, `12.500`, `-47.3`

This applies to: `x`, `y`, `z`, `width`, `length`, `height`, `width1`, `length1`, `width2`, `length2`, `main_width`, `main_length`, `wing_width`, `wing_length`, `outer_width`, `outer_length`, `inner_width`, `inner_length`, `rotation_deg`, `start`, `end`, `points`, `rx_height`, `aoi_half_size_m`, `map_size_m`, and all TX/RX/RT coordinate fields.

**NEVER use plain integers** for any numeric scene field.

---

## 2. Rotation Uniqueness

- Every building object **must** include the `rotation_deg` field.
- The value range is **0.00–359.99** (degrees, clockwise from north/+Y axis).
- **All `rotation_deg` values must be unique across the entire scene.** No two buildings may share the same rotation value, even if the difference is less than 0.01°.
- Suggestion: distribute rotations across the full range or use small increments (e.g., 0.00, 15.30, 27.80, ...) rather than clustering near 0°.

---

## 3. Dimension Diversity

For any group of **N buildings of the same type** in the same scene:
- Every building must have **individually different** geometric dimensions.
- Each dimension (width, length, height, etc.) must vary by **at least ±2 m** from every other building of the same type.
- This rule prevents visually repetitive scenes and ensures RF simulation diversity.

Example (rectangular): if building A has width=12.00, length=20.00, height=18.00, then building B must differ by ≥2 m on at least one dimension — e.g., width=14.50, length=25.00, height=22.00.

---

## 4. Spatial Clearance

Two clearance constraints must both be satisfied simultaneously:

### 4a. Building-to-Building Clearance
The **minimum edge-to-edge distance** between any two building footprints (using their axis-aligned bounding boxes after rotation) must be **≥ 5.00 m**.

### 4b. Building-to-Road Clearance
The **minimum distance** from any building footprint edge to the nearest road edge (road centreline ± width/2) must be **≥ 5.00 m**.

If a placement would violate either constraint, the building must be repositioned or the road must be rerouted before output.

---

## 5. Road Validity

- **Straight roads**: `start` and `end` coordinates must be distinct (not equal). Minimum recommended length: 10.00 m.
- **Curved roads**: the `points` array must contain **at least 2 entries**. Consecutive control points must be spaced **more than 20.00 m apart** to produce a non-degenerate curve.
- A curved road with `smooth: false` is rendered as a piecewise polyline; with `smooth: true` a Catmull-Rom spline is applied.
- Roads may intersect each other (junctions are handled by the Blender script).
- Roads must not pass through any building footprint.

---

## 6. TX / RX / RT Inclusion Policy

- Only include `tx`, `rx`, or `rt` objects in the JSON output when the user **explicitly mentions** the corresponding parameter in their prompt.
- **Never invent default values** for TX power, frequency, height, array configuration, AOI size, or map size.
- If the user says "add a transmitter at (10, 20) at 5 GHz", include `tx` with `x`, `y`, `frequency_ghz` — but do NOT add `power_dbm`, `z`, or `array` unless also stated.
- If the user does not mention any TX/RX/RT parameters at all, omit those objects entirely.

---

## 7. Material Defaults

- Building material default: `"concrete"` (used when user does not specify).
- Road material default: `"marble"` (used when user does not specify).
- Material must be one of the five valid keys: `concrete`, `marble`, `metal`, `wood`, `glass`.
- For `frequency_ghz > 10`, default building material to `"concrete"` for simulation accuracy.

---

## 8. Scene Completeness

- A scene must have at least **1 building** and at least **1 road**.
- For random or open-ended prompts (no explicit count), generate a **complex road network** with at least **2 roads at different angles** OR **1 curved road** plus **1 straight road**.
- Building count for open-ended prompts: **4–8 buildings** unless the user specifies.
- Every building must have a non-zero footprint (all dimensions ≥ 6.00 m).

---

## Summary Checklist

Before emitting the final JSON, verify:

- [ ] All numeric values have exactly 2 decimal places
- [ ] All `rotation_deg` values are present and unique
- [ ] Same-type buildings have dimension differences ≥ 2 m
- [ ] No building-building clearance violation (≥ 5.00 m)
- [ ] No building-road clearance violation (≥ 5.00 m)
- [ ] Straight roads have distinct start ≠ end
- [ ] Curved roads have ≥ 2 points, each pair > 20.00 m apart
- [ ] TX/RX/RT only present if explicitly mentioned
- [ ] Materials are valid keys
- [ ] Output is pure JSON with no markdown fences or prose
