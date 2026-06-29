"""
ATS JSON Parser
Converts ATS JSON into a canonical intermediate format.
"""

SOURCE = "ats_json"
BASE_CONFIDENCE = 0.85


FIELD_ALIASES = {
    "full_name": ["candidate_name", "name", "full_name"],
    "emails": ["mail", "email", "email_address"],
    "phones": ["mobile", "phone", "contact"],
    "skills": ["skills", "skill_set", "technologies"]
}


def tagged(value, confidence=BASE_CONFIDENCE):
    return {
        "value": value,
        "confidence": confidence,
        "source": SOURCE
    }


def find_field(data, field_name):

    aliases = FIELD_ALIASES.get(field_name, [])

    for alias in aliases:
        if alias in data:
            return data[alias]

    return None


def parse(data):

    result = {}

    # Full Name
    name = find_field(data, "full_name")

    if name:
        result["full_name"] = tagged(name)

    # Emails
    emails = find_field(data, "emails")

    if emails:

        if isinstance(emails, str):
            emails = [emails]

        result["emails"] = tagged(
            [e.strip().lower() for e in emails]
        )

    # Phones
    phones = find_field(data, "phones")

    if phones:

        if isinstance(phones, str):
            phones = [phones]

        result["phones"] = tagged(phones)

    # Skills
    skills = find_field(data, "skills")

    if skills:

        if isinstance(skills, str):
            skills = [skills]

        result["skills"] = [
            {
                "name": skill,
                "confidence": BASE_CONFIDENCE,
                "source": SOURCE
            }
            for skill in skills
        ]

    return result