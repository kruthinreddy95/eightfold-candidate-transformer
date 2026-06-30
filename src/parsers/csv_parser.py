"""
Recruiter CSV Parser
Converts Recruiter CSV export data into a canonical intermediate format.
"""

import csv
import os
import json

SOURCE = "recruiter_csv"
try:
    with open("configs/settings.json") as f:
        settings = json.load(f)
        BASE_CONFIDENCE = settings.get("csv_confidence", 0.80)
except Exception:
    BASE_CONFIDENCE = 0.80


def tagged(value, confidence=BASE_CONFIDENCE):
    return {
        "value": value,
        "confidence": confidence,
        "source": SOURCE
    }


def parse_csv(path):
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
    if not rows:
        return {}

    row = rows[0]
    result = {}

    data = {k.lower().strip(): v for k, v in row.items()}

    name = data.get("name") or data.get("candidate_name") or data.get("full_name")
    if name:
        result["full_name"] = tagged(name.strip())

    email = data.get("email") or data.get("mail") or data.get("email_address")
    if email:
        result["emails"] = tagged([email.strip()])

    phone = data.get("phone") or data.get("mobile") or data.get("contact")
    if phone:
        result["phones"] = tagged([phone.strip()])

    company = data.get("current_company") or data.get("company")
    title = data.get("title") or data.get("role")
    
    if company or title:
        result["experience"] = [{
            "company": company.strip() if company else None,
            "title": title.strip() if title else None,
            "start": None,
            "end": None,
            "summary": "Synthesized from Recruiter CSV Row"
        }]

    if title:
        result["headline"] = tagged(title.strip())

    return result
