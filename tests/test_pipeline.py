import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from src.pipeline import run_pipeline
from src.project import project
from src.normalize import normalize_phone, normalize_date, normalize_skill

CSV = "data/samples/recruiter_export.csv"
JSON_BLOB = "data/samples/ats_blob.json"
RESUMES = [
    "data/samples/resume_C001.pdf",
    "data/samples/resume_C004.pdf",
    "data/samples/resume_C005_garbage.pdf",
]


def test_determinism():
    """Same inputs run twice must produce identical output."""
    run1 = run_pipeline(csv_path=CSV, json_path=JSON_BLOB, resume_paths=RESUMES)
    run2 = run_pipeline(csv_path=CSV, json_path=JSON_BLOB, resume_paths=RESUMES)
    assert json.dumps(run1, sort_keys=True) == json.dumps(run2, sort_keys=True)


def test_garbage_resume_does_not_crash():
    """A garbage/unparseable resume must degrade gracefully, not raise."""
    results = run_pipeline(resume_paths=["data/samples/resume_C005_garbage.pdf"])
    assert len(results) == 1
    candidate = results[0]
    assert candidate["full_name"] is None
    assert candidate["overall_confidence"] == 0.0


def test_agreement_yields_higher_confidence_than_conflict():
    results = run_pipeline(csv_path=CSV, json_path=JSON_BLOB, resume_paths=RESUMES)
    by_id = {r["candidate_id"]: r for r in results}

    c001_phone_prov = [p for p in by_id["C001"]["provenance"] if p["field"] == "phone"]
    assert all(p["method"] == "agreement" for p in c001_phone_prov)

    c003_email_prov = [p for p in by_id["C003"]["provenance"] if p["field"] == "email"]
    assert c003_email_prov[0]["method"] == "conflict-resolved"
    assert "rejected_values" in c003_email_prov[0]


def test_missing_field_is_null_not_invented():
    results = run_pipeline(csv_path=CSV, json_path=JSON_BLOB, resume_paths=RESUMES)
    by_id = {r["candidate_id"]: r for r in results}
    assert by_id["C004"]["company"] is None


def test_phone_format_difference_resolves_to_agreement():
    results = run_pipeline(csv_path=CSV, json_path=JSON_BLOB)
    by_id = {r["candidate_id"]: r for r in results}
    c002_phone_prov = [p for p in by_id["C002"]["provenance"] if p["field"] == "phone"]
    assert all(p["method"] == "agreement" for p in c002_phone_prov)


def test_custom_config_projection_matches_assignment_example():
    results = run_pipeline(csv_path=CSV, json_path=JSON_BLOB, resume_paths=RESUMES)
    c001 = next(r for r in results if r["candidate_id"] == "C001")
    config = json.load(open("configs/example_config.json"))
    shaped = project(c001, config)

    assert shaped["primary_email"] == "asha.menon@gmail.com"
    assert shaped["phone"].startswith("+91")
    assert isinstance(shaped["skills"], list)
    assert "Python" in shaped["skills"]


def test_normalize_phone_e164():
    assert normalize_phone("9876543210") == "+919876543210"
    assert normalize_phone("") is None


def test_normalize_skill_aliases():
    assert normalize_skill("JS") == "JavaScript"
    assert normalize_skill("ReactJS") == "React"
    assert normalize_skill("SomeUnknownSkill") == "SomeUnknownSkill"                              


def test_location_and_experience_and_education_merging():
    results = run_pipeline(csv_path=CSV, json_path=JSON_BLOB, resume_paths=RESUMES)
    by_id = {r["candidate_id"]: r for r in results}

    c001 = by_id["C001"]
    assert c001["location"] == {
        "city": "Bengaluru",
        "region": None,
        "country": "IN"
    }

    assert len(c001["experience"]) == 1
    exp = c001["experience"][0]
    assert exp["company"] == "TechNova Private Limited"
    assert exp["title"] == "Backend Software Engineer"
    assert exp["start"] == "2022-01"
    assert exp["end"] == "present"
    assert "REST APIs" in exp["summary"]

    assert c001["years_experience"] == 4.5

    assert len(c001["education"]) == 1
    edu = c001["education"][0]
    assert edu["institution"] == "Anna University"
    assert edu["degree"] == "B.E."
    assert edu["field"] == "Computer Science"
    assert edu["end_year"] == "2022"
