"""
Projector
Applies configurable output schema to the canonical record.
Supports index selectors, nested property mappings, per-field normalizations,
and custom missing value strategies.

Output strictly follows the assignment default schema:
  candidate_id, full_name, emails, phones (E.164), location {city,region,country},
  links {linkedin,github,portfolio,other[]}, headline, years_experience,
  skills [{name,confidence,sources[]}], experience [{company,title,start,end,summary}],
  education [{institution,degree,field,end_year}],
  provenance [{field,source,method}], overall_confidence
"""

import re
from src.normalizers.normalizer import normalize_phone, normalize_skill


# ── Path resolver ──────────────────────────────────────────────────────────────

def resolve_path(profile, path_str):
    if not path_str:
        return None

    # List indexing: e.g. emails[0]
    match_index = re.match(r'^(\w+)\[(\d+)\]$', path_str)
    if match_index:
        field = match_index.group(1)
        idx = int(match_index.group(2))
        val_list = profile.get(field)
        if isinstance(val_list, list) and len(val_list) > idx:
            return val_list[idx]
        return None

    # List projection: e.g. skills[].name
    match_list_proj = re.match(r'^(\w+)\[\]\.(\w+)$', path_str)
    if match_list_proj:
        field = match_list_proj.group(1)
        subfield = match_list_proj.group(2)
        val_list = profile.get(field)
        if isinstance(val_list, list):
            res = [item[subfield] for item in val_list if isinstance(item, dict) and subfield in item]
            return res if res else None
        return None

    # Nested object: e.g. location.city
    if "." in path_str:
        parts = path_str.split(".")
        curr = profile
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return None
        return curr

    return profile.get(path_str)


# ── Normalization ──────────────────────────────────────────────────────────────

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


# ── Shape enforcers (guarantee spec-compliant object shapes) ───────────────────

def _enforce_location(val):
    """Ensure location is always { city, region, country }."""
    if not isinstance(val, dict):
        return {"city": None, "region": None, "country": None}
    return {
        "city":    val.get("city") or None,
        "region":  val.get("region") or None,
        "country": val.get("country") or None,
    }


def _enforce_links(val):
    """Ensure links is always { linkedin, github, portfolio, other[] }."""
    if not isinstance(val, dict):
        return {"linkedin": None, "github": None, "portfolio": None, "other": []}
    return {
        "linkedin":  val.get("linkedin") or None,
        "github":    val.get("github") or None,
        "portfolio": val.get("portfolio") or None,
        "other":     val.get("other") if isinstance(val.get("other"), list) else [],
    }


def _enforce_skills(val):
    """Ensure every skill has { name, confidence, sources[] }."""
    if not isinstance(val, list):
        return []
    out = []
    for s in val:
        if not isinstance(s, dict):
            continue
        out.append({
            "name":       s.get("name") or "",
            "confidence": s.get("confidence") or 0.0,
            "sources":    s.get("sources") if isinstance(s.get("sources"), list) else [],
        })
    return out


def _enforce_experience(val):
    """Ensure every experience entry has { company, title, start, end, summary }."""
    if not isinstance(val, list):
        return []
    out = []
    for e in val:
        if not isinstance(e, dict):
            continue
        out.append({
            "company": e.get("company") or None,
            "title":   e.get("title") or None,
            "start":   e.get("start") or None,   # YYYY-MM
            "end":     e.get("end") or None,      # YYYY-MM or null (present)
            "summary": e.get("summary") or None,
        })
    return out


def _enforce_education(val):
    """Ensure every education entry has { institution, degree, field, end_year }."""
    if not isinstance(val, list):
        return []
    out = []
    for e in val:
        if not isinstance(e, dict):
            continue
        out.append({
            "institution": e.get("institution") or None,
            "degree":      e.get("degree") or None,
            "field":       e.get("field") or None,
            "end_year":    e.get("end_year") or None,
        })
    return out


def _enforce_provenance(val):
    """Ensure every provenance entry has { field, source, method }."""
    if not isinstance(val, list):
        return []
    out = []
    for p in val:
        if not isinstance(p, dict):
            continue
        out.append({
            "field":  p.get("field") or "",
            "source": p.get("source") or "",
            "method": p.get("method") or "",
        })
    return out


# Map field names to their shape enforcer functions
_SHAPE_ENFORCERS = {
    "location":   _enforce_location,
    "links":      _enforce_links,
    "skills":     _enforce_skills,
    "experience": _enforce_experience,
    "education":  _enforce_education,
    "provenance": _enforce_provenance,
}


# ── Main project function ──────────────────────────────────────────────────────

def project(profile, config):
    output = {}
    on_missing = config.get("on_missing", "null")
    fields = config.get("fields", [])

    for field in fields:
        output_field = field["path"]
        source_field = field.get("from", output_field)
        is_required = field.get("required", False)

        # Extract value
        val = resolve_path(profile, source_field)

        # Per-field normalization (e.g. E164 for phones)
        if val is not None and "normalize" in field:
            val = apply_normalization(val, field["normalize"])

        # Enforce spec-compliant object shapes
        if output_field in _SHAPE_ENFORCERS and val is not None:
            val = _SHAPE_ENFORCERS[output_field](val)

        # Missing value handling
        is_missing = val is None or (isinstance(val, list) and len(val) == 0)

        if is_missing:
            if is_required and on_missing == "error":
                raise ValueError(f"Required projected field '{output_field}' is missing.")
            if on_missing == "null":
                output[output_field] = None
            # on_missing == "omit" → skip entirely
        else:
            output[output_field] = val

    # Backwards-compat: if include_confidence / include_provenance are set
    # but those fields weren't already written via the fields list, append them.
    if config.get("include_confidence", False) and "overall_confidence" not in output:
        output["overall_confidence"] = profile.get("overall_confidence", 0.0)

    if config.get("include_provenance", False) and "provenance" not in output:
        prov = profile.get("provenance", [])
        output["provenance"] = _enforce_provenance(prov)

    return output