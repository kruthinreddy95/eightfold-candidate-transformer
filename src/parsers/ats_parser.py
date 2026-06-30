"""
ATS JSON Parser
Converts ATS JSON into a canonical intermediate format.
"""

SOURCE = "ats_json"
BASE_CONFIDENCE = 0.85


FIELD_ALIASES = {
    "full_name": ["candidate_name", "name", "full_name"],
    "emails": ["mail", "email", "email_address", "emails"],
    "phones": ["mobile", "phone", "contact", "phones"],
    "skills": ["skills", "skill_set", "technologies"],
    "location": ["location", "address", "city"],
    "links": ["links", "urls", "github", "linkedin"],
    "headline": ["headline", "title", "designation"],
    "years_experience": ["years_experience", "experience_years", "exp_years"],
    "experience": ["experience", "work_history", "history"],
    "education": ["education", "academic_history"]
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
        result["emails"] = tagged([e.strip() for e in emails if e])

    # Phones
    phones = find_field(data, "phones")
    if phones:
        if isinstance(phones, str):
            phones = [phones]
        result["phones"] = tagged([p.strip() for p in phones if p])

    # Skills
    skills = find_field(data, "skills")
    if skills:
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        result["skills"] = [
            {
                "name": skill,
                "confidence": BASE_CONFIDENCE,
                "source": SOURCE
            }
            for skill in skills
        ]

    # Location
    loc = find_field(data, "location")
    if loc:
        if isinstance(loc, str):
            parts = [p.strip() for p in loc.split(",")]
            if len(parts) >= 2:
                loc_dict = {"city": parts[0], "country": parts[-1]}
            else:
                loc_dict = {"city": loc, "country": None}
        elif isinstance(loc, dict):
            loc_dict = {
                "city": loc.get("city") or loc.get("town"),
                "region": loc.get("region") or loc.get("state"),
                "country": loc.get("country")
            }
        else:
            loc_dict = None
        
        if loc_dict:
            result["location"] = tagged(loc_dict)

    # Links
    links = find_field(data, "links")
    links_dict = {"linkedin": None, "github": None, "portfolio": None, "other": []}
    if isinstance(links, dict):
        links_dict.update(links)
        result["links"] = tagged(links_dict)
    elif isinstance(links, list):
        for l in links:
            if "linkedin.com" in l:
                links_dict["linkedin"] = l
            elif "github.com" in l:
                links_dict["github"] = l
            else:
                links_dict["other"].append(l)
        result["links"] = tagged(links_dict)
    else:
        github = data.get("github") or data.get("github_url")
        linkedin = data.get("linkedin") or data.get("linkedin_url")
        if github or linkedin:
            links_dict["github"] = github
            links_dict["linkedin"] = linkedin
            result["links"] = tagged(links_dict)

    # Headline
    headline = find_field(data, "headline")
    if headline:
        result["headline"] = tagged(headline)

    # Years of experience
    years_exp = find_field(data, "years_experience")
    if years_exp is not None:
        try:
            result["years_experience"] = tagged(float(years_exp))
        except ValueError:
            pass

    # Experience
    exp_list = find_field(data, "experience")
    if exp_list and isinstance(exp_list, list):
        parsed_exp = []
        for e in exp_list:
            if isinstance(e, dict):
                parsed_exp.append({
                    "company": e.get("company") or e.get("employer"),
                    "title": e.get("title") or e.get("role"),
                    "start": e.get("start") or e.get("start_date"),
                    "end": e.get("end") or e.get("end_date"),
                    "summary": e.get("summary") or e.get("description")
                })
        if parsed_exp:
            result["experience"] = parsed_exp
    else:
        curr_company = data.get("current_company") or data.get("company")
        curr_title = data.get("title") or data.get("role")
        if curr_company or curr_title:
            result["experience"] = [{
                "company": curr_company,
                "title": curr_title,
                "start": None,
                "end": None,
                "summary": "Synthesized from root fields"
            }]

    # Education
    edu_list = find_field(data, "education")
    if edu_list and isinstance(edu_list, list):
        parsed_edu = []
        for edu in edu_list:
            if isinstance(edu, dict):
                try:
                    end_yr = int(edu.get("end_year")) if edu.get("end_year") else None
                except ValueError:
                    end_yr = None
                parsed_edu.append({
                    "institution": edu.get("institution") or edu.get("school") or edu.get("college"),
                    "degree": edu.get("degree"),
                    "field": edu.get("field") or edu.get("major") or edu.get("field_of_study"),
                    "end_year": end_yr
                })
        if parsed_edu:
            result["education"] = parsed_edu

    return result