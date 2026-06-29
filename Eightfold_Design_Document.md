# Multi-Source Candidate Data Transformer

**Author:** Kruthin Reddy  
**Assignment:** Eightfold Engineering Intern Assignment (Jul–Dec 2026)

---

## Problem Statement

Candidate information often exists across multiple heterogeneous sources such as ATS exports and resumes. These sources may contain duplicate, incomplete, or conflicting information.

The objective of this project is to ingest data from multiple sources, normalize and reconcile records, and generate a canonical candidate profile while preserving provenance and confidence information.

---

## Architecture

ATS JSON + Resume DOCX
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

---

## Components

### ATS Parser
Parses structured ATS JSON and maps source-specific fields into a canonical intermediate representation.

### Resume Parser
Extracts candidate information from DOCX resumes using document parsing and pattern matching.

### Normalizer
Standardizes:
- Email addresses
- Phone numbers (E.164)
- Skills

### Merge Engine
Combines records using:
- Confidence-based conflict resolution
- Duplicate elimination
- Agreement-based confidence boosting

### Validator
Ensures required candidate information is present before output generation.

### Projector
Generates configurable output schemas using runtime configuration files.

---

## Conflict Resolution Strategy

1. Select the highest-confidence value.
2. Preserve provenance metadata.
3. Increase confidence when multiple independent sources agree.

Example:

ATS: Python (0.85)

Resume: Python (0.75)

Final: Python (0.95)

---

## Output

The system generates a canonical candidate profile containing:

- Candidate ID
- Full Name
- Emails
- Skills
- Confidence Scores
- Provenance Metadata

---

## Design Principles

- Modular Architecture
- Configurable Processing
- Explainable Confidence Scoring
- Source Traceability
- Extensible Parser Framework

---

## Future Enhancements

- LinkedIn Profile Ingestion
- GitHub Profile Ingestion
- OCR-Based PDF Parsing
- ML-Based Confidence Calibration
- Advanced Entity Resolution
