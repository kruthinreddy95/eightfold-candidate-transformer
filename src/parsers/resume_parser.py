"""
Resume Parser
Supports DOCX, PDF, TXT, JSON and Markdown files.
Extracts candidate information into a structured intermediate format.
"""

import os
import json
import re
from docx import Document
import pdfplumber
import phonenumbers

SOURCE = "resume_docx"
try:
    with open("configs/settings.json") as f:
        settings = json.load(f)
        BASE_CONFIDENCE = settings.get("resume_confidence", 0.75)
except Exception:
    BASE_CONFIDENCE = 0.75


def tagged(value, confidence=BASE_CONFIDENCE, source_name=SOURCE):
    return {
        "value": value,
        "confidence": confidence,
        "source": source_name
    }


def extract_docx(path):
    doc = Document(path)
    return "\n".join(
        paragraph.text
        for paragraph in doc.paragraphs
    )


def extract_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text


def extract_txt(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def extract_json(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
        if isinstance(data, dict):
            return json.dumps(data)
        return str(data)


def extract_md(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def extract_phones(text):
    phones = []
    # Use phonenumbers library for robust extraction
    try:
        for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
            formatted = phonenumbers.format_number(
                match.number,
                phonenumbers.PhoneNumberFormat.E164
            )
            if formatted not in phones:
                phones.append(formatted)
    except Exception:
        pass

    # Regex fallback
    if not phones:
        matches = re.findall(r'\+?\d[\d\s\-\(\).]{8,14}\d', text)
        for m in matches:
            clean = re.sub(r'[^\d+]', '', m)
            if len(clean) >= 10 and len(clean) <= 15:
                phones.append(m.strip())
    return phones


def extract_emails(text):
    # Clean up common spaces around @ and . from PDF extract layouts
    cleaned = re.sub(r'\s*@\s*', '@', text)
    cleaned = re.sub(r'\s*\.\s*(com|org|net|edu|gov|in|io|co|info|me)\b', r'.\1', cleaned, flags=re.IGNORECASE)
    return list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', cleaned)))


def extract_links(text):
    links = {"linkedin": None, "github": None, "portfolio": None, "other": []}
    # Look for URLs
    urls = re.findall(r'(https?://[^\s|]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[^\s|]+)', text)
    # Add domain patterns that might not start with http/https
    domain_urls = re.findall(r'\b(github\.com/[^\s|]+|linkedin\.com/in/[^\s|]+)\b', text)
    for u in set(urls + domain_urls):
        u_clean = u.rstrip('.,;|)')
        u_lower = u_clean.lower()
        if "linkedin.com" in u_lower:
            if not links["linkedin"]:
                links["linkedin"] = u_clean
        elif "github.com" in u_lower:
            if not links["github"]:
                links["github"] = u_clean
        else:
            if u_clean not in links["other"] and not any(p in u_lower for p in ["gmail.com", "email.com"]):
                links["other"].append(u_clean)
    return links


def extract_location(text):
    lines = text.split("\n")
    # Check first 5 lines for "City, Country"
    for line in lines[:5]:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            for part in parts:
                match = re.search(r'^([A-Za-z\s]+),\s*([A-Za-z\s]+)$', part)
                if match:
                    return {"city": match.group(1).strip(), "country": match.group(2).strip()}
        else:
            match = re.search(r'^([A-Za-z\s]+),\s*([A-Za-z\s]+)$', line.strip())
            if match:
                return {"city": match.group(1).strip(), "country": match.group(2).strip()}

    # General fallback search in the whole text
    match = re.search(r'\b([A-Za-z\s]+),\s*(India|USA|United States|UK|United Kingdom|Germany|Singapore|Canada|Australia)\b', text, re.IGNORECASE)
    if match:
        return {"city": match.group(1).strip(), "country": match.group(2).strip()}
    return None


def segment_sections(text):
    sections = {}
    current_section = "HEADER"
    sections[current_section] = []
    
    lines = text.split("\n")
    headers = [
        "PROFESSIONAL SUMMARY", "SUMMARY",
        "TECHNICAL SKILLS", "SKILLS",
        "INTERNSHIP EXPERIENCE", "WORK EXPERIENCE", "EXPERIENCE", "INTERNSHIPS",
        "PROJECTS", "PROJECT",
        "EDUCATION",
        "CERTIFICATIONS",
        "ACHIEVEMENTS",
        "LANGUAGES",
        "DECLARATION"
    ]
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
        
        is_header = False
        for h in headers:
            if cleaned_line.upper() == h or cleaned_line.upper().startswith(h + " ") or cleaned_line.upper().endswith(" " + h) or (len(cleaned_line) < 30 and h in cleaned_line.upper() and cleaned_line.isupper()):
                current_section = h
                sections[current_section] = []
                is_header = True
                break
        
        if not is_header:
            sections[current_section].append(cleaned_line)
            
    return sections


def parse_skills_section(lines):
    skills = []
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            skill_part = parts[1]
        elif "—" in line:
            parts = line.split("—", 1)
            skill_part = parts[1]
        else:
            skill_part = line
        
        # Replace parentheses with commas so nested skill sets split nicely (e.g. HTML,CSS)
        skill_part_clean = skill_part.replace("(", ",").replace(")", ",")
        items = [i.strip() for i in re.split(r'[,|&]|—', skill_part_clean)]
        for item in items:
            if item and len(item) < 40:
                item_clean = re.sub(r'^[\*\-\•\s]+', '', item).strip()
                if item_clean:
                    skills.append(item_clean)
    return list(set(skills))


def parse_experience_section(lines):
    experience = []
    current_exp = None
    
    date_regex = r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*(?:-|–|to)\s*(?:(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present|Current)\b"
    year_span_regex = r"\b(20\d{2}|19\d{2})\s*(?:-|–|to)\s*(?:(20\d{2}|19\d{2})|Present|Current)\b"
    
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
            
        date_match = re.search(date_regex, cleaned, re.IGNORECASE) or re.search(year_span_regex, cleaned, re.IGNORECASE)
        
        is_new_exp = False
        title = None
        company = None
        start_date = None
        end_date = None
        
        if "|" in cleaned:
            parts = [p.strip() for p in cleaned.split("|")]
            title = parts[0]
            company = parts[1] if len(parts) > 1 else None
            
            if date_match:
                date_str = date_match.group(0)
                if company:
                    company = company.replace(date_str, "").strip()
                title = title.replace(date_str, "").strip()
            is_new_exp = True
        elif date_match:
            date_str = date_match.group(0)
            parts = cleaned.split(date_str)
            title = parts[0].strip()
            is_new_exp = True
            
        if is_new_exp:
            if current_exp:
                experience.append(current_exp)
                
            if date_match:
                date_str = date_match.group(0)
                dates = [d.strip() for d in re.split(r'-|–|to', date_str)]
                start_date = dates[0]
                end_date = dates[1] if len(dates) > 1 else "Present"
                
            if title:
                title = re.sub(r'\s+', ' ', title).strip()
            if company:
                company = re.sub(r'\s+', ' ', company).strip()
                
            current_exp = {
                "company": company or "Unknown",
                "title": title or "Unknown",
                "start": start_date,
                "end": end_date,
                "summary": ""
            }
        else:
            if current_exp:
                cleaned_bullet = re.sub(r'^[\*\-\•\s]+', '', cleaned).strip()
                if current_exp["summary"]:
                    current_exp["summary"] += "\n" + cleaned_bullet
                else:
                    current_exp["summary"] = cleaned_bullet
                      
    if current_exp:
        experience.append(current_exp)
          
    return experience


def parse_education_section(lines):
    education = []
    i = 0
    degree_keywords = ["b.tech", "b.e", "b.sc", "bachelor", "master", "phd", "intermediate", "secondary", "class xii", "class x", "cbse", "icse", "school"]
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        is_degree_line = any(k in line.lower() for k in degree_keywords)
        
        if is_degree_line:
            degree = line
            field = None
            for sep in ["–", "-", "|"]:
                if sep in line:
                    parts = line.split(sep, 1)
                    degree = parts[0].strip()
                    field = re.sub(r'\s*(?:CGPA|%|Percent|Score|Grade).*$', '', parts[1], flags=re.IGNORECASE).strip()
                    field = re.sub(r'\s*\b\d+(?:\.\d+)?%?\b', '', field)
                    field = re.sub(r'\s+', ' ', field).strip()
                    break
            
            institution = None
            end_year = None
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                institution_parts = [p.strip() for p in next_line.split("|")]
                institution = institution_parts[0]
                
                years = re.findall(r'\b(20\d{2}|19\d{2})\b', next_line)
                if years:
                    end_year = int(years[-1])
                i += 1
            
            degree = re.sub(r'\s*(?:CGPA|%|Percent|Score|Grade).*$', '', degree, flags=re.IGNORECASE).strip()
            degree = re.sub(r'\s*\b\d+(?:\.\d+)?%?\b', '', degree)
            degree = re.sub(r'\s+', ' ', degree).strip()
            
            education.append({
                "institution": institution,
                "degree": degree,
                "field": field,
                "end_year": end_year
            })
        i += 1
    return education


def calculate_years_experience(experience):
    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
    }
    
    def parse_month_year(date_str):
        if not date_str:
            return None
        date_str = date_str.lower().strip()
        if "present" in date_str or "current" in date_str:
            return 2026, 6  # standard local time anchor from metadata
        
        year_match = re.search(r'\b(20\d{2}|19\d{2})\b', date_str)
        if not year_match:
            return None
        year = int(year_match.group(1))
        
        for m_name, m_val in month_map.items():
            if m_name in date_str:
                return year, m_val
        
        num_match = re.search(r'\b(0?[1-9]|1[0-2])\b', date_str)
        if num_match:
            return year, int(num_match.group(1))
            
        return year, 1
        
    unique_months = set()
    for exp in experience:
        start_parsed = parse_month_year(exp.get("start"))
        end_parsed = parse_month_year(exp.get("end"))
        if start_parsed and end_parsed:
            sy, sm = start_parsed
            ey, em = end_parsed
            curr_y, curr_m = sy, sm
            while (curr_y < ey) or (curr_y == ey and curr_m <= em):
                unique_months.add((curr_y, curr_m))
                curr_m += 1
                if curr_m > 12:
                    curr_m = 1
                    curr_y += 1
    if unique_months:
        return round(len(unique_months) / 12, 2)
    return 0.0


def parse_resume(path):
    extension = os.path.splitext(path)[1].lower()
    source_name = f"resume_{extension[1:]}"

    if extension == ".docx":
        text = extract_docx(path)
    elif extension == ".pdf":
        text = extract_pdf(path)
    elif extension == ".txt":
        text = extract_txt(path)
    elif extension == ".json":
        text = extract_json(path)
    elif extension == ".md":
        text = extract_md(path)
    else:
        raise ValueError(f"Unsupported resume format: {extension}")

    # Section extraction
    sections = segment_sections(text)
    
    # Extract fields
    # 1. Name
    name = None
    header_lines = sections.get("HEADER", [])
    if header_lines:
        name = header_lines[0].strip()
        # Ensure it's not a list of sections or too long
        if len(name.split()) > 6 or name.isupper() and any(h in name for h in ["RESUME", "CURRICULUM"]):
            name = None

    # 2. Headline
    headline = None
    if header_lines and len(header_lines) > 1:
        headline = header_lines[1].strip()

    # 3. Emails & Phones
    emails = extract_emails(text)
    phones = extract_phones(text)
    
    # 4. Links
    links = extract_links(text)
    
    # 5. Location
    location = extract_location(text)
    
    # 6. Skills
    skills_lines = sections.get("TECHNICAL SKILLS", []) or sections.get("SKILLS", [])
    skills_raw = parse_skills_section(skills_lines)
    
    # If no skills section, fall back to keyword search in text
    if not skills_raw:
        common_skills = ["python", "java", "mysql", "html", "css", "git", "github", "javascript", "cloud computing", "oop", "docker"]
        for cs in common_skills:
            if re.search(rf'\b{cs}\b', text, re.IGNORECASE):
                skills_raw.append(cs.capitalize() if cs != "oop" else "OOP")
                
    skills = [
        {
            "name": s,
            "confidence": BASE_CONFIDENCE,
            "source": source_name
        }
        for s in skills_raw
    ]

    # 7. Experience
    exp_lines = (
        sections.get("INTERNSHIP EXPERIENCE", []) or 
        sections.get("WORK EXPERIENCE", []) or 
        sections.get("EXPERIENCE", []) or
        sections.get("INTERNSHIPS", [])
    )
    experience = parse_experience_section(exp_lines)
    
    # 8. Years of experience
    years_exp = calculate_years_experience(experience)

    # 9. Education
    edu_lines = sections.get("EDUCATION", [])
    education = parse_education_section(edu_lines)

    # Wrap in tagged format
    result = {}
    if name:
        result["full_name"] = tagged(name, BASE_CONFIDENCE, source_name)
    if emails:
        result["emails"] = tagged(emails, BASE_CONFIDENCE, source_name)
    if phones:
        result["phones"] = tagged(phones, BASE_CONFIDENCE, source_name)
    if location:
        result["location"] = tagged(location, BASE_CONFIDENCE, source_name)
    if any(links.values()):
        result["links"] = tagged(links, BASE_CONFIDENCE, source_name)
    if headline:
        result["headline"] = tagged(headline, BASE_CONFIDENCE, source_name)
    if years_exp > 0:
        result["years_experience"] = tagged(years_exp, BASE_CONFIDENCE, source_name)
    if skills:
        result["skills"] = skills
    if experience:
        result["experience"] = experience
    if education:
        result["education"] = education

    return result