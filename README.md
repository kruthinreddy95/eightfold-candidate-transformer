# Multi-Source Candidate Data Transformer

### Eightfold Engineering Intern Assignment

---

## Overview

This project implements a configurable candidate data transformation pipeline that ingests candidate information from multiple heterogeneous sources (such as ATS exports and Resume documents), normalizes formats, validates quality, reconciles conflicting information, and produces a projected candidate profile based on a runtime configuration file.

The engine features robust confidence-based conflict resolution, agreement-based confidence boosting, provenance tracking, and list/index-based custom projection schemas.

---

## Assignment Requirements Coverage

| Requirement | Status | Implemented Details |
|:---|:---:|:---|
| **Structured Source** | ✅ | ATS JSON parser with aliases & auto fallback mappings |
| **Unstructured Source** | ✅ | Resume parser (DOCX, PDF, TXT) with regex & heuristics |
| **Data Normalization** | ✅ | E.164 phone normalization, ISO ISO-3166-1 country codes, YYYY-MM dates |
| **Canonical Candidate Profile** | ✅ | Complete schema including Locations, Links, Education, Experience |
| **Provenance Tracking** | ✅ | Tracks source name and reconciliation method per resolved field |
| **Confidence Scoring** | ✅ | Resolves field values by confidence & averages overall confidence |
| **Agreement Boosting** | ✅ | Boosts skill confidences when independent sources agree |
| **Runtime Configuration** | ✅ | Dynamic JSONPath-like projections, type conversions, missing-value strategy |
| **Validation Layer** | ✅ | Canonical quality checks and projected output validation schema |
| **CLI Input/Output Surface**| ✅ | Argparse-based CLI supporting customizable sources and config paths |
| **Unit Tests** | ✅ | Pytest/unittest suite covering all parsing, merging, projecting logic |

---

## Technology Stack

- **Python 3**
- **python-docx** (DOCX structure extraction)
- **pdfplumber** (PDF text extraction)
- **phonenumbers** (E.164 format parsing)
- **pydantic** (Canonical schema model validation)

---

## Project Structure

```text
eightfold-assignment/
├── Eightfold_Design_Document.md    # Detailed system design
├── README.md                       # Execution guide & requirements coverage
├── configs/
│   ├── default.json                # Default projection configuration
│   ├── custom.json                 # Custom projection configuration
│   └── settings.json               # Pipeline confidence settings
├── data/
│   ├── ats.json                    # Sample structured ATS data
│   └── resume.docx                 # Sample unstructured resume
├── output/
│   ├── candidate_profile.json      # Output projected profile
│   ├── canonical_profile.json      # Raw intermediate canonical profile
│   └── validation_report.json      # Canonical profile validation status
├── src/
│   ├── main.py                     # CLI entrypoint
│   ├── merger.py                   # Conflict resolution & merge logic
│   ├── projector.py                # JSONPath-like projection & remapping
│   ├── validator.py                # Dual validation rules
│   ├── models/
│   │   └── schema.py               # Pydantic canonical models
│   ├── normalizers/
│   │   └── normalizer.py           # Field normalizations (dates, country, skills, etc.)
│   └── parsers/
│       ├── ats_parser.py           # Structured ATS JSON mapping
│       └── resume_parser.py        # Text & heuristic Resume entity extractor
└── tests/                          # Test suite
```

---

## Installation

Install the required dependencies:

```bash
pip3 install python-docx pdfplumber phonenumbers pydantic
```

---

## Running the Project

Run the pipeline using the default files:

```bash
python3 -m src.main
```

### CLI Arguments

You can customize the input files, configuration, and output location using flags:

```bash
python3 -m src.main --ats data/ats.json --resume data/resume.docx --config configs/custom.json --output output/candidate_profile_custom.json
```

- `--ats`: Path to ATS JSON file (default: `data/ats.json`)
- `--resume`: Path to Resume file (default: `data/resume.docx`)
- `--config`: Path to projection config JSON (default: `configs/default.json`)
- `--output`: Path to save the final projected profile (default: `output/candidate_profile.json`)

---

## Running Tests

To run the unit test suite:

```bash
python3 -m unittest discover -s tests
```

---

## Configuration Schema

The runtime projection config supports:
1. `fields`: An array of items specifying:
   - `path`: The key name in the output profile.
   - `from`: The path in the canonical model (e.g. `emails[0]`, `phones[0]`, `skills[].name`).
   - `type`: Target validator type (`string`, `string[]`, `number`, `object`).
   - `normalize`: Conversion normalizations (`E164`, `canonical`, `upper`, `lower`).
   - `required`: Strict check validation boolean.
2. `include_confidence`: Toggle inclusion of `overall_confidence`.
3. `include_provenance`: Toggle inclusion of the `provenance` log.
4. `on_missing`: Missing field strategy: `"null"`, `"omit"`, or `"error"`.
