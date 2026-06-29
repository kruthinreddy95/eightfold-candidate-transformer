import json

from parsers.ats_parser import parse as parse_ats
from parsers.resume_parser import parse_resume

from normalizers.normalizer import normalize_profile
from merger import merge
from validator import validate
from projector import project


def main():

    # ATS

    with open("data/ats.json") as file:

        ats_data = json.load(file)

    ats_profile = parse_ats(
        ats_data
    )

    ats_profile = normalize_profile(
        ats_profile
    )

    # Resume

    resume_profile = parse_resume(
        "data/resume.docx"
    )

    resume_profile = normalize_profile(
        resume_profile
    )

    # Merge

    final_profile = merge([
        ats_profile,
        resume_profile
    ])

    # Validate

    errors = validate(
        final_profile
    )

    if errors:

        print(
            "\nValidation Errors:\n"
        )

        for error in errors:

            print(
                f"- {error}"
            )

        return

    print(
        "\n✅ Profile Valid\n"
    )

    # Load Config

    with open(
        "configs/default.json"
    ) as file:

        config = json.load(
            file
        )

    # Project

    projected_output = project(
        final_profile,
        config
    )

    print(
        json.dumps(
            projected_output,
            indent=2
        )
    )


if __name__ == "__main__":
    main()