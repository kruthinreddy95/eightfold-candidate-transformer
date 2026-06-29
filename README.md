# Multi-Source Candidate Data Transformer

### Eightfold Engineering Intern Assignment

---

## Overview

This project implements a configurable candidate data transformation pipeline that ingests candidate information from multiple heterogeneous sources, normalizes, validates, reconciles conflicting information, and produces a canonical candidate profile.

The system demonstrates real-world data engineering concepts including multi-source ingestion, data normalization, confidence-based conflict resolution, provenance tracking, configurable output projection, and validation.

---

## Assignment Requirements Coverage

| Requirement | Status |
|------------|---------|
| Structured Source | ✅ ATS JSON |
| Unstructured Source | ✅ Resume DOCX |
| Canonical Candidate Profile | ✅ |
| Data Normalization | ✅ |
| Provenance Tracking | ✅ |
| Confidence Scoring | ✅ |
| Runtime Configuration | ✅ |
| Validation | ✅ |

---

## Supported Sources

### Structured Source
#### ATS JSON

```json
{
  "candidate_name": "Kruthin Reddy",
  "mail": "kruthin@gmail.com",
  "mobile": "+91 9876543210",
  "skills": ["Python", "SQL", "Git"]
}
```

### Unstructured Source
#### Resume Document (DOCX)

The parser extracts:
- Candidate Name
- Email Address
- Phone Number
- Skills

---

## Technology Stack

- Python 3
- JSON
- python-docx
- phonenumbers
- Regular Expressions (Regex)

---

## Pipeline Flow

```text
ATS JSON
     +
Resume DOCX
     ↓
Parsers
     ↓
Normalization
     ↓
Merge Engine
     ↓
Validation
     ↓
Projection
     ↓
Canonical Candidate Profile
```

---

## Features

- ATS JSON Parsing
- Resume DOCX Parsing
- Phone Normalization (E.164)
- Skill Standardization
- Confidence-Based Conflict Resolution
- Candidate ID Generation
- Provenance Tracking
- Configurable Output Projection

---

## Project Structure

```text
eightfold-assignment/
├── README.md
├── Eightfold_Design_Document.md
├── configs/
├── data/
├── output/
├── src/
└── tests/
```

---

## Installation

```bash
pip3 install python-docx
pip3 install phonenumbers
pip3 install pydantic
pip3 install pdfplumber
```

---

## Running The Project

```bash
python3 src/main.py
```

---

## Sample Output

```json
{
  "candidate_id": "8f4e76e1359002c69d634f7eaaa028a8",
  "full_name": "Kruthin Reddy",
  "overall_confidence": 0.81
}
```

---

## Design Decisions

1. Canonical intermediate representation.
2. Confidence-based conflict resolution.
3. Agreement-based confidence boosting.
4. Provenance tracking.
5. Configurable output projection.

---

## Future Improvements

- LinkedIn Profile Ingestion
- GitHub Profile Ingestion
- OCR-Based PDF Parsing
- Machine Learning Confidence Calibration

---

## Author

Kruthin Reddy

Eightfold Engineering Intern Assignment
