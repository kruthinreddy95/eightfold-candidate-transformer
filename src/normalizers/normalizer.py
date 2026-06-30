"""
Normalization Layer
Standardizes formats for emails, phones, skills, locations, and dates.
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
    "java": "Java",
    "html": "HTML",
    "css": "CSS",
    "html5": "HTML",
    "css3": "CSS",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "cloud computing": "Cloud Computing",
    "oop": "OOP",
    "object-oriented programming": "OOP"
}

COUNTRY_MAP = {
    "india": "IN",
    "united states": "US",
    "usa": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "germany": "DE",
    "singapore": "SG",
    "canada": "CA",
    "australia": "AU"
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
    
    # clean non-digits except leading plus
    clean = re.sub(r'[^\d+]', '', phone)
    if clean.startswith("91") and len(clean) == 12:
        return "+" + clean
    if len(clean) == 10:
        return "+91" + clean
    return phone


def normalize_skill(skill):
    key = skill.strip().lower()
    return SKILL_MAP.get(key, skill.strip())


def normalize_email(email):
    return email.strip().lower()


def normalize_country(country):
    if not country:
        return None
    key = country.strip().lower()
    return COUNTRY_MAP.get(key, country.upper()[:2])


def normalize_date(date_str):
    if not date_str:
        return None
    date_str = date_str.lower().strip()
    if "present" in date_str or "current" in date_str:
        return "Present"
    
    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
        "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
        "january": "01", "february": "02", "march": "03", "april": "04", "may": "05", "june": "06",
        "july": "07", "august": "08", "september": "09", "october": "10", "november": "11", "december": "12"
    }
    
    year_match = re.search(r'\b(20\d{2}|19\d{2})\b', date_str)
    if not year_match:
        return date_str
    year = year_match.group(1)
    
    for m_name, m_val in month_map.items():
        if m_name in date_str:
            return f"{year}-{m_val}"
            
    num_match = re.search(r'\b(0?[1-9]|1[0-2])\b', date_str)
    if num_match:
        val = int(num_match.group(1))
        return f"{year}-{val:02d}"
        
    return f"{year}-01"


def normalize_profile(profile):
    # Emails
    if "emails" in profile and profile["emails"]:
        profile["emails"]["value"] = [
            normalize_email(e)
            for e in profile["emails"]["value"]
        ]

    # Phones
    if "phones" in profile and profile["phones"]:
        profile["phones"]["value"] = [
            normalize_phone(p)
            for p in profile["phones"]["value"]
        ]

    # Skills
    if "skills" in profile and profile["skills"]:
        for skill in profile["skills"]:
            skill["name"] = normalize_skill(
                skill["name"]
            )

    # Location
    if "location" in profile and profile["location"]:
        loc = profile["location"]["value"]
        if loc:
            loc["country"] = normalize_country(loc.get("country"))

    # Experience
    if "experience" in profile and profile["experience"]:
        for exp in profile["experience"]:
            exp["start"] = normalize_date(exp.get("start"))
            exp["end"] = normalize_date(exp.get("end"))

    # Education
    if "education" in profile and profile["education"]:
        for edu in profile["education"]:
            if edu.get("end_year") is not None:
                try:
                    edu["end_year"] = int(edu["end_year"])
                except Exception:
                    edu["end_year"] = None

    return profile