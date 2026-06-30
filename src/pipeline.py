from collections import defaultdict
from .extract.csv_extractor import extract_csv
from .extract.json_extractor import extract_json
from .extract.resume_extractor import extract_resume
from .merge import merge_candidate
from .schema import validate_output


def run_pipeline(csv_path: str = None, json_path: str = None, resume_paths: list = None) -> list:
    resume_paths = resume_paths or []
    all_records = []

    if csv_path:
        all_records.extend(extract_csv(csv_path))
    if json_path:
        all_records.extend(extract_json(json_path))
    for path in resume_paths:
        all_records.append(extract_resume(path))

    grouped = defaultdict(list)
    for record in all_records:
        key = record.candidate_key or f"UNLINKED::{record.source_id}"
        grouped[key].append(record)

    results = []
    for candidate_key, records in grouped.items():
        canonical = merge_candidate(records)

                                                                        
        canonical.setdefault("company", None)
        canonical.setdefault("headline", None)
        canonical.setdefault("years_experience", None)
        canonical.setdefault("skills", [])
        canonical.setdefault("experience", [])
        canonical.setdefault("education", [])
        canonical.setdefault("emails", [])
        canonical.setdefault("phones", [])
        canonical.setdefault("location", None)
        canonical.setdefault("links", None)

        errors = validate_output(canonical, None)
        canonical["_validation_errors"] = errors

        results.append(canonical)

    return results