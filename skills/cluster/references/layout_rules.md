# Cluster Layout — Detailed Spatial Rules

## Cluster Center Positions

### 4 clusters (quadrant layout)
| Cluster | Base center     | Random offset    |
|---------|-----------------|------------------|
| NW      | (−70, +70)      | ±random(0, 15)   |
| NE      | (+70, +70)      | ±random(0, 15)   |
| SW      | (−70, −70)      | ±random(0, 15)   |
| SE      | (+70, −70)      | ±random(0, 15)   |

### 3 clusters (triangle layout)
| Cluster      | Base center  |
|--------------|-------------|
| Top          | (0, +80)    |
| Bottom-left  | (−70, −50)  |
| Bottom-right | (+70, −50)  |

Verify inter-cluster distance: distance(center_a, center_b) ≥ 50 m (post building-placement edge distance).

---

## Intra-Cluster Building Placement

1. Pick `cluster_radius` ∈ [15, 25] m per cluster.
2. For each building i in the cluster:
   - `x_i = center_x + round(random.uniform(-cluster_radius, cluster_radius), 2)`
   - `y_i = center_y + round(random.uniform(-cluster_radius, cluster_radius), 2)`
3. Ensure edge-to-edge gap ≥ 5 m between buildings within the cluster.
4. All positions at 0.01 m precision.

---

## Cluster Orientation Angle

Each cluster picks a `cluster_angle` ∈ [0°, 360°).
- Different clusters must have `cluster_angle` values ≥ 30° apart.
- All buildings in the cluster: `rotation_deg = round(cluster_angle + random.uniform(-10, +10), 2)`.
- All `rotation_deg` values must be globally unique across the entire scene (add 0.01 offsets if needed).

---

## Internal Road (1 per cluster)

Aligned with `cluster_angle`, passing through the cluster center:
```
start_x = round(center_x - 20 * cos(radians(cluster_angle)), 2)
start_y = round(center_y - 20 * sin(radians(cluster_angle)), 2)
end_x   = round(center_x + 20 * cos(radians(cluster_angle)), 2)
end_y   = round(center_y + 20 * sin(radians(cluster_angle)), 2)
```
Road width: 7–10 m. Material: "marble".

---

## Inter-Cluster Connecting Roads

Straight roads connecting cluster centers:
- For 4 clusters: connect NW↔NE, SW↔SE, and one diagonal (NW↔SE or NE↔SW). = 3 roads.
- For 3 clusters: connect all 3 pairs (triangle). = 3 roads.
- `start = [center_x_a, center_y_a]`, `end = [center_x_b, center_y_b]`.
- Road width: 8–12 m (slightly wider than internal roads). Material: "marble".

---

## Dimension and Height Rules

- Every building: unique height (differ ≥ 3 m from all others in scene).
- Same-type buildings: unique dimensions (differ ≥ 2 m per geometric dimension).
- All float values: exactly 2 decimal places.

---

## Clearance Rules

| Pair                    | Minimum clearance |
|-------------------------|-------------------|
| Building–building       | ≥ 5.00 m (edge to edge) |
| Building–road edge      | ≥ 5.00 m          |
| Cluster–cluster edge    | ≥ 50.00 m         |
