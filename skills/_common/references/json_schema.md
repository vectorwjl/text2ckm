# JSON Output Schema

The AI must return ONLY valid JSON with this structure:

```json
{
  "intent": "scene_generation" | "ckm_generation" | "parameter_update" | "location_query" | "unrelated",
  "location": { "latitude": number, "longitude": number, "description": string },
  "scene": {
    "buildings": [ ...building objects... ],
    "roads": [ ...road objects... ]
  },
  "tx": {
    "power_dbm": number (0–100),
    "frequency_ghz": number (0.5–100),
    "x": number, "y": number, "z": number,
    "array": { "num_rows": int, "num_cols": int, "vertical_spacing": number, "horizontal_spacing": number,
               "pattern": "iso"|"dipole"|"tr38901", "polarization": "V"|"H"|"VH"|"cross" }
  },
  "rx": {
    "rx_height": number (>0),
    "array": { ...same as tx array... }
  },
  "rt": {
    "aoi_half_size_m": number (≥50),
    "map_size_m": number (≥50)
  },
  "confidence": number (0–1),
  "explanation": string
}
```

## Field Rules
- `intent`: always present
- `location`, `tx`, `rx`, `rt`: only include if explicitly mentioned by user — never invent default values
- `scene`: only present when intent is "scene_generation"
- `confidence`: 0.85–0.95 for successful extraction
- `explanation`: brief Chinese or English description of what was generated

## Building Object Schema
```json
{
  "type": "rectangular",
  "x": float,  "y": float,
  "height": float,
  "width": float,  "length": float,
  "material": "concrete",
  "rotation_deg": float
}
```
```json
{
  "type": "l_shaped",
  "x": float,  "y": float,  "height": float,
  "width1": float, "length1": float,
  "width2": float, "length2": float,
  "material": "concrete",
  "rotation_deg": float
}
```
```json
{
  "type": "t_shaped",
  "x": float,  "y": float,  "height": float,
  "main_width": float, "main_length": float,
  "wing_width": float, "wing_length": float,
  "material": "concrete",
  "rotation_deg": float
}
```
```json
{
  "type": "u_shaped",
  "x": float,  "y": float,  "height": float,
  "outer_width": float, "outer_length": float,
  "inner_width": float, "inner_length": float,
  "material": "concrete",
  "rotation_deg": float
}
```

## Road Object Schema
```json
{ "type": "straight", "start": [x, y], "end": [x, y], "width": float, "material": "marble" }
{ "type": "curved",   "points": [[x1,y1],[x2,y2],...], "width": float, "smooth": true, "material": "marble" }
```
