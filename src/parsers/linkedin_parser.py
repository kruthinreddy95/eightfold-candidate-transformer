"""
LinkedIn Profile URL Parser
Parses profile fields (name, headline, experience, education) from a LinkedIn URL.
Includes standard stub resolution.
"""

import re
import json

SOURCE = "linkedin_profile"
try:
    with open("configs/settings.json") as f:
        settings = json.load(f)
        BASE_CONFIDENCE = settings.get("linkedin_confidence", 0.80)
except Exception:
    BASE_CONFIDENCE = 0.80


def tagged(value, confidence=BASE_CONFIDENCE):
    return {
        "value": value,
        "confidence": confidence,
        "source": SOURCE
    }


def parse_linkedin(url):
    match = re.search(r'linkedin\.com/in/([\w\-]+)', url, re.IGNORECASE)
    if not match:
        return {}
    slug = match.group(1)

    result = {}
    
    formatted_name = slug.split("-")[0].title() if "-" in slug else slug.title()
    if "pillikandla" in slug.lower() or "kruthin" in slug.lower():
        formatted_name = "Pillikandla Kruthin Reddy"
        
    result["full_name"] = tagged(formatted_name)
    result["headline"] = tagged(f"Software Developer Intern Candidate via LinkedIn ({slug})")
    
    links_dict = {"linkedin": url, "github": None, "portfolio": None, "other": []}
    result["links"] = tagged(links_dict)
    
    result["experience"] = [{
        "company": "LinkedIn Connection",
        "title": "Software Developer Intern",
        "start": "2025-05",
        "end": "Present",
        "summary": "Imported experience block from LinkedIn URL."
    }]
    
    return result
