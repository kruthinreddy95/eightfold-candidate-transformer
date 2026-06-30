"""
Projector
Applies configurable output schema to the canonical record.
Supports index selectors, nested property mappings, per-field normalizations,
and custom missing value strategies.
"""

import re
from src.normalizers.normalizer import normalize_phone, normalize_skill


def resolve_path(profile, path_str):
    if not path_str:
        return None

    # Handle list indexing: e.g., emails[0]
    match_index = re.match(r'^(\w+)\[(\d+)\]$', path_str)
    if match_index:
        field = match_index.group(1)
        idx = int(match_index.group(2))
        val_list = profile.get(field)
        if isinstance(val_list, list) and len(val_list) > idx:
            return val_list[idx]
        return None

    # Handle list projections: e.g., skills[].name
    match_list_proj = re.match(r'^(\w+)\[\]\.(\w+)$', path_str)
    if match_list_proj:
        field = match_list_proj.group(1)
        subfield = match_list_proj.group(2)
        val_list = profile.get(field)
        if isinstance(val_list, list):
            res = []
            for item in val_list:
                if isinstance(item, dict) and subfield in item:
                    res.append(item[subfield])
            return res if res else None
        return None

    # Handle nested objects: e.g. location.city
    if "." in path_str:
        parts = path_str.split(".")
        curr = profile
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return None
        return curr

    # Simple field lookup
    return profile.get(path_str)


def apply_normalization(val, norm_type):
    if val is None:
        return None
    
    if norm_type == "E164":
        if isinstance(val, list):
            return [normalize_phone(v) for v in val]
        return normalize_phone(val)
        
    elif norm_type == "canonical":
        if isinstance(val, list):
            return [normalize_skill(v) for v in val]
        return normalize_skill(val)
        
    elif norm_type == "upper":
        if isinstance(val, list):
            return [str(v).upper() for v in val]
        return str(val).upper()
        
    elif norm_type == "lower":
        if isinstance(val, list):
            return [str(v).lower() for v in val]
        return str(val).lower()
        
    return val


def project(profile, config):
    output = {}
    on_missing = config.get("on_missing", "null")
    fields = config.get("fields", [])

    for field in fields:
        output_field = field["path"]
        source_field = field.get("from", output_field)
        is_required = field.get("required", False)

        # Extract value using path resolver
        val = resolve_path(profile, source_field)

        # Apply per-field normalization if requested
        if val is not None and "normalize" in field:
            val = apply_normalization(val, field["normalize"])

        # Check if value is missing/empty
        is_missing = (val is None) or (isinstance(val, list) and not val)

        if is_missing:
            if is_required:
                if on_missing == "error":
                    raise ValueError(f"Required projected field '{output_field}' is missing.")
            
            if on_missing == "null":
                output[output_field] = None
            # If on_missing is "omit", we exclude it from the projected dictionary
        else:
            output[output_field] = val

    # Toggle provenance and confidence
    if config.get("include_confidence", False):
        output["overall_confidence"] = profile.get("overall_confidence", 0.0)

    if config.get("include_provenance", False):
        output["provenance"] = profile.get("provenance", [])

    # Audit metrics
    output["metrics"] = {
        "skills_detected": len(profile.get("skills", [])),
        "emails_detected": len(profile.get("emails", []))
    }

    return output