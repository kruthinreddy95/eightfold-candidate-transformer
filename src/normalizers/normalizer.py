"""
Normalization Layer
"""

import re
import phonenumbers


SKILL_MAP = {
    "py": "Python",
    "python": "Python",
    "python3": "Python",
    "sql": "SQL",
    "mysql": "MySQL",
    "git": "Git",
    "github": "GitHub",
}


def normalize_phone(phone):

    try:
        parsed = phonenumbers.parse(phone, "IN")

        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )

    except Exception:
        pass

    return phone


def normalize_skill(skill):

    key = skill.strip().lower()

    return SKILL_MAP.get(key, skill)


def normalize_email(email):

    return email.strip().lower()


def normalize_profile(profile):

    # Emails
    if "emails" in profile:

        profile["emails"]["value"] = [
            normalize_email(e)
            for e in profile["emails"]["value"]
        ]

    # Phones
    if "phones" in profile:

        profile["phones"]["value"] = [
            normalize_phone(p)
            for p in profile["phones"]["value"]
        ]

    # Skills
    if "skills" in profile:

        for skill in profile["skills"]:
            skill["name"] = normalize_skill(
                skill["name"]
            )

    return profile