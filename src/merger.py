"""
Merge Engine
Combines multiple candidate sources into one profile.
"""

import hashlib


def generate_candidate_id(profile):

    email = None

    if "emails" in profile and profile["emails"]:
        email = profile["emails"][0]

    if email:
        return hashlib.md5(email.encode()).hexdigest()

    return "unknown"


def merge(profiles):

    result = {}

    provenance = []

    # -----------------------
    # FULL NAME
    # -----------------------

    names = []

    for profile in profiles:

        if "full_name" in profile:
            names.append(profile["full_name"])

    if names:

        winner = max(
            names,
            key=lambda x: x["confidence"]
        )

        result["full_name"] = winner["value"]

        provenance.append({
            "field": "full_name",
            "source": winner["source"],
            "method": "highest_confidence"
        })

    # -----------------------
    # EMAILS
    # -----------------------

    emails = []

    for profile in profiles:

        if "emails" in profile:

            for email in profile["emails"]["value"]:

                if email not in emails:
                    emails.append(email)

    result["emails"] = emails

    # -----------------------
    # PHONES
    # -----------------------

    phones = []

    for profile in profiles:

        if "phones" in profile:

            for phone in profile["phones"]["value"]:

                if phone not in phones:
                    phones.append(phone)

    result["phones"] = phones

    # -----------------------
    # SKILLS
    # -----------------------

    skills = {}

    for profile in profiles:

        if "skills" not in profile:
            continue

        for skill in profile["skills"]:

            name = skill["name"]

            if name not in skills:

                skills[name] = {
                    "name": name,
                    "confidence": skill["confidence"],
                    "sources": [skill["source"]],
                    "agreement_count": 1
                }

            else:

                if skill["source"] not in skills[name]["sources"]:

                    skills[name]["sources"].append(
                        skill["source"]
                    )

                    skills[name]["agreement_count"] += 1

                    skills[name]["confidence"] = min(
                        1.0,
                        skills[name]["confidence"] + 0.10
                    )

    result["skills"] = sorted(
        list(skills.values()),
        key=lambda x: x["confidence"],
        reverse=True
    )

    # -----------------------
    # CANDIDATE ID
    # -----------------------

    result["candidate_id"] = generate_candidate_id(
        result
    )

    # -----------------------
    # OVERALL CONFIDENCE
    # -----------------------

    if result["skills"]:

        total = sum(
            skill["confidence"]
            for skill in result["skills"]
        )

        result["overall_confidence"] = round(
            total / len(result["skills"]),
            2
        )

    else:

        result["overall_confidence"] = 0.0

    # -----------------------
    # PROVENANCE
    # -----------------------

    result["provenance"] = provenance

    return result