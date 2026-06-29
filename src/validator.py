"""
Validator
Checks final candidate profile quality.
"""


def validate(profile):

    errors = []

    # Required fields

    if not profile.get("full_name"):
        errors.append(
            "Missing full_name"
        )

    if not profile.get("emails"):
        errors.append(
            "Missing emails"
        )

    if not profile.get("phones"):
        errors.append(
            "Missing phones"
        )

    if not profile.get("skills"):
        errors.append(
            "Missing skills"
        )

    # Confidence checks

    overall_confidence = profile.get(
        "overall_confidence",
        0
    )

    if overall_confidence < 0.5:

        errors.append(
            "Low profile confidence"
        )

    return errors