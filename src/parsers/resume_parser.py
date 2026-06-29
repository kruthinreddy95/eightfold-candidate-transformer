from docx import Document
import re

SOURCE = "resume_docx"
BASE_CONFIDENCE = 0.75


def tagged(value, confidence=BASE_CONFIDENCE):
    return {
        "value": value,
        "confidence": confidence,
        "source": SOURCE
    }


def extract_text(docx_path):

    doc = Document(docx_path)

    lines = []

    for para in doc.paragraphs:
        if para.text.strip():
            lines.append(para.text.strip())

    return "\n".join(lines)


def parse_resume(docx_path):

    text = extract_text(docx_path)

    result = {}

    # Name
    first_line = text.split("\n")[0]
    result["full_name"] = tagged(first_line, 0.80)

    # Email
    emails = re.findall(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        text
    )

    if emails:
        result["emails"] = tagged(
            list(set(emails))
        )

    # Phone
    phones = re.findall(
        r'\+91\s?\d{10}|\d{10}',
        text
    )

    if phones:
        result["phones"] = tagged(
            list(set(phones))
        )

    # Skills
    catalog = [
        "Python",
        "Java",
        "MySQL",
        "Git",
        "GitHub",
        "HTML",
        "CSS"
    ]

    skills = []

    for skill in catalog:

        if skill.lower() in text.lower():

            skills.append({
                "name": skill,
                "confidence": BASE_CONFIDENCE,
                "source": SOURCE
            })

    result["skills"] = skills

    return result