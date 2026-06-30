"""
Recruiter Notes Parser
Parses free text recruiter notes (.txt) into a canonical intermediate format.
"""

import re
import json
import os
from src.parsers.resume_parser import (
    extract_emails,
    extract_phones,
    extract_links,
    extract_location
)

SOURCE = "recruiter_notes"
try:
    with open("configs/settings.json") as f:
        settings = json.load(f)
        BASE_CONFIDENCE = settings.get("recruiter_notes_confidence", 0.70)
except Exception:
    BASE_CONFIDENCE = 0.70


def tagged(value, confidence=BASE_CONFIDENCE):
    return {
        "value": value,
        "confidence": confidence,
        "source": SOURCE
    }


def parse_notes(path):
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as file:
        text = file.read()

    emails = extract_emails(text)
    phones = extract_phones(text)
    links = extract_links(text)
    location = extract_location(text)
    
    result = {}
    
    name_match = re.search(r'(?:Candidate|Name|Notes on):\s*([^\n\r]+)', text, re.IGNORECASE)
    if name_match:
        result["full_name"] = tagged(name_match.group(1).strip())
    else:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines and len(lines[0].split()) < 5:
            result["full_name"] = tagged(lines[0])

    if emails:
        result["emails"] = tagged(emails)
    if phones:
        result["phones"] = tagged(phones)
    if location:
        result["location"] = tagged(location)
    if any(links.values()):
        result["links"] = tagged(links)

    headline_match = re.search(r'(?:Current Role|Headline|Role|Title):\s*([^\n]+)', text, re.IGNORECASE)
    if headline_match:
        result["headline"] = tagged(headline_match.group(1).strip())

    skills_match = re.search(r'(?:Skills|Technologies):\s*([^\n]+)', text, re.IGNORECASE)
    if skills_match:
        skills_raw = [s.strip() for s in re.split(r'[,|&]', skills_match.group(1))]
        result["skills"] = [
            {"name": s, "confidence": BASE_CONFIDENCE, "source": SOURCE}
            for s in skills_raw if s
        ]

    exp_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:years|yrs)\s+of\s+experience', text, re.IGNORECASE)
    if exp_match:
        try:
            result["years_experience"] = tagged(float(exp_match.group(1)))
        except ValueError:
            pass

    return result
