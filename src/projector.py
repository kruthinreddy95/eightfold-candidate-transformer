"""
Projector
Applies configurable output schema.
"""


def project(profile, config):

    output = {}

    fields = config.get("fields", [])

    for field in fields:

        source_field = field.get(
            "from",
            field["path"]
        )

        output_field = field["path"]

        output[output_field] = profile.get(
            source_field
        )

    if config.get(
        "include_confidence",
        False
    ):

        output["overall_confidence"] = (
            profile.get(
                "overall_confidence"
            )
        )

    if config.get(
        "include_provenance",
        False
    ):

        output["provenance"] = (
            profile.get(
                "provenance"
            )
        )

    return output