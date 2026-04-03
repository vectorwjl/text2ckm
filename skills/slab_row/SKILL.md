# 技能：行列式场景生成 (Slab Row Layout)

## 技能名称
行列式场景生成 (Slab Row Layout)

## 职责
Generates urban scenes composed of elongated slab-type residential or commercial buildings arranged in parallel rows. The layout mimics classic mid-20th century urban planning where identical or near-identical rectangular slabs are spaced evenly to maximise natural light and ventilation. Roads run parallel to the rows and a single cross road provides perpendicular access.

## 触发关键词
- 行列式
- 板式行列
- slab row
- 板楼行列
- 兵营式布局
- 行列布局
- 平行板式

If any of these keywords appear in the user's prompt, this skill's system prompt (`assets/system_prompt.txt`) must be loaded instead of the base system prompt.

## 执行步骤

1. **决定行数与每行楼栋数 (Decide number of rows and buildings per row)**
   - Number of rows: 3 or 4
   - Buildings per row: 2 or 3
   - Row direction angle: typically 0° (east-west slabs, north/south facing) or 90° (north-south slabs); rarely ±5° for slight rotation variety

2. **确定行方向角度 (Determine row direction angle)**
   - Choose `row_angle` ∈ {0.00, 90.00}; or occasionally a small deviation like 5.00
   - All buildings within the same row share the same `rotation_deg` = `row_angle`
   - Adjacent rows may differ by ±5° for mild visual variety (e.g., row 1 = 0.00°, row 2 = 5.00°, row 3 = 0.00°)

3. **按等间距排列各行 (Place rows at equal spacing)**
   - Row spacing (center-to-center, perpendicular to row direction): 30–50 m
   - Row positions: `y_i = (i - (n_rows-1)/2) × row_spacing` for i = 0 … n_rows−1 (centred at origin when row_angle=0)
   - This ensures the entire layout is symmetric about the origin

4. **行内楼栋间距 (Space buildings within each row)**
   - Buildings within a row are spaced along the row direction with a gap of 8–15 m (edge-to-edge)
   - Each building is centred at: `x_j = (j - (n_bldg-1)/2) × (slab_length + gap)` for j = 0 … n_bldg−1
   - All buildings in the same row share the same Y coordinate (the row's y_i)

5. **板式建筑尺寸约束 (Building dimensions: slab aspect ratio)**
   - Each building: `type = "rectangular"` (slab shape)
   - Width (short dimension, perpendicular to row): 8–14 m
   - Length (long dimension, along row): width × 3 to width × 5 (aspect ratio ≥ 3:1)
   - Every building in the same row must have a different length (vary ≥ 5 m between buildings in the same row)
   - rotation_deg for all buildings in the same row must be identical and equal to the row angle

6. **添加道路 (Add roads)**
   - 2 roads parallel to the row direction, positioned at midpoints between adjacent rows
   - 1 cross road perpendicular to the row direction, passing through x=0 (or another central position)
   - Road width: 6–9 m; material: marble (default)
   - Parallel road positions: `y_road_i = (y_i + y_{i+1}) / 2` for each adjacent row pair

## 输出标准

| Property                     | Requirement                                               |
|------------------------------|-----------------------------------------------------------|
| Building type                | `rectangular` (slab shape)                               |
| Aspect ratio                 | length / width ≥ 3.0                                     |
| Row rotation consistency     | All buildings in same row have identical rotation_deg     |
| Adjacent row rotation        | May differ by ±5° for variety; all same if not specified  |
| Row spacing (centre-to-centre)| 30–50 m perpendicular to row direction                   |
| Intra-row gap (edge-to-edge) | 8–15 m between adjacent buildings in same row            |
| Height range                 | 9–30 m (3–10 floors); each building unique height        |
| Road layout                  | 2 roads parallel to rows + 1 perpendicular cross road    |
| Clearance                    | Building-to-building ≥ 5 m; building-to-road ≥ 5 m       |
| Precision                    | All float fields: exactly 2 decimal places               |

## 调用方式

Generate a single random slab row prompt:
```
python skills/slab_row/scripts/generate_prompt.py --count 1
```

Generate multiple prompts (e.g., 5):
```
python skills/slab_row/scripts/generate_prompt.py --count 5
```

## 相关文件

- `references/layout_rules.md` — Detailed slab row spatial computation rules
- `assets/system_prompt.txt` — Full system prompt for this skill
- `assets/example_output.json` — Reference valid JSON output
- `scripts/generate_prompt.py` — Prompt generator script
