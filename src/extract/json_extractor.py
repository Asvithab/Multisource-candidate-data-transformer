"""
extract/json_extractor.py
Extracts candidates from an ATS JSON blob, whose field names do NOT
match our canonical names -- that's the whole point of this source type.
"""

import json
from pathlib import Path

from .base import RawCandidateFields

                                                                     
                                                                      
                     
FIELD_MAP = {
    "full_name": "full_name",
    "primary_email": "email",
    "contact_number": "phone",
    "employer": "company",
    "designation": "title",
    "city": "city",
    "country_name": "country",
    "skills_list": "skills",
}


def extract_json(path: str) -> list:
    """
    Reads an ATS JSON export and returns one RawCandidateFields per
    candidate entry. Degrades gracefully: a malformed top-level file
    returns a single error record rather than crashing, and an
    individual malformed entry is still included with an error noted
    rather than dropped silently.
    """
    file_path = Path(path)
    results = []

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        results.append(
            RawCandidateFields(
                source_type="ats_json",
                source_id=file_path.name,
                candidate_key=None,
                parse_errors=[f"failed to parse ATS file: {e}"],
            )
        )
        return results

    entries = data.get("candidates", []) if isinstance(data, dict) else []

    for index, entry in enumerate(entries):
        source_id = f"{file_path.name}:candidates[{index}]"
        record = RawCandidateFields(
            source_type="ats_json",
            source_id=source_id,
            candidate_key=entry.get("id") or None,
        )
        for ats_key, raw_field_name in FIELD_MAP.items():
            value = entry.get(ats_key)
            if value not in (None, "", []):
                record.fields[raw_field_name] = value
        
                                                                 
        employer = entry.get("employer")
        designation = entry.get("designation")
        if employer or designation:
            record.fields["experience_entries"] = [{
                "company": employer,
                "title": designation,
                "start": None,
                "end": None,
                "summary": None,
            }]

        if not record.candidate_key:
            record.parse_errors.append("missing id in ATS entry")
        results.append(record)

    return results