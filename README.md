# Multi-Source Candidate Data Transformer

Eightfold Engineering Intern Assignment — Asvitha B

## What this does

Ingests candidate data from multiple messy, conflicting sources (recruiter CSV, ATS JSON, resume PDF) and merges it into one clean canonical profile per candidate — with every field traced back to its source and scored by confidence. Missing data is left `null`, never invented. Conflicting data is resolved by source trust, logged transparently in `provenance`.

## Pipeline

`detect → extract → normalize → merge → project → validate`

- **extract**: per-source parsers (`src/extract/`) convert CSV rows, ATS JSON entries, and resume PDF text into a common raw-fields shape.
- **normalize**: dates → `YYYY-MM`, phones → E.164, skills → canonical names (`src/normalize.py`).
- **merge**: trust-weighted conflict resolution + confidence scoring + provenance (`src/merge.py`).
- **project**: applies a runtime config to reshape the canonical record into a custom output, fully decoupled from merge logic (`src/project.py`).
- **validate**: schema-checks output before returning (`src/schema.py`).

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Run (CLI)

Default schema:
```bash
python -m src.cli --csv data/samples/recruiter_export.csv --json data/samples/ats_blob.json --resume data/samples/resume_C001.pdf --resume data/samples/resume_C004.pdf --resume data/samples/resume_C005_garbage.pdf --out output_default.json
```

Custom config:
```bash
python -m src.cli --csv data/samples/recruiter_export.csv --json data/samples/ats_blob.json --resume data/samples/resume_C001.pdf --config configs/example_config.json --out output_custom.json
```

## Run tests
```bash
pytest tests/ -v
```

## Design decisions

- **Trust weighting**: structured sources (CSV/ATS) are trusted highest for identity/contact fields; resume is trusted highest for skills, since it's the candidate's own self-reported detail.
- **Conflict resolution**: values are normalized before comparison (e.g. phone formats), so genuinely identical values across sources are never flagged as false conflicts. Real disagreements pick the highest-trust source, cap confidence lower, and log all rejected values in provenance.
- **Config/projection layer**: built as a generic engine driven by path strings and a normalizer registry, so new configs work without touching merge logic — verified against the assignment's own example config.

## Known limitation (left in deliberately)

For candidate C004, the merge picks `full_name = "Vikram"` (from the CSV, a higher-trust source) over `"Vikram Raghavan"` (from the resume, lower-trust but more complete). The current policy resolves conflicts purely by source trust, not by value completeness. A more sophisticated version could prefer the most complete value when trust is close — left out of scope under time pressure, but the tradeoff is intentional and documented here rather than hidden.

## Explicitly descoped

Cross-candidate identity resolution (e.g. determining a resume with no ID belongs to "C004" when names differ across sources) is out of scope. The pipeline assumes resumes are pre-linked to a candidate via filename convention (`resume_<candidate_id>.pdf`).

## Sample data

`data/samples/` contains 5 candidates with deliberately built-in conflicts: format differences, genuine field conflicts, missing fields, a candidate present in only one source, and one fully garbage/unparseable resume to test robustness.

output

(venv) C:\Users\asvit\OneDrive\eightfold-candidate-transformer>python -m src.cli --csv data\samples\recruiter_export.csv --json data\samples\ats_blob.json --resume data\samples\resume_C001.pdf --config configs\example_config.json --out output_custom.json 

Candidate: C001
{
  "full_name": "Asha S. Menon",
  "primary_email": "asha.menon@gmail.com",
  "phone": "+919876543210",
  "skills": [
    "Python",
    "Django",
    "PostgreSQL",
    "Docker",
    "AWS"
  ],
  "overall_confidence": 0.83,
  "provenance": [
    {
      "field": "full_name",
      "source": "ats_blob.json:candidates[0]",
      "method": "conflict-resolved",
      "rejected_values": [
        "Asha Menon",
        "Asha Menon"
      ]
    },
    {
      "field": "email",
      "source": "recruiter_export.csv:row2",
      "method": "agreement"
    },
    {
      "field": "email",
      "source": "ats_blob.json:candidates[0]",
      "method": "agreement"
    },
    {
      "field": "email",
      "source": "resume_C001.pdf",
      "method": "agreement"
    },
    {
      "field": "phone",
      "source": "recruiter_export.csv:row2",
      "method": "agreement"
    },
    {
      "field": "phone",
      "source": "ats_blob.json:candidates[0]",
      "method": "agreement"
    },
    {
      "field": "phone",
      "source": "resume_C001.pdf",
      "method": "agreement"
    },
    {
      "field": "location.city",
      "source": "ats_blob.json:candidates[0]",
      "method": "agreement"
    },
    {
      "field": "location.city",
      "source": "resume_C001.pdf",
      "method": "agreement"
    },
    {
      "field": "location.country",
      "source": "ats_blob.json:candidates[0]",
      "method": "agreement"
    },
    {
      "field": "location.country",
      "source": "resume_C001.pdf",
      "method": "agreement"
    },
    {
      "field": "headline",
      "source": "ats_blob.json:candidates[0]",
      "method": "conflict-resolved",
      "rejected_values": [
        "Backend Engineer"
      ]
    },
    {
      "field": "company",
      "source": "recruiter_export.csv:row2",
      "method": "agreement"
    },
    {
      "field": "company",
      "source": "ats_blob.json:candidates[0]",
      "method": "agreement"
    },
    {
      "field": "title",
      "source": "ats_blob.json:candidates[0]",
      "method": "conflict-resolved",
      "rejected_values": [
        "Backend Engineer"
      ]
    },
    {
      "field": "experience.company",
      "source": "ats_blob.json:candidates[0]",
      "method": "conflict-resolved",
      "rejected_values": [
        "TechNova Pvt Ltd",
        "TechNova Pvt Ltd"
      ]
    },
    {
      "field": "experience.title",
      "source": "ats_blob.json:candidates[0]",
      "method": "conflict-resolved",
      "rejected_values": [
        "Backend Engineer",
        "Backend Software Engineer"
      ]
    },
    {
      "field": "experience.start",
      "source": "resume_C001.pdf",
      "method": "single-source"
    },
    {
      "field": "experience.end",
      "source": "resume_C001.pdf",
      "method": "single-source"
    },
    {
      "field": "experience.summary",
      "source": "resume_C001.pdf",
      "method": "single-source"
    },
    {
      "field": "education.institution",
      "source": "resume_C001.pdf",
      "method": "single-source"
    },
    {
      "field": "education.degree",
      "source": "resume_C001.pdf",
      "method": "single-source"
    },
    {
      "field": "education.field",
      "source": "resume_C001.pdf",
      "method": "single-source"
    },
    {
      "field": "education.end_year",
      "source": "resume_C001.pdf",
      "method": "single-source"
    }
  ]
}

Candidate: C002
{
  "full_name": "Rohan K Iyer",
  "primary_email": "rohan.k.iyer@gmail.com",
  "phone": "+919876512345",
  "skills": [
    "SQL",
    "Excel",
    "Power BI"
  ],
  "overall_confidence": 0.71,
  "provenance": [
    {
      "field": "full_name",
      "source": "recruiter_export.csv:row3",
      "method": "conflict-resolved",
      "rejected_values": [
        "Rohan Iyer"
      ]
    },
    {
      "field": "email",
      "source": "ats_blob.json:candidates[1]",
      "method": "conflict-resolved",
      "rejected_values": [
        "rohan.iyer@yahoo.com"
      ]
    },
    {
      "field": "phone",
      "source": "recruiter_export.csv:row3",
      "method": "agreement"
    },
    {
      "field": "phone",
      "source": "ats_blob.json:candidates[1]",
      "method": "agreement"
    },
    {
      "field": "location.city",
      "source": "ats_blob.json:candidates[1]",
      "method": "single-source"
    },
    {
      "field": "location.country",
      "source": "ats_blob.json:candidates[1]",
      "method": "single-source"
    },
    {
      "field": "headline",
      "source": "ats_blob.json:candidates[1]",
      "method": "conflict-resolved",
      "rejected_values": [
        "Data Analyst"
      ]
    },
    {
      "field": "company",
      "source": "recruiter_export.csv:row3",
      "method": "agreement"
    },
    {
      "field": "company",
      "source": "ats_blob.json:candidates[1]",
      "method": "agreement"
    },
    {
      "field": "title",
      "source": "ats_blob.json:candidates[1]",
      "method": "conflict-resolved",
      "rejected_values": [
        "Data Analyst"
      ]
    },
    {
      "field": "experience.company",
      "source": "ats_blob.json:candidates[1]",
      "method": "conflict-resolved",
      "rejected_values": [
        "DataForge Inc"
      ]
    },
    {
      "field": "experience.title",
      "source": "ats_blob.json:candidates[1]",
      "method": "conflict-resolved",
      "rejected_values": [
        "Data Analyst"
      ]
    }
  ]
}

Candidate: C003
{
  "full_name": "Priya Sundaram",
  "primary_email": "priya.sundaram@gmail.com",
  "phone": "+919123456780",
  "skills": [
    "JavaScript",
    "React"
  ],
  "overall_confidence": 0.73,
  "provenance": [
    {
      "field": "full_name",
      "source": "ats_blob.json:candidates[2]",
      "method": "conflict-resolved",
      "rejected_values": [
        "Priya S"
      ]
    },
    {
      "field": "email",
      "source": "ats_blob.json:candidates[2]",
      "method": "conflict-resolved",
      "rejected_values": [
        "p.s@outlook.com"
      ]
    },
    {
      "field": "phone",
      "source": "ats_blob.json:candidates[2]",
      "method": "single-source"
    },
    {
      "field": "location.city",
      "source": "ats_blob.json:candidates[2]",
      "method": "single-source"
    },
    {
      "field": "location.country",
      "source": "ats_blob.json:candidates[2]",
      "method": "single-source"
    },
    {
      "field": "headline",
      "source": "recruiter_export.csv:row4",
      "method": "agreement"
    },
    {
      "field": "headline",
      "source": "ats_blob.json:candidates[2]",
      "method": "agreement"
    },
    {
      "field": "company",
      "source": "ats_blob.json:candidates[2]",
      "method": "conflict-resolved",
      "rejected_values": [
        "QuantumSoft"
      ]
    },
    {
      "field": "title",
      "source": "recruiter_export.csv:row4",
      "method": "agreement"
    },
    {
      "field": "title",
      "source": "ats_blob.json:candidates[2]",
      "method": "agreement"
    },
    {
      "field": "experience.company",
      "source": "recruiter_export.csv:row4",
      "method": "single-source"
    },
    {
      "field": "experience.title",
      "source": "recruiter_export.csv:row4",
      "method": "single-source"
    },
    {
      "field": "experience.company",
      "source": "ats_blob.json:candidates[2]",
      "method": "single-source"
    },
    {
      "field": "experience.title",
      "source": "ats_blob.json:candidates[2]",
      "method": "single-source"
    }
  ]
}

Output written to output_custom.json

(venv) C:\Users\asvit\OneDrive\eightfold-candidate-transformer>pytest tests\ -v
================ test session starts =================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\asvit\OneDrive\eightfold-candidate-transformer\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\asvit\OneDrive\eightfold-candidate-transformer
collected 9 items                                     

tests/test_pipeline.py::test_determinism PASSED [ 11%]
tests/test_pipeline.py::test_garbage_resume_does_not_crash PASSED [ 22%]
tests/test_pipeline.py::test_agreement_yields_higher_confidence_than_conflict PASSED [ 33%]
tests/test_pipeline.py::test_missing_field_is_null_not_invented PASSED [ 44%]
tests/test_pipeline.py::test_phone_format_difference_resolves_to_agreement PASSED [ 55%]
tests/test_pipeline.py::test_custom_config_projection_matches_assignment_example PASSED [ 66%]
tests/test_pipeline.py::test_normalize_phone_e164 PASSED [ 77%]
tests/test_pipeline.py::test_normalize_skill_aliases PASSED [ 88%]
tests/test_pipeline.py::test_location_and_experience_and_education_merging PASSED [100%]

================= 9 passed in 0.76s ================== 

(venv) C:\Users\asvit\OneDrive\eightfold-candidate-transformer>