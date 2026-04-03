# Material Reference

Five surface materials are available for buildings and roads. Each material has distinct visual properties in Blender and distinct electromagnetic properties used by the ray-tracing engine. All material names in JSON must be lowercase strings exactly as shown below.

---

## Material Table

| JSON key    | Chinese name   | English name     | Default for   | Visual description                           |
|-------------|----------------|------------------|---------------|----------------------------------------------|
| `concrete`  | 混凝土          | Concrete          | Buildings     | Grey matte surface, rough texture            |
| `marble`    | 大理石          | Marble            | Roads         | Light grey polished surface, slight sheen    |
| `metal`     | 金属            | Metal             | —             | Shiny metallic, high specular reflectance    |
| `wood`      | 木材            | Wood              | —             | Warm brown, low reflectance                  |
| `glass`     | 玻璃幕墙        | Glass curtain wall| —             | Highly transparent, strong specular highlight|

---

## Defaults

- **Buildings**: `"concrete"` is used when the user does not specify a material.
- **Roads**: `"marble"` is used when the user does not specify a material.
- If the user specifies a material by name (Chinese or English), the matching JSON key from the table above must be used.

---

## ITU Electromagnetic Properties

The following values are based on ITU-R P.2040 (building material electromagnetic properties) and are used by the ray-tracing simulation engine to compute reflection, transmission, and scattering coefficients.

| Material    | Relative permittivity εr | Conductivity σ (S/m) @ 1 GHz | Typical reflection loss (dB) | Typical transmission loss (dB/m) |
|-------------|--------------------------|-------------------------------|------------------------------|-----------------------------------|
| `concrete`  | 5.31                     | 0.0326                        | 5–8                          | 10–15                             |
| `marble`    | 7.07                     | 0.0特                         | 6–9                          | 8–13                              |
| `metal`     | 1.00 (conductor)         | ≥10⁶ (PEC approximation)     | 0–1 (near-total reflection)  | >60 (opaque)                      |
| `wood`      | 1.99                     | 0.0047                        | 2–4                          | 4–8                               |
| `glass`     | 6.27                     | 0.0043                        | 3–6                          | 2–5 (thin pane)                   |

> Note: Values above are representative at 1–3 GHz. For frequencies above 10 GHz, dielectric loss increases significantly and `concrete` becomes the conservative fallback material for simulation accuracy (see frequency fallback rule below).

---

## Frequency Fallback Rule

When the simulation frequency (`frequency_ghz`) exceeds **10 GHz**:
- `wood` and `glass` have substantially increased penetration loss.
- `marble` behaves similarly to `concrete` in the millimetre-wave regime.
- The system prompt for CKM generation should default to `"concrete"` for all building surfaces when `frequency_ghz > 10` to ensure conservative, physically plausible ray-tracing results.
- This fallback applies **only to buildings**; road material remains `"marble"` unless specified.

---

## Usage in JSON

```json
{ "type": "rectangular", ..., "material": "glass" }
{ "type": "straight",    ..., "material": "marble" }
```

Material is always a string. Any value outside the five keys listed above will cause a validation error in `blender_script.py`.
