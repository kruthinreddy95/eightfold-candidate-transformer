"""
Merge Engine
Combines multiple candidate sources into one profile.
Resolves conflicts using confidence scores and tracks provenance.
"""

import hashlib
import json

try:
    with open("configs/settings.json") as f:
        settings = json.load(f)
        agreement_bonus = settings.get("agreement_bonus", 0.10)
except Exception:
    agreement_bonus = 0.10


def generate_candidate_id(profile):
    # Determine candidate ID from primary email, fallback to name, fallback to unknown
    email = None
    if "emails" in profile and profile["emails"]:
        email = profile["emails"][0]
    elif "full_name" in profile and profile["full_name"]:
        email = profile["full_name"]
        
    if email:
        return hashlib.md5(email.lower().strip().encode()).hexdigest()
    return "unknown"


def merge(profiles):
    result = {}
    provenance = []
    field_confidences = []

    # Filter out empty or None profiles
    valid_profiles = [p for p in profiles if p]

    # Helper for resolving single-value fields
    def resolve_single_field(field_name):
        candidates = []
        for profile in valid_profiles:
            if field_name in profile and profile[field_name]:
                candidates.append(profile[field_name])
        
        if not candidates:
            return None
        
        # Pick highest confidence candidate
        winner = max(candidates, key=lambda x: x["confidence"])
        
        provenance.append({
            "field": field_name,
            "source": winner["source"],
            "method": "highest_confidence"
        })
        field_confidences.append(winner["confidence"])
        return winner["value"]

    # Resolve Single-value Fields
    result["full_name"] = resolve_single_field("full_name")
    result["headline"] = resolve_single_field("headline")
    result["years_experience"] = resolve_single_field("years_experience")

    # Resolve Location
    location_val = resolve_single_field("location")
    result["location"] = location_val

    # Resolve Links (nested dict merge)
    links_candidates = []
    for profile in valid_profiles:
        if "links" in profile and profile["links"]:
            links_candidates.append(profile["links"])
            
    if links_candidates:
        # Merge links by taking highest confidence for each sub-field
        merged_links = {"linkedin": None, "github": None, "portfolio": None, "other": []}
        linkedin_winner = None
        github_winner = None
        portfolio_winner = None
        
        for candidate in links_candidates:
            val = candidate["value"]
            conf = candidate["confidence"]
            src = candidate["source"]
            
            if val.get("linkedin") and (not linkedin_winner or conf > linkedin_winner[1]):
                linkedin_winner = (val["linkedin"], conf, src)
            if val.get("github") and (not github_winner or conf > github_winner[1]):
                github_winner = (val["github"], conf, src)
            if val.get("portfolio") and (not portfolio_winner or conf > portfolio_winner[1]):
                portfolio_winner = (val["portfolio"], conf, src)
                
            for o in val.get("other", []):
                if o not in merged_links["other"]:
                    merged_links["other"].append(o)
                    
        if linkedin_winner:
            merged_links["linkedin"] = linkedin_winner[0]
            provenance.append({"field": "links.linkedin", "source": linkedin_winner[2], "method": "highest_confidence"})
        if github_winner:
            merged_links["github"] = github_winner[0]
            provenance.append({"field": "links.github", "source": github_winner[2], "method": "highest_confidence"})
        if portfolio_winner:
            merged_links["portfolio"] = portfolio_winner[0]
            provenance.append({"field": "links.portfolio", "source": portfolio_winner[2], "method": "highest_confidence"})
            
        result["links"] = merged_links
        # Average confidence of resolved links
        confs = [w[1] for w in [linkedin_winner, github_winner, portfolio_winner] if w]
        if confs:
            field_confidences.append(sum(confs) / len(confs))
    else:
        result["links"] = None

    # Resolve Emails (Union merge)
    emails = []
    email_confs = []
    email_sources = set()
    for profile in valid_profiles:
        if "emails" in profile and profile["emails"]:
            val = profile["emails"]["value"]
            conf = profile["emails"]["confidence"]
            src = profile["emails"]["source"]
            for email in val:
                if email not in emails:
                    emails.append(email)
            email_confs.append(conf)
            email_sources.add(src)
            
    if emails:
        result["emails"] = emails
        provenance.append({
            "field": "emails",
            "source": ", ".join(sorted(list(email_sources))),
            "method": "union"
        })
        field_confidences.append(sum(email_confs) / len(email_confs))
    else:
        result["emails"] = []

    # Resolve Phones (Union merge)
    phones = []
    phone_confs = []
    phone_sources = set()
    for profile in valid_profiles:
        if "phones" in profile and profile["phones"]:
            val = profile["phones"]["value"]
            conf = profile["phones"]["confidence"]
            src = profile["phones"]["source"]
            for phone in val:
                if phone not in phones:
                    phones.append(phone)
            phone_confs.append(conf)
            phone_sources.add(src)
            
    if phones:
        result["phones"] = phones
        provenance.append({
            "field": "phones",
            "source": ", ".join(sorted(list(phone_sources))),
            "method": "union"
        })
        field_confidences.append(sum(phone_confs) / len(phone_confs))
    else:
        result["phones"] = []

    # Resolve Skills (Conflict resolution & Boosting)
    skills = {}
    for profile in valid_profiles:
        if "skills" not in profile or not profile["skills"]:
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
                    skills[name]["sources"].append(skill["source"])
                    skills[name]["agreement_count"] += 1
                    # Base confidence is the max of the sources
                    base_conf = max(skills[name]["confidence"], skill["confidence"])
                    # Confidence boosting
                    skills[name]["confidence"] = min(
                        1.0,
                        base_conf + agreement_bonus
                    )
                    
    # Format skills to match schema and save confidence for overall metric
    result_skills = []
    skill_confs = []
    for s_name, s_data in skills.items():
        result_skills.append({
            "name": s_name,
            "confidence": s_data["confidence"],
            "sources": s_data["sources"]
        })
        skill_confs.append(s_data["confidence"])
        
    result["skills"] = sorted(result_skills, key=lambda x: x["confidence"], reverse=True)
    if skill_confs:
        field_confidences.append(sum(skill_confs) / len(skill_confs))

    # Resolve Experience
    experience_list = []
    for profile in valid_profiles:
        if "experience" in profile and profile["experience"]:
            experience_list.extend(profile["experience"])
            
    # Deduplicate experience
    deduped_exp = []
    for exp in experience_list:
        dup = False
        for m in deduped_exp:
            if m["company"] and exp["company"] and m["title"] and exp["title"]:
                # Simple check for company/title match
                if m["company"].lower().strip() == exp["company"].lower().strip() and m["title"].lower().strip() == exp["title"].lower().strip():
                    dup = True
                    # merge dates and summaries
                    if not m["start"] or len(str(exp["start"])) > len(str(m["start"])):
                        m["start"] = exp["start"]
                    if not m["end"] or len(str(exp["end"])) > len(str(m["end"])):
                        m["end"] = exp["end"]
                    if exp["summary"] and (not m["summary"] or len(exp["summary"]) > len(m["summary"])):
                        m["summary"] = exp["summary"]
                    break
        if not dup:
            deduped_exp.append(exp)
            
    result["experience"] = deduped_exp

    # Resolve Education
    education_list = []
    for profile in valid_profiles:
        if "education" in profile and profile["education"]:
            education_list.extend(profile["education"])
            
    # Deduplicate education
    deduped_edu = []
    for edu in education_list:
        dup = False
        for m in deduped_edu:
            if m["institution"] and edu["institution"] and m["degree"] and edu["degree"]:
                if m["institution"].lower().strip() == edu["institution"].lower().strip() and m["degree"].lower().strip() == edu["degree"].lower().strip():
                    dup = True
                    if not m["field"] or len(str(edu["field"])) > len(str(m["field"])):
                        m["field"] = edu["field"]
                    if not m["end_year"] or (edu["end_year"] and edu["end_year"] > m["end_year"]):
                        m["end_year"] = edu["end_year"]
                    break
        if not dup:
            deduped_edu.append(edu)
            
    result["education"] = deduped_edu

    # Generate Candidate ID
    result["candidate_id"] = generate_candidate_id(result)

    # Compute Overall Confidence
    if field_confidences:
        result["overall_confidence"] = round(sum(field_confidences) / len(field_confidences), 2)
    else:
        result["overall_confidence"] = 0.0

    result["provenance"] = provenance

    return result