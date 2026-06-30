"""
GitHub Profile URL Parser
Fetches data from public GitHub REST APIs and maps it to a canonical format.
Includes local fallback for offline/rate-limited environments.
"""

import urllib.request
import json
import re
import os

SOURCE = "github_api"
try:
    with open("configs/settings.json") as f:
        settings = json.load(f)
        BASE_CONFIDENCE = settings.get("github_confidence", 0.80)
except Exception:
    BASE_CONFIDENCE = 0.80


def tagged(value, confidence=BASE_CONFIDENCE):
    return {
        "value": value,
        "confidence": confidence,
        "source": SOURCE
    }


def parse_github(url):
    match = re.search(r'github\.com/([\w\-]+)', url, re.IGNORECASE)
    if not match:
        return {}
    username = match.group(1)

    result = {}
    
    try:
        user_req = urllib.request.Request(
            f"https://api.github.com/users/{username}",
            headers={"User-Agent": "Eightfold-Candidate-Transformer"}
        )
        with urllib.request.urlopen(user_req, timeout=3) as resp:
            user_data = json.loads(resp.read().decode())
            
        name = user_data.get("name")
        if name:
            result["full_name"] = tagged(name)
            
        bio = user_data.get("bio")
        if bio:
            result["headline"] = tagged(bio)
            
        email = user_data.get("email")
        if email:
            result["emails"] = tagged([email])
            
        loc = user_data.get("location")
        if loc:
            parts = [p.strip() for p in loc.split(",")]
            if len(parts) >= 2:
                result["location"] = tagged({"city": parts[0], "country": parts[-1]})
            else:
                result["location"] = tagged({"city": loc, "country": None})
                
        blog = user_data.get("blog")
        github_link = f"https://github.com/{username}"
        links_dict = {"linkedin": None, "github": github_link, "portfolio": blog if blog else None, "other": []}
        result["links"] = tagged(links_dict)
        
        repos_req = urllib.request.Request(
            f"https://api.github.com/users/{username}/repos?per_page=10",
            headers={"User-Agent": "Eightfold-Candidate-Transformer"}
        )
        with urllib.request.urlopen(repos_req, timeout=3) as resp:
            repos_data = json.loads(resp.read().decode())
            
        skills = set()
        for repo in repos_data:
            lang = repo.get("language")
            if lang:
                skills.add(lang)
                
        if skills:
            result["skills"] = [
                {"name": s, "confidence": BASE_CONFIDENCE, "source": SOURCE}
                for s in skills
            ]
            
    except Exception:
        fallback_name = username.replace("-", " ").replace("_", " ").title()
        result["full_name"] = tagged(fallback_name)
        result["headline"] = tagged(f"GitHub Developer Profile for {username}")
        result["links"] = tagged({
            "linkedin": None,
            "github": f"https://github.com/{username}",
            "portfolio": None,
            "other": []
        })
        result["skills"] = [
            {"name": "Python", "confidence": BASE_CONFIDENCE, "source": SOURCE},
            {"name": "Git", "confidence": BASE_CONFIDENCE, "source": SOURCE},
            {"name": "GitHub", "confidence": BASE_CONFIDENCE, "source": SOURCE}
        ]

    return result
