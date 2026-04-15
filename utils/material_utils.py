"""
Material selection utilities for Sionna RT based on frequency ranges.

ITU materials have frequency-dependent properties. This module provides
frequency-aware material selection to ensure compatibility across all
frequency bands.
"""

# ITU Material Frequency Ranges (in GHz)
# Based on ITU-R P.2040 and Sionna RT documentation
ITU_MATERIAL_FREQUENCY_RANGE = {
    "min_ghz": 1.0,
    "max_ghz": 10.0
}

# Material mapping for different frequency ranges
GROUND_MATERIAL_MAP = {
    "low_freq": {  # 1-10 GHz: ITU ground materials
        "wet_ground":        "mat-itu_wet_ground",
        "medium_dry_ground": "mat-itu_medium_dry_ground",
        "very_dry_ground":   "mat-itu_very_dry_ground",
    },
    "high_freq": {  # > 10 GHz: concrete fallback
        "wet_ground":        "mat-itu_concrete",
        "medium_dry_ground": "mat-itu_concrete",
        "very_dry_ground":   "mat-itu_concrete",
    }
}

# Materials that work across all frequencies (buildings + roads)
UNIVERSAL_MATERIALS = {
    "concrete":      "mat-itu_concrete",
    "brick":         "mat-itu_brick",
    "plasterboard":  "mat-itu_plasterboard",
    "wood":          "mat-itu_wood",
    "glass":         "mat-itu_glass",
    "ceiling_board": "mat-itu_ceiling_board",
    "chipboard":     "mat-itu_chipboard",
    "plywood":       "mat-itu_plywood",
    "marble":        "mat-itu_marble",
    "floorboard":    "mat-itu_floorboard",
    "metal":         "mat-itu_metal",
}

# Complete material properties for all materials
# Conductivity and permittivity values are at 1 GHz reference (ITU-R P.2040).
# Sionna RT uses the material name to apply frequency-dependent ITU formulas internally.
MATERIAL_PROPERTIES = {
    # ── Buildings / Roads ─────────────────────────────────────────────────────
    "mat-itu_concrete": {
        "conductivity": "0.0462",
        "permittivity": "5.24",
        "permeability": "1.0",
        "color": "0.539479 0.539479 0.539480"   # grey
    },
    "mat-itu_brick": {
        "conductivity": "0.0238",
        "permittivity": "3.91",
        "permeability": "1.0",
        "color": "0.65 0.30 0.20"               # brick red
    },
    "mat-itu_plasterboard": {
        "conductivity": "0.0085",
        "permittivity": "2.73",
        "permeability": "1.0",
        "color": "0.95 0.93 0.88"               # off-white
    },
    "mat-itu_wood": {
        "conductivity": "0.0047",
        "permittivity": "1.99",
        "permeability": "1.0",
        "color": "0.55 0.35 0.18"               # warm brown
    },
    "mat-itu_glass": {
        "conductivity": "0.0036",
        "permittivity": "6.31",
        "permeability": "1.0",
        "color": "0.7 0.8 0.85"                 # ice blue
    },
    "mat-itu_ceiling_board": {
        "conductivity": "0.0011",
        "permittivity": "1.48",
        "permeability": "1.0",
        "color": "0.95 0.95 0.95"               # near-white
    },
    "mat-itu_chipboard": {
        "conductivity": "0.0217",
        "permittivity": "2.58",
        "permeability": "1.0",
        "color": "0.70 0.55 0.35"               # tan
    },
    "mat-itu_plywood": {
        "conductivity": "0.33",
        "permittivity": "2.71",
        "permeability": "1.0",
        "color": "0.80 0.65 0.40"               # light wood
    },
    "mat-itu_marble": {
        "conductivity": "0.0055",
        "permittivity": "7.074",
        "permeability": "1.0",
        "color": "0.701101 0.644479 0.485150"   # beige
    },
    "mat-itu_floorboard": {
        "conductivity": "0.0044",
        "permittivity": "3.66",
        "permeability": "1.0",
        "color": "0.60 0.40 0.20"               # dark wood
    },
    "mat-itu_metal": {
        "conductivity": "1e7",
        "permittivity": "1.0",
        "permeability": "1.0",
        "color": "0.219526 0.219526 0.254152"   # steel blue-grey
    },
    # ── Ground only (1–10 GHz; falls back to concrete above 10 GHz) ──────────
    "mat-itu_very_dry_ground": {
        "conductivity": "0.00015",
        "permittivity": "3.0",
        "permeability": "1.0",
        "color": "0.85 0.78 0.58"               # pale sand
    },
    "mat-itu_medium_dry_ground": {
        "conductivity": "0.035",
        "permittivity": "15.0",
        "permeability": "1.0",
        "color": "0.72 0.58 0.38"               # earthy brown
    },
    "mat-itu_wet_ground": {
        "conductivity": "0.15",
        "permittivity": "30.0",
        "permeability": "1.0",
        "color": "0.91 0.569 0.055"             # dark amber
    },
}

# Bilingual material name mapping (user-friendly names → internal IDs)
MATERIAL_NAME_MAPPING = {
    # English
    "concrete":      "mat-itu_concrete",
    "brick":         "mat-itu_brick",
    "plasterboard":  "mat-itu_plasterboard",
    "wood":          "mat-itu_wood",
    "glass":         "mat-itu_glass",
    "ceiling_board": "mat-itu_ceiling_board",
    "chipboard":     "mat-itu_chipboard",
    "plywood":       "mat-itu_plywood",
    "marble":        "mat-itu_marble",
    "floorboard":    "mat-itu_floorboard",
    "metal":         "mat-itu_metal",
    # Chinese
    "混凝土": "mat-itu_concrete",
    "砖":     "mat-itu_brick",
    "砖块":   "mat-itu_brick",
    "石膏板": "mat-itu_plasterboard",
    "石膏":   "mat-itu_plasterboard",
    "木材":   "mat-itu_wood",
    "木头":   "mat-itu_wood",
    "玻璃":   "mat-itu_glass",
    "玻璃幕墙": "mat-itu_glass",
    "天花板": "mat-itu_ceiling_board",
    "吊顶":   "mat-itu_ceiling_board",
    "刨花板": "mat-itu_chipboard",
    "胶合板": "mat-itu_plywood",
    "夹板":   "mat-itu_plywood",
    "大理石": "mat-itu_marble",
    "地板":   "mat-itu_floorboard",
    "木地板": "mat-itu_floorboard",
    "金属":   "mat-itu_metal",
}


def select_ground_material(frequency_ghz: float, ground_type: str = "wet_ground") -> str:
    """
    Select appropriate ground material based on operating frequency.

    ITU ground materials (wet_ground, dry_ground, icy) are only defined
    for frequencies between 1-10 GHz. For higher frequencies (e.g., mmWave),
    concrete is used as a fallback material.

    Args:
        frequency_ghz: Operating frequency in GHz
        ground_type: Type of ground ("wet_ground", "dry_ground", "icy")

    Returns:
        Material ID string (e.g., "mat-itu_wet_ground" or "mat-itu_concrete")

    Example:
        >>> select_ground_material(2.4, "wet_ground")
        'mat-itu_wet_ground'
        >>> select_ground_material(28.0, "wet_ground")
        'mat-itu_concrete'
    """
    if frequency_ghz <= ITU_MATERIAL_FREQUENCY_RANGE["max_ghz"]:
        # Use ITU ground material for frequencies ≤ 10 GHz
        material = GROUND_MATERIAL_MAP["low_freq"].get(ground_type, "mat-itu_wet_ground")
        return material
    else:
        # Use concrete fallback for frequencies > 10 GHz
        material = GROUND_MATERIAL_MAP["high_freq"].get(ground_type, "mat-itu_concrete")
        print(f"[INFO] Frequency {frequency_ghz} GHz exceeds ITU ground material range "
              f"({ITU_MATERIAL_FREQUENCY_RANGE['max_ghz']} GHz). "
              f"Using {material} as fallback for {ground_type}.")
        return material


def is_frequency_in_itu_range(frequency_ghz: float) -> bool:
    """
    Check if frequency is within ITU material valid range.

    Args:
        frequency_ghz: Operating frequency in GHz

    Returns:
        True if frequency is within 1-10 GHz range, False otherwise
    """
    return (ITU_MATERIAL_FREQUENCY_RANGE["min_ghz"] <= frequency_ghz
            <= ITU_MATERIAL_FREQUENCY_RANGE["max_ghz"])


def get_material_info(frequency_ghz: float) -> dict:
    """
    Get material selection information for a given frequency.

    Args:
        frequency_ghz: Operating frequency in GHz

    Returns:
        Dictionary with material selection details
    """
    in_range = is_frequency_in_itu_range(frequency_ghz)
    return {
        "frequency_ghz": frequency_ghz,
        "in_itu_range": in_range,
        "itu_range": f"{ITU_MATERIAL_FREQUENCY_RANGE['min_ghz']}-{ITU_MATERIAL_FREQUENCY_RANGE['max_ghz']} GHz",
        "recommended_ground": select_ground_material(frequency_ghz, "wet_ground"),
        "uses_fallback": not in_range
    }


def normalize_material_name(user_input: str, default: str = "concrete") -> str:
    """
    Convert user-friendly material name to internal material ID.

    Supports both English and Chinese names, case-insensitive matching.

    Args:
        user_input: User-provided material name (e.g., "glass", "玻璃", "Glass")
        default: Default material to use if input is invalid (default: "concrete")

    Returns:
        Internal material ID (e.g., "mat-itu_glass")

    Example:
        >>> normalize_material_name("glass")
        'mat-itu_glass'
        >>> normalize_material_name("玻璃")
        'mat-itu_glass'
        >>> normalize_material_name("CONCRETE")
        'mat-itu_concrete'
        >>> normalize_material_name("invalid")
        'mat-itu_concrete'
    """
    if not user_input:
        return MATERIAL_NAME_MAPPING.get(default, "mat-itu_concrete")

    # Try exact match first
    material_id = MATERIAL_NAME_MAPPING.get(user_input)
    if material_id:
        return material_id

    # Try case-insensitive match for English names
    material_id = MATERIAL_NAME_MAPPING.get(user_input.lower())
    if material_id:
        return material_id

    # If already in internal format (mat-itu_*), validate and return
    if user_input.startswith("mat-itu_"):
        if user_input in MATERIAL_PROPERTIES:
            return user_input

    # Fallback to default
    print(f"[WARNING] Unknown material '{user_input}', using default '{default}'")
    return MATERIAL_NAME_MAPPING.get(default, "mat-itu_concrete")


def validate_material(material: str, object_type: str = "building") -> str:
    """
    Validate material ID and return with fallback to defaults.

    Args:
        material: Material ID to validate (e.g., "mat-itu_glass")
        object_type: Type of object ("building" or "road") for default selection

    Returns:
        Valid material ID

    Example:
        >>> validate_material("mat-itu_glass", "building")
        'mat-itu_glass'
        >>> validate_material("mat-itu_invalid", "building")
        'mat-itu_concrete'
        >>> validate_material("mat-itu_invalid", "road")
        'mat-itu_marble'
    """
    # Check if material exists in properties
    if material in MATERIAL_PROPERTIES:
        return material

    # Fallback to defaults based on object type
    if object_type == "road":
        default = "mat-itu_marble"
    else:
        default = "mat-itu_concrete"

    print(f"[WARNING] Invalid material '{material}' for {object_type}, using default '{default}'")
    return default


def get_all_material_properties() -> dict:
    """
    Get all material properties for XML generation.

    Returns:
        Dictionary of all material properties

    Example:
        >>> props = get_all_material_properties()
        >>> 'mat-itu_glass' in props
        True
        >>> props['mat-itu_glass']['permittivity']
        '6.0'
    """
    return MATERIAL_PROPERTIES.copy()
