"""
Validator
Validates intermediate canonical candidate profiles and projected output schemas.
Creates validation reports in the output directory.
"""

import json
import os


def validate(profile):
    """
    Validates the canonical intermediate profile.
    Checks basic quality constraints and records results in output/validation_report.json.
    """
    errors = []

    checks = {
        "candidate_id_present": bool(profile.get("candidate_id")),
        "name_present": bool(profile.get("full_name")),
        "email_present": bool(profile.get("emails")),
        "phone_present": bool(profile.get("phones")),
        "skills_present": bool(profile.get("skills")),
        "experience_present": bool(profile.get("experience")),
        "education_present": bool(profile.get("education"))
    }

    if not checks["candidate_id_present"]:
        errors.append("Missing candidate_id")
    if not checks["name_present"]:
        errors.append("Missing full_name")
    if not checks["email_present"]:
        errors.append("Missing emails")
    if not checks["phone_present"]:
        errors.append("Missing phones")
    if not checks["skills_present"]:
        errors.append("Missing skills")

    overall_confidence = profile.get("overall_confidence", 0.0)
    if overall_confidence < 0.5:
        errors.append(f"Low profile confidence: {overall_confidence} < 0.5")

    report = {
        "status": "PASS" if len(errors) == 0 else "FAIL",
        "checks": checks,
        "error_count": len(errors),
        "errors": errors
    }

    os.makedirs("output", exist_ok=True)
    with open("output/validation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return errors


def validate_projected(projected, config):
    """
    Validates projected dictionary fields against configuration rules (types, required fields).
    """
    errors = []
    fields = config.get("fields", [])

    for field in fields:
        path = field["path"]
        is_required = field.get("required", False)
        target_type = field.get("type")

        # Check required fields
        val = projected.get(path)
        is_missing = (val is None) or (isinstance(val, list) and not val)

        if is_required and is_missing:
            errors.append(f"Projected field '{path}' is required but missing or empty.")

        # Check types if specified
        if val is not None and target_type:
            if target_type == "string":
                if not isinstance(val, str):
                    errors.append(f"Projected field '{path}' should be string, got {type(val).__name__}.")
            elif target_type == "string[]":
                if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
                    errors.append(f"Projected field '{path}' should be a list of strings.")
            elif target_type == "number":
                if not isinstance(val, (int, float)):
                    errors.append(f"Projected field '{path}' should be number, got {type(val).__name__}.")
            elif target_type == "object":
                if not isinstance(val, dict):
                    errors.append(f"Projected field '{path}' should be object, got {type(val).__name__}.")
            elif target_type == "object[]":
                if not isinstance(val, list) or not all(isinstance(x, dict) for x in val):
                    errors.append(f"Projected field '{path}' should be a list of objects.")

    return errors