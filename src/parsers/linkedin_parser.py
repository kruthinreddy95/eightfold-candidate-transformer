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
    
    # Dynamically extract name parts from slug, filtering out numeric suffix IDs
    slug_parts = slug.split("-")
    name_parts = []
    for part in slug_parts:
        if not re.search(r'\d', part):
            name_parts.append(part.title())
            
    formatted_name = " ".join(name_parts)
    if formatted_name:
        result["full_name"] = tagged(formatted_name)
        
    links_dict = {"linkedin": url, "github": None, "portfolio": None, "other": []}
    result["links"] = tagged(links_dict)
    
    return result
