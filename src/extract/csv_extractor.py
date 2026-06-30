"""
extract/csv_extractor.py
Extracts candidates from a recruiter CSV export.
"""

import csv
from pathlib import Path

from .base import RawCandidateFields

                                                                   
                                                                   
                                                                
COLUMN_MAP = {
    "candidate_id": "candidate_id",
    "name": "full_name",
    "email": "email",
    "phone": "phone",
    "current_company": "company",
    "title": "title",
}


def extract_csv(path: str) -> list:
    """
    Reads a recruiter CSV and returns one RawCandidateFields per row.
    Never raises on a malformed row -- the row is still included with
    a parse_error noted, so one bad row can't crash a batch.
    """
    file_path = Path(path)
    results = []

    with file_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_number, row in enumerate(reader, start=2):                   
            source_id = f"{file_path.name}:row{row_number}"
            record = RawCandidateFields(
                source_type="recruiter_csv",
                source_id=source_id,
                candidate_key=row.get("candidate_id") or None,
            )
            for csv_col, raw_field_name in COLUMN_MAP.items():
                value = row.get(csv_col, "")
                value = value.strip() if isinstance(value, str) else value
                if value:                                                 
                    record.fields[raw_field_name] = value
            
                                                                     
            current_company = row.get("current_company")
            title = row.get("title")
            if current_company or title:
                record.fields["experience_entries"] = [{
                    "company": current_company,
                    "title": title,
                    "start": None,
                    "end": None,
                    "summary": None,
                }]

            if not record.candidate_key:
                record.parse_errors.append("missing candidate_id in CSV row")
            results.append(record)

    return results