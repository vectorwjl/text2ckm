# 技能：组团式场景生成 (Cluster Layout)

## 技能名称
组团式场景生成 (Cluster Layout)

## 职责
Generates scenes with 3–4 distinct, spatially separated building clusters, each occupying a different quadrant or triangular zone of the scene. Each cluster has its own internal road and tightly grouped buildings sharing a common orientation. Clusters are connected to each other by inter-cluster roads.

## 触发关键词
- 组团式
- 组团
- cluster
- 多组团
- 分散组团

If any of these keywords appear in the user's prompt, this skill's system prompt (`assets/system_prompt.txt`) must be loaded instead of the base system prompt.

## 执行步骤

1. **确定组团数量与位置 (Determine cluster count and positions)**
   - Choose number of clusters N ∈ {3, 4}.
   - For N=4: place one cluster per quadrant.
     - NW: center ≈ (−70, 70) ± random(−15, 15)
     - NE: center ≈ (70, 70) ± random(−15, 15)
     - SW: center ≈ (−70, −70) ± random(−15, 15)
     - SE: center ≈ (70, −70) ± random(−15, 15)
   - For N=3: triangle arrangement.
     - Top: center ≈ (0, 80) ± random(−15, 15)
     - Bottom-left: center ≈ (−70, −50) ± random(−15, 15)
     - Bottom-right: center ≈ (70, −50) ± random(−15, 15)
   - Verify that the distance between any two cluster centers is ≥ 50 m (after adding buildings).

2. **为每个组团选择朝向角 (Assign orientation angle per cluster)**
   - Each cluster picks a unique cluster_angle ∈ [0°, 360°).
   - Ensure different clusters have cluster_angle values that are at least 30° apart.

3. **在每个组团内布置建筑 (Place buildings within each cluster)**
   - Place 3–5 buildings per cluster, scattered around the cluster center within radius 15–25 m.
   - Building position: x = center_x + random(−radius, +radius), y = center_y + random(−radius, +radius).
   - Each building: rotation_deg = round(cluster_angle + random(−10, 10), 2).
   - All rotation_deg values must be globally unique across the entire scene.
   - Intra-cluster building gap: 5–15 m edge-to-edge between buildings in the same cluster.

4. **添加组团内部道路 (Add internal road per cluster)**
   - One short straight road per cluster, aligned with cluster_angle, passing through the cluster center.
   - start = [center_x − 20 × cos(radians(cluster_angle)), center_y − 20 × sin(radians(cluster_angle))]
   - end   = [center_x + 20 × cos(radians(cluster_angle)), center_y + 20 × sin(radians(cluster_angle))]
   - Road width: 7–10 m. Material: marble (default).

5. **添加组团间连接道路 (Add inter-cluster connecting roads)**
   - Add 2–3 straight roads connecting cluster centers.
   - For N=4: connect NW-NE, SW-SE, and one diagonal (e.g., NW-SE or NE-SW).
   - For N=3: connect all three cluster centers (3 roads forming a triangle).
   - These are longer straight roads using the cluster center coordinates as start/end.

6. **分配唯一高度与尺寸 (Assign unique heights and dimensions)**
   - Every building must have a unique height (vary by ≥ 3 m between all buildings).
   - Every building of the same type must have unique dimensions (vary ≥ 2 m per dimension).
   - All values to exactly 2 decimal places.

## 输出标准

| Property                  | Requirement                                                               |
|---------------------------|---------------------------------------------------------------------------|
| Cluster count             | 3 or 4 clusters, one per quadrant (for N=4) or triangle (for N=3)        |
| Cluster spacing           | ≥ 50 m clear distance between any two cluster edges                      |
| Intra-cluster building gap| 5–15 m edge-to-edge between buildings within the same cluster             |
| Cluster orientation       | Each cluster has a unique cluster_angle; all its buildings within ±10°    |
| rotation_deg uniqueness   | All rotation_deg values globally unique across entire scene               |
| Internal roads            | 1 per cluster, short straight road aligned with cluster_angle             |
| Inter-cluster roads       | 2–3 connecting roads between cluster centers                              |
| Dimension diversity       | Every building has unique dimensions (same-type vary ≥ 2 m per dimension) |
| Height diversity          | Every building has a unique height                                        |
| Road width                | 7–10 m                                                                    |
| Precision                 | All float fields: exactly 2 decimal places                                |
| Clearance                 | Building-to-building ≥ 5 m; building-to-road edge ≥ 5 m                  |

## 相关文件

- `references/layout_rules.md` — Detailed spatial computation rules
- `assets/system_prompt.txt` — Full self-contained system prompt for this skill
- `assets/example_output.json` — Reference valid JSON output (4 clusters)
- `scripts/generate_prompt.py` — Prompt generator script

## 调用方式

Generate a single random cluster layout prompt:
```
python skills/cluster/scripts/generate_prompt.py --count 1
```

Generate multiple prompts (e.g., 5):
```
python skills/cluster/scripts/generate_prompt.py --count 5
```

The script outputs one Chinese-language prompt per line, suitable for sending to the LLM API with `assets/system_prompt.txt` as the system prompt.
