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